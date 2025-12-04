import io
import json
import os
from typing import Dict, List, Optional, Tuple

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from openai import OpenAI
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv

load_dotenv()

# Require the caller to provide an API key via environment variables; do not ship a default.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit


def extract_pdf_text_and_fields(pdf_stream: io.BytesIO) -> Tuple[str, List[str]]:
    """Return concatenated PDF text content and a list of form field names."""
    reader = PdfReader(pdf_stream)
    text_parts: List[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    fields = reader.get_fields() or {}
    return "\n".join(text_parts), list(fields.keys())


def call_chatgpt(prompt: str, field_names: List[str], pdf_text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Send a structured prompt to ChatGPT and expect a JSON object for field values.

    Returns a tuple of (field_values, warning_message).
    """
    instruction = (
        "You are filling a PDF form for the user. "
        "Return ONLY JSON mapping PDF form field names to their values without markdown."
    )
    field_hint = ", ".join(field_names) if field_names else "field1, field2"
    combined_prompt = (
        f"{instruction}\n\n"
        f"PDF field names: {field_hint}\n"
        f"User prompt: {prompt}\n"
        f"Optional PDF text for context: {pdf_text[:2000]}"
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    api_key_present = bool(OPENAI_API_KEY)

    if api_key_present:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": combined_prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content
        except Exception as exc:  # openai raises rich subclasses; catching all keeps UX smooth
            fallback_values = {
                name: f"{prompt[:40]}" if prompt else f"Sample value for {name}"
                for name in (field_names or ["notes"])
            }
            return fallback_values, f"OpenAI request failed; used placeholder data ({exc})."
    else:
        fallback_values = {
            name: f"{prompt[:40]}" if prompt else f"Sample value for {name}"
            for name in (field_names or ["notes"])
        }
        return fallback_values, "No OPENAI_API_KEY detected; returning placeholder values."

    try:
        return json.loads(content), None
    except json.JSONDecodeError:
        return {name: content for name in field_names}, "Received non-JSON response; used plain text instead."


def fill_pdf_fields(original_pdf: io.BytesIO, field_values: Dict[str, str]) -> io.BytesIO:
    """Fill a PDF with the provided field values and return an in-memory stream."""
    reader = PdfReader(original_pdf)
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)

    for page in reader.pages:
        writer.add_page(page)

    if writer._root_object.get("/AcroForm"):
        writer._root_object["/AcroForm"].update({"/NeedAppearances": True})

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return output_stream


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("pdf_file")
        prompt = request.form.get("prompt", "").strip()

        if not uploaded_file or uploaded_file.filename == "":
            flash("Please upload a PDF file to continue.")
            return redirect(url_for("index"))

        if not uploaded_file.filename.lower().endswith(".pdf"):
            flash("The uploaded file must be a PDF.")
            return redirect(url_for("index"))

        pdf_bytes = uploaded_file.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        pdf_text, field_names = extract_pdf_text_and_fields(pdf_stream)
        pdf_stream.seek(0)

        field_values, warning_message = call_chatgpt(prompt, field_names, pdf_text)
        filled_pdf_stream = fill_pdf_fields(io.BytesIO(pdf_bytes), field_values)

        if warning_message:
            flash(warning_message)

        download_name = uploaded_file.filename.rsplit(".pdf", 1)[0] + "-filled.pdf"
        return send_file(
            filled_pdf_stream,
            as_attachment=True,
            download_name=download_name,
            mimetype="application/pdf",
        )

    return render_template("index.html")


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
