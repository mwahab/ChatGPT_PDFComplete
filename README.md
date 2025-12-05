# ChatGPT PDF Complete

A minimal Flask web app that pairs a user prompt with a PDF and asks ChatGPT to answer four clinical assessment questions. The app reads PDF text plus your notes, sends them with the pre-set questions, and displays the answers in a popup for quick review.


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
4. Open http://localhost:4000 and upload a PDF along with your notes to receive the four answers in the popup.

## Notes
- If `OPENAI_API_KEY` is not provided, the app still returns placeholder answers using the supplied notes.
- PDF content is read in memory for context only; nothing is stored permanently on disk.

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
3. In your browser, open http://localhost:4000.
4. Upload a PDF and enter any notes you want ChatGPT to consider. Submit the form.
5. Confirm a popup appears showing answers to the four questions. If you run without an API key, the placeholders will still display so you can verify the flow.
