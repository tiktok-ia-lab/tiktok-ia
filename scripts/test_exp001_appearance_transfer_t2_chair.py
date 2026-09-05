from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

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

CHAIR_MASK = (
    ROOT / "videos" / "EXP-001" / "blender"
    / "passes" / CAMERA / "CHAIR-01_mask.png"
)

OUTPUT_DIR = (
    ROOT / "videos" / "EXP-001" / "ai-tests"
    / "transfer" / CAMERA
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "T2_chair_detail_transfer.png"

for path in (BLENDER, AI, CHAIR_MASK):
    if not path.exists():
        raise SystemExit(f"ERROR: falta {path}")


# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

blender = Image.open(BLENDER).convert("RGB")
ai = Image.open(AI).convert("RGB").resize(
    blender.size,
    Image.Resampling.LANCZOS,
)

mask = Image.open(CHAIR_MASK).convert("L")


# ------------------------------------------------------------
# PROTECT SILHOUETTE
#
# Erode the Blender chair mask so transfer only happens
# inside the object, never on its projected border.
# ------------------------------------------------------------

inner_mask = mask.filter(
    ImageFilter.MinFilter(21)
)

m = (
    np.asarray(inner_mask).astype(np.float32)
    / 255.0
)

m = m[..., None]


# ------------------------------------------------------------
# HIGH-FREQUENCY DETAIL FROM AI
#
# Extract medium/high-frequency local appearance.
# This contains texture and microcontrast more than global
# lighting or large geometry.
# ------------------------------------------------------------

ai_arr = np.asarray(ai).astype(np.float32)
blender_arr = np.asarray(blender).astype(np.float32)

ai_blur = np.asarray(
    ai.filter(
        ImageFilter.GaussianBlur(8)
    )
).astype(np.float32)

detail = ai_arr - ai_blur

# Limit extreme edges/details that could encode wrong geometry.
detail = np.clip(
    detail,
    -28.0,
    28.0
)

strength = 0.65

candidate = (
    blender_arr
    + detail * strength
)

candidate = np.clip(
    candidate,
    0,
    255
)


# ------------------------------------------------------------
# COMPOSITE ONLY INSIDE BLENDER CHAIR
# ------------------------------------------------------------

result = (
    blender_arr * (1.0 - m)
    + candidate * m
)

result = np.clip(
    result,
    0,
    255
).astype(np.uint8)

Image.fromarray(
    result,
    "RGB"
).save(
    OUTPUT,
    quality=95
)

print("Blender:", BLENDER)
print("AI reference:", AI)
print("Chair mask:", CHAIR_MASK)
print("Saved:")
print(OUTPUT)
