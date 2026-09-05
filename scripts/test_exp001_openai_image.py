import argparse
import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# ARGUMENTS
# ============================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--camera",
    default="CAM-003",
    choices=("CAM-002", "CAM-003", "CAM-004"),
)

args = parser.parse_args()

CAMERA_NAME = args.camera


# ============================================================
# ENV / CLIENT
# ============================================================

ROOT = Path.cwd()
ENV_PATH = ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit(
        "ERROR: OPENAI_API_KEY no definida"
    )

client = OpenAI()


# ============================================================
# PATHS
# ============================================================

input_path = (
    ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / CAMERA_NAME
    / "beauty.png"
)

output_dir = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / CAMERA_NAME
)

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

if not input_path.exists():
    raise SystemExit(
        f"ERROR: no existe {input_path}"
    )


# ============================================================
# PROMPT
# ============================================================

prompt = """
EXP-001 geometry-preservation test.

The input image is a deterministic Blender render of ROOM-01.

Use the input image as fixed spatial ground truth.

PRESERVE EXACTLY:
- camera and perspective
- architecture
- door position, size and orientation
- window position, structure and orientation if visible
- table position, rotation, dimensions and silhouette
- chair position, rotation, dimensions and silhouette if visible
- stove position, size and silhouette
- hearth position and dimensions
- rug position, dimensions and orientation
- wall and chimney geometry
- number and placement of existing objects

DO NOT:
- move existing objects
- rotate existing objects
- resize existing objects
- add furniture
- add decorative objects
- add paintings
- add books
- add cups
- add candles
- add fruit
- add logs
- add tools
- add kettles
- invent a door handle if none is visible in the input
- change the table orientation
- redesign the stove
- alter architecture

ALLOWED CHANGES ONLY:
- realistic wood surface texture
- realistic iron surface texture
- realistic stone/plaster texture
- realistic fabric and rug texture
- subtle surface wear
- photographic shading
- realistic warm lighting response

The output must remain a spatially faithful material and realism
enhancement of the exact Blender image, not a redesigned room.
""".strip()


# ============================================================
# API EDIT
# ============================================================

print("Camera:", CAMERA_NAME)
print("Model: gpt-image-2")
print("Input:", input_path)
print("Calling API...")

with input_path.open("rb") as image_file:

    result = client.images.edit(
        model="gpt-image-2",
        image=image_file,
        prompt=prompt,
        quality="medium",
        size="1024x1536",
    )


# ============================================================
# SAVE
# ============================================================

if not result.data:
    raise SystemExit(
        "ERROR: respuesta sin imágenes"
    )

item = result.data[0]

if not item.b64_json:
    raise SystemExit(
        "ERROR: respuesta sin b64_json"
    )

output_path = (
    output_dir
    / "C1_api_beauty_only.png"
)

output_path.write_bytes(
    base64.b64decode(
        item.b64_json
    )
)

print("Saved:", output_path)
