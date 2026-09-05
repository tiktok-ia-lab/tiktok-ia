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
    / "api" / CAMERA / "C8_api_photographic_limit.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C9_api_stress_test.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 C9 — aggressive photorealism stress test.

The current image is already compositionally correct and must remain
spatially identical.

ABSOLUTE REQUIREMENT:
Do not change geometry.

Preserve exactly:
- camera
- framing
- perspective
- architecture
- object positions
- object proportions
- object silhouettes
- furniture orientation
- occlusions
- number of objects

The chair, stove, hearth, table, rug, chimney, walls, floor and ceiling
must remain exactly where they are.

Do not:
- move anything
- rotate anything
- resize anything
- redesign anything
- add or remove objects
- add openings, recesses, handles, ornaments or architectural details
- alter the stove design
- alter the chair design
- change the rug shape
- change the table shape

GOAL:
Push the image as far as possible toward premium cinematic photography
while preserving the existing geometry.

Increase strongly:
- realistic multi-scale material variation
- deep natural wood grain and pores
- subtle scratches and hand-worn areas
- realistic woven upholstery fibers
- realistic rug fibers and weave
- convincing cast iron microtexture
- subtle oxidation and age on metal
- natural plaster variation
- realistic floor wear
- physically plausible reflected light
- contact shadows
- tonal richness
- subtle atmospheric depth
- photographic microcontrast
- realistic exposure response
- natural imperfections from age and use
- richer material separation
- high-end cinematic realism

IMPORTANT:
Do not make textures procedural-looking.
Do not make all surfaces share the same texture language.
Do not exaggerate relief.
Do not stylize.
Do not add decorative content.

The result should look like a high-end photograph of EXACTLY the same
room, with the strongest possible increase in realism that does not alter
the underlying scene.
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
