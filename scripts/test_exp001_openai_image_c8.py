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
    / "api" / CAMERA / "C7_api_refinement_strong.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C8_api_photographic_limit.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 C8 — photographic realism limit test.

The supplied image is already compositionally correct.
Treat it as fixed spatial ground truth.

ABSOLUTELY PRESERVE:
- exact camera and framing
- exact perspective
- exact architecture
- exact object positions
- exact object dimensions
- exact object silhouettes
- exact furniture orientation
- exact occlusions
- exact number of objects

Do not move, rotate, resize, redesign, replace, add or remove anything.

The chair, stove, hearth, table, rug, chimney, walls, floor and ceiling
must remain spatially identical to the input image.

GOAL:
Push the image toward high-end photographic realism without increasing
geometric interpretation.

Improve:
- subtle multi-scale wood grain
- realistic wood pores and restrained wear
- fine natural upholstery fibers
- convincing rug weave without exaggerated patterning
- matte iron with realistic roughness variation
- subtle edge wear on metal
- natural plaster and stone microvariation
- believable floor-board roughness and grain
- realistic contact shadows
- physically plausible indirect warm illumination
- richer tonal separation
- subtle local contrast
- material-dependent reflections
- gentle imperfections from real use and age
- realistic photographic depth and atmosphere
- natural sensor-like tonal response
- cinematic realism without stylization

IMPORTANT:
Do not create repeating procedural-looking texture.
Do not exaggerate wall texture.
Do not exaggerate rug pattern.
Do not sharpen edges artificially.
Do not invent structural detail.
Do not add handles, openings, recesses, ornaments, props or decoration.

The result should look less like a rendered image and more like a real
photograph of EXACTLY the same room.
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
