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
    / "CAM-001"
    / "beauty.png"
)

OUTPUT_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / "CAM-001"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C1_api_beauty_only.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe {INPUT}")

PROMPT = """
EXP-001 CAM-001 exterior geometry-preservation test.

The input image is a deterministic Blender render and is the
spatial ground truth.

Preserve exactly:
- camera position, framing and perspective
- cabin footprint and facade geometry
- roof geometry
- chimney position and silhouette
- door position and dimensions
- front window position, dimensions and pane layout
- upper window position and dimensions
- porch geometry
- railings
- stairs
- stone path trajectory and arrangement
- fence geometry
- lantern positions
- existing vegetation placement
- all current silhouettes and occlusions

Do not:
- move, rotate or resize objects
- redesign the cabin
- alter the roof shape
- alter window structure
- move the door
- add or remove windows
- add architectural features
- change the path trajectory
- add or remove major vegetation
- invent new structures
- alter camera or perspective

Only enhance appearance:
- realistic wet wood
- realistic stone
- realistic roofing
- realistic glass
- rain interaction
- wet reflections
- vegetation materials
- subtle natural imperfections
- atmospheric moisture
- cinematic but plausible night lighting
- photographic material response

The output must be a realistic photograph of exactly the same
Blender scene, not a redesigned cabin.
""".strip()

print("CAM-001 — C1")
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
