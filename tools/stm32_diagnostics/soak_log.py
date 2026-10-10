#!/usr/bin/env python3
# 한글: 자체 펌웨어(rrc_m4) 장시간 안정성 기록. SWD(openocd)로 1분마다 변수 몇 개를 읽어 CSV에 남긴다 — UART를 안 쓰므로
#       base_node/다른 시험과 겹치지 않고, 코어를 멈추지 않는다(IWDG가 있어 halt하면 리셋됨). J-Link는 한 번에 한 프로그램만 쓰므로
#       flash할 때는 이 기록을 먼저 멈춘다(Ctrl+C 또는 kill).
"""Long-run stability log for the rrc_m4 firmware, read over SWD (no UART, no halt).

Usage: python3 tools/stm32_diagnostics/soak_log.py [--interval 60] [--elf <rrc_m4.elf>] [--out Log/soak.csv]
Every interval one openocd session reads (memory only, `mdw`): HAL tick (uptime), the boot reset-cause latch,
the five task heartbeats, IMU samples/errors, battery mV, rejected commands, e-stop/low-battery flags.
Each row also carries verdict flags computed against the previous row:
  RESET   uptime went backwards (the MCU restarted; reset_cause says why: 0x20 IWDG, 0x04 power-on ...)
  FROZEN  the tick advanced much less than the wall clock (MCU stuck without a reset)
  STALL   a task heartbeat or the IMU sample counter did not advance
  SWDFAIL the read failed (J-Link busy / board off); not a firmware verdict
The struct offsets come from compiling a 10-line file with the firmware's own flags (needs the arm toolchain
on PATH: ~/.local/opt/stm32/bin), so they always match the ELF that is flashed.
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
import time

TOOLCHAIN = os.path.expanduser('~/.local/opt/stm32/bin')
FW = os.path.expanduser('~/jetrover_ws/firmware/rrc_m4')


def offsets(build_dir):
    """offsetof() of the fields we read, compiled with the ELF's own flags."""
    flags = open(os.path.join(build_dir, 'CMakeFiles/rrc_m4.elf.dir/flags.make')).read()
    pick = lambda k: re.search(rf'^{k} = (.*)$', flags, re.M).group(1)  # noqa: E731
    src = ('#include <stddef.h>\n#include "app.h"\n'
           'const unsigned o_hb = offsetof(app_t, hb);\n'
           'const unsigned o_imu_samples = offsetof(app_t, imu_samples);\n'
           'const unsigned o_imu_errors = offsetof(app_t, imu_errors);\n'
           'const unsigned o_batt = offsetof(app_t, battery) + offsetof(battery_t, millivolts);\n'
           'const unsigned o_rejected = offsetof(app_t, robot) + offsetof(robot_ctrl_t, rejected_cmds);\n'
           'const unsigned o_estop = offsetof(app_t, robot) + offsetof(robot_ctrl_t, estop);\n'
           'const unsigned o_lowbat = offsetof(app_t, robot) + offsetof(robot_ctrl_t, low_battery);\n')
    with tempfile.TemporaryDirectory() as d:
        c = os.path.join(d, 'o.c')
        open(c, 'w').write(src)
        cmd = [os.path.join(TOOLCHAIN, 'arm-none-eabi-gcc'), '-S', '-o', '-', c] + \
            pick('C_DEFINES').split() + pick('C_INCLUDES').split() + pick('C_FLAGS').split()
        asm = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    out = {}
    for name in ('o_hb', 'o_imu_samples', 'o_imu_errors', 'o_batt', 'o_rejected', 'o_estop', 'o_lowbat'):
        m = re.search(rf'^{name}:\s*\n\s*\.word\s+(\d+)', asm, re.M)
        out[name] = int(m.group(1))
    return out


def symbols(elf):
    nm = subprocess.run([os.path.join(TOOLCHAIN, 'arm-none-eabi-nm'), elf], capture_output=True, text=True).stdout
    sym = {}
    for line in nm.splitlines():
        p = line.split()
        if len(p) == 3 and p[2] in ('g_app', 'g_reset_cause', 'uwTick'):
            sym[p[2]] = int(p[0], 16)
    return sym


