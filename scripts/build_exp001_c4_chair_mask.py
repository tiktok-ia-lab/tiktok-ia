from pathlib import Path
from PIL import Image, ImageFilter

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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

source_path = PASS_DIR / "CHAIR-01_mask.png"

if not source_path.exists():
    raise SystemExit(f"ERROR: falta {source_path}")

mask = Image.open(source_path).convert("L")

# Erosión fuerte: deja editable solo el interior de CHAIR-01.
# Así protegemos el contorno geométrico proyectado por Blender.
eroded = mask.filter(
    ImageFilter.MinFilter(31)
)

# En la máscara de edición:
# alpha=0   -> editable
# alpha=255 -> protegido
alpha = Image.eval(
    eroded,
    lambda px: 255 - px
)

rgba = Image.new(
    "RGBA",
    eroded.size,
    (255, 255, 255, 255),
)

rgba.putalpha(alpha)

output_path = OUTPUT_DIR / "C4_CHAIR-01_edit_mask.png"
rgba.save(output_path)

print("Saved:")
print(output_path)
