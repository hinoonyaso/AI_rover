#!/usr/bin/env python3
# 한글: ROS 없이 돌아가는 정적 검사(CI L0): Python 문법, YAML/XML 파싱, package.xml/setup.py 메타데이터 TODO 검사.
"""Static checks that need no ROS and no hardware (CI L0).

Covers the packages whose logic is mostly launch/config/scripts (bringup, navigation, perception,
description) as well as the rest of src/ and tools/:
  - every .py compiles (syntax)
  - every config YAML parses; every XML-ish file (package.xml, BT .xml, .urdf, .xacro) is well-formed
  - package.xml / setup.py contain no leftover TODO metadata and declare a license
Usage: python3 tools/ci/static_checks.py [repo_root]    (exit code 1 if anything fails)
"""
import os
import sys
import xml.etree.ElementTree as ET

import yaml

SKIP_DIRS = {'.git', 'build', 'install', 'log', 'OrbbecSDK_ROS2', 'third_party', '__pycache__',
             'firmware_source', 'node_modules'}
# 한글: rviz 설정은 YAML이지만 일부 도구가 비표준 태그를 써서 제외하고, 로컬 맵 메타(.yaml)는 포함.
YAML_SKIP_SUFFIX = ('.rviz',)


def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(exts):
                yield os.path.join(dirpath, f)


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
    errors = []

    n_py = 0
    for path in walk(root, ('.py',)):
        n_py += 1
        try:
            with open(path, encoding='utf-8') as f:
                compile(f.read(), path, 'exec')  # 문법만 검사, .pyc는 만들지 않는다
        except (SyntaxError, ValueError) as e:
            errors.append('python syntax: %s: %s' % (os.path.relpath(path, root), e))

    n_yaml = 0
    for path in walk(os.path.join(root, 'src'), ('.yaml', '.yml')):
        if path.endswith(YAML_SKIP_SUFFIX):
            continue
        n_yaml += 1
        try:
            with open(path, encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append('yaml: %s: %s' % (os.path.relpath(path, root), e))

    n_xml = 0
    for path in walk(os.path.join(root, 'src'), ('.xml', '.urdf', '.xacro')):
        n_xml += 1
        try:
            ET.parse(path)
        except ET.ParseError as e:
            errors.append('xml: %s: %s' % (os.path.relpath(path, root), e))

    n_pkg = 0
    for path in walk(os.path.join(root, 'src'), ('package.xml',)):
        n_pkg += 1
        rel = os.path.relpath(path, root)
        try:
            tree = ET.parse(path).getroot()
        except ET.ParseError:
            continue  # 위에서 이미 보고됨
        for tag in ('description', 'license', 'maintainer', 'version'):
            node = tree.find(tag)
            text = (node.text or '').strip() if node is not None else ''
            if not text or 'TODO' in text.upper() or 'todo.todo' in (node.get('email', '') if node is not None else ''):
                errors.append('package.xml: %s: <%s> is missing or still a TODO' % (rel, tag))
        setup_py = os.path.join(os.path.dirname(path), 'setup.py')
        if os.path.exists(setup_py):
            with open(setup_py, encoding='utf-8') as f:
                text = f.read()
            if 'TODO' in text or 'todo.todo' in text:
                errors.append('setup.py: %s still has TODO metadata' % os.path.relpath(setup_py, root))

    print('checked: %d python, %d yaml, %d xml, %d package.xml' % (n_py, n_yaml, n_xml, n_pkg))
    for e in errors:
        print('ERROR', e)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