def read_all(sym, off):
    g = sym['g_app']
    cmds = [f'mdw 0x{sym["uwTick"]:08x} 1', f'mdw 0x{sym["g_reset_cause"]:08x} 1',
            f'mdw 0x{g + off["o_hb"]:08x} 5', f'mdw 0x{g + off["o_imu_samples"]:08x} 1',
            f'mdw 0x{g + off["o_imu_errors"]:08x} 1', f'mdh 0x{g + off["o_batt"]:08x} 1',
            f'mdw 0x{g + off["o_rejected"]:08x} 1', f'mdb 0x{g + off["o_estop"]:08x} 1',
            f'mdb 0x{g + off["o_lowbat"]:08x} 1']
    args = ['openocd', '-f', 'interface/jlink.cfg', '-c', 'transport select swd', '-c', 'adapter speed 1000',
            '-f', 'target/stm32f4x.cfg', '-c', 'reset_config none', '-c', 'init']
    for c in cmds:
        args += ['-c', c]
    args += ['-c', 'shutdown']
    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    vals = []
    for line in (r.stdout + r.stderr).splitlines():
        m = re.match(r'^0x[0-9a-f]{8}: ((?:[0-9a-f]+ ?)+)\s*$', line)
        if m:
            vals.append([int(x, 16) for x in m.group(1).split()])
    if len(vals) != len(cmds):
        raise RuntimeError('SWD read failed: ' + (r.stderr.strip().splitlines() or ['no output'])[-1])
    return {'tick': vals[0][0], 'reset_cause': vals[1][0], 'hb': vals[2], 'imu_samples': vals[3][0],
            'imu_errors': vals[4][0], 'batt_mv': vals[5][0], 'rejected': vals[6][0], 'estop': vals[7][0],
            'lowbat': vals[8][0]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--interval', type=float, default=60.0)
    ap.add_argument('--elf', default=os.path.join(FW, 'build-arm-motor/rrc_m4.elf'))
    ap.add_argument('--out', default=os.path.expanduser('~/jetrover_ws/Log/soak.csv'))
    args = ap.parse_args()
    build_dir = os.path.dirname(os.path.abspath(args.elf))
    off, sym = offsets(build_dir), symbols(args.elf)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    prev, prev_t, resets = None, None, 0
    fields = ['time', 'uptime_s', 'reset_cause', 'hb_control', 'hb_imu', 'hb_rx', 'hb_tx', 'hb_ui', 'imu_samples',
              'imu_errors', 'batt_mv', 'rejected', 'estop', 'lowbat', 'verdict']
    with open(args.out, 'a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(fields)
        print(f'logging every {args.interval:g} s to {args.out} (Ctrl+C to stop)', flush=True)
        while True:
            t = time.time()
            try:
                d = read_all(sym, off)
                verdict = []
                if prev:
                    dt = t - prev_t
                    if d['tick'] < prev['tick']:
                        verdict.append('RESET')
                        resets += 1
                    elif (d['tick'] - prev['tick']) / 1000.0 < 0.5 * dt:
                        verdict.append('FROZEN')
                    elif d['imu_samples'] == prev['imu_samples'] or any(
                            d['hb'][i] == prev['hb'][i] for i in (0, 1, 2, 4)):
                        # heartbeat 3 (comm_tx) never beats by design: the UI task vouches for TX health
                        verdict.append('STALL')
                row = [time.strftime('%Y-%m-%d %H:%M:%S'), round(d['tick'] / 1000.0, 1), hex(d['reset_cause'])] + \
                    d['hb'][:5] + [d['imu_samples'], d['imu_errors'], d['batt_mv'], d['rejected'], d['estop'],
                                   d['lowbat'], ' '.join(verdict) or 'ok']
                prev, prev_t = d, t
            except Exception as e:  # noqa: BLE001
                row = [time.strftime('%Y-%m-%d %H:%M:%S')] + [''] * 13 + ['SWDFAIL ' + str(e)[:60]]
            w.writerow(row)
            f.flush()
            print(','.join(str(x) for x in row), flush=True)
            time.sleep(max(1.0, args.interval - (time.time() - t)))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
