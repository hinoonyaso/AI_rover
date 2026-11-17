"""Track bounded odometry observations without publishing motion commands.

한글: 이동 명령을 발행하지 않고 오도메트리 관측을 추적한다.
"""
import math
import uuid


class OdomTracker:
    """Unwrap heading only across continuously received same-frame messages.

    한글: 같은 프레임에서 연속 수신된 메시지만 방향각을 누적한다.
    """
    def __init__(self):
        self.value = None

    def update(self, msg, received_at):
        """Accept a valid observation and start a new generation after a gap.

        한글: 유효한 관측을 기록하고 중단 후에는 새 세대로 분리한다.
        """
        try:
            p, q = msg.pose.pose.position, msg.pose.pose.orientation
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            numbers = [p.x,p.y,q.x,q.y,q.z,q.w,stamp,received_at]
            if not all(math.isfinite(v) for v in numbers) or stamp <= 0 or not msg.header.frame_id or not msg.child_frame_id:
                self.value = None; return
            norm = math.sqrt(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w)
            if abs(norm-1) > .01 or abs(q.x) > .1 or abs(q.y) > .1:
                self.value = None; return
            yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
            old=self.value
            continuous=(old is not None and 0 <= received_at-old['received_at'] < 1.5 and stamp>old['stamp']
                        and msg.header.frame_id==old['frame_id'] and msg.child_frame_id==old['child_frame_id'])
            if continuous:
                delta=math.atan2(math.sin(yaw-old['yaw']),math.cos(yaw-old['yaw']))
                total=old['yaw_unwrapped']+delta
                generation=old['generation']
            else:
                total=yaw;generation=uuid.uuid4().hex
            self.value={'x_m':p.x,'y_m':p.y,'yaw':yaw,'yaw_unwrapped':total,'stamp':stamp,
                        'received_at':received_at,'frame_id':msg.header.frame_id,'child_frame_id':msg.child_frame_id,
                        'generation':generation}
        except (AttributeError, TypeError, ValueError, OverflowError):
            self.value=None


def fresh_odom(snapshot, source, now):
    """Read one recent odometry stream, never substitute another source.

    한글: 최근 오도메트리 한 종류만 읽고 다른 출처로 대체하지 않는다.
    """
    try:
        timestamp=snapshot['timestamp']; data=snapshot['odometry'][source]; received=data['received_at']
        values=[timestamp,received,data['x_m'],data['y_m'],data['yaw'],data['yaw_unwrapped'],data['stamp']]
        if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in values): return None
        if not 0<=now-timestamp<8 or not 0<=now-received<3 or received>timestamp: return None
        if not all(isinstance(data[k],str) and data[k] for k in ('frame_id','child_frame_id','generation')): return None
        return data
    except (KeyError, TypeError, ValueError):
        return None


def odom_displacement(start, end, motion):
    """Return start-body-frame displacement in cm or unwrapped rotation in degrees.

    한글: 시작 몸체 기준 이동 cm 또는 누적 회전각 도를 반환한다.
    """
    if start['generation'] != end['generation'] or end['stamp'] <= start['stamp']:
        raise ValueError('odom_discontinuity')
    dx,dy=end['x_m']-start['x_m'],end['y_m']-start['y_m']
    yaw=start['yaw']
    if motion=='forward': return 100*(math.cos(yaw)*dx+math.sin(yaw)*dy)
    if motion=='lateral': return 100*(-math.sin(yaw)*dx+math.cos(yaw)*dy)
    if motion=='rotation': return math.degrees(end['yaw_unwrapped']-start['yaw_unwrapped'])
    raise ValueError('invalid_motion')
