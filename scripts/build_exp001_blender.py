import bpy
import json
import math
from pathlib import Path
from mathutils import Vector


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXP_DIR = PROJECT_ROOT / "videos" / "EXP-001"
GEOMETRY_PATH = EXP_DIR / "geometry.json"

OUTPUT_DIR = EXP_DIR / "blender"
RENDER_DIR = OUTPUT_DIR / "renders"
OUTPUT_BLEND = OUTPUT_DIR / "EXP-001_geometry.blend"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

with open(GEOMETRY_PATH, "r", encoding="utf-8") as f:
    geometry = json.load(f)

objects = geometry["objects"]


# ============================================================
# COORDINATE SYSTEM
# ============================================================

def bx(x):
    """
    Canonical X -> Blender X.

    geometry.json defines X as left->right when looking
    toward the cabin.

    Blender scene uses the opposite X direction.
    """
    return -x


def point_xyz(x, y, z):
    return (bx(x), y, z)


# ============================================================
# BASIC HELPERS
# ============================================================

def clear_scene():

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_material(name, color):

    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*color, 1.0)

    return mat


def make_wood_material(name, dark, light):
    """Procedural wet rustic wood material."""

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.65

    mapping = nodes.new("ShaderNodeMapping")
    texcoord = nodes.new("ShaderNodeTexCoord")

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].color = (*light, 1.0)

    links.new(
        texcoord.outputs["Generated"],
        mapping.inputs["Vector"]
    )
    links.new(
        mapping.outputs["Vector"],
        noise.inputs["Vector"]
    )
    links.new(
        noise.outputs["Fac"],
        ramp.inputs["Fac"]
    )
    links.new(
        ramp.outputs["Color"],
        bsdf.inputs["Base Color"]
    )

    bsdf.inputs["Roughness"].default_value = 0.32

    return mat



def add_box(
    name,
    location,
    dimensions,
    material=None
):

    bpy.ops.mesh.primitive_cube_add(
        location=location
    )

    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions

    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True
    )

    if material:
        obj.data.materials.append(material)

    return obj


def cut_front_opening(
    target,
    name,
    canonical_x_min,
    canonical_x_max,
    y,
    z_min,
    z_max,
):
    """Cut a real opening through the cabin front wall."""

    blender_x_a = bx(canonical_x_min)
    blender_x_b = bx(canonical_x_max)

    x_min = min(blender_x_a, blender_x_b)
    x_max = max(blender_x_a, blender_x_b)

    width = x_max - x_min
    height = z_max - z_min

    cutter = add_box(
        name,
        (
            (x_min + x_max) / 2,
            y - 0.02,
            (z_min + z_max) / 2,
        ),
        (
            width,
            0.40,
            height,
        ),
        material=None,
    )

    modifier = target.modifiers.new(
        name=f"{name}_BOOLEAN",
        type="BOOLEAN",
    )

    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter

    bpy.context.view_layer.objects.active = target
    target.select_set(True)

    bpy.ops.object.modifier_apply(
        modifier=modifier.name
    )

    target.select_set(False)

    bpy.data.objects.remove(
        cutter,
        do_unlink=True
    )



def add_cylinder(
    name,
    location,
    radius,
    depth,
    material=None,
    vertices=32
):

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location
    )

    obj = bpy.context.object
    obj.name = name

    if material:
        obj.data.materials.append(material)

    return obj


def add_camera(
    name,
    location,
    target,
    lens=35
):

    camera_data = bpy.data.cameras.new(name)

    camera = bpy.data.objects.new(
        name,
        camera_data
    )

    bpy.context.collection.objects.link(camera)

    camera.location = location
    camera.data.lens = lens

    direction = (
        Vector(target)
        - camera.location
    )

    camera.rotation_euler = (
        direction
        .to_track_quat("-Z", "Y")
        .to_euler()
    )

    return camera


# ============================================================
# FRONT GABLE
# ============================================================

def add_front_gable(
    name,
    center_x,
    front_y,
    width,
    base_z,
    ridge_z,
    material
):

    half_w = width / 2

    mesh = bpy.data.meshes.new(
        f"{name}_MESH"
    )

    verts = [
        (
            center_x - half_w,
            front_y,
            base_z
        ),
        (
            center_x + half_w,
            front_y,
            base_z
        ),
        (
            center_x,
            front_y,
            ridge_z
        )
    ]

    mesh.from_pydata(
        verts,
        [],
        [(0, 1, 2)]
    )

    mesh.update()

    obj = bpy.data.objects.new(
        name,
        mesh
    )

    bpy.context.collection.objects.link(obj)

    if material:
        obj.data.materials.append(material)

    return obj


# ============================================================
# ROOF
# ============================================================

def add_roof_planes(
    name,
    center_x,
    center_y,
    width,
    depth,
    eave_z,
    ridge_z,
    material
):

    half_w = width / 2
    half_d = depth / 2

    mesh = bpy.data.meshes.new(
        f"{name}_MESH"
    )

    verts = [
        (
            center_x - half_w,
            center_y + half_d,
            eave_z
        ),
        (
            center_x - half_w,
            center_y - half_d,
            eave_z
        ),
        (
            center_x,
            center_y + half_d,
            ridge_z
        ),
        (
            center_x,
            center_y - half_d,
            ridge_z
        ),
        (
            center_x + half_w,
            center_y + half_d,
            eave_z
        ),
        (
            center_x + half_w,
            center_y - half_d,
            eave_z
        )
    ]

    faces = [
        (0, 1, 3, 2),
        (2, 3, 5, 4)
    ]

    mesh.from_pydata(
        verts,
        [],
        faces
    )

    mesh.update()

    obj = bpy.data.objects.new(
        name,
        mesh
    )

    bpy.context.collection.objects.link(obj)

    if material:
        obj.data.materials.append(material)

    return obj


