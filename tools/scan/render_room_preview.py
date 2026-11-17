#!/usr/bin/env python3
"""Render sampled vertices from the scanned-room GLB.

한글: 스캔 방 GLB의 정점을 표본 추출해 시각화한다.
"""
import argparse
import json
from pathlib import Path
import struct

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import numpy as np


def read_positions(path):
    """Read contiguous float32 POSITION data from the project's GLB.

    한글: 프로젝트 GLB의 연속된 float32 POSITION 데이터를 읽는다.
    """
    data = path.read_bytes()
    magic, version, total = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or total != len(data):
        raise ValueError('expected a complete GLB 2.0 file')
    json_len, chunk_type = struct.unpack_from('<II', data, 12)
    if chunk_type != 0x4E4F534A:
        raise ValueError('expected GLB JSON chunk')
    document = json.loads(data[20:20 + json_len])
    binary_offset = 20 + json_len
    binary_len, chunk_type = struct.unpack_from('<II', data, binary_offset)
    if chunk_type != 0x004E4942:
        raise ValueError('expected GLB binary chunk')
    primitive = document['meshes'][0]['primitives'][0]
    accessor = document['accessors'][primitive['attributes']['POSITION']]
    view = document['bufferViews'][accessor['bufferView']]
    if accessor['type'] != 'VEC3' or accessor['componentType'] != 5126 or view.get('byteStride', 12) != 12:
        raise ValueError('expected contiguous float32 3D positions')
    nodes = [node for node in document.get('nodes', []) if node.get('mesh') == 0]
    if len(nodes) != 1 or any(field in nodes[0] for field in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('expected one untransformed mesh node')
    start = binary_offset + 8 + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = start + accessor['count'] * 12
    if end > binary_offset + 8 + binary_len:
        raise ValueError('position data exceeds binary chunk')
    return np.frombuffer(data, dtype='<f4', count=accessor['count'] * 3, offset=start).reshape(-1, 3)


def main():
    """Generate a two-view plot of actual mesh geometry. / 실제 메쉬 형상의 두 시점을 그림으로 만든다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    positions = read_positions(args.mesh)
    chosen = np.random.default_rng(42).choice(len(positions), min(100000, len(positions)), replace=False)
    points = positions[chosen]
    fig = plt.figure(figsize=(14, 6.3), facecolor='#f6f8f6')
    for index, (azimuth, elevation, title) in enumerate(
            [(-65, 42, 'Reconstructed room · perspective'), (-90, 88, 'Reconstructed room · top view')], 1):
        axis = fig.add_subplot(1, 2, index, projection='3d', computed_zorder=False)
        axis.set_facecolor('#f6f8f6')
        axis.scatter(points[:, 0], points[:, 1], points[:, 2], c=points[:, 2], cmap='viridis',
                     vmin=0, vmax=1.8, s=.35, linewidths=0, depthshade=False, rasterized=True)
        axis.view_init(elev=elevation, azim=azimuth)
        axis.set_box_aspect((3.6, 3.6, 1.8))
        axis.set_xlabel('X (m)', labelpad=-1)
        axis.set_ylabel('Y (m)', labelpad=-1)
        axis.set_zlabel('Z (m)', labelpad=-1)
        if index == 2:
            axis.set_zticks([])
        axis.tick_params(labelsize=7, pad=-2)
        axis.set_title(title, fontsize=12, fontweight='bold', pad=4)
        for pane in (axis.xaxis.pane, axis.yaxis.pane, axis.zaxis.pane):
            pane.set_alpha(.05)
    fig.suptitle('JETINSPECT-M   /   RGB-D ROOM RECONSTRUCTION', fontsize=14, fontweight='bold',
                 y=.98, color='#244139')
    bar_axis = fig.add_axes([.36, .10, .28, .015])
    fig.colorbar(ScalarMappable(norm=Normalize(0, 1.8), cmap='viridis'), cax=bar_axis,
                 orientation='horizontal', label='Height Z (m)')
    bar_axis.tick_params(labelsize=7)
    fig.text(.5, .015, 'Original scanned-room mesh (Open3D / RTAB-Map) · colors indicate height, not camera texture',
             ha='center', fontsize=9, color='#566b61')
    fig.subplots_adjust(left=.01, right=.99, top=.92, bottom=.15, wspace=.02)
    fig.savefig(args.output, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == '__main__':
    main()
