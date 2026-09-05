from pathlib import Path
from PIL import Image, ImageFilter, ImageChops, ImageEnhance

ROOT = Path.cwd()
CAMERA = "CAM-004"

BLENDER = (
    ROOT / "videos" / "EXP-001" / "blender"
    / "passes" / CAMERA / "beauty.png"
)

AI = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "api" / CAMERA / "C1_api_beauty_only.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "transfer" / CAMERA
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "T1_appearance_transfer.png"

if not BLENDER.exists():
    raise SystemExit(f"ERROR: falta {BLENDER}")

if not AI.exists():
    raise SystemExit(f"ERROR: falta {AI}")


# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

blender = Image.open(BLENDER).convert("RGB")
ai = Image.open(AI).convert("RGB")

# OpenAI devuelve 1024x1536 y Blender 540x960.
# Para T1 llevamos la referencia IA al tamaño exacto de Blender.
ai = ai.resize(
    blender.size,
    Image.Resampling.LANCZOS
)


# ------------------------------------------------------------
# LOW-FREQUENCY APPEARANCE
#
# Difuminamos fuertemente ambas imágenes.
# Así intentamos capturar iluminación/color global,
# no detalles geométricos de la IA.
# ------------------------------------------------------------

radius = 45

blender_low = blender.filter(
    ImageFilter.GaussianBlur(radius)
)

ai_low = ai.filter(
    ImageFilter.GaussianBlur(radius)
)


# ------------------------------------------------------------
# APPEARANCE RATIO
#
# Calculamos aproximadamente:
#
#     AI_low / Blender_low
#
# y aplicamos esa relación al Blender original.
#
# Así las aristas originales siguen viniendo de Blender.
# ------------------------------------------------------------

import numpy as np

b = np.asarray(blender).astype(np.float32)
b_low = np.asarray(blender_low).astype(np.float32)
a_low = np.asarray(ai_low).astype(np.float32)

ratio = (a_low + 8.0) / (b_low + 8.0)

# Evitamos correcciones extremas.
ratio = np.clip(
    ratio,
    0.55,
    1.80
)

# Reducimos deliberadamente la fuerza.
strength = 0.65

correction = (
    1.0
    + (ratio - 1.0) * strength
)

result = b * correction

result = np.clip(
    result,
    0,
    255
).astype(np.uint8)

result = Image.fromarray(result, "RGB")


# ------------------------------------------------------------
# SMALL FINISH
# ------------------------------------------------------------

result = ImageEnhance.Contrast(
    result
).enhance(1.05)

result.save(
    OUTPUT,
    quality=95
)

print("Blender:", BLENDER)
print("AI reference:", AI)
print("Saved:")
print(OUTPUT)
