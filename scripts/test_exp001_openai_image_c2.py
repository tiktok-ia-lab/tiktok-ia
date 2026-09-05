import argparse
import base64
import os
from contextlib import ExitStack
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# ARGUMENTS
# ============================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--camera",
    default="CAM-004",
    choices=("CAM-002", "CAM-003", "CAM-004"),
)

args = parser.parse_args()
CAMERA_NAME = args.camera


# ============================================================
# ENV / CLIENT
# ============================================================

ROOT = Path.cwd()

load_dotenv(
    dotenv_path=ROOT / ".env"
)

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit(
        "ERROR: OPENAI_API_KEY no definida"
    )

client = OpenAI()


# ============================================================
# INPUTS
# ============================================================

PASS_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / CAMERA_NAME
)

input_names = [
    "beauty.png",
    "CHAIR-01_mask.png",
    "STOVE-01_mask.png",
    "HEARTH-01_mask.png",
    "TABLE-01_mask.png",
    "RUG-01_mask.png",
]

input_paths = [
    PASS_DIR / name
    for name in input_names
]

for path in input_paths:
    if not path.exists():
        raise SystemExit(
            f"ERROR: falta {path}"
        )


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / CAMERA_NAME
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

output_path = (
    OUTPUT_DIR
    / "C2_api_beauty_plus_guides.png"
)


# ============================================================
# PROMPT
# ============================================================

prompt = """
EXP-001 geometry-preservation test, C2.

INPUT IMAGE ORDER:

1. The FIRST image is the deterministic Blender BEAUTY render.
   It is the spatial ground truth and exact composition.

2. The SECOND image is the exact Blender silhouette mask
   of CHAIR-01.

3. The THIRD image is the exact Blender silhouette mask
   of STOVE-01.

4. The FOURTH image is the exact Blender silhouette mask
   of HEARTH-01.

5. The FIFTH image is the exact Blender silhouette mask
   of TABLE-01.

6. The SIXTH image is the exact Blender silhouette mask
   of RUG-01.

The mask images are NOT visual style references.
White pixels indicate the exact projected region occupied by
that named object in the Blender camera.
Black pixels indicate areas outside that object.

Treat those silhouettes as spatial constraints.

GOAL:
Enhance the FIRST image only in material realism and
photographic appearance.

PRESERVE EXACTLY:
- camera and perspective
- room architecture
- CHAIR-01 projected position, silhouette, scale and rotation
- STOVE-01 projected position and visible silhouette
- HEARTH-01 projected position and silhouette
- TABLE-01 projected position, orientation and silhouette
- RUG-01 projected position, dimensions and orientation
- all existing occlusions
- object count

IMPORTANT:
If an object is only partially visible or cut by the image
boundary, preserve exactly that visible fragment.
Do NOT reinterpret a partially visible object as a hole,
recess, doorway, shadow or architectural feature.

DO NOT:
- move any object
- rotate any object
- resize any object
- alter the chair location
- alter the stove location
- turn the stove into a recess or opening
- change the table orientation
- add furniture
- add decoration
- add paintings
- add cups
- add candles
- add books
- add fruit
- add logs
- add tools
- add kettles
- invent new architectural features

ALLOWED CHANGES ONLY:
- realistic wood texture
- realistic fabric texture
- realistic rug texture
- realistic iron texture
- realistic stone/plaster texture
- subtle material wear
- realistic photographic shading
- warm physically plausible light response

The result must remain spatially faithful to the FIRST image.
The additional masks describe exact Blender geometry and must
not be treated as objects to reproduce visually.
""".strip()


# ============================================================
# API EDIT
# ============================================================

print("Camera:", CAMERA_NAME)
print("Model: gpt-image-2")
print("Input fidelity: high")
print()

for index, path in enumerate(
    input_paths,
    start=1,
):
    print(f"{index}: {path.name}")

print()
print("Calling API...")


# Keep every file handle open until the request completes.
with ExitStack() as stack:

    image_files = [
        stack.enter_context(
            path.open("rb")
        )
        for path in input_paths
    ]

    result = client.images.edit(
        model="gpt-image-2",
        image=image_files,
        prompt=prompt,
        quality="medium",
        size="1024x1536",
        output_format="png",
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

output_path.write_bytes(
    base64.b64decode(
        item.b64_json
    )
)

print()
print("Saved:")
print(output_path)
