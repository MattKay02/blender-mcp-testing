"""
build_matt_scene.py
-------------------
Builds the "Matt" 3D wave-pop animation scene in Blender from scratch.

Run from inside Blender (Scripting workspace -> open this file -> Run Script),
or via the blender-mcp tool execute_blender_code over MCP.

This file is the source of truth for the scene. Anything in .blend is rebuildable
by running this script on an empty Blender startup file.
"""

import bpy
import math
import mathutils

# ---------- 1. CLEAN any prior "Matt" stuff ----------
for obj in list(bpy.data.objects):
    if obj.name.startswith("Matt_") or obj.name == "Cube":
        bpy.data.objects.remove(obj, do_unlink=True)


# ---------- 2. FONT ----------
# Bahnschrift ships with Windows 10/11. Swap path on macOS/Linux.
FONT_PATH = r"C:\Windows\Fonts\BAHNSCHRIFT.TTF"
font = bpy.data.fonts.load(FONT_PATH, check_existing=True)


# ---------- 3. GOLD MATERIAL (Principled BSDF) ----------
gold = bpy.data.materials.get("Matt_Gold") or bpy.data.materials.new("Matt_Gold")
gold.use_nodes = True
bsdf = gold.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.78, 0.31, 1.0)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.18


# ---------- 4. GROUND PLANE (dark, slightly glossy) ----------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.5))
plane = bpy.context.active_object
plane.name = "Matt_Ground"
ground_mat = bpy.data.materials.new("Matt_Ground_Mat")
ground_mat.use_nodes = True
gb = ground_mat.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.04, 0.04, 0.06, 1.0)
gb.inputs["Roughness"].default_value = 0.25
plane.data.materials.append(ground_mat)


# ---------- 5. LETTERS ("M", "a", "t", "t") ----------
LETTERS = list("Matt")
letter_objs = []
for i, ch in enumerate(LETTERS):
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = f"Matt_Letter_{i}_{ch}"
    obj.data.font = font
    obj.data.body = ch
    obj.data.extrude = 0.28          # depth of the 3D extrusion
    obj.data.bevel_depth = 0.035     # rounded edge
    obj.data.bevel_resolution = 4
    obj.data.size = 1.6
    obj.data.align_x = 'CENTER'
    obj.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH')          # text -> mesh (so it can shade smooth)
    bpy.ops.object.shade_smooth()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    obj.data.materials.append(gold)
    letter_objs.append(obj)

# Lay letters out horizontally using each letter's actual rendered width
GAP = 0.14
widths = [o.dimensions.x for o in letter_objs]
total = sum(widths) + GAP * (len(widths) - 1)
cursor = -total / 2
final_x = []
for w in widths:
    final_x.append(cursor + w / 2)
    cursor += w + GAP


# ---------- 6. WAVE-POP ANIMATION ----------
scn = bpy.context.scene
scn.render.fps = 24
scn.frame_start = 1
scn.frame_end = 84              # 3.5 s at 24 fps

START = 6                       # first letter starts on this frame
STAGGER = 7                     # frames between each letter's start (the "wave")
DROP_Z = -2.0                   # hidden below the ground plane
PEAK_Z = 0.6                    # overshoot above the final spot
BOUNCE_Z = -0.1                 # tiny dip after overshoot
FINAL_Z = 0.0
TILT_DEG = 25

for i, (obj, fx) in enumerate(zip(letter_objs, final_x)):
    obj.location = (fx, 0, DROP_Z)
    obj.rotation_mode = 'XYZ'
    s = START + i * STAGGER
    sign = -1 if i % 2 == 0 else 1   # alternate tilt direction for character

    # Z bounce: hidden -> peak -> small bounce -> settle
    for frame, z in [(1, DROP_Z), (s, DROP_Z), (s+8, PEAK_Z),
                     (s+14, BOUNCE_Z), (s+20, FINAL_Z)]:
        obj.location.z = z
        obj.keyframe_insert(data_path="location", index=2, frame=frame)

    # X-axis tilt during the pop
    for frame, deg in [(1, 0), (s, 0), (s+5, TILT_DEG * sign),
                       (s+12, -TILT_DEG * 0.5 * sign), (s+20, 0)]:
        obj.rotation_euler[0] = math.radians(deg)
        obj.keyframe_insert(data_path="rotation_euler", index=0, frame=frame)

    # Subtle Z-axis spin during the pop
    for frame, deg in [(1, 0), (s, 0), (s+10, 15 * sign), (s+20, 0)]:
        obj.rotation_euler[2] = math.radians(deg)
        obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)


# ---------- 7. CAMERA DOLLY ----------
cam = bpy.data.objects.get("Camera") or bpy.data.cameras.new("Camera")
if not bpy.data.objects.get("Camera"):
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam = cam_obj
cam.rotation_mode = 'XYZ'

START_LOC = mathutils.Vector((1.0, -9.0, 2.6))
END_LOC = mathutils.Vector((-0.4, -5.5, 1.4))
FOCUS = mathutils.Vector((0, 0, 0.2))

def aim(loc, target):
    return (target - loc).to_track_quat('-Z', 'Y').to_euler()

cam.location = START_LOC
cam.rotation_euler = aim(START_LOC, FOCUS)
cam.keyframe_insert("location", frame=1)
cam.keyframe_insert("rotation_euler", frame=1)

cam.location = END_LOC
cam.rotation_euler = aim(END_LOC, FOCUS)
cam.keyframe_insert("location", frame=scn.frame_end)
cam.keyframe_insert("rotation_euler", frame=scn.frame_end)

# Subtle lens zoom-in across the shot
cam.data.lens = 50
cam.data.keyframe_insert("lens", frame=1)
cam.data.lens = 65
cam.data.keyframe_insert("lens", frame=scn.frame_end)


# ---------- 8. LIGHTING ----------
light = bpy.data.objects.get("Light")
if light:
    light.data.energy = 1200
    light.location = (3, -4, 7)


# ---------- 9. SIMPLE SKY-BLUE WORLD ----------
world = scn.world
world.use_nodes = True
wnt = world.node_tree
wnt.nodes.clear()
out = wnt.nodes.new("ShaderNodeOutputWorld")
bg = wnt.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.55, 0.7, 0.85, 1.0)
bg.inputs["Strength"].default_value = 1.2
wnt.links.new(bg.outputs[0], out.inputs[0])


# ---------- 10. RENDER SETTINGS (Cycles + OPTIX if available) ----------
scn.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type = 'OPTIX'
    prefs.refresh_devices()
    for d in prefs.devices:
        d.use = (d.type == 'OPTIX')
    scn.cycles.device = 'GPU'
except Exception:
    scn.cycles.device = 'CPU'

scn.cycles.samples = 24                # low for laptop GPUs; OIDN cleans it up
scn.cycles.use_denoising = True
scn.cycles.denoiser = 'OPENIMAGEDENOISE'
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.02

scn.render.resolution_x = 720
scn.render.resolution_y = 405
scn.render.image_settings.file_format = 'PNG'

scn.frame_set(1)
print("Scene built. Letters:", [o.name for o in letter_objs])
