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
    / "api" / CAMERA / "C6_api_refinement.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C7_api_refinement_strong.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
This is a high-end photorealistic MATERIAL REFINEMENT of the supplied image.

The current image composition is already correct.

ABSOLUTELY PRESERVE:
- exact camera and perspective
- exact architecture
- exact object positions
- exact object dimensions
- exact silhouettes
- exact furniture orientation
- exact occlusions
- exact number of objects

Do not redesign, reconstruct, move, resize, rotate, add or remove anything.

The chair, table, stove, hearth, rug, door, window, walls and floor must
remain spatially identical to the input.

Push the existing visual quality significantly further while changing
SURFACE APPEARANCE ONLY.

Increase:
- highly convincing natural wood grain at multiple scales
- subtle pores, scratches and handmade imperfections in wood
- fine woven textile fibers on upholstery
- rich but restrained woven rug detail
- physically convincing matte cast iron
- subtle oxidation and roughness variation on metal
- natural plaster and stone microstructure
- realistic floor-board grain and wear
- tiny material imperfections
- contact shadows
- realistic indirect warm illumination
- material-dependent reflections
- photographic microcontrast
- subtle depth and tonal richness
- high-end cinematic photorealism

The room should feel physically real and tactile.

Do NOT make the room more decorative.
Do NOT introduce props.
Do NOT alter furniture design.
Do NOT add handles, ornaments, openings, recesses or architectural details.

This must look like a higher quality photograph of EXACTLY THE SAME ROOM,
not another interpretation of the room.
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
