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

OUTPUT = OUTPUT_DIR / "C10_api_cabin_material_identity.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 C10 — rustic cabin material identity test.

The supplied image already has the correct geometry and composition.
Treat all spatial information as immutable ground truth.

ABSOLUTELY PRESERVE:
- exact camera
- exact framing
- exact perspective
- exact architecture
- exact object positions
- exact dimensions
- exact silhouettes
- exact furniture orientation
- exact occlusions
- exact number of objects

Do not move, resize, rotate, replace, redesign, add or remove anything.

The chair, stove, hearth, table, rug, chimney, walls, floor and ceiling
must remain spatially identical to the input.

GOAL:

Transform the surface appearance into a highly convincing real old
rustic mountain cabin interior.

Do NOT add generic microtexture everywhere.

Every surface must have a clearly different, physically plausible
material identity.

WOODEN CABIN SURFACES:
Where a surface is wood, make it unmistakably real aged cabin timber.
Use natural longitudinal wood grain, restrained knots where plausible,
subtle board-to-board tonal variation, real seams between boards,
small scratches, worn areas and non-uniform roughness.
Avoid decorative or exaggerated grain.

FLOOR:
Preserve the exact floor geometry.
Make the existing floor read as real aged wooden floorboards with
longitudinal grain, natural board seams, restrained wear from use,
subtle scratches and realistic roughness variation.

TABLE AND CHAIR WOOD:
Keep their exact geometry.
Use solid natural wood with visible directional grain, subtle pores,
small handmade imperfections and localized wear.
Their wood must remain visually distinct from the floor and walls.

CHAIR UPHOLSTERY:
Preserve its exact shape.
Make it clearly read as woven natural fabric with fine fibers,
subtle irregularities and realistic softness.
It must not resemble plaster, wall texture or rug texture.

RUG:
Preserve its exact dimensions, outline and position.
Give it a distinct natural woven fiber structure with restrained
irregularity.
Do not invent a strong decorative pattern.

CHIMNEY:
Preserve its exact geometry.
It must remain mineral/plaster, never wood.
Use hand-applied irregular plaster, fine mineral granularity,
subtle tonal variation and restrained signs of age.
No repeating embossed pattern.

STOVE:
Preserve its exact design, dimensions and position.
Make it read as heavy matte black cast iron.
Use subtle heat-aged roughness, very restrained oxidation,
fine surface variation and realistic edge response.
Do not add doors, handles, vents or details that are not already present.

WALLS AND CEILING:
Give them physically believable cabin construction and material
character appropriate to what already exists in the input.
Do not invent beams, panels, openings or structural features.
Avoid uniform procedural-looking noise.

LIGHTING:
Keep the same lighting direction and overall warm atmosphere.
Improve realistic indirect illumination, contact shadows,
material-dependent reflections and natural tonal separation.

PHOTOGRAPHIC QUALITY:
Aim for subtle high-end photographic realism.
Natural exposure.
Realistic local contrast.
Tactile materials.
Fine but restrained microdetail.
No artificial sharpening.
No stylization.

CRITICAL MATERIAL RULE:

Wood must look like wood.
Fabric must look like fabric.
Rug fibers must look like rug fibers.
Plaster must look like plaster.
Iron must look like iron.

Do not make different materials share the same texture pattern.

The final image must look like a real, old, lived-in mountain cabin,
while remaining EXACTLY the same room and composition as the input.
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
