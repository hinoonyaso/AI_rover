import React, {useEffect, useState} from 'react';
import Database from './Database.jsx';
import RobotView from './RobotView.jsx';
import Missions from './Missions.jsx';
import Calibration from './Calibration.jsx';
import SensorServices from './SensorServices.jsx';
import {MonitoringSummary, ResourceTrend} from './MonitoringInsights.jsx';

const timeLabel = value => {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('ko-KR');
};

export function Dashboard({data, statusError, events, history, now, receivedAt, page = 'overview', onNavigate = () => {}, role = 'operator', onSignOut = () => {}, onChangePassword = () => {}}) {
  const h = data?.host;
  const robot = data?.robot;
  // Age values from the server using elapsed browser time; the two machines' wall clocks may differ.
  // 한글: 원격 브라우저와 서버의 시계가 다를 수 있으므로 서버 경과 시간에 브라우저 경과 시간을 더한다.
  const elapsed = receivedAt == null ? Infinity : Math.max(0, (now - receivedAt) / 1000);
  const snapshotAge = robot?.snapshot_age_seconds == null ? null : robot.snapshot_age_seconds + elapsed;
  const monitoring = snapshotAge != null && snapshotAge >= 0 && snapshotAge < 8 && robot?.status === 'monitoring';
  const age = seconds => {
    const value = seconds + elapsed;
    return typeof seconds === 'number' && Number.isFinite(value) && value >= 0 && value < 10 ? value : null;
  };
  const ageLabel = seconds => `최근 수신 ${seconds.toFixed(1)}초 전`;
  const batteryAge = monitoring ? age(robot.battery_age_seconds) : null;
  const card = (index, label, value, note, percent) => <article className="metric-card"><div className="metric-top"><span>{label}</span><span className="metric-index">{index}</span></div><strong>{value}</strong><div className="metric-foot"><span>{note}</span>{percent != null && <div className="meter" aria-hidden="true"><i style={{width: `${Math.min(100, Math.max(0, percent))}%`}}/></div>}</div></article>;
  const recordState = result => result.error ? '데이터를 가져오지 못했습니다.' : result.data?.database === 'unavailable' ? '데이터베이스를 사용할 수 없습니다.' : !result.data ? '확인 중' : null;
  const eventsState = recordState(events);
  const historyState = recordState(history);
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark" aria-hidden="true">J<span>.</span></span><div><b>JETINSPECT</b><small>ROBOT OPERATIONS</small></div></div><div className="side-label">WORKSPACE</div><nav className="side-nav" aria-label="워크스페이스"><button type="button" className={page === 'overview' ? 'nav-current' : 'nav-item'} onClick={() => onNavigate('overview')} aria-current={page === 'overview' ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">▦</span> 운영 현황</button><button type="button" className={page === 'robot' ? 'nav-current' : 'nav-item'} onClick={() => onNavigate('robot')} aria-current={page === 'robot' ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">⌖</span> 로봇 관제</button><button type="button" className={page === 'missions' ? 'nav-current' : 'nav-item'} onClick={() => onNavigate('missions')} aria-current={page === 'missions' ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">☷</span> 임무 관리</button><button type="button" className={page === 'calibration' ? 'nav-current' : 'nav-item'} onClick={() => onNavigate('calibration')} aria-current={page === 'calibration' ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">⚙</span> 센서 보정</button><button type="button" className={page === 'database' ? 'nav-current' : 'nav-item'} onClick={() => onNavigate('database')} aria-current={page === 'database' ? 'page' : undefined}><span className="nav-icon" aria-hidden="true">▤</span> 데이터베이스</button></nav><div className="session-menu"><span>{role === 'operator' ? '운영자' : '조회자'}</span><button type="button" onClick={onChangePassword}>비밀번호 변경</button><button type="button" onClick={onSignOut}>로그아웃</button></div><div className="side-bottom"><div className="side-indicator"/><div><b>모의 임무 지원</b><small>Robot control unavailable</small></div></div></aside>
    <main className="workspace"><div className="topbar"><span>WORKSPACE <i>/</i> {page === 'overview' ? 'OVERVIEW' : page === 'robot' ? 'ROBOT' : page === 'missions' ? 'MISSIONS' : page === 'calibration' ? 'CALIBRATION' : 'DATABASE'}</span><span className="topbar-right"><span className="status-dot"/> JETSON ORIN NANO <i>/</i> ROBOT READ ONLY</span></div>
    {page === 'calibration' ? <Calibration role={role}/> : page === 'database' ? <Database/> : page === 'robot' ? <RobotView {...{data, statusError, onNavigate}}/> : page === 'missions' ? <Missions role={role}/> : <div className="content"><header className="page-header"><div><p className="eyebrow"><span/> LIVE MONITORING</p><h1>운영 현황<span className="title-dot">.</span></h1><p className="subtitle">로봇과 시스템의 현재 상태를 확인합니다.</p></div><div className="header-meta"><div className={statusError ? 'badge bad' : 'badge'}><span className="status-dot"/>{statusError ? '서버 연결 끊김' : data ? '서버 연결됨' : '연결 중'}</div><span>마지막 갱신 {timeLabel(h?.timestamp)}</span></div></header>
    {statusError && <p className="warning" role="status">서버에서 현재 상태를 가져오지 못했습니다. 표시된 호스트 값은 이전 값입니다. 마지막 측정: {timeLabel(h?.timestamp)}</p>}
    <MonitoringSummary {...{data, statusError, monitoring, batteryAge}} streamAge={age}/><SensorServices {...{role, onNavigate}} robot={robot}/>
    <div className="section-title"><div><span className="section-kicker">01 / SYSTEM</span><h2>시스템 리소스</h2></div><span className="section-note">JETSON HOST <span>·</span> LIVE</span></div>
    <section className="cards" aria-label="호스트 상태">
      {card('01', 'CPU 사용률', h ? `${h.cpu_percent}%` : '—', '프로세서', h?.cpu_percent)}
      {card('02', '메모리', h ? `${h.memory_percent}%` : '—', h ? `${h.memory_used_gb} / ${h.memory_total_gb} GiB` : '확인 중', h?.memory_percent)}
      {card('03', '저장 공간', h ? `${h.disk_percent}%` : '—', h ? `여유 ${h.disk_free_gb} GiB` : '확인 중', h?.disk_percent)}
      {card('04', '시스템 온도', h?.temperature_c != null ? `${h.temperature_c}°C` : '—', '확인 가능한 센서 중 최대값', null)}
    </section>
    <ResourceTrend history={history}/>
    <div className="section-title sensor-heading"><div><span className="section-kicker">02 / CONNECTIVITY</span><h2>연결 상태</h2></div><span className="section-note">SENSOR STATUS</span></div>
    <section className="connect-grid" aria-label="연결 상태"><div className="panel sensor-panel"><div className="panel-head"><div><h3>센서 모니터링</h3><p>연결된 센서의 데이터 수신 상태</p></div><span className="panel-symbol" aria-hidden="true">⌁</span></div>
      <div className="sensor-list"><div className="sensor-row"><div className="sensor-name"><span className="sensor-icon">V</span><div><b>배터리 전압</b><small>POWER SUPPLY</small></div></div><div className="sensor-value">{batteryAge != null && robot.battery_voltage != null ? <><b>{robot.battery_voltage.toFixed(2)} V</b><small>{ageLabel(batteryAge)} · 원본 전압{robot.battery_display_calibrated_v != null ? ` · 보정 표시 ${robot.battery_display_calibrated_v.toFixed(2)} V` : ''}</small></> : <><b className="muted">측정값 미확인</b><small>데이터 수신 대기</small></>}</div></div>
      {[['imu', 'IMU', 'INERTIAL SENSOR', '◉'], ['scan', 'LiDAR', 'DISTANCE SENSOR', '◌'], ['camera', '카메라 토픽', 'IMAGE STREAM', '◧']].map(([key, label, description, icon]) => {
        const stream = robot?.streams?.[key];
        const streamAge = monitoring ? age(stream?.age_seconds) : null;
        return <div className="sensor-row" key={key}><div className="sensor-name"><span className="sensor-icon">{icon}</span><div><b>{label}</b><small>{description}</small></div></div><div className="sensor-value">{streamAge == null ? <><b className="muted">수신 미확인</b><small>데이터 수신 대기</small></> : <><b>{stream.hz == null ? '주기 계산 중' : `${stream.hz} Hz`}</b><small>{ageLabel(streamAge)}</small></>}</div></div>;
      })}</div><p className="sensor-disclaimer"><span>ⓘ</span> 수신 미확인은 로봇 고장을 뜻하지 않습니다.</p></div>
      <div className="panel service-panel"><div className="panel-head"><div><h3>서비스 상태</h3><p>운영 환경 연결 상태</p></div><span className="panel-symbol" aria-hidden="true">↗</span></div>
      <div className="service-list"><div className="service-row"><span>운영 데이터베이스</span><b className={!statusError && data?.database === 'connected' ? 'pill online' : 'pill neutral'}>{!data ? '확인 중' : statusError ? '상태 미확인' : data.database === 'connected' ? '연결됨' : '연결 안 됨'}</b></div><div className="service-row"><span>ROS 센서 모니터</span><b className={monitoring ? 'pill online' : 'pill neutral'}>{!data ? '확인 중' : monitoring ? '수신 중' : '미확인'}</b></div><div className="service-row"><span>실제 임무</span><b className="pill neutral">미연결</b></div></div><div className="service-note"><b>관제 전용</b><p>센서와 카메라는 읽기 전용이며 로봇 제어는 연결되어 있지 않습니다.</p></div></div></section>
    <div className="section-title records-heading"><div><span className="section-kicker">03 / RECORDS</span><h2>기록 및 이력</h2></div><span className="section-note">SYSTEM LOGS</span></div>
    <div className="records-grid"><section className="panel history-panel"><div className="panel-head"><div><h3>시스템 지표 이력</h3><p>최근 최대 120개 기록</p></div><span className="panel-symbol" aria-hidden="true">↗</span></div>
      {historyState ? <p className="empty-state" role="status">{historyState}</p> : !history.data.samples.length ? <p className="empty-state">표시할 지표 기록이 없습니다.</p> : <div className="table-wrap"><table><thead><tr><th>기록 시각 (DB)</th><th>CPU</th><th>메모리</th><th>저장 공간</th><th>온도</th></tr></thead><tbody>{history.data.samples.map((sample, index) => <tr key={`${sample.recorded_at}-${index}`}><td>{sample.recorded_at?.replace('T', ' ')}</td><td>{sample.cpu_percent}%</td><td>{sample.memory_percent}%</td><td>{sample.disk_percent}%</td><td>{sample.temperature_c == null ? '—' : `${sample.temperature_c}°C`}</td></tr>)}</tbody></table></div>}
      <p className="record-note">DB 기록 시각의 시간대는 미확인</p></section>
    <section className="panel events-panel"><div className="panel-head"><div><h3>최근 운영 기록</h3><p>최근 시스템 이벤트</p></div><span className="panel-symbol" aria-hidden="true">↗</span></div>{eventsState ? <p className="empty-state" role="status">{eventsState}</p> : events.data.events.length ? <div className="event-list">{events.data.events.slice(0, 8).map((event, i) => <div className="event-row" key={i}><span className="event-dot"/><div><b>{event.source}</b><p>{event.message}</p><small>{event.recorded_at.replace('T', ' ')}</small></div></div>)}</div> : <p className="empty-state">표시할 운영 기록이 없습니다.</p>}<p className="record-note">DB 기록 시각의 시간대는 미확인</p></section></div>
    <footer><span>JETINSPECT-M <i> / </i> OPERATIONS DASHBOARD</span><span>호스트 최종 측정: {timeLabel(h?.timestamp)}</span></footer></div>}</main></div>;
}

export default function App({role = 'operator', onSignOut = () => {}, onChangePassword = () => {}}) {
  const [page, setPage] = useState('overview');
  const [data, setData] = useState(null);
  const [statusError, setStatusError] = useState(false);
  const [events, setEvents] = useState({data: null, error: false});
  const [history, setHistory] = useState({data: null, error: false});
  const [now, setNow] = useState(Date.now());
  const [receivedAt, setReceivedAt] = useState(null);
  useEffect(() => {
    let active = true;
    let refreshing = false;
    async function get(path) {
      const response = await fetch(path, {cache: 'no-store', signal: AbortSignal.timeout(4000)});
      if (!response.ok) throw new Error('unavailable');
      return response.json();
    }
    async function refresh() {
      if (refreshing) return;
      refreshing = true;
      const requestedAt = Date.now();
      const results = await Promise.allSettled(['/api/status', '/api/events', '/api/metrics'].map(get));
      refreshing = false;
      if (!active) return;
      if (results[0].status === 'fulfilled') { setData(results[0].value); setReceivedAt(requestedAt); setStatusError(false); }
      else setStatusError(true);
      setEvents(results[1].status === 'fulfilled' ? {data: results[1].value, error: false} : {data: null, error: true});
      setHistory(results[2].status === 'fulfilled' ? {data: results[2].value, error: false} : {data: null, error: true});
      setNow(Date.now());
    }
    refresh();
    const refreshId = setInterval(refresh, 5000);
    const clockId = setInterval(() => setNow(Date.now()), 1000);
    return () => { active = false; clearInterval(refreshId); clearInterval(clockId); };
  }, []);
  return <Dashboard {...{data, statusError, events, history, now, receivedAt, page, role, onSignOut, onChangePassword}} onNavigate={setPage}/>;
}
