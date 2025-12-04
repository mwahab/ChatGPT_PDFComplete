# ChatGPT PDF Complete

A minimal Flask web app that pairs a user prompt with a PDF form, asks ChatGPT for field values, and returns a filled copy of the PDF for download. The app extracts form field names and PDF text to give the model context, then writes the returned JSON into the form fields.

## Getting started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key (optional – without it the app uses local placeholders):
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
3. Run the server:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000 and upload a PDF form along with your prompt to download a filled copy.

## Notes
- If `OPENAI_API_KEY` is not provided, the app still returns a filled PDF using the supplied prompt as placeholder data.
- The generated PDF is held in memory and streamed back to the browser; nothing is stored permanently on disk.

## Troubleshooting
- **`pip install -r requirements.txt` fails with `ProxyError` or `403 Forbidden`:**
  - Verify your proxy variables are set (for example `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`) and match your network's requirements.
  - If your organization mirrors PyPI, point pip directly at it:
    ```bash
    pip install --index-url https://your.mirror/simple --trusted-host your.mirror -r requirements.txt
    ```
 - When outbound HTTPS is blocked entirely, download the wheels from a reachable network and install locally:
    ```bash
    pip install --no-index --find-links /path/to/offline-wheels -r requirements.txt
    ```

- **Uploads are limited to 16 MB:** Larger PDFs are rejected to protect the server. Reduce file size before retrying.

## How to test the site locally
1. Install dependencies and export your `OPENAI_API_KEY` as described above.
2. Start the app locally:
   ```bash
   python app.py
   ```
3. In your browser, open http://localhost:5000.
4. Upload a PDF form and enter a natural-language prompt describing how to fill it. Submit the form.
5. Verify the download starts automatically and that the returned PDF contains filled fields based on your prompt. If you run without an API key, the placeholders will reflect the prompt text so you can still confirm the flow works.
