import bpy
import sys
from pathlib import Path


# ============================================================
# ARGUMENTS
# ============================================================

CAMERA_NAME = "CAM-003"

if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    for i, arg in enumerate(args):
        if arg == "--camera" and i + 1 < len(args):
            CAMERA_NAME = args[i + 1]


# ============================================================
# PATHS
# ============================================================

REPO_ROOT = Path.cwd()

OUTPUT_DIR = (
    REPO_ROOT
    / "videos"
    / "EXP-001"
    / "blender"
    / "passes"
    / CAMERA_NAME
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SCENE / CAMERA
# ============================================================

scene = bpy.context.scene

camera = bpy.data.objects.get(CAMERA_NAME)

if camera is None:
    raise RuntimeError(
        f"Camera not found: {CAMERA_NAME}"
    )

scene.camera = camera

view_layer = scene.view_layers[0]

# Depth pass.
view_layer.use_pass_z = True

# Cryptomatte object pass.
view_layer.use_pass_cryptomatte_object = True
view_layer.pass_cryptomatte_depth = 6


# ============================================================
# CONTINUITY GROUPS
# ============================================================

groups = {
    "DOOR-01": (
        "DOOR-01",
    ),
    "WINDOW-FRONT-01": (
        "WINDOW-FRONT-01",
    ),
    "TABLE-01": (
        "TABLE-01",
    ),
    "CHAIR-01": (
        "CHAIR-01",
    ),
    "STOVE-01": (
        "STOVE-01",
    ),
    "HEARTH-01": (
        "HEARTH-01",
    ),
    "RUG-01": (
        "RUG-01",
    ),
}


def matches_prefix(obj_name, prefixes):
    return any(
        obj_name == prefix
        or obj_name.startswith(prefix + "_")
        for prefix in prefixes
    )


print()
print("=" * 72)
print("EXP-001 — RENDER PASSES / CRYPTOMATTE")
print("=" * 72)
print()
print(f"Camera: {CAMERA_NAME}")
print(f"Output: {OUTPUT_DIR}")
print()


# ============================================================
# REPORT LOGICAL GROUPS
# ============================================================

for group_name, prefixes in groups.items():

    matched = [
        obj.name
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and matches_prefix(obj.name, prefixes)
    ]

    print(
        f"{group_name:20s}"
        f" objects={len(matched)}"
    )

    for name in matched:
        print(f"    {name}")


# ============================================================
# COMPOSITOR
# ============================================================

scene.use_nodes = True

tree = scene.node_tree
nodes = tree.nodes
links = tree.links

nodes.clear()


# ------------------------------------------------------------
# Render Layers
# ------------------------------------------------------------

render_layers = nodes.new(
    "CompositorNodeRLayers"
)

render_layers.location = (-1200, 200)


# ------------------------------------------------------------
# Composite / beauty
# ------------------------------------------------------------

composite = nodes.new(
    "CompositorNodeComposite"
)

composite.location = (900, 500)

links.new(
    render_layers.outputs["Image"],
    composite.inputs["Image"]
)


# ============================================================
# DEPTH PREVIEW
# ============================================================

depth_map = nodes.new(
    "CompositorNodeMapRange"
)

depth_map.location = (-750, 250)

depth_map.inputs["From Min"].default_value = 0.5
depth_map.inputs["From Max"].default_value = 8.0
depth_map.inputs["To Min"].default_value = 1.0
depth_map.inputs["To Max"].default_value = 0.0

try:
    depth_map.use_clamp = True
except Exception:
    pass

links.new(
    render_layers.outputs["Depth"],
    depth_map.inputs["Value"]
)


depth_out = nodes.new(
    "CompositorNodeOutputFile"
)

depth_out.location = (900, 250)
depth_out.base_path = str(OUTPUT_DIR)

depth_out.format.file_format = "PNG"
depth_out.format.color_mode = "BW"
depth_out.format.color_depth = "16"

depth_out.file_slots[0].path = "depth_preview_"

links.new(
    depth_map.outputs["Value"],
    depth_out.inputs[0]
)


# ============================================================
# CRYPTOMATTE MASKS
# ============================================================

mask_y = 0

for group_name, prefixes in groups.items():

    matched_names = [
        obj.name
        for obj in bpy.data.objects
        if obj.type == "MESH"
        and matches_prefix(obj.name, prefixes)
    ]

    if not matched_names:
        print(
            f"WARNING: no objects matched for {group_name}"
        )
        continue

    crypto = nodes.new(
        "CompositorNodeCryptomatteV2"
    )

    crypto.location = (-450, mask_y)
    crypto.source = "RENDER"

    # Connect Render Layers cryptomatte passes.
    # Blender 4.x exposes CryptoObject00/01/02...
    for socket_name in (
        "CryptoObject00",
        "CryptoObject01",
        "CryptoObject02",
    ):
        if (
            socket_name in render_layers.outputs
            and socket_name in crypto.inputs
        ):
            links.new(
                render_layers.outputs[socket_name],
                crypto.inputs[socket_name]
            )

    # The Matte ID field accepts comma-separated names.
    crypto.matte_id = ",".join(
        matched_names
    )

    file_out = nodes.new(
        "CompositorNodeOutputFile"
    )

    file_out.location = (900, mask_y)
    file_out.base_path = str(OUTPUT_DIR)

    file_out.format.file_format = "PNG"
    file_out.format.color_mode = "BW"
    file_out.format.color_depth = "8"

    file_out.file_slots[0].path = (
        f"{group_name}_mask_"
    )

    links.new(
        crypto.outputs["Matte"],
        file_out.inputs[0]
    )

    mask_y -= 180


# ============================================================
# BEAUTY OUTPUT
# ============================================================

scene.render.filepath = str(
    OUTPUT_DIR / "beauty.png"
)


# ============================================================
# RENDER
# ============================================================

print()
print("Rendering beauty + depth + cryptomatte masks...")

bpy.ops.render.render(
    write_still=True
)


# ============================================================
# NORMALIZE FILE OUTPUT NAMES
# ============================================================

rename_prefixes = [
    "depth_preview",
]

rename_prefixes.extend(
    f"{name}_mask"
    for name in groups
)


for prefix in rename_prefixes:

    candidates = sorted(
        OUTPUT_DIR.glob(
            f"{prefix}_*.png"
        )
    )

    if not candidates:
        print(
            f"WARNING: output missing: {prefix}"
        )
        continue

    source = candidates[-1]
    target = OUTPUT_DIR / f"{prefix}.png"

    if target.exists():
        target.unlink()

    source.rename(target)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 72)
print("PASS PACKAGE COMPLETE")
print("=" * 72)

for path in sorted(OUTPUT_DIR.glob("*")):
    print(path.name)

print()
print(
    "NOTE: the .blend file has NOT been saved."
)
print()
