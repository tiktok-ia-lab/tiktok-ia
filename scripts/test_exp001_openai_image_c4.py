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
mask_path = OUTPUT_DIR / "C4_CHAIR-01_edit_mask.png"
output_path = OUTPUT_DIR / "C4_api_chair_only.png"

for path in (beauty_path, mask_path):
    if not path.exists():
        raise SystemExit(f"ERROR: falta {path}")

prompt = """
EXP-001 C4 — CHAIR-01 material-only edit.

The Blender image is spatial ground truth.

Only the transparent region of the mask may be edited.

That editable region is inside CHAIR-01 only.

Preserve exactly:
- chair position
- chair rotation
- chair dimensions
- chair silhouette
- chair arms
- chair legs
- chair back geometry
- chair seat geometry
- camera
- perspective
- all other objects
- architecture

Do not:
- move the chair
- resize the chair
- rotate the chair
- redesign the chair
- add or remove chair parts
- modify any other object
- add decoration
- change the room

Only enhance material appearance inside the editable region:
- realistic fabric
- realistic wood
- subtle surface wear
- photographic lighting response

This is a material enhancement only, not a reconstruction.
""".strip()

print("Camera:", CAMERA)
print("Model: gpt-image-2")
print("Mode: CHAIR-01 micro-localized edit")
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

if not result.data:
    raise SystemExit("ERROR: respuesta sin imágenes")

item = result.data[0]

if not item.b64_json:
    raise SystemExit("ERROR: respuesta sin b64_json")

output_path.write_bytes(
    base64.b64decode(item.b64_json)
)

print("Saved:")
print(output_path)
