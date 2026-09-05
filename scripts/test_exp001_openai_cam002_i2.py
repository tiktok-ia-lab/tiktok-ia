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
    / "api" / CAMERA / "C1_api_beauty_only_retry.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "I2_api_cabin_material_identity.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 CAM-002 — cabin material identity refinement.

The supplied image already has the correct geometry,
camera and composition.

Treat all spatial information as immutable ground truth.

ABSOLUTELY PRESERVE:
- exact camera and framing
- exact perspective
- exact room architecture
- exact door position, size and silhouette
- exact window position, size and pane structure
- exact table position, rotation, dimensions and silhouette
- exact rug position, dimensions and orientation
- exact visible stove/chimney geometry
- exact occlusions
- exact number of objects

Do not move, resize, rotate, replace, redesign,
add or remove anything.

Do not invent:
- door handles
- openings
- recesses
- furniture
- decoration
- architectural details
- props

GOAL:

Make the existing interior read as a convincing
old rustic mountain cabin through MATERIAL IDENTITY,
not through generic texture.

Every existing surface must retain a distinct and
physically plausible material character.

WOODEN CABIN SURFACES:
Where wood already exists, make it read as real aged timber.
Use directional natural grain, subtle board variation,
restrained knots where plausible, fine pores,
localized wear and non-uniform roughness.

Do not invent beams, panels or structural wood
that are not already present.

FLOOR:
Preserve exact board geometry and perspective.
Give the existing boards realistic longitudinal grain,
natural seams, subtle wear and restrained roughness variation.

TABLE:
Preserve exact position, orientation, size and silhouette.
Use believable solid natural wood with directional grain,
fine pores and subtle handmade wear.
Do not change its shape or leg arrangement.

RUG:
Preserve exact outline, position, dimensions and orientation.
Give it realistic woven natural fibers and restrained
irregularity.
Do not invent a strong new decorative pattern.

DOOR:
Preserve exact design, dimensions and position.
Improve only the existing material.
Do not add a knob, handle, lock or hardware
that is not already visible.

WINDOW:
Preserve exact position, size, frame and pane layout.
Improve only glass and frame material response.
Do not alter its geometry.

STOVE / CHIMNEY:
Preserve exactly the visible geometry.
Any partially visible dark stove fragment must remain
part of the stove and must not become a hole,
recess, doorway or wall feature.

Where iron is visible, make it read as matte black iron
with subtle roughness and restrained heat aging.

Where chimney/plaster exists, keep it mineral/plaster,
with fine natural variation and no repeating embossed pattern.

LIGHTING:
Preserve the current warm atmosphere and direction.
Improve physically plausible bounce light,
contact shadows and material-dependent response.

CRITICAL MATERIAL RULE:

Wood must look like wood.
Fabric must look like fabric.
Rug must look like woven rug.
Iron must look like iron.
Plaster must look like plaster.
Glass must look like glass.

Do not make different materials share one generic
procedural texture.

PHOTOGRAPHIC QUALITY:
Natural high-end realism.
Fine restrained detail.
No artificial sharpening.
No fantasy lighting.
No generic microtexture everywhere.

The result must look like a real photograph of EXACTLY
the same room shown in the input image.
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
