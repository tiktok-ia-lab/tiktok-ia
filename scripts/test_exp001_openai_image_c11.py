import argparse
import base64
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path.cwd()

parser = argparse.ArgumentParser()
parser.add_argument("--camera", default="CAM-004")
args = parser.parse_args()

CAMERA = args.camera

load_dotenv(dotenv_path=ROOT / ".env")

INPUT = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA / "C10_api_cabin_material_identity.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C11_api_cabin_cinematic.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 C11 — cinematic cabin photography test.

The supplied image already has the correct geometry, composition and
material identity.

Treat all spatial information and existing material identities as fixed.

ABSOLUTELY PRESERVE:
- exact camera and framing
- exact perspective
- exact architecture
- exact object positions
- exact dimensions and proportions
- exact silhouettes
- exact furniture orientation
- exact occlusions
- exact number of objects
- existing material identity of every surface

Do not move, rotate, resize, replace, redesign, add or remove anything.

Preserve the current aged timber walls and ceiling.
Preserve the wooden floorboards.
Preserve the existing table and chair design.
Preserve the chair upholstery.
Preserve the rug.
Preserve the mineral/plaster chimney.
Preserve the cast-iron stove.

GOAL:

Make this exact cabin interior look like a premium real photograph,
primarily through lighting, optical response, tonal depth and physically
plausible interaction between light and the existing materials.

Do NOT solve this by adding more texture.

Improve strongly:
- physically plausible warm interior illumination
- natural indirect bounce light
- realistic contact shadows
- subtle ambient occlusion
- realistic light falloff
- material-dependent highlights
- restrained wood reflections
- matte iron response
- soft textile response
- believable plaster light scattering
- richer shadow detail
- natural highlight rolloff
- deeper but realistic tonal separation
- subtle atmospheric depth
- photographic dynamic range
- realistic exposure
- natural microcontrast
- gentle depth cues
- convincing low-light photography
- warm cinematic atmosphere

The warm light should interact differently with wood, textile, plaster,
iron and rug according to their physical properties.

Preserve fine material detail already present, but do not increase
surface relief or introduce additional procedural texture.

IMPORTANT:
No new objects.
No decorations.
No candles.
No lamps.
No additional light fixtures.
No new windows.
No openings or recesses.
No new handles.
No structural changes.
No exaggerated glow.
No fantasy lighting.
No artificial HDR appearance.
No excessive sharpening.

The scene should feel warmer, deeper, quieter and more photographic,
not more decorated.

It must look like a real photograph taken inside EXACTLY the same old
mountain cabin.
"""


client = OpenAI()

print("Camera:", CAMERA)
print("Model: gpt-image-2")
print("Input:")
print(INPUT)
print()
print("Calling API...")

with INPUT.open("rb") as image_file:
    result = client.images.edit(
        model="gpt-image-2",
        image=image_file,
        prompt=PROMPT,
        size="1024x1536",
        quality="high",
        output_format="png",
    )

if not result.data:
    raise RuntimeError("La API no devolvió ninguna imagen.")

item = result.data[0]

if not item.b64_json:
    raise RuntimeError(
        "La respuesta no contiene b64_json."
    )

OUTPUT.write_bytes(
    base64.b64decode(item.b64_json)
)

print()
print("Saved:")
print(OUTPUT)
