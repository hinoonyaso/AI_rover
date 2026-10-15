# 한글: (host) Blender 헤드리스로 텍스처를 입힌 바닥 판 glb를 만든다(room_fill.py의 floor_albedo.png + floor.json).
#       UV는 판 전체 0..1, 이미지 위쪽 = +y 쪽. Z-up 그대로 내보낸다(Gazebo는 glTF Y-up을 되돌리지 않음, troubleshooting/040).
# (host) Headless Blender: textured floor quad GLB from room_fill.py's floor_albedo.png + floor.json (Z-up export).
#
# Usage: blender -b --python tools/scan/blender_textured_plane.py -- <model_dir>
import json
import os
import sys

import bpy

d = sys.argv[sys.argv.index('--') + 1]
f = json.load(open(os.path.join(d, 'floor.json')))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=1.0)
obj = bpy.context.active_object
obj.scale = (f['w'], f['h'], 1.0)
obj.location = (f['x0'] + f['w'] / 2, f['y0'] + f['h'] / 2, f['z'])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

mat = bpy.data.materials.new('floor')
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
bsdf = nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value = 0.9
tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(os.path.join(d, 'floor_albedo.png'))
links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
obj.data.materials.append(mat)

out = os.path.join(d, 'meshes', 'floor.glb')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_yup=False)
print(f'floor plane {f["w"]:.2f} x {f["h"]:.2f} m at z {f["z"]} -> {out}')