# ============================================================
# OPEN PORCH RAILING
# ============================================================

def add_open_railing(
    name,
    canonical_x_min,
    canonical_x_max,
    y,
    z_min,
    z_max,
    material,
    baluster_spacing=0.28
):

    xa = bx(canonical_x_min)
    xb = bx(canonical_x_max)

    x_min = min(xa, xb)
    x_max = max(xa, xb)

    width = x_max - x_min
    center_x = (x_min + x_max) / 2

    rail_depth = 0.10
    rail_height = 0.10

    baluster_width = 0.055
    baluster_depth = 0.055

    # Top rail

    top_z = (
        z_max
        - rail_height / 2
    )

    add_box(
        f"{name}_TOP",
        (
            center_x,
            y,
            top_z
        ),
        (
            width,
            rail_depth,
            rail_height
        ),
        material
    )

    # Bottom rail

    bottom_z = (
        z_min + 0.12
    )

    add_box(
        f"{name}_BOTTOM",
        (
            center_x,
            y,
            bottom_z
        ),
        (
            width,
            rail_depth,
            rail_height
        ),
        material
    )

    # Balusters

    baluster_bottom = (
        bottom_z
        + rail_height / 2
    )

    baluster_top = (
        top_z
        - rail_height / 2
    )

    baluster_height = (
        baluster_top
        - baluster_bottom
    )

    baluster_center_z = (
        baluster_bottom
        + baluster_height / 2
    )

    usable_width = max(
        0.0,
        width - 0.16
    )

    count = max(
        2,
        int(
            usable_width
            / baluster_spacing
        ) + 1
    )

    start_x = x_min + 0.08
    end_x = x_max - 0.08

    for i in range(count):

        if count == 1:
            x = center_x
        else:
            x = (
                start_x
                + (
                    end_x - start_x
                )
                * i
                / (count - 1)
            )

        add_box(
            f"{name}_BALUSTER_{i + 1:02d}",
            (
                x,
                y,
                baluster_center_z
            ),
            (
                baluster_width,
                baluster_depth,
                baluster_height
            ),
            material
        )


# ============================================================
# PATH INTERPOLATION
# ============================================================

def prepare_path(points):

    blender_points = [
        Vector(
            (
                bx(p["x"]),
                p["y"],
                0.0
            )
        )
        for p in points
    ]

    lengths = []
    total = 0.0

    for i in range(
        len(blender_points) - 1
    ):

        length = (
            blender_points[i + 1]
            - blender_points[i]
        ).length

        lengths.append(length)
        total += length

    return (
        blender_points,
        lengths,
        total
    )


def interpolate_path(
    prepared_path,
    t
):

    (
        blender_points,
        segment_lengths,
        total_length
    ) = prepared_path

    target_distance = (
        max(0.0, min(1.0, t))
        * total_length
    )

    accumulated = 0.0

    for i, segment_length in enumerate(
        segment_lengths
    ):

        if (
            accumulated
            + segment_length
            >= target_distance
        ):

            local_t = (
                target_distance
                - accumulated
            ) / segment_length

            p1 = blender_points[i]
            p2 = blender_points[i + 1]

            position = p1.lerp(
                p2,
                local_t
            )

            direction = (
                p2 - p1
            ).normalized()

            return (
                position,
                direction
            )

        accumulated += segment_length

    direction = (
        blender_points[-1]
        - blender_points[-2]
    ).normalized()

    return (
        blender_points[-1].copy(),
        direction
    )


# ============================================================
# IRREGULAR STONE
# ============================================================

def add_irregular_stone(
    name,
    center,
    direction,
    width,
    length,
    shape,
    material,
    rotation_offset_deg=0.0,
    thickness=0.055
):
    """
    Creates an independent irregular polygonal stone.

    'shape' contains normalized (x,y) coordinates.

    This is deterministic:
    no random module is used.
    """

    path_angle = math.atan2(
        direction.y,
        direction.x
    )

    angle = (
        path_angle
        + math.radians(
            rotation_offset_deg
        )
    )

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    bottom_z = 0.005
    top_z = (
        bottom_z + thickness
    )

    bottom_vertices = []
    top_vertices = []

    for sx, sy in shape:

        local_x = (
            sx * width
        )

        local_y = (
            sy * length
        )

        rotated_x = (
            local_x * cos_a
            - local_y * sin_a
        )

        rotated_y = (
            local_x * sin_a
            + local_y * cos_a
        )

        bottom_vertices.append(
            (
                center.x + rotated_x,
                center.y + rotated_y,
                bottom_z
            )
        )

        top_vertices.append(
            (
                center.x + rotated_x,
                center.y + rotated_y,
                top_z
            )
        )

    vertices = (
        bottom_vertices
        + top_vertices
    )

    n = len(shape)

    faces = []

    # Bottom face
    faces.append(
        tuple(
            range(n - 1, -1, -1)
        )
    )

    # Top face
    faces.append(
        tuple(
            range(n, 2 * n)
        )
    )

    # Side faces

    for i in range(n):

        next_i = (
            (i + 1) % n
        )

        faces.append(
            (
                i,
                next_i,
                n + next_i,
                n + i
            )
        )

    mesh = bpy.data.meshes.new(
        f"{name}_MESH"
    )

    mesh.from_pydata(
        vertices,
        [],
        faces
    )

    mesh.update()

    obj = bpy.data.objects.new(
        name,
        mesh
    )

    bpy.context.collection.objects.link(
        obj
    )

    if material:
        obj.data.materials.append(
            material
        )

    return obj


