#!/usr/bin/env python3
# 한글: 디컴파일 결과에서 GPIO 초기화를 뽑는 도구(핀 구조체 필드: 핀, 모드, 풀, 속도, 대체기능).
"""decompiled.c에서 HAL_GPIO_Init(FUN_08001dd8)/HAL_GPIO_WritePin(FUN_08001f84) 호출을 함수별로 뽑는다.
Ghidra 의사코드의 local_XX 대입을 호출 직전 값으로 해석하는 휴리스틱이다 (확정 아님, 검증용 1차 후보)."""
import re, sys
src = open(sys.argv[1] if len(sys.argv) > 1 else
           '/home/sang/jetrover_ws/firmware_source/decompile/decompiled.c').read()
PORT = {0x40020000:'A',0x40020400:'B',0x40020800:'C',0x40020c00:'D',0x40021000:'E',0x40021400:'F'}
MODE = {0:'IN',1:'OUT_PP',2:'AF_PP',3:'ANALOG',0x110000:'IT_FALL?',0x11:'OUT_OD',0x12:'AF_OD'}
funcs = re.split(r'\n/\* ([0-9a-f]{8}) \*/\n', src)
# 한글: 함수별로 HAL_GPIO_Init(FUN_08001dd8) 호출을 찾아 핀/모드/AF를 출력한다. Ghidra 의사코드 휴리스틱이라 확정이 아니라 1차 후보다.
for i in range(1, len(funcs), 2):
    addr, body = funcs[i], funcs[i+1]
    if 'FUN_08001dd8' not in body or addr == '08001dd8':
        continue
    print(f'== func {addr}')
    vals = {}
    for line in body.splitlines():
        m = re.match(r'\s+(local_\w+) = (0x[0-9a-f]+|\d+);', line)
        if m: vals[m.group(1)] = int(m.group(2), 0)
        m = re.search(r'FUN_08001dd8\(([^,]+),&(local_\w+)', line)
        if m:
            base = m.group(1); base = int(base, 0) if base.startswith('0x') else base
            # init struct: pin, mode, pull, speed, alternate at descending local offsets
            n = int(m.group(2).split('_')[1], 16)
            f = lambda k: vals.get(f'local_{n-4*k:x}')
            print(f'  port={PORT.get(base, base)} pin=0x{(f(0) or 0):04x} mode={f(1)} pull={f(2)} speed={f(3)} af={f(4)}  | {line.strip()}')
