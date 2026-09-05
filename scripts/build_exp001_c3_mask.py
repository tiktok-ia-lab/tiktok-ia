from pathlib import Path

from PIL import Image, ImageFilter, ImageChops


ROOT = Path.cwd()

CAMERA = "CAM-004"

PASS_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / CAMERA
)

OUTPUT_DIR = (
    ROOT
    / "videos"
    / "EXP-001"
    / "ai-tests"
    / "api"
    / CAMERA
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


MASK_NAMES = [
    "CHAIR-01_mask.png",
    "STOVE-01_mask.png",
    "HEARTH-01_mask.png",
    "TABLE-01_mask.png",
    "RUG-01_mask.png",
]


# ============================================================
# LOAD + UNION
# ============================================================

masks = []

for name in MASK_NAMES:

    path = PASS_DIR / name

    if not path.exists():
        raise SystemExit(
            f"ERROR: falta {path}"
        )

    mask = Image.open(path).convert("L")

    masks.append(mask)


union = masks[0]

for mask in masks[1:]:

    union = ImageChops.lighter(
        union,
        mask,
    )


# ============================================================
# ERODE EDITABLE REGIONS
#
# MinFilter shrinks white regions.
# This protects object silhouettes/borders.
# ============================================================

eroded = union.filter(
    ImageFilter.MinFilter(15)
)


# ============================================================
# API MASK
#
# GPT image editing uses transparency to indicate
# editable pixels.
#
# alpha = 0   -> editable
# alpha = 255 -> preserve
# ============================================================

alpha = Image.eval(
    eroded,
    lambda px: 255 - px
)


mask_rgba = Image.new(
    "RGBA",
    eroded.size,
    (255, 255, 255, 255),
)

mask_rgba.putalpha(alpha)


output_path = (
    OUTPUT_DIR
    / "C3_edit_mask.png"
)

mask_rgba.save(output_path)

print("Saved:")
print(output_path)