# ============================================================
# PATH STONES
# ============================================================

def add_path_stones(
    points,
    path_width,
    material
):
    """
    Builds PATH-01 as separated irregular stones.

    The centerline remains authoritative.

    There are no random values.

    Several rows contain two stones to break the visual
    impression of a continuous slab.
    """

    prepared = prepare_path(
        points
    )

    # --------------------------------------------------------
    # NORMALIZED POLYGON SHAPES
    # --------------------------------------------------------

    shapes = [

        [
            (-0.48, -0.30),
            (-0.12, -0.48),
            (0.36, -0.39),
            (0.50, -0.05),
            (0.39, 0.36),
            (0.05, 0.48),
            (-0.40, 0.34)
        ],

        [
            (-0.43, -0.38),
            (0.05, -0.49),
            (0.44, -0.27),
            (0.49, 0.14),
            (0.24, 0.45),
            (-0.18, 0.42),
            (-0.50, 0.10)
        ],

        [
            (-0.50, -0.18),
            (-0.25, -0.46),
            (0.25, -0.43),
            (0.48, -0.12),
            (0.38, 0.35),
            (-0.02, 0.48),
            (-0.43, 0.27)
        ],

        [
            (-0.45, -0.35),
            (0.10, -0.46),
            (0.47, -0.20),
            (0.42, 0.30),
            (0.08, 0.47),
            (-0.34, 0.39),
            (-0.49, 0.02)
        ]
    ]

    # --------------------------------------------------------
    # STONE SPECIFICATION
    #
    # t        = longitudinal position
    # lateral  = offset from centerline
    # width
    # length
    # shape
    # rotation
    # --------------------------------------------------------

    stone_specs = [

        # Near porch

        (0.045, -0.28, 0.62, 0.46, 0, -7),
        (0.050,  0.31, 0.58, 0.42, 2,  5),

        (0.145,  0.02, 0.72, 0.50, 1, -3),

        (0.245, -0.30, 0.55, 0.47, 3,  8),
        (0.250,  0.31, 0.60, 0.44, 0, -6),

        (0.350, -0.04, 0.70, 0.52, 2,  4),

        (0.455, -0.32, 0.57, 0.45, 1, -5),
        (0.460,  0.30, 0.55, 0.48, 3,  7),

        (0.565,  0.03, 0.74, 0.49, 0, -4),

        (0.670, -0.29, 0.58, 0.44, 2,  6),
        (0.675,  0.32, 0.54, 0.46, 1, -7),

        (0.780, -0.02, 0.68, 0.50, 3,  5),

        (0.885, -0.31, 0.56, 0.43, 0, -6),
        (0.890,  0.30, 0.59, 0.45, 2,  8),

        (0.975,  0.00, 0.66, 0.46, 1, -2)
    ]

    max_lateral = (
        path_width / 2
        - 0.25
    )

    for index, spec in enumerate(
        stone_specs,
        start=1
    ):

        (
            t,
            lateral,
            width,
            length,
            shape_index,
            rotation
        ) = spec

        position, direction = (
            interpolate_path(
                prepared,
                t
            )
        )

        lateral = max(
            -max_lateral,
            min(
                max_lateral,
                lateral
            )
        )

        perpendicular = Vector(
            (
                -direction.y,
                direction.x,
                0.0
            )
        )

        center = (
            position
            + perpendicular
            * lateral
        )

        add_irregular_stone(
            name=(
                f"PATH_STONE_{index:03d}"
            ),
            center=center,
            direction=direction,
            width=width,
            length=length,
            shape=shapes[
                shape_index
            ],
            material=material,
            rotation_offset_deg=rotation,
            thickness=(
                0.045
                + (
                    index % 3
                ) * 0.008
            )
        )


# ============================================================
# RENDER
# ============================================================

def add_vegetation_cluster(name, x, y, height, radius, material):
    """Provisional deterministic low-poly vegetation."""

    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=1.0,
        location=(x, y, height * 0.42)
    )

    shrub = bpy.context.object
    shrub.name = name
    shrub.scale = (
        radius,
        radius * 0.82,
        height * 0.42
    )
    shrub.data.materials.append(material)



def add_conifer(name, x, y, height, material_trunk, material_needles):
    """Deterministic low-poly conifer for TREE-LINE blocking."""

    trunk_height = height * 0.38

    add_cylinder(
        f"{name}_TRUNK",
        (x, y, trunk_height / 2),
        radius=height * 0.035,
        depth=trunk_height,
        material=material_trunk
    )

    crown_specs = [
        (0.38, 0.42, 0.30),
        (0.55, 0.34, 0.27),
        (0.70, 0.25, 0.23),
    ]

    for i, (z_ratio, radius_ratio, depth_ratio) in enumerate(
        crown_specs,
        start=1
    ):
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=height * radius_ratio,
            radius2=0.0,
            depth=height * depth_ratio,
            location=(
                x,
                y,
                height * z_ratio
            )
        )

        crown = bpy.context.object
        crown.name = f"{name}_CROWN_{i}"
        crown.data.materials.append(material_needles)



