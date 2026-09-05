import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path.cwd()
CAMERA = "CAM-004"

load_dotenv(dotenv_path=ROOT / ".env")

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("ERROR: OPENAI_API_KEY no definida")

client = OpenAI()


# ============================================================
# PATHS
# ============================================================

PASS_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / CAMERA
)

OUTPUT_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / CAMERA
)

beauty_path = PASS_DIR / "beauty.png"
mask_path = OUTPUT_DIR / "C3_edit_mask.png"
output_path = OUTPUT_DIR / "C3_api_localized_edit.png"


for path in (beauty_path, mask_path):
    if not path.exists():
        raise SystemExit(f"ERROR: falta {path}")


# ============================================================
# PROMPT
# ============================================================

prompt = """
EXP-001 localized material enhancement test.

The input is a deterministic Blender render.
Its geometry is the spatial ground truth.

The mask restricts the editable regions.

Within the editable regions, improve surface realism while
preserving the exact existing geometry.

PRESERVE:
- exact camera and perspective
- exact object positions
- exact object rotations
- exact object proportions
- exact silhouettes
- exact occlusions

In particular:
- CHAIR-01 must not move
- STOVE-01 must not move or change shape
- HEARTH-01 must not move
- TABLE-01 must not move or rotate
- RUG-01 must not move or change dimensions

DO NOT:
- add objects
- remove objects
- redesign objects
- reinterpret geometry
- change architecture
- add decoration

ONLY improve material appearance:
- wood
- fabric
- iron
- hearth material
- rug texture

The result must remain spatially faithful to the Blender render.
""".strip()


# ============================================================
# API
# ============================================================

print("Camera:", CAMERA)
print("Model: gpt-image-2")
print("Image:", beauty_path)
print("Mask:", mask_path)
print("Mode: localized masked edit")
print("Calling API...")


with (
    beauty_path.open("rb") as image_file,
    mask_path.open("rb") as mask_file,
):
    result = client.images.edit(
        model="gpt-image-2",
        image=image_file,
        mask=mask_file,
        prompt=prompt,
        quality="medium",
        size="1024x1536",
        output_format="png",
    )


# ============================================================
# SAVE
# ============================================================

if not result.data:
    raise SystemExit("ERROR: respuesta sin imágenes")

item = result.data[0]

if not item.b64_json:
    raise SystemExit("ERROR: respuesta sin b64_json")

output_path.write_bytes(
    base64.b64decode(item.b64_json)
)

print()
print("Saved:")
print(output_path)
