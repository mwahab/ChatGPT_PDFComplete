import base64
import io
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import trimesh
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit


@dataclass
class MeshDescription:
    name: str
    details: str
    shape: str
    dimensions: Dict[str, float]


SHAPE_KEYWORDS: Dict[str, List[str]] = {
    "box": ["box", "cube", "rectangle", "rectangular"],
    "sphere": ["sphere", "ball", "orb"],
    "cylinder": ["cylinder", "tube", "pipe"],
    "cone": ["cone", "pyramid"],
    "torus": ["torus", "donut", "doughnut", "ring"],
}


DEFAULT_DIMENSIONS = {
    "box": {"width": 1.0, "height": 1.0, "depth": 1.0},
    "sphere": {"radius": 0.65},
    "cylinder": {"radius": 0.4, "height": 1.2},
    "cone": {"radius": 0.6, "height": 1.2},
    "torus": {"radius": 0.65, "tube_radius": 0.22},
}


SAMPLE_PROMPTS = [
    "A sturdy cube-shaped planter with slightly taller height than width",
    "A sleek cylindrical pencil holder with a wide opening",
    "A hollow torus ring that could serve as a napkin holder",
]


FLOAT_PATTERN = re.compile(r"\d+(?:\.\d+)?")


def _extract_numbers(prompt: str) -> List[float]:
    return [float(match) for match in FLOAT_PATTERN.findall(prompt)]


def _choose_shape(prompt: str) -> str:
    lower_prompt = prompt.lower()
    for shape, keywords in SHAPE_KEYWORDS.items():
        if any(keyword in lower_prompt for keyword in keywords):
            return shape
    return "box"


def _dimensions_from_numbers(shape: str, numbers: List[float]) -> Dict[str, float]:
    if not numbers:
        return DEFAULT_DIMENSIONS[shape]

    if shape == "box":
        values = (numbers + numbers[:3])[:3]
        width, height, depth = values
        return {"width": width, "height": height, "depth": depth}

    if shape == "sphere":
        return {"radius": max(numbers[0], 0.1)}

    if shape == "cylinder":
        values = (numbers + numbers[:2])[:2]
        radius, height = values
        return {"radius": max(radius, 0.1), "height": height}

    if shape == "cone":
        values = (numbers + numbers[:2])[:2]
        radius, height = values
        return {"radius": max(radius, 0.1), "height": height}

    if shape == "torus":
        values = (numbers + numbers[:2])[:2]
        radius, tube = values
        return {"radius": max(radius, 0.1), "tube_radius": max(tube * 0.25, 0.05)}

    return DEFAULT_DIMENSIONS[shape]


def _build_mesh(shape: str, dimensions: Dict[str, float]) -> trimesh.Trimesh:
    if shape == "box":
        return trimesh.creation.box(
            extents=(dimensions["width"], dimensions["height"], dimensions["depth"])
        )
    if shape == "sphere":
        return trimesh.creation.icosphere(radius=dimensions["radius"], subdivisions=3)
    if shape == "cylinder":
        return trimesh.creation.cylinder(
            radius=dimensions["radius"], height=dimensions["height"], sections=48
        )
    if shape == "cone":
        return trimesh.creation.cone(
            radius=dimensions["radius"], height=dimensions["height"], sections=64
        )
    if shape == "torus":
        return trimesh.creation.torus(
            radius=dimensions["radius"], tube_radius=dimensions["tube_radius"],
        )
    return trimesh.creation.box(extents=(1.0, 1.0, 1.0))


def generate_mesh_from_prompt(prompt: str) -> Tuple[trimesh.Trimesh, MeshDescription]:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("A description is required to generate a model.")

    shape = _choose_shape(prompt)
    numbers = _extract_numbers(prompt)
    dimensions = _dimensions_from_numbers(shape, numbers)
    mesh = _build_mesh(shape, dimensions)

    description = MeshDescription(
        name=f"{shape.capitalize()} concept",
        details=(
            "The mesh is procedurally generated based on keywords in your prompt. "
            "You can download the STL to tweak it further in your favorite CAD tool."
        ),
        shape=shape,
        dimensions=dimensions,
    )
    return mesh, description


def export_mesh_to_stl(mesh: trimesh.Trimesh) -> str:
    buffer = io.BytesIO()
    mesh.export(buffer, file_type="stl")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


@app.route("/")
def index():
    return render_template("index.html", sample_prompts=SAMPLE_PROMPTS)


@app.route("/generate", methods=["POST"])
def generate():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt") or request.form.get("prompt") or ""

    try:
        mesh, description = generate_mesh_from_prompt(prompt)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    stl_data = export_mesh_to_stl(mesh)
    bbox = mesh.bounding_box.extents.tolist()

    return jsonify(
        {
            "stl": stl_data,
            "mesh": {
                "name": description.name,
                "details": description.details,
                "shape": description.shape,
                "dimensions": description.dimensions,
                "bounds": {"width": bbox[0], "height": bbox[1], "depth": bbox[2]},
                "faces": int(mesh.faces.shape[0]),
                "vertices": int(mesh.vertices.shape[0]),
            },
        }
    )


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=4000, debug=debug_mode)
