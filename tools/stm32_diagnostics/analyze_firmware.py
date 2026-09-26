#!/usr/bin/env python3
"""Static analysis of the Hiwonder RosRobotControllerM4.hex (no source available).

Usage: python3 analyze_firmware.py ~/jetrover_ws/firmware_source/RosRobotControllerM4.zip
       (a bare .hex file works too)

Reports: vector table, whether the IWDG is configured (reload/prescaler), who calls
HAL_IWDG_Refresh, and every FreeRTOS task's stack size / priority / entry function.
Thumb-2 only; addresses are heuristic (function starts = nearest PUSH). Use with
`objdump -D -b binary -m arm -M force-thumb --adjust-vma=0x08000000` to read the code.
"""
import struct
import sys
import zipfile

BASE = 0x08000000
IWDG = 0x40003000


def load_hex(path):
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if n.lower().endswith(".hex"))
        text = z.read(name).decode()
    else:
        text = open(path).read()
    mem, upper = {}, 0
    for line in text.splitlines():
        if not line.startswith(":"):
            continue
        n = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        typ = int(line[7:9], 16)
        data = bytes.fromhex(line[9:9 + 2 * n])
        if typ == 0:
            for i, b in enumerate(data):
                mem[upper + addr + i] = b
        elif typ == 4:
            upper = int.from_bytes(data, "big") << 16
    lo = min(mem)
    return lo, bytes(mem.get(lo + i, 0xFF) for i in range(max(mem) - lo + 1))


def sx(v, bits):
    return v - (1 << bits) if v & (1 << (bits - 1)) else v


def decode_mov(d, i):
    hw1, hw2 = struct.unpack_from("<HH", d, i)
    if (hw2 & 0x8000) == 0 and (hw1 & 0xFBF0) in (0xF240, 0xF2C0):
        imm = (((hw1 & 0xF) << 12) | (((hw1 >> 10) & 1) << 11) |
               (((hw2 >> 12) & 7) << 8) | (hw2 & 0xFF))
        return ("MOVT" if (hw1 & 0xFBF0) == 0xF2C0 else "MOVW"), (hw2 >> 8) & 0xF, imm
    return None


def constants(d):
    """32-bit constants built by MOVW+MOVT pairs: yields (value, address)."""
    for i in range(0, len(d) - 4, 2):
        x = decode_mov(d, i)
        if x and x[0] == "MOVT":
            for back in range(2, 17, 2):
                y = decode_mov(d, i - back) if i - back >= 0 else None
                if y and y[0] == "MOVW" and y[1] == x[1]:
                    yield (x[2] << 16) | y[2], BASE + i - back
                    break


def branch_target(d, i):
    hw1, hw2 = struct.unpack_from("<HH", d, i)
    if (hw1 & 0xF800) == 0xF000 and ((hw2 & 0xC000) == 0xC000 or (hw2 & 0xD000) == 0x9000):
        s = (hw1 >> 10) & 1
        j1, j2 = (hw2 >> 13) & 1, (hw2 >> 11) & 1
        i1, i2 = ~(j1 ^ s) & 1, ~(j2 ^ s) & 1
        off = (s << 24) | (i1 << 23) | (i2 << 22) | ((hw1 & 0x3FF) << 12) | ((hw2 & 0x7FF) << 1)
        return BASE + i + 4 + sx(off, 25)
    return None


def callers(d, target):
    return [BASE + i for i in range(0, len(d) - 3, 2) if branch_target(d, i) == target]


def func_start(d, addr):
    for a in range(addr, addr - 0x600, -2):
        hw = struct.unpack_from("<H", d, a - BASE)[0]
        if (hw & 0xFF00) == 0xB500 or hw == 0xE92D:
            return a
    return None


def main():
    lo, d = load_hex(sys.argv[1])
    assert lo == BASE, hex(lo)
    sp, reset = struct.unpack_from("<II", d, 0)
    print(f"image {len(d)} bytes, SP=0x{sp:08X}, reset=0x{reset:08X}")

    consts = list(constants(d))
    init_sites = [a for v, a in consts if v == IWDG]
    print(f"IWDG base 0x{IWDG:08X} built at: {[hex(a) for a in init_sites]}")
    for a in init_sites:
        hw = struct.unpack_from("<H", d, func_start(d, a) - BASE)[0]
        print(f"  MX_IWDG_Init ~0x{func_start(d, a):08X} (see it with objdump; expect prescaler/reload stores)")

    refresh = [BASE + i for i in range(0, len(d) - 3, 2)
               if (m := decode_mov(d, i)) and m[0] == "MOVW" and m[2] == 0xAAAA]
    print(f"IWDG reload key 0xAAAA loaded at: {[hex(a) for a in refresh]}")
    for a in refresh:
        # HAL_IWDG_Refresh is a tiny leaf without PUSH: `ldr r1,[r0]; movw r2,#0xAAAA; ...`,
        # so the function starts 2 bytes before the MOVW. Also try the nearest PUSH.
        for f in dict.fromkeys([a - 2, func_start(d, a)]):
            cs = callers(d, f) if f else []
            if cs:
                print(f"  function 0x{f:08X}: called from {[hex(c) for c in cs]}"
                      f" -> in functions {[hex(func_start(d, c)) for c in cs]}")

    attrs = {}
    for name in ("defaultTask", "oled_task", "bluetooth_task", "gui_task", "app_task",
                 "imu_task", "sbus_rx_task", "packet_rx_task", "packet_tx_task"):
        k = d.find(name.encode() + b"\0")
        if k < 0:
            continue
        ptr = BASE + k
        for i in range(0, len(d) - 31, 4):
            if struct.unpack_from("<I", d, i)[0] == ptr:
                w = struct.unpack_from("<8I", d, i)
                attrs[BASE + i] = (name, w[5], w[6])
    print("\nFreeRTOS tasks (CMSIS attr: stack bytes, priority 8=Low 16=BelowNormal 24=Normal 32=AboveNormal):")
    for a, (n, stack, prio) in sorted(attrs.items()):
        print(f"  {n:15s} stack={stack:5d}  prio={prio}")
    print("\nTask -> entry function: run with objdump around the osThreadNew calls near 0x08006020-0x080060F0.")


if __name__ == "__main__":
    main()
