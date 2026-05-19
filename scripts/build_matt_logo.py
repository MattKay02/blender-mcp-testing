"""
build_matt_logo.py
------------------
A clean, web-ready 3D logo of "Matt" — no animation, no ground plane, no camera,
just the four gold letters centered at the origin. Export this as .glb and embed
on any webpage with <model-viewer>, Three.js, or React Three Fiber.

Run inside Blender, or via blender-mcp execute_blender_code.
"""

import bpy

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
    bpy.ops.object.shade_smooth()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    obj.data.materials.append(gold)
    letter_objs.append(obj)


# ---------- 5. LAY OUT and PARENT under one empty for easy export/transform ----------
GAP = 0.14
widths = [o.dimensions.x for o in letter_objs]
total = sum(widths) + GAP * (len(widths) - 1)
cursor = -total / 2
for obj, w in zip(letter_objs, widths):
    obj.location.x = cursor + w / 2
    obj.location.y = 0
    obj.location.z = 0
    cursor += w + GAP

# Group all letters under one parent empty so they move/rotate as one in 3-party viewers
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
root = bpy.context.active_object
root.name = "Matt_Logo"
for obj in letter_objs:
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()


# ---------- 6. JOIN INTO A SINGLE MESH (optional but tidier .glb) ----------
bpy.ops.object.select_all(action='DESELECT')
for obj in letter_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = letter_objs[0]
bpy.ops.object.join()
joined = bpy.context.active_object
joined.name = "Matt_Logo_Mesh"
joined.parent = root
# Recenter origin to the geometric center so rotation in the browser feels natural
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
joined.location = (0, 0, 0)


print("OK. Root empty:", root.name, "| mesh:", joined.name, "| dims:", tuple(round(d,2) for d in joined.dimensions))