def add_rain_field(material):
    """Deterministic rain blocking for CAM-001."""

    drop_count = 420

    for i in range(drop_count):
        # Deterministic pseudo-distribution. No random module.
        x = -6.5 + ((i * 37) % 130) / 10.0
        y =  1.5 + ((i * 53) % 130) / 10.0
        z =  0.4 + ((i * 29) % 55) / 10.0

        # Three deterministic drop lengths.
        length = 0.10 + (i % 4) * 0.035

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=6,
            radius=0.003,
            depth=length,
            location=(x, y, z)
        )

        drop = bpy.context.object
        drop.name = f"RAIN_{i + 1:03d}"

        # Slight wind slant.
        drop.rotation_euler[1] = math.radians(-12.0)

        drop.data.materials.append(material)



def add_fog_volume(name, location, scale, density):
    """Very light local atmospheric fog volume."""

    bpy.ops.mesh.primitive_cube_add(
        location=location
    )

    fog = bpy.context.object
    fog.name = name
    fog.scale = scale

    mat = bpy.data.materials.new(
        name=f"{name}_MATERIAL"
    )

    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    output = nodes.new(
        "ShaderNodeOutputMaterial"
    )

    volume = nodes.new(
        "ShaderNodeVolumePrincipled"
    )

    volume.inputs["Density"].default_value = density

    volume.inputs["Color"].default_value = (
        0.32,
        0.40,
        0.50,
        1.0
    )

    links.new(
        volume.outputs["Volume"],
        output.inputs["Volume"]
    )

    fog.data.materials.append(mat)



def render_camera(
    scene,
    camera,
    filename
):

    scene.camera = camera

    scene.render.filepath = str(
        RENDER_DIR / filename
    )

    print()
    print(
        f"Rendering {camera.name}"
    )

    print(
        f"Output: {scene.render.filepath}"
    )

    bpy.ops.render.render(
        write_still=True
    )


# ============================================================
# RESET
# ============================================================

clear_scene()


# ============================================================
# SCENE
# ============================================================

scene = bpy.context.scene

scene.render.engine = (
    "BLENDER_EEVEE_NEXT"
)

scene.render.resolution_x = 540
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = (
    "PNG"
)

scene.render.film_transparent = False

scene.world.color = (
    0.008,
    0.018,
    0.032
)

try:
    scene.view_settings.look = (
        "AgX - Medium High Contrast"
    )
except Exception:
    pass


# ============================================================
# MATERIALS
# ============================================================

mat_cabin = make_wood_material(
    "MAT_CABIN",
    dark=(0.055, 0.018, 0.008),
    light=(0.28, 0.10, 0.025)
)

mat_gable = make_wood_material(
    "MAT_GABLE",
    dark=(0.065, 0.022, 0.010),
    light=(0.30, 0.11, 0.030)
)

mat_roof = make_material(
    "MAT_ROOF",
    (0.10, 0.07, 0.05)
)

mat_chimney = make_material(
    "MAT_CHIMNEY",
    (0.24, 0.23, 0.21)
)

mat_porch = make_material(
    "MAT_PORCH",
    (0.30, 0.18, 0.08)
)

mat_window = make_material(
    "MAT_WINDOW",
    (0.90, 0.65, 0.18)
)

mat_path = make_material(
    "MAT_PATH",
    (0.18, 0.18, 0.18)
)

mat_fence = make_material(
    "MAT_FENCE",
    (0.20, 0.11, 0.05)
)

mat_lamp = make_material(
    "MAT_LAMP",
    (0.80, 0.48, 0.08)
)

mat_rain = make_material(
    "MAT_RAIN",
    (0.42, 0.55, 0.68)
)


mat_tree_trunk = make_material(
    "MAT_TREE_TRUNK",
    (0.10, 0.055, 0.025)
)

mat_tree_needles = make_material(
    "MAT_TREE_NEEDLES",
    (0.025, 0.065, 0.030)
)


mat_vegetation = make_material(
    "MAT_VEGETATION",
    (0.055, 0.11, 0.045)
)


mat_ground = make_material(
    "MAT_GROUND",
    (0.06, 0.09, 0.05)
)

mat_door = make_material(
    "MAT_DOOR",
    (0.45, 0.08, 0.04)
)


# ============================================================
# GROUND
# ============================================================

add_box(
    "GROUND",
    (
        0,
        4,
        -0.10
    ),
    (
        22,
        22,
        0.20
    ),
    mat_ground
)


# ============================================================
# CABIN
# ============================================================

cabin = objects["CABIN-01"]

cabin_position = cabin["position"]
cabin_dimensions = cabin["dimensions"]
cabin_walls = cabin["walls"]

cabin_width = (
    cabin_dimensions["width"]
)

cabin_depth = (
    cabin_dimensions["depth"]
)

wall_base_z = (
    cabin_walls["base_z"]
)

wall_top_z = (
    cabin_walls["top_z"]
)

wall_height = (
    wall_top_z
    - wall_base_z
)

cabin_x = bx(
    cabin_position["x"]
)

cabin_y = (
    cabin_position["y"]
)

front_y = (
    cabin["front_facade"]["y"]
)


# CABIN-01 is a real hollow shell, not a solid blocking cube.
# Exterior dimensions remain identical to geometry.json.

wall_thickness = 0.14
half_width = cabin_width / 2

back_y = front_y - cabin_depth


