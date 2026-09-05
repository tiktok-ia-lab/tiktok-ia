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
    / "api" / CAMERA / "E2_api_exterior_weathered.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "E3_api_exterior_cinematic.png"

if not INPUT.exists():
    raise SystemExit(f"ERROR: no existe:\n{INPUT}")


PROMPT = """
EXP-001 CAM-001 E3 — premium cinematic rain photography test.

The supplied image is already the correct final scene.

Its architecture, materials, weathering, vegetation, path, stepping
stones and composition are successful and must be preserved.

This is NOT a redesign and NOT a material-generation pass.

Treat the supplied image as immutable spatial ground truth.

ABSOLUTELY PRESERVE:
- exact camera and framing
- exact perspective
- exact cabin silhouette
- exact roof geometry
- exact chimney
- exact door
- exact windows and window divisions
- exact porch
- exact railings and posts
- exact path geometry and direction
- exact stepping-stone positions, sizes and spacing
- exact vegetation distribution
- exact lights and their positions
- exact architectural proportions
- exact number of all major elements
- existing material identities
- existing weathering character

Do not move, rotate, resize, replace, redesign, add or remove anything.

CRITICAL:
The path and every stepping stone must remain exactly where they are.
The cabin must remain exactly the same cabin.

GOAL:

Improve ONLY the photographic and cinematic realism of this exact
rainy-night photograph.

Do not increase generic texture.
Do not make the cabin older.
Do not add damage.
Do not add objects.
Do not redesign materials.

Improve:

- physically plausible low-light photography
- natural cinematic exposure
- realistic dynamic range
- richer but readable shadow information
- smooth highlight rolloff
- restrained warm-light bloom
- realistic wet-surface reflections
- subtle variation in reflection intensity
- realistic interaction between rain and light
- rain depth at near, middle and far distances
- natural variation in rain visibility
- subtle humid atmospheric depth
- realistic separation between cabin and distant forest
- convincing depth in the dark background
- natural optical softness in distant elements
- restrained local contrast
- realistic fine detail in focal areas
- natural lens response
- subtle photographic depth cues
- physically plausible light falloff
- realistic warm light reflecting from wet surfaces
- convincing cold ambient night illumination

LIGHTING:

Preserve the existing lighting design.

Maintain the emotional contrast between:
cold blue-gray rainy forest exterior
and
warm amber welcoming cabin interior.

The warm light should interact naturally with wet wood, glass,
vegetation, stones and saturated ground.

Do not increase brightness globally.
Do not make the image orange.
Do not crush the blacks.
Do not create artificial HDR.

RAIN:

Preserve the existing rainfall.

Make it photographically convincing at different depths:
some closer streaks may be more visible,
mid-distance rain should remain readable,
far rain should integrate naturally into atmospheric depth.

Do not turn the rain into uniform white lines.
Do not obscure the cabin.

WET SURFACES:

Preserve the existing wetness and material identities.

Improve only physically plausible optical response:
subtle specular reflections,
natural highlight breakup,
small variations in roughness,
realistic reflected warm light.

Do not add excessive puddles.
Do not make all surfaces glossy.

CAMERA FEEL:

The final result should feel as though photographed with a high-end
full-frame camera in difficult real rainy-night conditions.

It should retain natural photographic imperfections and believable
low-light behavior rather than looking digitally perfect.

No fantasy effects.
No dramatic fog.
No new light sources.
No lens flare.
No artificial glow.
No excessive sharpening.
No excessive microcontrast.
No added decorations.
No structural changes.

FINAL REQUIREMENT:

This must be a more cinematic, deeper and more convincing photograph
of EXACTLY the supplied scene.

If improving an effect would require changing geometry, composition,
objects or materials, preserve the input instead.
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
