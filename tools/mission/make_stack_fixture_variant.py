"""Create a separate inverted-colour fixture for Gazebo tests.

한글: Gazebo 시험용 색상 반전 월드를 별도 파일로 만든다.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main():
    """Write the temporary fixture requested by the caller. / 지정한 경로에 시험 월드를 쓴다."""
    if len(sys.argv) != 2:
        raise SystemExit('usage: make_stack_fixture_variant.py OUTPUT_SDF')
    output = Path(sys.argv[1]).resolve()
    if output.parent != Path('/tmp') or output.exists():
        raise SystemExit('output must be a new file directly under /tmp')
    tree = ET.parse(Path(__file__).with_name('stack_light_fixture.sdf'))
    for name, colour in (('red', '0.025 0 0 1'), ('yellow', '1 1 0 1')):
        material = tree.find(f".//model[@name='stack_light']/link/visual[@name='{name}']/material")
        if material is None:
            raise RuntimeError('fixture visual missing')
        for tag in ('ambient', 'diffuse', 'emissive'):
            material.find(tag).text = colour
    with output.open('x') as stream:
        tree.write(stream, encoding='unicode', xml_declaration=True)


if __name__ == '__main__':
    main()
