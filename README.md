# Prompt to 3D Model

This Flask app turns a short text description into a printable 3D starter mesh. The mesh is generated procedurally with [trimesh](https://trimsh.org/), previewed in a Three.js viewer, and can be downloaded as an STL for further editing.

## Running locally

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the development server:
   ```bash
   python app.py
   ```
3. Open http://localhost:4000 in your browser.

## How model generation works

* The prompt is scanned for shape keywords (box, sphere, cylinder, cone, torus) and any numbers that look like dimensions.
* If no dimensions are provided, sensible defaults are used. Numbers are mapped to relevant parameters such as width/height/depth for boxes or radius/height for cylinders.
* The mesh is built with trimesh and exported to STL directly in memory, then streamed to the browser for preview and download.

## Notes

* File uploads are not required. Only text prompts are accepted.
* Everything runs locally without external API calls.
