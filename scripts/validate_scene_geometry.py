import json
import math
from pathlib import Path

BASE = Path("videos/EXP-001")

GEOMETRY_FILE = BASE / "geometry.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def vec_sub(a, b):
    return {
        "x": a["x"] - b["x"],
        "y": a["y"] - b["y"],
        "z": a.get("z", 0.0) - b.get("z", 0.0),
    }


def vec_add(a, b):
    return {
        "x": a["x"] + b["x"],
        "y": a["y"] + b["y"],
        "z": a.get("z", 0.0) + b.get("z", 0.0),
    }


def vec_mul(v, scalar):
    return {
        "x": v["x"] * scalar,
        "y": v["y"] * scalar,
        "z": v["z"] * scalar,
    }


def vec_len(v):
    return math.sqrt(
        v["x"] ** 2 +
        v["y"] ** 2 +
        v["z"] ** 2
    )


def normalize(v):
    length = vec_len(v)

    if length == 0:
        return {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        }

    return {
        "x": v["x"] / length,
        "y": v["y"] / length,
        "z": v["z"] / length,
    }


def dot(a, b):
    return (
        a["x"] * b["x"] +
        a["y"] * b["y"] +
        a["z"] * b["z"]
    )


def angle_deg(a, b):
    na = normalize(a)
    nb = normalize(b)

    value = max(
        -1.0,
        min(1.0, dot(na, nb))
    )

    return math.degrees(math.acos(value))


def point_from_relative(base, relative):
    return {
        "x": base["x"] + relative["x"],
        "y": base["y"] + relative["y"],
        "z": base.get("z", 0.0) + relative.get("z", 0.0),
    }


def classify_horizontal_side(camera_position, forward, point):
    to_point = vec_sub(point, camera_position)

    right = {
        "x": forward["y"],
        "y": -forward["x"],
        "z": 0.0
    }

    side_value = dot(to_point, right)

    if side_value > 0.25:
        return "right"

    if side_value < -0.25:
        return "left"

    return "center"


def ray_intersects_box(origin, direction, box):
    """
    Intersección rayo / AABB.

    Devuelve:
        (True, distancia)
        (False, None)
    """

    t_min = -math.inf
    t_max = math.inf

    axes = ["x", "y", "z"]

    for axis in axes:
        origin_value = origin[axis]
        direction_value = direction[axis]

        min_value = box[f"{axis}_min"]
        max_value = box[f"{axis}_max"]

        if abs(direction_value) < 1e-9:
            if (
                origin_value < min_value
                or origin_value > max_value
            ):
                return False, None

            continue

        t1 = (
            min_value - origin_value
        ) / direction_value

        t2 = (
            max_value - origin_value
        ) / direction_value

        if t1 > t2:
            t1, t2 = t2, t1

        t_min = max(t_min, t1)
        t_max = min(t_max, t2)

        if t_min > t_max:
            return False, None

    if t_max < 0:
        return False, None

    hit_distance = (
        t_min if t_min >= 0 else t_max
    )

    return True, hit_distance


def ray_to_point(camera, point):
    return normalize(
        vec_sub(point, camera)
    )


