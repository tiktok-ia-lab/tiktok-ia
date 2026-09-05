import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path.cwd()

load_dotenv(dotenv_path=ROOT / ".env")

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("ERROR: OPENAI_API_KEY no definida")

client = OpenAI()

INPUT = (
    ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / "CAM-003"
    / "beauty.png"
)

OUTPUT_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / "CAM-003"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C1_api_beauty_only.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe {INPUT}")

PROMPT = """
EXP-001 CAM-003 interior geometry-preservation test.

The input image is a deterministic Blender render and is the
spatial ground truth.

Preserve exactly:
- camera position, framing and perspective
- room architecture
- door position and dimensions
- visible window geometry if present
- table position, dimensions, orientation and silhouette
- chair position, dimensions, orientation and silhouette if visible
- stove position, dimensions and visible silhouette
- hearth position and dimensions
- rug position, dimensions and orientation
- chimney geometry
- all current occlusions and partially visible fragments

IMPORTANT:
If the stove is only partially visible near an image boundary,
preserve that visible fragment exactly as part of the stove.
Do not reinterpret it as a recess, opening, hole, shadow or wall feature.

Do not:
- move, rotate or resize objects
- redesign furniture
- redesign the stove
- add or remove furniture
- add decoration
- invent openings, recesses or architectural features
- invent a door handle if none is visible
- change camera or perspective

Only enhance appearance:
- realistic wood grain
- realistic fabric
- realistic rug texture
- realistic matte iron
- realistic stone/plaster
- subtle surface wear
- photographic shading
- warm cinematic but physically plausible lighting
- realistic material response

The result must be a realistic photograph of exactly the same
Blender scene, not a redesigned room.
""".strip()

print("CAM-003 — C1")
print("Model: gpt-image-2")
print("Input:", INPUT)
print("Calling API...")

with INPUT.open("rb") as image_file:
    result = client.images.edit(
        model="gpt-image-2",
        image=image_file,
        prompt=PROMPT,
        quality="medium",
        size="1024x1536",
        output_format="png",
    )

if not result.data:
    raise RuntimeError("La API no devolvió ninguna imagen.")

item = result.data[0]

if not item.b64_json:
    raise RuntimeError("La respuesta no contiene b64_json.")

OUTPUT.write_bytes(
    base64.b64decode(item.b64_json)
)

print("Saved:")
print(OUTPUT)
