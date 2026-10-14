# 한글: (host) Blender 헤드리스로 정점 색 PLY → glb 변환. Open3D가 쓴 glb는 Gazebo(Assimp)가 못 읽는다
#       ("Cannot load mesh with zero sub-meshes", 2026-10-14) — Blender glTF 내보내기는 읽힌다. 정점 색은 머티리얼로 연결.
# (host) Headless Blender: vertex-coloured PLY -> GLB that Gazebo's Assimp loader accepts (Open3D's GLB is rejected).
#
# Usage: blender -b --python tools/scan/blender_ply_to_glb.py -- in.ply out.glb [yup] [bake=2048]
#   bake=N: 정점 색을 N×N 알베도 텍스처로 굽는다(Cycles DIFFUSE COLOR만, 조명 제외) — Gazebo Harmonic은 glb의 정점 색(COLOR_0)을
#           반영하지 않아 회색으로 보인다(2026-10-14). PNG도 out.glb 옆에 저장(SDF albedo_map 대안용).
#   bake=N: bake the vertex colours into an N x N albedo texture (diffuse colour only, no lighting); Gazebo Harmonic
#           does not show glb vertex colours. The PNG is also written next to out.glb.
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[:2]
# Z-up 그대로 내보낸다: Gazebo는 glb를 Y-up으로 바꾸지 않는다(2026-10-14: Y-up이면 시뮬레이션 LiDAR와 지도 벽 중앙값 19.7 cm,
# Z-up이면 메쉬 직접 레이캐스트와 5 cm 이내). Keep Z-up: Gazebo does not convert glTF Y-up back. Pass 'yup' to override.
YUP = 'yup' in argv[2:]
BAKE = next((int(a.split('=')[1]) for a in argv[2:] if a.startswith('bake=')), 0)
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

export_kw = {}
if BAKE and attr:
    import os
    import time
    t0 = time.time()
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # 스캔 메쉬는 울퉁불퉁해 smart_project가 삼각형마다 섬을 만들어 2048² 중 4.9 %만 채웠다(2026-10-14) —
    # lightmap_pack은 면마다 같은 크기 칸을 줘서 텍스처를 고르게 쓴다. 칸이 작으면(30만 삼각형/2048²: 약 4×4 px) mipmap이
    # 이웃 칸 색을 섞어 검은 얼룩이 생기므로 visual은 10만 삼각형으로 줄인다(room_assets.py 기본값).
    # Noisy scan meshes break smart_project into per-triangle islands (4.9 % texture use); lightmap_pack fills evenly.
    # Tiny cells (300k tris on 2048^2) let mipmaps mix neighbouring cells (black speckles): keep the visual at 100k tris.
    bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_PACK_IN_ONE=True, PREF_MARGIN_DIV=0.1)
    bpy.ops.object.mode_set(mode='OBJECT')
    t_uv = time.time() - t0
    img = bpy.data.images.new('room_albedo', BAKE, BAKE)
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = img
    nodes.active = tex                      # 굽기 대상 / bake target
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    # margin을 크게(빈 픽셀을 이웃 색으로 채움): 칸이 몇 픽셀뿐이라 빈 칸(검정)이 mipmap에 섞여 검은 얼룩/어두운 화면이 됐다(margin 1).
    # Large margin fills empty texels with neighbouring colour; with margin 1 black gaps bled into mipmaps (dark speckles).
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=16, margin_type='EXTEND', use_clear=True)
    # 정점 색 대신 구운 텍스처를 Base Color로 / the baked texture replaces the vertex colour input
    links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nodes.remove(vc)
    png = os.path.splitext(dst)[0] + '_albedo.png'
    img.filepath_raw = png
    img.file_format = 'PNG'
    img.save()
    export_kw['export_vertex_color'] = 'NONE'
    print(f'baked {BAKE}x{BAKE}: uv {t_uv:.0f} s, total {time.time() - t0:.0f} s -> {png}')

bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_yup=YUP, **export_kw)
print(f'converted {src} -> {dst}: {len(mesh.polygons)} faces, color attribute {attr}, bake {BAKE}')