def add_front_wall_segment(
    name,
    canonical_x_min,
    canonical_x_max,
    z_min,
    z_max,
):
    x_a = bx(canonical_x_min)
    x_b = bx(canonical_x_max)

    x_min = min(x_a, x_b)
    x_max = max(x_a, x_b)

    add_box(
        name,
        (
            (x_min + x_max) / 2,
            front_y - wall_thickness / 2,
            (z_min + z_max) / 2,
        ),
        (
            x_max - x_min,
            wall_thickness,
            z_max - z_min,
        ),
        mat_cabin,
    )


# ------------------------------------------------------------
# SIDE WALLS
# ------------------------------------------------------------

add_box(
    "CABIN-WALL-LEFT",
    (
        cabin_x - half_width + wall_thickness / 2,
        cabin_y,
        wall_base_z + wall_height / 2,
    ),
    (
        wall_thickness,
        cabin_depth,
        wall_height,
    ),
    mat_cabin,
)

add_box(
    "CABIN-WALL-RIGHT",
    (
        cabin_x + half_width - wall_thickness / 2,
        cabin_y,
        wall_base_z + wall_height / 2,
    ),
    (
        wall_thickness,
        cabin_depth,
        wall_height,
    ),
    mat_cabin,
)


# ------------------------------------------------------------
# REAR WALL
# ------------------------------------------------------------

add_box(
    "CABIN-WALL-REAR",
    (
        cabin_x,
        back_y + wall_thickness / 2,
        wall_base_z + wall_height / 2,
    ),
    (
        cabin_width,
        wall_thickness,
        wall_height,
    ),
    mat_cabin,
)


# Door geometry is needed here to build the physical opening
# before the later DOOR rendering block.

door = objects["DOOR-01"]
door_position = door["position"]
door_w = door["dimensions"]["width"]
door_h = door["dimensions"]["height"]


# ------------------------------------------------------------
# FRONT WALL
#
# Canonical facade:
#
# cabin:  x = -3.0 .. 3.0
# door:   x = -0.5 .. 0.5
# window: x = 0.975 .. 2.625
#
# Both openings are physically real.
# ------------------------------------------------------------

door_x_min = (
    door_position["x"]
    - door_w / 2
)

door_x_max = (
    door_position["x"]
    + door_w / 2
)

door_z_min = door_position["z"]
door_z_max = door_position["z"] + door_h

window_opening = objects[
    "WINDOW-FRONT-01"
]["opening"]

window_x_min = window_opening["x_min"]
window_x_max = window_opening["x_max"]
window_z_min = window_opening["z_min"]
window_z_max = window_opening["z_max"]


# Full-height wall left of door.
add_front_wall_segment(
    "CABIN-FRONT-LEFT",
    -half_width,
    door_x_min,
    wall_base_z,
    wall_top_z,
)

# Wall above door.
add_front_wall_segment(
    "CABIN-FRONT-ABOVE-DOOR",
    door_x_min,
    door_x_max,
    door_z_max,
    wall_top_z,
)

# Wall between door and front window.
add_front_wall_segment(
    "CABIN-FRONT-MIDDLE",
    door_x_max,
    window_x_min,
    wall_base_z,
    wall_top_z,
)

# Wall below window.
add_front_wall_segment(
    "CABIN-FRONT-BELOW-WINDOW",
    window_x_min,
    window_x_max,
    wall_base_z,
    window_z_min,
)

# Wall above window.
add_front_wall_segment(
    "CABIN-FRONT-ABOVE-WINDOW",
    window_x_min,
    window_x_max,
    window_z_max,
    wall_top_z,
)

# Remaining facade right of window.
add_front_wall_segment(
    "CABIN-FRONT-RIGHT",
    window_x_max,
    half_width,
    wall_base_z,
    wall_top_z,
)



# ============================================================
# ROOF + GABLE
# ============================================================

roof = objects["ROOF-01"]

roof_center = roof["center"]

roof_x = bx(
    roof_center["x"]
)

roof_y = (
    roof_center["y"]
)

roof_width = (
    roof["width"]
)

roof_depth = (
    roof["depth"]
)

roof_eave_z = (
    roof["eave_z"]
)

roof_ridge_z = (
    roof["ridge_z"]
)


add_front_gable(
    "FRONT-GABLE-01",
    center_x=cabin_x,
    front_y=front_y + 0.015,
    width=cabin_width,
    base_z=wall_top_z,
    ridge_z=roof_ridge_z,
    material=mat_gable
)


add_roof_planes(
    "ROOF-01",
    center_x=roof_x,
    center_y=roof_y,
    width=roof_width,
    depth=roof_depth,
    eave_z=roof_eave_z,
    ridge_z=roof_ridge_z,
    material=mat_roof
)


# ============================================================
# CHIMNEY
# ============================================================

chimney = objects["CHIMNEY-01"]

chimney_pos = chimney["position"]
chimney_dim = chimney["dimensions"]

chimney_height = (
    chimney_dim["top_z"]
    - chimney_dim["base_z"]
)


add_box(
    "CHIMNEY-01",
    point_xyz(
        chimney_pos["x"],
        chimney_pos["y"],
        chimney_dim["base_z"]
        + chimney_height / 2
    ),
    (
        chimney_dim["width"],
        chimney_dim["depth"],
        chimney_height
    ),
    mat_chimney
)


# ============================================================
# DOOR
# ============================================================

door = objects["DOOR-01"]

