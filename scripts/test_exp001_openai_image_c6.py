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
    / "api" / CAMERA / "C1_api_beauty_only.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "C6_api_refinement.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
Refine the supplied image into a more photorealistic, richly textured
cinematic interior while preserving the existing scene exactly.

ABSOLUTE STRUCTURAL CONSTRAINTS:

Preserve exactly the current camera position, framing, perspective,
composition, geometry, object positions, object sizes, silhouettes,
proportions, orientation and occlusions.

Do not move, rotate, resize, replace, redesign, add or remove any object.

The chair must remain exactly where it is and retain exactly its current
shape, proportions, arms, seat, back and four legs.

The stove must remain exactly where it is and retain its existing outer
shape and dimensions.

The hearth, table, rug, walls, floor and chimney structure must remain
exactly where they currently are.

Do not create new openings, recesses, holes, doors, windows, handles,
knobs, decorations, furniture or architectural features.

This is a MATERIAL AND SURFACE REFINEMENT ONLY.

Improve only the visual appearance of the existing surfaces:

- richer natural wood grain with subtle variation and realistic roughness
- convincing woven beige upholstery with fine textile fibers
- realistic matte black iron with restrained microtexture
- subtle natural stone/plaster texture
- detailed woven rug fibers
- more convincing wooden floor grain and surface variation
- subtle imperfections appropriate to real handmade rustic materials
- richer but natural warm cinematic lighting
- realistic contact shadows and material response
- subtle microcontrast and photographic detail

Avoid excessive stylization.
Avoid glossy or polished furniture.
Avoid exaggerated texture.
Avoid changing object edges.

The result should look like a high-quality photograph of EXACTLY the same
room shown in the input image, not a redesigned or reconstructed room.
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
