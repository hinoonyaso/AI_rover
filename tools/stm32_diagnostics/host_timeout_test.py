# 한글: 호스트가 죽었을 때 STM32가 스스로 바퀴를 세우는지 확인한다(0.3rps로 구동 후 2초에 쓰는 프로세스를 SIGKILL, 15초에 정지 전송). 결과: 펌웨어에 호스트 timeout이 없어서 STOP 때까지 계속 돌았다. 바퀴를 띄울 것.
"""Does the STM32 stop the wheels by itself when the host dies? Runs the wheels at 0.3 rps,
SIGKILLs the writer after 2 s, and sends STOP at t=15 s. Watch the wheels. WHEELS OFF THE GROUND.
Result on this robot: wheels kept spinning until STOP (no host timeout in firmware).
"""
import os,signal,struct,sys,time,serial
PORT="/dev/serial/by-id/usb-1a86_USB_Single_Serial_596F003889-if00"
# 한글: RRC CRC-8/MAXIM(호스트 rrc_protocol.cpp와 동일).
def crc(b):
    c=0
    for x in b:
        c^=x
        for _ in range(8): c=(c>>1)^0x8C if c&1 else c>>1
    return c
def frame(func,data):
    f=bytes([0xAA,0x55,func,len(data)])+bytes(data); return f+bytes([crc(f[2:])])
def motors(sp):
    d=[1,len(sp)]
    for i,v in sp: d+=list(struct.pack("<Bf",i-1,v))
    return frame(3,d)
STOP=motors([(1,0),(2,0),(3,0),(4,0)])
R=0.3; FWD=motors([(1,R),(2,R),(3,-R),(4,-R)])

pid=os.fork()
if pid==0:                      # child = stand-in for the crashing base_node
    s=serial.Serial(PORT,1000000,timeout=0); s.rts=False; s.dtr=False
    while True:
        s.write(FWD); time.sleep(0.1)
t0=time.monotonic()
print("t=0.0  motors ON (0.3 rps, resent at 10 Hz)",flush=True)
try:
    time.sleep(2.0)
    os.kill(pid,signal.SIGKILL); os.waitpid(pid,0)
    print(f"t={time.monotonic()-t0:.1f}  writer KILLED (-9), no stop sent. STOP will be sent at t=15",flush=True)
    time.sleep(13.0)
finally:
    try: os.kill(pid,signal.SIGKILL)
    except Exception: pass
    s=serial.Serial(PORT,1000000,timeout=0.1); s.rts=False; s.dtr=False
    for _ in range(5): s.write(STOP); time.sleep(0.02)
    print(f"t={time.monotonic()-t0:.1f}  STOP sent by supervisor",flush=True)
    time.sleep(0.5); n=len(s.read(4096)); print("STM32 bytes after:",n); s.close()
