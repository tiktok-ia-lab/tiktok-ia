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

OUTPUT = OUTPUT_DIR / "I2b_api_canonical_cabin_identity.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 CAM-002 — canonical cabin continuity test.

The supplied image already has the correct camera,
geometry, object positions and composition.

Treat all spatial information as immutable ground truth.

This image must become another photograph of EXACTLY
the same cabin already established in EXP-001 CAM-004.

CAM-002 determines:
- geometry
- camera
- perspective
- object positions
- object sizes
- silhouettes
- occlusions

The canonical cabin identity determines:
- materials
- texture family
- board orientation
- colors
- aging
- roughness
- photographic style

ABSOLUTELY PRESERVE:
- exact camera and framing
- exact perspective
- exact architecture
- exact door position, size and silhouette
- exact window position, dimensions and pane structure
- exact table position, rotation, dimensions and silhouette
- exact table-leg positions
- exact rug position, outline, dimensions and orientation
- exact stove/chimney visible geometry
- exact wall boundaries
- exact object contacts with floor
- exact occlusions
- exact number of objects

MATERIAL ENHANCEMENT MUST NEVER CHANGE OBJECT BOUNDARIES.

Do not move, resize, rotate, replace, redesign,
add or remove anything.

Do not invent:
- door knobs
- door handles
- locks
- hinges
- new trim
- recesses
- holes
- bases
- feet
- plinths
- ledges
- furniture
- props
- decorations
- structural details

CANONICAL INTERIOR MATERIAL IDENTITY:

WOOD WALLS:
Use the same visual identity as the established CAM-004 cabin:
dark warm aged timber,
matte finish,
natural restrained grain,
moderate wear,
subtle tonal variation.

CRITICAL:
All wooden wall cladding must read as HORIZONTAL boards.

Do NOT create vertical wooden wall boards.

Board scale, color, aging and roughness must be compatible
with the established CAM-004 interior.

FLOOR:
Preserve the existing floor geometry.
Use dark aged wooden floorboards with directional grain,
subtle wear and restrained roughness variation.

The floor must remain visually compatible with CAM-004.

TABLE:
Preserve exact geometry, position and orientation.
Use aged solid wood compatible with CAM-004:
warm dark-brown tone,
directional grain,
matte finish,
subtle pores and restrained wear.

Do not alter any leg position.

RUG:
Preserve exact position, outline and dimensions.

CRITICAL:
Do not enlarge the rug.
Do not move the rug.
Do not extend the rug toward any table leg.
Do not move any table leg toward the rug.

Preserve the exact spatial relationship between
the table legs and rug from the supplied input.

Use natural beige woven fibers compatible with CAM-004,
with restrained weave and no strong new decorative pattern.

DOOR:
Preserve exact geometry, size, position and plain design.

Use the same muted terracotta / red-orange identity
established for this cabin.

CRITICAL:
Do not add a knob.
Do not add a handle.
Do not add any hardware that is not already visible.

WINDOW:
Preserve exact frame, pane layout, size and position.
Improve only existing wood and glass material response.

CHIMNEY / PLASTER COLUMN:
Preserve exact shape and exact floor contact.

Use aged light mineral plaster compatible with CAM-004.

CRITICAL:
Do not create any base, foot, plinth, ledge,
step, pedestal or extension at the bottom.

The column must meet the floor exactly as in the input.

STOVE:
Preserve exactly the visible stove fragment.

Any partially visible dark form at the image boundary
must remain part of the stove.

Do not reinterpret it as:
- a hole
- a recess
- an opening
- a wall feature

Use matte black iron compatible with CAM-004.

COLOR CONTINUITY:
Maintain the same cabin palette across cameras:

- dark warm aged timber
- muted terracotta door
- beige natural rug
- light aged plaster
- matte black iron
- warm restrained interior illumination

Do not introduce a new color palette.

TEXTURE CONTINUITY:
The same material must retain compatible:
- grain scale
- direction
- roughness
- aging
- tonal range
- visual density

across CAM-002 and CAM-004.

PHOTOGRAPHIC QUALITY:
Realistic high-end cabin photography.
Natural warm low-light atmosphere.
Restrained microdetail.
Realistic contact shadows.
No generic procedural texture.
No excessive sharpening.
No stylization.

FINAL REQUIREMENT:

This must look like another real photograph of EXACTLY
the same cabin seen in CAM-004, while preserving
the exact geometry and composition of CAM-002.
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
