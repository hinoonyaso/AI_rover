# 한글: (host) Blender 헤드리스로 정점 색 PLY → glb 변환. Open3D가 쓴 glb는 Gazebo(Assimp)가 못 읽는다
#       ("Cannot load mesh with zero sub-meshes", 2026-10-14) — Blender glTF 내보내기는 읽힌다. 정점 색은 머티리얼로 연결.
# (host) Headless Blender: vertex-coloured PLY -> GLB that Gazebo's Assimp loader accepts (Open3D's GLB is rejected).
#
# Usage: blender -b --python tools/scan/blender_ply_to_glb.py -- in.ply out.glb [yup]
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[:2]
# Z-up 그대로 내보낸다: Gazebo는 glb를 Y-up으로 바꾸지 않는다(2026-10-14: Y-up이면 시뮬레이션 LiDAR와 지도 벽 중앙값 19.7 cm,
# Z-up이면 메쉬 직접 레이캐스트와 5 cm 이내). Keep Z-up: Gazebo does not convert glTF Y-up back. Pass 'yup' to override.
YUP = len(argv) >= 3 and argv[2] == 'yup'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=src)
obj = bpy.context.selected_objects[0]
mesh = obj.data
attr = mesh.color_attributes[0].name if mesh.color_attributes else None

mat = bpy.data.materials.new('room')
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
bsdf = nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value = 0.9
if attr:
    vc = nodes.new('ShaderNodeVertexColor')
    vc.layer_name = attr
    links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
mesh.materials.append(mat)

bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_yup=YUP)
print(f'converted {src} -> {dst}: {len(mesh.polygons)} faces, color attribute {attr}')
