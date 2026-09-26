"""Alternate all four wheels forward/reverse every 2 s at +-RPS while watching the IMU
heartbeat and battery voltage; stops and reports if the STM32 goes silent.
Usage: python3 motor_load_test.py 0.3 180   (rps, seconds). WHEELS MUST BE OFF THE GROUND.
"""
import serial,struct,time,sys
RPS=float(sys.argv[1]); DUR=float(sys.argv[2]); PHASE=2.0
def crc(b):
    c=0
    for x in b:
        c^=x
        for _ in range(8): c=(c>>1)^0x8C if c&1 else c>>1
    return c
def frame(func,data):
    f=bytes([0xAA,0x55,func,len(data)])+bytes(data)
    return f+bytes([crc(f[2:])])
def motors(sp):
    d=[1,len(sp)]
    for i,v in sp: d+=list(struct.pack("<Bf",i-1,v))
    return frame(3,d)
STOP=motors([(1,0),(2,0),(3,0),(4,0)])
assert crc(b"123456789")==0xA1
ser=serial.Serial("/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00",1000000,timeout=0.01); ser.rts=False; ser.dtr=False
buf=bytearray(); n_imu=0; last_imu=time.monotonic(); bat=[]; win=time.monotonic(); T0=win; hang=None; cmd="stop"
def pump():
    global buf,n_imu,last_imu
    buf+=ser.read(4096)
    while True:
        i=buf.find(b"\xAA\x55")
        if i<0: buf=buf[-1:] if buf.endswith(b"\xAA") else bytearray(); return
        del buf[:i]
        if len(buf)<4: return
        n=4+buf[3]+1
        if len(buf)<n: return
        f=bytes(buf[:n]); del buf[:n]
        if crc(f[2:-1])!=f[-1]: continue
        if f[2]==7: n_imu+=1; last_imu=time.monotonic()
        elif f[2]==0 and f[4]==4: bat.append(struct.unpack("<H",f[5:7])[0])
try:
    ser.write(STOP); time.sleep(0.3)
    print(f"test2 start: +-{RPS} rps, {PHASE}s phases, {DUR:.0f}s",flush=True)
    nxt=0
    while time.monotonic()-T0<DUR:
        t=time.monotonic()-T0
        d= 1 if int(t/PHASE)%2==0 else -1
        cmd=f"{'FWD' if d>0 else 'REV'} {RPS*d:+.2f}"
        ser.write(motors([(1,RPS*d),(2,RPS*d),(3,-RPS*d),(4,-RPS*d)]))
        end=time.monotonic()+0.1
        while time.monotonic()<end: pump()
        now=time.monotonic()
        if now-last_imu>1.0:
            hang=(t,cmd); print(f"!!! IMU SILENT {now-last_imu:.1f}s at t={t:.1f}s, last cmd={cmd}",flush=True); break
        if now-win>=10:
            print(f"t={t:5.0f}s imu/10s={n_imu:4d} bat_mV min/max={min(bat) if bat else '-'}/{max(bat) if bat else '-'} cmd={cmd}",flush=True)
            n_imu=0; bat=[]; win=now
finally:
    for _ in range(5): ser.write(STOP); time.sleep(0.02)
    print("STOP sent; hang =",hang,flush=True); ser.close()
