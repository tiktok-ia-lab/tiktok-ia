from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path.cwd()

CAMERAS = [
    (
        "CAM-001",
        ROOT / "videos/EXP-001/blender/passes/CAM-001/beauty.png",
        ROOT / "videos/EXP-001/ai-tests/api/CAM-001/C1_api_beauty_only.png",
    ),
    (
        "CAM-002",
        ROOT / "videos/EXP-001/blender/passes/CAM-002/beauty.png",
        ROOT / "videos/EXP-001/ai-tests/api/CAM-002/C1_api_beauty_only_retry.png",
    ),
    (
        "CAM-003",
        ROOT / "videos/EXP-001/blender/passes/CAM-003/beauty.png",
        ROOT / "videos/EXP-001/ai-tests/api/CAM-003/C1_api_beauty_only.png",
    ),
    (
        "CAM-004",
        ROOT / "videos/EXP-001/blender/passes/CAM-004/beauty.png",
        ROOT / "videos/EXP-001/ai-tests/api/CAM-004/C1_api_beauty_only.png",
    ),
]


OUT_DIR = ROOT / "videos/EXP-001/comparisons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUT_DIR / "EXP-001_blender_vs_openai_C1.png"


# ------------------------------------------------------------
# Validación
# ------------------------------------------------------------

missing = []

for camera, blender_path, ai_path in CAMERAS:
    for p in (blender_path, ai_path):
        if not p.exists():
            missing.append(p)

if missing:
    print("ERROR: faltan archivos:")
    for p in missing:
        print("  ", p)
    raise SystemExit(1)


# ------------------------------------------------------------
# Diseño
# ------------------------------------------------------------

CELL_W = 540
CELL_H = 960

HEADER_H = 70
ROW_LABEL_H = 45
GAP = 12
MARGIN = 20

SHEET_W = (
    MARGIN * 2
    + CELL_W * 2
    + GAP
)

ROW_H = ROW_LABEL_H + CELL_H

SHEET_H = (
    MARGIN
    + HEADER_H
    + len(CAMERAS) * ROW_H
    + GAP * (len(CAMERAS) - 1)
    + MARGIN
)


sheet = Image.new(
    "RGB",
    (SHEET_W, SHEET_H),
    (24, 24, 24),
)

draw = ImageDraw.Draw(sheet)

try:
    font_title = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        28,
    )
    font_label = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        22,
    )
except OSError:
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()


# ------------------------------------------------------------
# Cabecera
# ------------------------------------------------------------

draw.text(
    (MARGIN + CELL_W // 2, MARGIN + 10),
    "BLENDER",
    fill="white",
    font=font_title,
    anchor="ma",
)

draw.text(
    (MARGIN + CELL_W + GAP + CELL_W // 2, MARGIN + 10),
    "OPENAI C1",
    fill="white",
    font=font_title,
    anchor="ma",
)


# ------------------------------------------------------------
# Filas
# ------------------------------------------------------------

y = MARGIN + HEADER_H

for camera, blender_path, ai_path in CAMERAS:

    draw.text(
        (SHEET_W // 2, y),
        camera,
        fill="white",
        font=font_label,
        anchor="ma",
    )

    image_y = y + ROW_LABEL_H

    blender = Image.open(blender_path).convert("RGB")
    ai = Image.open(ai_path).convert("RGB")

    blender = blender.resize(
        (CELL_W, CELL_H),
        Image.Resampling.LANCZOS,
    )

    ai = ai.resize(
        (CELL_W, CELL_H),
        Image.Resampling.LANCZOS,
    )

    sheet.paste(
        blender,
        (MARGIN, image_y),
    )

    sheet.paste(
        ai,
        (MARGIN + CELL_W + GAP, image_y),
    )

    y += ROW_H + GAP


sheet.save(
    OUTPUT,
    quality=95,
)

print()
print("Saved:")
print(OUTPUT)
print()
print("Size:", sheet.size)