door_position = door["position"]

door_w = (
    door["dimensions"]["width"]
)

door_h = (
    door["dimensions"]["height"]
)


add_box(
    "DOOR-01",
    point_xyz(
        door_position["x"],
        door_position["y"] + 0.03,
        door_position["z"]
        + door_h / 2
    ),
    (
        door_w,
        0.08,
        door_h
    ),
    mat_door
)


# ============================================================
# FRONT WINDOW
# ============================================================

window = objects[
    "WINDOW-FRONT-01"
]

window_position = (
    window[
        "position_relative_to_DOOR-01"
    ]
)

wx = window_position["x"]
wy = window_position["y"]
wz = window_position["z"]

ww = (
    window["dimensions"]["width"]
)

wh = (
    window["dimensions"]["height"]
)

window_center_z = (
    wz + wh / 2
)


window_panel = add_box(
    "WINDOW-FRONT-01",
    point_xyz(
        wx,
        wy + 0.04,
        window_center_z
    ),
    (
        ww,
        0.06,
        wh
    ),
    mat_window
)


# ============================================================
# FRONT WINDOW MULLIONS
# ============================================================

columns = (
    window[
        "pane_layout"
    ]["columns"]
)

rows = (
    window[
        "pane_layout"
    ]["rows"]
)

mullion_width = 0.06


for i in range(
    1,
    columns
):

    canonical_x = (
        wx
        - ww / 2
        + ww * i / columns
    )

    add_box(
        f"WINDOW_FRONT_MULLION_V_{i}",
        point_xyz(
            canonical_x,
            wy,
            window_center_z
        ),
        (
            mullion_width,
            0.10,
            wh
        ),
        mat_cabin
    )


for i in range(
    1,
    rows
):

    z = (
        wz
        + wh * i / rows
    )

    add_box(
        f"WINDOW_FRONT_MULLION_H_{i}",
        point_xyz(
            wx,
            wy,
            z
        ),
        (
            ww,
            0.10,
            mullion_width
        ),
        mat_cabin
    )


# ============================================================
# UPPER WINDOW
# ============================================================

upper_window = objects[
    "WINDOW-UPPER-01"
]

upper_pos = (
    upper_window[
        "position_relative_to_DOOR-01"
    ]
)

uwx = upper_pos["x"]
uwz = upper_pos["z"]

uww = (
    upper_window["dimensions"]["width"]
)

uwh = (
    upper_window["dimensions"]["height"]
)

upper_center_z = (
    uwz + uwh / 2
)


add_box(
    "WINDOW-UPPER-01",
    point_xyz(
        uwx,
        front_y + 0.05,
        upper_center_z
    ),
    (
        uww,
        0.08,
        uwh
    ),
    mat_window
)


upper_frame = 0.06


add_box(
    "WINDOW_UPPER_FRAME_LEFT",
    point_xyz(
        uwx + uww / 2,
        front_y + 0.055,
        upper_center_z
    ),
    (
        upper_frame,
        0.10,
        uwh
    ),
    mat_cabin
)


add_box(
    "WINDOW_UPPER_FRAME_RIGHT",
    point_xyz(
        uwx - uww / 2,
        front_y + 0.055,
        upper_center_z
    ),
    (
        upper_frame,
        0.10,
        uwh
    ),
    mat_cabin
)


add_box(
    "WINDOW_UPPER_FRAME_TOP",
    point_xyz(
        uwx,
        front_y + 0.055,
        uwz + uwh
    ),
    (
        uww,
        0.10,
        upper_frame
    ),
    mat_cabin
)


add_box(
    "WINDOW_UPPER_FRAME_BOTTOM",
    point_xyz(
        uwx,
        front_y + 0.055,
        uwz
    ),
    (
        uww,
        0.10,
        upper_frame
    ),
    mat_cabin
)


# ============================================================
# PORCH
# ============================================================

porch = objects["PORCH-01"]
vol = porch["volume"]

xa = bx(
    vol["x_min"]
)

xb = bx(
    vol["x_max"]
)

px_min = min(xa, xb)
px_max = max(xa, xb)

py_min = vol["y_min"]
py_max = vol["y_max"]

porch_width = (
    px_max - px_min
)

porch_depth = (
    py_max - py_min
)

porch_center_x = (
    px_min + px_max
) / 2

porch_center_y = (
    py_min + py_max
) / 2


# ============================================================
# PORCH FLOOR
# ============================================================

floor = porch["floor"]

add_box(
    "PORCH_FLOOR",
    (
        porch_center_x,
        porch_center_y,
        floor["z"]
    ),
    (
        porch_width,
        porch_depth,
        floor["thickness"]
    ),
    mat_porch
)


# ============================================================
# PORCH ROOF
# ============================================================

porch_roof = porch["roof"]

porch_roof_height = (
    porch_roof["z_max"]
    - porch_roof["z_min"]
)


add_box(
    "PORCH_ROOF",
    (
        porch_center_x,
        porch_center_y,
        (
            porch_roof["z_min"]
            + porch_roof["z_max"]
        ) / 2
    ),
    (
        porch_width,
        porch_depth,
        porch_roof_height
    ),
    mat_porch
)


# ============================================================
# PORCH RAILING
# ============================================================

railing = porch["railing"]

rail_y = (
    railing["front_y"]
)

rail_z_min = (
    railing["z_min"]
)

rail_z_max = (
    railing["z_max"]
)


