import React, {useEffect, useState} from 'react';
import {missionLabel, missionName, stageLabel} from './Missions.jsx';

export default function RobotView({data, statusError, onNavigate}) {
  const [tick, setTick] = useState(Date.now());
  const [imageError, setImageError] = useState(false);
  const [pose, setPose] = useState(null);
  const [missions, setMissions] = useState(null);
  const [missionError, setMissionError] = useState(false);
  const [hasOlderMissions, setHasOlderMissions] = useState(false);
  useEffect(() => {
    const timer = setInterval(() => setTick(Date.now()), 2000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/gazebo/pose', {cache: 'no-store', signal: controller.signal})
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(setPose).catch(error => { if (error.name !== 'AbortError') setPose(null); });
    return () => controller.abort();
  }, [tick]);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/missions?limit=50', {cache: 'no-store', signal: controller.signal})
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(result => { setMissions(result.missions); setHasOlderMissions(Boolean(result.next_cursor)); setMissionError(false); })
      .catch(error => { if (error.name !== 'AbortError') setMissionError(true); });
    return () => controller.abort();
  }, [tick]);
  const activeMission = missions?.find(item => ['queued', 'running', 'cancel_requested'].includes(item.state));
  const px = pose ? (pose.x + 1.254) / 0.05 : null;
  const py = pose ? 68 - (pose.y + 1.184) / 0.05 : null;
  const inMap = pose && px >= 0 && px <= 83 && py >= 0 && py <= 68;
  return <div className="content"><header className="page-header"><div><p className="eyebrow"><span/> ROBOT MONITORING</p><h1>로봇 관제<span className="title-dot">.</span></h1><p className="subtitle">카메라와 저장된 지도를 확인합니다.</p></div><div className="header-meta"><div className="badge">읽기 전용</div><span>로봇 제어 미연결</span></div></header>
    <div className="robot-grid"><section className="panel camera-panel"><div className="panel-head"><div><h3>카메라 미리보기</h3><p>컬러 카메라 · 약 2초마다 갱신</p></div><span className="panel-symbol" aria-hidden="true">◧</span></div><div className="camera-frame"><img src={`/api/camera/preview?t=${tick}`} alt="로봇 컬러 카메라 미리보기" onError={() => setImageError(true)} onLoad={() => setImageError(false)} style={{visibility: imageError ? 'hidden' : 'visible'}}/>{imageError && <div className="camera-placeholder" role="status"><b>카메라 영상 미확인</b><span>카메라 토픽과 모니터 연결을 확인해 주세요.</span></div>}</div><p className="record-note">실시간 동영상이 아닌 주기적 정지 화면입니다. 지연될 수 있으므로 안전 판단에 사용하지 마세요.</p></section>
    <section className="panel map-panel"><div className="panel-head"><div><h3>저장된 지도</h3><p>lap2_20261005 · Gazebo 위치</p></div><span className="panel-symbol" aria-hidden="true">⌖</span></div><div className="map-frame"><svg viewBox="0 0 83 68" role="img" aria-label="저장 지도와 Gazebo 위치"><image href="/saved-map.png" width="83" height="68"/>{inMap && <g transform={`translate(${px} ${py}) rotate(${-pose.yaw * 180 / Math.PI})`}><circle r="2.5" fill="#16a06f" stroke="white" strokeWidth="0.7"/><path d="M 0 -1.4 L 4 0 L 0 1.4 Z" fill="white"/></g>}</svg></div><p className="record-note">{inMap ? `시뮬레이션 위치: ${pose.x.toFixed(2)}, ${pose.y.toFixed(2)} m` : pose ? 'Gazebo 위치가 지도 범위 밖입니다.' : 'Gazebo 위치 미확인'} · 저장 지도이며 실제 로봇 위치가 아닙니다.</p></section>
    <section className="panel mission-panel"><div className="panel-head"><div><h3>시뮬레이션 임무</h3><p>모의 및 Gazebo 임무 현황</p></div><span className="pill neutral">{missionError ? '확인 불가' : activeMission ? missionLabel(activeMission.state, activeMission.mode) : missions ? '최근 임무 확인됨' : '확인 중'}</span></div><p className="mission-empty">{missionError ? '임무 상태를 불러오지 못했습니다.' : activeMission ? `${missionName(activeMission)} · ${missionLabel(activeMission.state, activeMission.mode)} · ${stageLabel(activeMission.stage)}` : missions ? (hasOlderMissions ? '최근 50개 임무 중 진행 중인 임무가 없습니다. 전체 기록은 임무 관리에서 확인하세요.' : '현재 진행 중인 시뮬레이션 임무가 없습니다.') : '임무 상태를 확인하고 있습니다.'}</p><button type="button" className="db-button" onClick={() => onNavigate('missions')}>임무 관리로 이동</button><p className="record-note">실제 로봇 임무 관리자는 연결되지 않았습니다.</p></section>
    <section className="panel mission-panel"><div className="panel-head"><div><h3>관제 연결</h3><p>데이터 제공 상태</p></div></div><div className="service-list"><div className="service-row"><span>관제 서버</span><b className={statusError ? 'pill neutral' : data ? 'pill online' : 'pill neutral'}>{statusError ? '연결 끊김' : data ? '연결됨' : '확인 중'}</b></div><div className="service-row"><span>Gazebo 위치</span><b className={pose ? 'pill online' : 'pill neutral'}>{pose ? '수신 중' : '미확인'}</b></div><div className="service-row"><span>실제 임무 관리자</span><b className="pill neutral">미연결</b></div></div></section></div>
  </div>;
}
