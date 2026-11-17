#!/usr/bin/python3
"""Launch camera with one explicitly selected depth input.

한글: 명시적으로 선택한 깊이 입력으로 카메라를 실행한다.
"""
import json
import os
from pathlib import Path


def main():
    """Reject invalid saved choices instead of falling back silently.

    한글: 저장된 선택이 잘못되면 조용히 기본값으로 대체하지 않는다.
    """
    root=Path.home()/'.local/share/jetinspect-ops/calibration';path=root/'depth-source.json'
    config={'source':'default'}
    if path.exists():
        if path.is_symlink() or path.stat().st_size>65536:raise SystemExit('invalid depth source configuration')
        config=json.loads(path.read_text())
    source=config.get('source')
    if source not in ('default','corrected'):raise SystemExit('invalid depth source')
    args=['ros2','launch','jetrover_perception','camera.launch.py','colorizer:=false','depth_source:='+source]
    if source=='corrected':
        reference=config.get('background_path')
        if not isinstance(reference,str) or not reference.startswith(str(root/'backgrounds')+'/'):raise SystemExit('invalid background path')
        args.append('corrected_background_path:='+reference)
    os.execvp(args[0],args)

if __name__=='__main__':main()
