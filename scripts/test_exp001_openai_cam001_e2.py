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

OUTPUT = OUTPUT_DIR / "E2_api_exterior_weathered.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 CAM-001 E2 — aged wet cabin exterior material test.

The supplied image already contains the correct cabin, camera,
composition, architecture, path, vegetation and spatial relationships.

Treat the entire spatial structure as immutable ground truth.

ABSOLUTELY PRESERVE:
- exact camera
- exact framing
- exact perspective
- exact cabin silhouette
- exact roof geometry
- exact chimney position and dimensions
- exact door position and dimensions
- exact windows and their positions
- exact porch structure
- exact railings and posts
- exact path position, shape, direction and perspective
- exact stepping-stone positions
- exact vegetation masses
- exact foreground/background relationships
- exact number and placement of architectural elements

Do not move, resize, rotate, redesign, add or remove any architectural
element or major scene element.

CRITICAL:
The existing path must remain in exactly the same location and follow
exactly the same direction and perspective as in the input.

GOAL:

Make this exact exterior feel like a real old mountain cabin that has
been exposed to years of rain, cold weather and forest humidity.

Do NOT achieve this by adding generic texture everywhere.

Give every material its own physically plausible identity.

CABIN WOOD:
Make the existing timber read as genuinely aged exterior wood.
Preserve every board and architectural boundary.
Use natural wood grain, subtle weathering, restrained discoloration,
darkened wet areas, small imperfections and realistic variation in
roughness.

The wood is wet from rain.
Wetness must affect reflections and darkness naturally without making
the entire cabin uniformly glossy.

ROOF:
Preserve its exact shape and silhouette.
Make it convincingly rain-soaked with subtle wet roughness variation,
small water accumulation where physically plausible and restrained
specular response.

Do not redesign roofing materials.

WINDOWS:
Preserve exact dimensions, divisions and positions.
Keep the existing warm interior illumination.
Make the glass convincingly wet with restrained droplets, thin water
trails, condensation and physically plausible reflections.

Do not alter window geometry.

DOOR:
Preserve exact design, position and dimensions.
Give the existing material subtle age, moisture and realistic surface
response without redesigning it.

PATH AND STEPPING STONES:
Preserve exact geometry, positions, spacing, direction and perspective.
Make the existing surfaces genuinely rain-wet.
Use realistic darkening, restrained reflections and small physically
plausible water accumulation.
Do not add, remove or move stones.

VEGETATION:
Preserve the existing vegetation distribution and silhouettes.
Make leaves and forest plants look naturally wet, with varied restrained
specular highlights and realistic depth.
Do not add new large plants or change the composition.

GROUND:
Make existing soil and ground surfaces convincingly saturated by rain,
with natural darkening, subtle mud and physically plausible wet
reflections.
Do not change terrain geometry.

RAIN:
Preserve the rainy atmosphere.
Improve physical realism and depth of rainfall.
Rain should exist at different distances from the camera with natural
variation in visibility.
Avoid uniform artificial streaks.

ATMOSPHERE:
Increase believable humid forest atmosphere and subtle depth.
Preserve visibility of the cabin.
No heavy artificial fog.

LIGHT:
Preserve the existing warm/cool relationship:
cold rainy exterior versus warm welcoming cabin interior.

Improve realistic interaction of warm window and porch light with wet
wood, wet vegetation, stones and ground.

MATERIAL RULE:

Wet wood must look like wet wood.
Glass must look like wet glass.
Leaves must look like wet leaves.
Stone must look like wet stone.
Soil must look like saturated soil.

Do not make different materials share the same procedural texture.

PHOTOGRAPHIC QUALITY:
Premium realistic night photography.
Natural dynamic range.
Deep but readable shadows.
Realistic highlight rolloff.
Physically plausible reflections.
Fine restrained detail.
No artificial HDR.
No fantasy atmosphere.
No excessive sharpening.

The final result must look older, wetter, richer and more photographic
while remaining EXACTLY the same cabin and composition as the input.
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