for segment in railing["segments"]:

    add_open_railing(
        name=segment["id"],
        canonical_x_min=segment["x_min"],
        canonical_x_max=segment["x_max"],
        y=rail_y,
        z_min=rail_z_min,
        z_max=rail_z_max,
        material=mat_porch,
        baluster_spacing=0.28
    )


# ============================================================
# PORCH POSTS
# ============================================================

for post in porch["posts"]:

    post_height = (
        post["z_max"]
        - post["z_min"]
    )

    add_box(
        post["id"],
        point_xyz(
            post["x"],
            post["y"],
            post["z_min"]
            + post_height / 2
        ),
        (
            0.18,
            0.18,
            post_height
        ),
        mat_porch
    )


# ============================================================
# STAIRS
# ============================================================

stairs = objects["STAIRS-01"]

stairs_x = bx(
    stairs["center"]["x"]
)

stairs_y = (
    stairs["center"]["y"]
)

stairs_width = (
    stairs["width"]
)


for i in range(3):

    depth = 0.35
    height = 0.12

    add_box(
        f"STAIR_{i + 1}",
        (
            stairs_x,
            stairs_y
            + 0.35
            + i * depth,
            height / 2
            + i * height
        ),
        (
            stairs_width,
            depth,
            height
        ),
        mat_porch
    )


# ============================================================
# PATH — IRREGULAR STONES
# ============================================================

path = objects["PATH-01"]

add_path_stones(
    points=path["centerline"],
    path_width=path["approx_width"],
    material=mat_path
)



# ============================================================
# LOW VEGETATION — PROVISIONAL / DETERMINISTIC
# ============================================================

vegetation_specs = [
    ("VEG_LEFT_01",  -1.8, 1.9, 0.45, 0.38),
    ("VEG_LEFT_02",  -2.2, 2.6, 0.60, 0.46),
    ("VEG_LEFT_03",  -1.7, 3.3, 0.52, 0.42),
    ("VEG_LEFT_04",  -2.5, 3.7, 0.72, 0.52),
    ("VEG_LEFT_05",  -1.9, 4.4, 0.58, 0.44),
    ("VEG_LEFT_06",  -2.7, 5.0, 0.78, 0.56),
    ("VEG_LEFT_07",  -1.8, 5.6, 0.48, 0.40),
    ("VEG_LEFT_08",  -2.6, 6.1, 0.68, 0.50),
    ("VEG_LEFT_09",  -1.9, 6.7, 0.55, 0.43),
    ("VEG_LEFT_10",  -2.8, 7.1, 0.74, 0.54),

    ("VEG_RIGHT_01",  1.7, 1.8, 0.48, 0.40),
    ("VEG_RIGHT_02",  2.3, 2.4, 0.66, 0.48),
    ("VEG_RIGHT_03",  1.8, 3.1, 0.54, 0.42),
    ("VEG_RIGHT_04",  2.6, 3.6, 0.76, 0.54),
    ("VEG_RIGHT_05",  1.9, 4.2, 0.50, 0.40),
    ("VEG_RIGHT_06",  2.8, 4.8, 0.70, 0.52),
    ("VEG_RIGHT_07",  2.0, 5.5, 0.58, 0.44),
    ("VEG_RIGHT_08",  2.9, 6.0, 0.80, 0.56),
    ("VEG_RIGHT_09",  2.1, 6.6, 0.52, 0.42),
    ("VEG_RIGHT_10",  3.0, 7.1, 0.72, 0.52),
]

for name, canonical_x, y, height, radius in vegetation_specs:
    add_vegetation_cluster(
        name,
        bx(canonical_x),
        y,
        height,
        radius,
        mat_vegetation
    )


# ============================================================
# LANTERNS
# ============================================================

for lamp_id in (
    "LAMP-EXT-01",
    "LAMP-EXT-02"
):

    lamp = objects[lamp_id]

    pos = lamp["position"]
    height = lamp["height"]

    add_cylinder(
        lamp_id,
        point_xyz(
            pos["x"],
            pos["y"],
            height / 2
        ),
        radius=0.13,
        depth=height,
        material=mat_lamp
    )

    light_data = bpy.data.lights.new(
        name=f"{lamp_id}_LIGHT",
        type="POINT"
    )

    light_data.energy = 60

    light_data.color = (
        1.0,
        0.55,
        0.20
    )

    light_obj = bpy.data.objects.new(
        f"{lamp_id}_LIGHT",
        light_data
    )

    bpy.context.collection.objects.link(
        light_obj
    )

    light_obj.location = point_xyz(
        pos["x"],
        pos["y"],
        height
    )


# ============================================================
# FENCE
# ============================================================

fence = objects["FENCE-01"]

fx = bx(
    fence["start"]["x"]
)

fy = fence["start"]["y"]
fz = fence["start"]["z"]

fh = fence["approx_height"]

direction = Vector(
    (
        bx(
            fence["direction"]["x"]
        ),
        fence["direction"]["y"],
        0
    )
).normalized()


post_spacing = 0.9
post_count = 5

fence_points = []


for i in range(post_count):

    p = (
        Vector(
            (fx, fy, fz)
        )
        + direction
        * (
            i * post_spacing
        )
    )

    fence_points.append(p)

    add_box(
        f"FENCE_POST_{i + 1}",
        (
            p.x,
            p.y,
            fh / 2
        ),
        (
            0.12,
            0.12,
            fh
        ),
        mat_fence
    )