def report(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


geometry = load_json(GEOMETRY_FILE)
objects = geometry["objects"]

door = objects["DOOR-01"]["position"]

window_rel = (
    objects["WINDOW-FRONT-01"]
    ["position_relative_to_DOOR-01"]
)

window = point_from_relative(
    door,
    window_rel
)

forward = normalize(
    objects["WINDOW-FRONT-01"]
    ["orientation"]
    ["normal_vector"]
)

camera_distance_inside = 1.0

camera = {
    "x": window["x"] - forward["x"] * camera_distance_inside,
    "y": window["y"] - forward["y"] * camera_distance_inside,
    "z": 1.55
}

report("MODELO DE CÁMARA")

print(f"Ventana: {window}")
print(f"Cámara:  {camera}")
print(f"Forward: {forward}")

report("PROYECCIÓN DEL SENDERO")

for index, p in enumerate(
    objects["PATH-01"]["centerline"]
):
    point = {
        "x": p["x"],
        "y": p["y"],
        "z": 0.0
    }

    direction = vec_sub(point, camera)

    print(
        f"P{index}: "
        f"ángulo={angle_deg(forward, direction):5.1f}° "
        f"lado={classify_horizontal_side(camera, forward, point)}"
    )

report("FAROLES")

for object_id in [
    "LAMP-EXT-01",
    "LAMP-EXT-02"
]:
    obj = objects[object_id]

    point = {
        "x": obj["position"]["x"],
        "y": obj["position"]["y"],
        "z": obj["height"]
    }

    direction = vec_sub(point, camera)

    print(
        f"{object_id}: "
        f"distancia={vec_len(direction):5.2f} "
        f"ángulo={angle_deg(forward, direction):5.1f}° "
        f"lado={classify_horizontal_side(camera, forward, point)}"
    )

report("INTERSECCIÓN CON EL PORCHE")

porch_box = objects["PORCH-01"]["volume"]

targets = {}

for index, p in enumerate(
    objects["PATH-01"]["centerline"]
):
    targets[f"PATH-{index}"] = {
        "x": p["x"],
        "y": p["y"],
        "z": 0.0
    }

for object_id in [
    "LAMP-EXT-01",
    "LAMP-EXT-02"
]:
    obj = objects[object_id]

    targets[object_id] = {
        "x": obj["position"]["x"],
        "y": obj["position"]["y"],
        "z": obj["height"]
    }

for name, point in targets.items():
    direction = ray_to_point(
        camera,
        point
    )

    hit, distance = ray_intersects_box(
        camera,
        direction,
        porch_box
    )

    object_distance = vec_len(
        vec_sub(point, camera)
    )

    if hit and distance < object_distance:
        print(
            f"{name:14} -> "
            f"RAYO ATRAVIESA PORCHE "
            f"a {distance:.2f} "
            f"antes del objeto ({object_distance:.2f})"
        )
    else:
        print(
            f"{name:14} -> "
            f"vista sin intersección de volumen principal"
        )

report("ELEMENTOS ESTRUCTURALES DEL PORCHE")

railing = objects["PORCH-01"]["railing"]

print(
    "Barandilla frontal:",
    f"y={railing['front_y']}, "
    f"z={railing['z_min']}..{railing['z_max']}"
)

print()

for post in objects["PORCH-01"]["posts"]:
    print(
        f"{post['id']}: "
        f"x={post['x']} "
        f"y={post['y']} "
        f"z={post['z_min']}..{post['z_max']}"
    )

report("VALIDACIONES")

errors = []
warnings = []

path_points = objects["PATH-01"]["centerline"]

window_path_offset = abs(
    window["x"] -
    path_points[0]["x"]
)

if window_path_offset < 0.5:
    errors.append(
        "La ventana está demasiado alineada con PATH-01."
    )
else:
    print(
        f"OK: ventana desplazada del eje del sendero "
        f"({window_path_offset:.2f})."
    )

lamp1 = objects["LAMP-EXT-01"]
lamp2 = objects["LAMP-EXT-02"]

if (
    lamp1["distance_from_facade"]
    <= lamp2["distance_from_facade"]
):
    errors.append(
        "LAMP-EXT-01 no está más lejos que LAMP-EXT-02."
    )
else:
    print(
        "OK: orden longitudinal de los faroles correcto."
    )

porch = objects["PORCH-01"]

if (
    porch["volume"]["y_min"] > 0.01
    or porch["volume"]["y_max"] <= 0.0
):
    errors.append(
        "El volumen del porche no comienza en la fachada."
    )
else:
    print(
        "OK: volumen del porche comienza en la fachada."
    )

window_x = window["x"]

if not (
    porch["volume"]["x_min"]
    <= window_x
    <= porch["volume"]["x_max"]
):
    errors.append(
        "WINDOW-FRONT-01 queda fuera del rango horizontal del porche."
    )
else:
    print(
        "OK: el porche cubre horizontalmente WINDOW-FRONT-01."
    )

pane = objects["WINDOW-FRONT-01"]["pane_layout"]

if (
    pane["columns"] != 3
    or pane["rows"] != 3
):
    errors.append(
        "La ventana no mantiene la estructura 3x3."
    )
else:
    print(
        "OK: ventana 3x3."
    )

report("RESULTADO")

if errors:
    print("ERRORES:")

    for item in errors:
        print(f"  - {item}")

if warnings:
    print("AVISOS:")

    for item in warnings:
        print(f"  - {item}")

if not errors and not warnings:
    print(
        "GEOMETRÍA COHERENTE. "
        "YA SE MODELA LA OCLUSIÓN DEL PORCHE."
    )

elif not errors:
    print(
        "GEOMETRÍA VÁLIDA CON AVISOS."
    )

else:
    print(
        "GEOMETRÍA NO VÁLIDA."
    )