"""
build_matt_logo.py
------------------
A clean, web-ready 3D logo of "Matt" — no animation, no ground plane, no camera,
just the four gold letters standing upright and centered at the origin. Export
as .glb and embed on any webpage with <model-viewer>, Three.js, or React Three Fiber.

Run inside Blender, or via blender-mcp execute_blender_code.
"""

import bpy
import math


# ---------- 1. CLEAN start ----------
for obj in list(bpy.data.objects):
    if obj.name.startswith("Matt") or obj.name in ("Cube",):
        bpy.data.objects.remove(obj, do_unlink=True)

# Also clear orphan meshes/curves/materials from prior runs
for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
    for item in list(collection):
        if item.users == 0:
            collection.remove(item)


# ---------- 2. FONT ----------
FONT_PATH = r"C:\Windows\Fonts\BAHNSCHRIFT.TTF"
font = bpy.data.fonts.load(FONT_PATH, check_existing=True)


# ---------- 3. GOLD MATERIAL ----------
gold = bpy.data.materials.new("Matt_Gold")
gold.use_nodes = True
bsdf = gold.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.78, 0.31, 1.0)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.22


# ---------- 4. LETTERS ----------
LETTERS = list("Matt")
letter_objs = []
for i, ch in enumerate(LETTERS):
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = f"Matt_Logo_{i}_{ch}"
    obj.data.font = font
    obj.data.body = ch
    obj.data.extrude = 0.28
    obj.data.bevel_depth = 0.035
    obj.data.bevel_resolution = 4
    obj.data.size = 1.6
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH')
    obj.data.materials.append(gold)
    letter_objs.append(obj)


# ---------- 5. LAY OUT horizontally based on each letter's actual width ----------
GAP = 0.14
widths = [o.dimensions.x for o in letter_objs]
total = sum(widths) + GAP * (len(widths) - 1)
cursor = -total / 2
for obj, w in zip(letter_objs, widths):
    obj.location.x = cursor + w / 2
    obj.location.y = 0
    obj.location.z = 0
    cursor += w + GAP


# ---------- 6. ROTATE to stand text upright ----------
# Blender creates text flat on XY facing +Z. Rotate +90deg around X so it stands in the
# XZ plane with top at +Z (proper "up" after the glTF Y-up conversion). The viewer then
# sees it from the correct angle when camera-orbit is set to "180deg 75deg" or similar.
for obj in letter_objs:
    obj.rotation_euler[0] = math.radians(90)

# Bake the rotation into vertex data so glTF export sees clean orientation
bpy.ops.object.select_all(action='DESELECT')
for obj in letter_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = letter_objs[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


# ---------- 7. JOIN INTO A SINGLE MESH ----------
bpy.ops.object.select_all(action='DESELECT')
for obj in letter_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = letter_objs[0]
bpy.ops.object.join()
joined = bpy.context.active_object
joined.name = "Matt_Logo"


# ---------- 8. SHADING: smooth-by-angle (keeps flat caps flat, smooths bevels) ----------
# Plain shade_smooth interpolates across flat faces and produces visible streaks on
# the flat top/bottom caps of extruded text. Auto-smooth at ~30 degrees solves this:
# only edges below 30deg between faces get smooth-interpolated normals.
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
except Exception:
    # Fallback for older Blender versions where the operator name differs
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))


# ---------- 9. CENTER ORIGIN, then move to world origin ----------
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
joined.location = (0, 0, 0)


print("OK | mesh:", joined.name, "| dims:", tuple(round(d, 2) for d in joined.dimensions))
