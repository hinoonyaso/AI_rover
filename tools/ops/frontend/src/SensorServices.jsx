import React, {useEffect, useState} from 'react';

export default function SensorServices({role, robot, onNavigate}) {
  const [services, setServices] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function refresh() {
    try { const r = await fetch('/api/sensor-services', {cache:'no-store'}); if (!r.ok) throw new Error(); setServices(await r.json()); }
    catch { setError('센서 서비스 상태를 불러오지 못했습니다.'); }
  }
  useEffect(() => { refresh(); const timer = setInterval(refresh, 4000); return () => clearInterval(timer); }, []);
  async function action(kind, name) {
    setError(''); setBusy(true);
    try {
      const r = await fetch(`/api/sensor-services/${kind}/${name}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);
      setServices(previous => ({...previous, ...data}));
    } catch (failure) {
      setError(({camera_already_running:'다른 카메라 노드가 이미 실행 중입니다. 기존 노드를 사용하거나 직접 종료하세요.', base_already_running:'다른 base_node가 이미 실행 중입니다. 센서 전용 모드를 먼저 종료하세요.', arm_already_running:'다른 base_node가 이미 실행 중입니다. 기존 노드를 사용하세요.', lidar_already_running:'다른 라이다 노드가 이미 실행 중입니다. 기존 노드를 사용하세요.', tf_already_running:'다른 로봇 좌표계 발행기가 이미 실행 중입니다. 기존 노드를 사용하세요.', ros_unavailable:'ROS 노드 상태를 확인할 수 없습니다.', service_failed:'센서 서비스를 시작하거나 중지하지 못했습니다.'})[failure.message] || '센서 서비스 요청에 실패했습니다.');
    } finally { setBusy(false); }
  }
  const received = key => robot?.status === 'monitoring' && robot?.streams?.[key]?.age_seconds != null && robot.streams[key].age_seconds < 10;
  const render = (kind, label, key) => {
    const unit = services?.[kind], running = unit?.active === 'active', available = unit?.load === 'loaded';
    return <div className="sensor-control-entry" key={kind}><div className="service-row"><span>{label}</span><b className={running ? 'pill online' : 'pill neutral'}>{!unit ? '확인 중' : !available ? '서비스 미설치' : running ? '실행 중' : unit.active === 'failed' ? '실행 실패' : '중지됨'}</b></div>{kind !== 'tf' && <div className="service-row"><span>{kind === 'camera' ? '카메라 영상' : kind === 'lidar' ? 'LiDAR 데이터' : 'IMU 데이터'}</span><b className={received(key) ? 'pill online' : 'pill neutral'}>{received(key) ? '수신 중' : '수신 미확인'}</b></div>}<div className="mission-actions"><button className="db-button" disabled={busy || role !== 'operator' || !available || running} onClick={() => action(kind,'start')}>연결</button><button className="db-button" disabled={busy || role !== 'operator' || !running} onClick={() => action(kind,'stop')}>종료</button>{kind === 'camera' && <button className="db-button" onClick={() => onNavigate('robot')}>카메라 보기</button>}</div></div>;
  };
  return <section className="panel sensor-control"><div className="panel-head"><div><h3>센서 연결</h3><p>센서 드라이버와 로봇 좌표계 발행을 따로 시작하고 상태를 확인합니다.</p></div></div><div className="sensor-control-grid">{render('camera','카메라 서비스','camera')}{render('base','IMU · base_node 센서 전용','imu')}{render('arm','IMU · 팔 관절 읽기 전용','imu')}{render('lidar','LiDAR 서비스','scan')}{render('tf','로봇 좌표계 (TF)',null)}</div>
    {role === 'viewer' && <p className="record-note">서비스 연결과 종료는 운영자 계정으로 할 수 있습니다.</p>}
    <p className="record-note">두 base 모드는 동시에 실행할 수 없습니다. 팔 관절 읽기를 사용하려면 센서 전용 모드를 먼저 종료하세요. 팔 읽기 모드는 위치·온도 조회만 수행하며 바퀴·팔 명령이나 비상정지 해제는 하지 않습니다. 서비스 실행과 데이터 수신은 별도 상태입니다. 종료 버튼은 대시보드가 실행한 서비스에만 적용됩니다.</p>
    {error && <p className="warning" role="alert">{error}</p>}</section>;
}
