# 한글: IMU 프레임을 N초 동안 세어 끊김(gap)을 보고하는 수동 heartbeat 시험. base_node가 포트를 열고 있으면 안 된다.
"""Passive heartbeat test: count IMU frames for N seconds and report gaps.
Usage: python3 imu_soak.py 600   (base_node must NOT be running: it opens the port)
"""
import serial,time,sys
DUR=float(sys.argv[1]); PORT="/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
T0=time.monotonic(); ser=serial.Serial(PORT,1000000,timeout=0.05); ser.rts=False; ser.dtr=False
buf=bytearray(); last=None; maxgap=0; n=0; nwin=0; win=T0; longest=0
print(f"soak {DUR:.0f}s start",flush=True)
while time.monotonic()-T0<DUR:
    d=ser.read(4096)
    now=time.monotonic()
    if d:
        buf+=d
        # count IMU frame starts AA 55 07 18 as a cheap heartbeat
        c=buf.count(b"\xAA\x55\x07\x18"); 
        if c:
            n+=c; nwin+=c; 
            if last is not None: maxgap=max(maxgap,now-last)
            last=now; buf=buf[-3:]
        else: buf=buf[-3:]
    if now-win>=30:
        print(f"t={now-T0:5.0f}s imu/30s={nwin:4d} max_gap={maxgap*1000:5.0f}ms since_last={now-(last or T0):.2f}s",flush=True)
        nwin=0; maxgap=0; win=now
print(f"DONE total imu={n} silence_at_end={time.monotonic()-(last or T0):.1f}s")
