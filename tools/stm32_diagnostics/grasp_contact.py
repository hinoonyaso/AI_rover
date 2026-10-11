#!/usr/bin/env python3
# 한글: 그리퍼(ID 10) 접촉 감지 로직(순수 함수, 하드웨어 없이 시뮬레이션으로 시험 — test_grasp_contact.py).
#       "조금씩 닫으며 명령을 위치가 따라오지 못하는 지점"을 찾는다. 서보는 힘을 알려 주지 않으므로 위치 정체만 본다 →
#       정체를 곧바로 '물체'라고 단정하지 않고, 접촉 위치 창(classify)과 닫힘 끝(693) 처리로 판정을 따로 한다.
"""Gripper contact detection (pure, simulated in test_grasp_contact.py; used by rrc_m4_io_test.py contact-validate).

The servo reports no force, so "contact" is only "the position stopped following the command". The detector therefore
returns FACTS (where it stopped, the lag, how many steps) and `classify` makes the separate decision whether that is the
object we expect (a contact position window measured for that object). prd/arm-control-path.md R3, D6.
"""
import time

CLOSED_END = 693        # jaws touch each other (measured 2026-10-11)
DEAD_BAND = 8           # lag (command - reading) above this is a candidate: servo dead band is 3-4 pulses
OPEN_START_MAX = 450    # refuse to start from a nearly closed gripper
STEP_MIN, STEP_MAX = 6, 16


def find_contact(move, read, step=12, max_pulse=900, dead_band=DEAD_BAND, max_steps=80, retries=2, log=None):
    """Close in `step` pulses until a commanded position is not reached AND repeating the same command does not move it.

    move(pulse, ms): command ID 10 and wait for it. read(): position, or None when the reply is missing.
    A missing reading is retried `retries` times; if it stays missing the search STOPS with status 'no_reading'
    (it never reports a contact it did not see).
    Returns dict(status, start, contact, lag, steps) with status in
      'contact'        blocked at `contact`
      'no_contact'     reached the limit (closed end - 6, or max_pulse) or max_steps without being blocked
      'no_reading'     the reading stayed missing
      'bad_start'      no reading at the start, or the gripper is nearly closed already
    """
    say = log or (lambda *_: None)

    def read_retry():
        for _ in range(retries + 1):
            v = read()
            if v is not None:
                return v
        return None

    step = min(max(step, STEP_MIN), STEP_MAX)
    start = read_retry()
    if start is None or start > OPEN_START_MAX:
        return {'status': 'bad_start', 'start': start, 'contact': None, 'lag': None, 'steps': 0}
    limit = min(max_pulse, CLOSED_END - 6)
    now = start
    for i in range(max_steps):
        target = now + step
        if target > limit:
            say(f'  reached the limit {limit} without contact')
            return {'status': 'no_contact', 'start': start, 'contact': None, 'lag': None, 'steps': i}
        move(target, 350)
        got = read_retry()
        if got is None:
            return {'status': 'no_reading', 'start': start, 'contact': None, 'lag': None, 'steps': i + 1}
        lag = target - got
        say(f'  step {i + 1}: commanded {target}, read {got} (lag {lag})')
        now = got
        if lag > dead_band:   # candidate: send the same target again and see whether it gives
            move(target, 350)
            again = read_retry()
            if again is None:
                return {'status': 'no_reading', 'start': start, 'contact': None, 'lag': None, 'steps': i + 1}
            if abs(again - got) <= 1:
                return {'status': 'contact', 'start': start, 'contact': again, 'lag': target - again, 'steps': i + 1}
            now = again
    return {'status': 'no_contact', 'start': start, 'contact': None, 'lag': None, 'steps': max_steps}


def classify(result, window):
    """Decide what a find_contact result means. window = (lo, hi) contact positions accepted for the expected object.
    Returns 'object' | 'outside_window' | 'no_contact' | 'no_reading' | 'bad_start'.
    'outside_window' covers both a smaller/larger thing and anything that is not the object (fingers, a wall)."""
    if result['status'] != 'contact':
        return result['status']
    lo, hi = window
    return 'object' if lo <= result['contact'] <= hi else 'outside_window'


def hold_check(read, target, seconds=2.0, tol=3, period=0.1):
    """After a squeeze: the reading must stay within `tol` pulses of the first one for `seconds`. Returns (ok, min, max)."""
    t0 = time.monotonic()
    vals = []
    while time.monotonic() - t0 < seconds:
        v = read()
        if v is not None:
            vals.append(v)
        time.sleep(period)
    if not vals:
        return False, None, None
    return max(vals) - min(vals) <= tol, min(vals), max(vals)