for i in range(
    len(fence_points) - 1
):

    p1 = fence_points[i]
    p2 = fence_points[i + 1]

    for z in (
        0.35,
        0.70
    ):

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        length = math.sqrt(
            dx * dx
            + dy * dy
        )

        angle = math.atan2(
            dy,
            dx
        )

        rail = add_box(
            f"FENCE_RAIL_{i}_{z}",
            (
                (
                    p1.x + p2.x
                ) / 2,
                (
                    p1.y + p2.y
                ) / 2,
                z
            ),
            (
                length,
                0.08,
                0.10
            ),
            mat_fence
        )

        rail.rotation_euler[2] = (
            angle
        )



# ============================================================
# TREE LINE — PROVISIONAL / DETERMINISTIC
# ============================================================

tree_specs = [
    ("TREE_01", -5.0, -1.5, 5.8),
    ("TREE_02", -5.8, -3.2, 7.0),
    ("TREE_03", -4.8, -5.0, 6.3),
    ("TREE_04", -3.8, -6.2, 7.5),

    ("TREE_05", -2.0, -6.5, 6.8),
    ("TREE_06",  0.0, -6.8, 7.8),
    ("TREE_07",  2.0, -6.5, 6.6),
    ("TREE_08",  3.8, -6.0, 7.4),

    ("TREE_09",  4.9, -4.8, 6.5),
    ("TREE_10",  5.8, -3.0, 7.2),
    ("TREE_11",  5.0, -1.2, 5.9),

    ("TREE_12", -6.2,  0.8, 6.6),
    ("TREE_13",  6.3,  0.6, 6.9),
]

for name, canonical_x, y, height in tree_specs:
    add_conifer(
        name,
        bx(canonical_x),
        y,
        height,
        mat_tree_trunk,
        mat_tree_needles
    )


# ============================================================
# RAIN — PROVISIONAL / DETERMINISTIC
# ============================================================

add_rain_field(
    material=mat_rain
)


# ============================================================
# CAM-001 — LOCKED
# ============================================================

camera_config = objects["CAM-001"]

if (
    camera_config["coordinate_space"]
    != "blender"
):
    raise ValueError(
        "CAM-001 must use coordinate_space='blender'"
    )

if not camera_config["locked"]:
    raise ValueError(
        "CAM-001 must remain locked"
    )

cam_location = (
    camera_config["location"]
)

cam_target = (
    camera_config["target"]
)


cam1 = add_camera(
    "CAM-001",
    (
        cam_location["x"],
        cam_location["y"],
        cam_location["z"]
    ),
    (
        cam_target["x"],
        cam_target["y"],
        cam_target["z"]
    ),
    lens=camera_config["lens_mm"]
)


# ============================================================
# CAM-002 — PROVISIONAL
# ============================================================

cam2 = add_camera(
    "CAM-002",
    (
        bx(1.8),
        -1.0,
        1.55
    ),
    (
        bx(1.8),
        5.0,
        1.40
    ),
    lens=32
)


# ============================================================
# GENERAL LIGHT
# ============================================================

light_data = bpy.data.lights.new(
    name="MOON_LIGHT",
    type="AREA"
)

light_data.energy = 250
light_data.shape = "DISK"
light_data.size = 8

light_obj = bpy.data.objects.new(
    "MOON_LIGHT",
    light_data
)

bpy.context.collection.objects.link(
    light_obj
)

light_obj.location = (
    -3,
    4,
    8
)

direction_to_scene = (
    Vector(
        (0, 1, 1)
    )
    - light_obj.location
)

light_obj.rotation_euler = (
    direction_to_scene
    .to_track_quat(
        "-Z",
        "Y"
    )
    .to_euler()
)


# ============================================================
# RENDER CAM-001 + CAM-002
# ============================================================

render_camera(
    scene,
    cam1,
    "CAM-001_exterior.png"
)

# CAM-002 looks through the same physical front window.
# The cabin is now a hollow shell; only the provisional
# opaque window pane is hidden for the interior view.
window_panel.hide_render = True

render_camera(
    scene,
    cam2,
    "CAM-002_interior.png"
)

window_panel.hide_render = False

scene.camera = cam1


# ============================================================
# SAVE
# ============================================================

bpy.ops.wm.save_as_mainfile(
    filepath=str(
        OUTPUT_BLEND
    )
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 72)

print(
    "EXP-001 — IRREGULAR STONE PATH"
)

print("=" * 72)

print()
print(
    f"Geometry: {GEOMETRY_PATH}"
)

print()
print("CAM-001:")
print("  LOCKED")
print(
    f"  lens = "
    f"{camera_config['lens_mm']} mm"
)

print()
print("PATH-01:")
print(
    f"  surface = "
    f"{path.get('surface')}"
)

print(
    "  centerline = PRESERVED"
)

print(
    "  rectangular slab = DISABLED"
)

print(
    "  irregular polygon stones = ENABLED"
)

print(
    "  separated stones = ENABLED"
)

print(
    "  deterministic = YES"
)

print(
    "  random = NO"
)

print()
print("PRESERVED:")
print("  cabin")
print("  roof")
print("  gable")
print("  chimney")
print("  door")
print("  windows")
print("  porch")
print("  open railing")
print("  stairs")
print("  lanterns")
print("  fence")

print()
print("OUTPUT:")
print(
    f"  "
    f"{RENDER_DIR / 'CAM-001_exterior.png'}"
)
print(
    f"  {OUTPUT_BLEND}"
)

print()
print("=" * 72)