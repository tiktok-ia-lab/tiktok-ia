import json
import math
from pathlib import Path

BASE = Path("videos/EXP-001")
GEOMETRY_FILE = BASE / "geometry.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sub(a, b):
    return {
        "x": a["x"] - b["x"],
        "y": a["y"] - b["y"],
        "z": a["z"] - b["z"],
    }


def length(v):
    return math.sqrt(
        v["x"] ** 2 +
        v["y"] ** 2 +
        v["z"] ** 2
    )


def normalize(v):
    l = length(v)

    if l == 0:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    return {
        "x": v["x"] / l,
        "y": v["y"] / l,
        "z": v["z"] / l
    }


def ray_box(origin, direction, box):
    t_min = -math.inf
    t_max = math.inf

    for axis in ("x", "y", "z"):
        o = origin[axis]
        d = direction[axis]

        minimum = box[f"{axis}_min"]
        maximum = box[f"{axis}_max"]

        if abs(d) < 1e-9:
            if o < minimum or o > maximum:
                return None
            continue

        t1 = (minimum - o) / d
        t2 = (maximum - o) / d

        if t1 > t2:
            t1, t2 = t2, t1

        t_min = max(t_min, t1)
        t_max = min(t_max, t2)

        if t_min > t_max:
            return None

    if t_max < 0:
        return None

    return t_min if t_min >= 0 else t_max


geometry = load_json(GEOMETRY_FILE)
objects = geometry["objects"]

door = objects["DOOR-01"]["position"]

window_rel = objects["WINDOW-FRONT-01"]["position_relative_to_DOOR-01"]

window = {
    "x": door["x"] + window_rel["x"],
    "y": door["y"] + window_rel["y"],
    "z": door["z"] + window_rel["z"],
}

camera = {
    "x": window["x"],
    "y": -1.0,
    "z": 1.55
}

porch = objects["PORCH-01"]

components = {}


# --------------------------------------------------
# SUELO
# --------------------------------------------------

floor = porch["floor"]

components["PORCH-FLOOR"] = {
    "x_min": porch["volume"]["x_min"],
    "x_max": porch["volume"]["x_max"],
    "y_min": porch["volume"]["y_min"],
    "y_max": porch["volume"]["y_max"],
    "z_min": floor["z"] - floor["thickness"] / 2,
    "z_max": floor["z"] + floor["thickness"] / 2,
}


# --------------------------------------------------
# TECHO
# --------------------------------------------------

roof = porch["roof"]

components["PORCH-ROOF"] = {
    "x_min": porch["volume"]["x_min"],
    "x_max": porch["volume"]["x_max"],
    "y_min": porch["volume"]["y_min"],
    "y_max": porch["volume"]["y_max"],
    "z_min": roof["z_min"],
    "z_max": roof["z_max"],
}


# --------------------------------------------------
# BARANDILLAS POR SEGMENTOS
# --------------------------------------------------

railing = porch["railing"]
railing_thickness = 0.12

for segment in railing["segments"]:
    components[segment["id"]] = {
        "x_min": segment["x_min"],
        "x_max": segment["x_max"],
        "y_min": railing["front_y"] - railing_thickness / 2,
        "y_max": railing["front_y"] + railing_thickness / 2,
        "z_min": railing["z_min"],
        "z_max": railing["z_max"]
    }


# --------------------------------------------------
# POSTES
# --------------------------------------------------

post_thickness = 0.16

for post in porch["posts"]:
    components[post["id"]] = {
        "x_min": post["x"] - post_thickness / 2,
        "x_max": post["x"] + post_thickness / 2,
        "y_min": post["y"] - post_thickness / 2,
        "y_max": post["y"] + post_thickness / 2,
        "z_min": post["z_min"],
        "z_max": post["z_max"],
    }


# --------------------------------------------------
# OBJETIVOS EXTERIORES
# --------------------------------------------------

targets = {}

for index, p in enumerate(objects["PATH-01"]["centerline"]):
    targets[f"PATH-{index}"] = {
        "x": p["x"],
        "y": p["y"],
        "z": 0.0
    }


for object_id in ("LAMP-EXT-01", "LAMP-EXT-02"):
    obj = objects[object_id]

    targets[object_id] = {
        "x": obj["position"]["x"],
        "y": obj["position"]["y"],
        "z": obj["height"]
    }


print()
print("=" * 76)
print("VISIBILIDAD REFINADA A TRAVÉS DEL PORCHE")
print("=" * 76)
print(f"Cámara: {camera}")
print()


results = {}

for target_name, target in targets.items():

    direction = normalize(sub(target, camera))
    target_distance = length(sub(target, camera))

    collisions = []

    for component_name, box in components.items():

        hit = ray_box(camera, direction, box)

        if hit is not None and hit < target_distance:
            collisions.append((hit, component_name))

    collisions.sort()

    if collisions:
        nearest_distance, nearest_component = collisions[0]

        results[target_name] = {
            "visible": False,
            "occluded_by": nearest_component
        }

        print(
            f"{target_name:14} -> "
            f"OCULTO POR {nearest_component:22} "
            f"a {nearest_distance:.2f}"
        )

    else:
        results[target_name] = {
            "visible": True,
            "occluded_by": None
        }

        print(
            f"{target_name:14} -> "
            f"VISIBLE A TRAVÉS DEL PORCHE"
        )


print()
print("=" * 76)
print("HUECO CENTRAL DE ESCALERA")
print("=" * 76)

opening = railing["stair_opening"]

print(
    f"x={opening['x_min']:.2f}..{opening['x_max']:.2f} "
    f"alineado con {opening['aligned_with']}"
)


print()
print("=" * 76)
print("RESUMEN PARA SCENE-002")
print("=" * 76)

visible = [
    name
    for name, result in results.items()
    if result["visible"]
]

hidden = [
    f"{name} ({result['occluded_by']})"
    for name, result in results.items()
    if not result["visible"]
]

print()
print("VISIBLE:")

for name in visible:
    print(f"  - {name}")

print()
print("OCULTO:")

for name in hidden:
    print(f"  - {name}")