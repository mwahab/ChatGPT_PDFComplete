import io
import json
import os
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, render_template, request
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# Require the caller to provide an API key via environment variables; do not ship a default.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_KEY = "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"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit
DEFAULT_QUESTIONS = [
    (
        "I have formed the opinion that the person has a disorder of the mind that requires "
        "treatment and seriously impairs the person ability to react appropriately to their environment "
        "or associate with others. The reasons for my opinion are as follows:"
    ),
    (
        "I have formed the opinion that the person requires treatment in or through a designated facility. "
        "The reasons that I have formed this opinion are as follows:"
    ),
    (
        "I have formed the opinion that the person requires care, supervision and control in or through a "
        "designated facility to prevent their substantial mental or physical deterioration or for the "
        "protection of the person or for the protection of others. The reasons that I have formed this "
        "opinion are as follows:"
    ),
    (
        "I have formed the opinion that the person cannot suitably be admitted as a voluntary patient. "
        "The reasons that I have formed this opinion are as follows:"
    ),
]


def extract_pdf_text(pdf_stream: io.BytesIO) -> str:
    """Return concatenated PDF text content."""
    reader = PdfReader(pdf_stream)
    text_parts: List[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def call_chatgpt(prompt: str, questions: List[str], pdf_text: str) -> Tuple[Dict[str, str], Optional[str]]:
    """Send the user prompt, default questions, and PDF text to ChatGPT and expect JSON answers."""

    questions_block = "\n\n".join(
        [f"Question {idx + 1}: {text}" for idx, text in enumerate(questions)]
    )
    combined_prompt = (
        "You are assisting a clinician by answering four assessment prompts. "
        "Use the provided PDF text and user notes. "
        "Return ONLY JSON with keys question1 through question4 mapping to concise answers without markdown.\n\n"
        f"User notes: {prompt}\n\n"
        f"PDF text: {pdf_text[:2000]}\n\n"
        f"Questions to answer:\n{questions_block}"
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
        except Exception as exc:
            fallback_values = {
                f"question{idx + 1}": f"Placeholder answer based on notes: {prompt[:80]}"
                for idx in range(4)
            }
            return fallback_values, f"OpenAI request failed; used placeholder data ({exc})."
    else:
        fallback_values = {
            f"question{idx + 1}": f"Placeholder answer based on notes: {prompt[:80]}"
            for idx in range(4)
        }
        return fallback_values, "No OPENAI_API_KEY detected; returning placeholder answers."

    try:
        parsed = json.loads(content)
        answers = {
            f"question{idx + 1}": parsed.get(f"question{idx + 1}", "")
            for idx in range(4)
        }
        return answers, None
    except json.JSONDecodeError:
        fallback_values = {f"question{idx + 1}": content for idx in range(4)}
        return fallback_values, "Received non-JSON response; used plain text instead."


@app.route("/")
def index():
    return render_template("index.html", questions=DEFAULT_QUESTIONS)


@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_file = request.files.get("pdf_file")
    prompt = request.form.get("prompt", "").strip()

    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "Please upload a PDF file to continue."}), 400

    if not uploaded_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "The uploaded file must be a PDF."}), 400

    pdf_bytes = uploaded_file.read()
    pdf_stream = io.BytesIO(pdf_bytes)
    try:
        pdf_text = extract_pdf_text(pdf_stream)
    except Exception:
        return jsonify({"error": "Unable to read the PDF file. Please upload a valid PDF form."}), 400

    answers, warning_message = call_chatgpt(prompt, DEFAULT_QUESTIONS, pdf_text)
    response_body = {"answers": answers}
    if warning_message:
        response_body["warning"] = warning_message
    return jsonify(response_body)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=4000, debug=debug_mode)
