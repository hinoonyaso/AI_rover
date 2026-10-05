# 한글: base_node의 crash guard를 가상 시리얼에서 시험한다(하드웨어 불필요). SEGV/ABRT/HUP/QUIT에는 마지막 프레임이 정지여야 하고 KILL은 잡을 수 없다.
"""Checks base_node's crash guard on a virtual serial port (no hardware needed):
Usage: python3 crash_guard_test.py 11 SIGSEGV   (signal number, label)
Expect: last frame written to the port is a STOP for SEGV/ABRT/HUP/QUIT, not for KILL.
"""
import struct,os,pty,signal,subprocess,sys,time,tty,select,tempfile
sig=int(sys.argv[1]); name=sys.argv[2]
master,slave=pty.openpty(); tty.setraw(master); path=os.ttyname(slave)
node=subprocess.Popen([os.path.expanduser("~/jetrover_ws/install/jetrover_base/lib/jetrover_base/base_node"),
    "--ros-args","-p",f"port:={path}","-p","cmd_vel_timeout:=1000.0","-p","stm32_timeout:=1000.0"],
    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
pub=subprocess.Popen(["ros2","topic","pub","-r","10","/cmd_vel","geometry_msgs/msg/Twist","{linear: {x: 0.1}}"],
    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def drain(t):
    buf=b""; end=time.time()+t
    while time.time()<end:
        if select.select([master],[],[],0.05)[0]: buf+=os.read(master,4096)
    return buf
before=drain(2.0)
os.kill(node.pid,sig)
after=drain(1.0); node.wait(timeout=5); pub.terminate()
frames=(before+after).split(b"\xaa\x55")[1:]
def parse(f):
    # f = FUNC LEN DATA.. CRC ; motor DATA = 01 N (id f32)*N
    if len(f)<4 or f[0]!=3 or len(f)<2+f[1]+1: return None
    d=f[2:2+f[1]]; n=d[1]
    return [struct.unpack("<f",d[2+5*k+1:2+5*k+5])[0] for k in range(n)]
def is_stop(f):
    v=parse(f); return v is not None and all(x==0.0 for x in v)
motion=[f for f in frames if parse(f) is not None and not is_stop(f)]
stops=[f for f in frames if is_stop(f)]
last=frames[-1] if frames else b""
print(f"{name:8s} node rc={node.returncode:4d}  motion frames={len(motion):3d}  stop frames={len(stops)}  last frame is STOP: {is_stop(last)}")
