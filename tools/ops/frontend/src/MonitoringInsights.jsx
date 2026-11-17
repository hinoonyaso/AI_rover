import React, {useState} from 'react';

const metrics = [
  {key: 'cpu_percent', label: 'CPU', unit: '%', fixed: [0, 100]},
  {key: 'memory_percent', label: '메모리', unit: '%', fixed: [0, 100]},
  {key: 'disk_percent', label: '저장 공간', unit: '%', fixed: [0, 100]},
  {key: 'temperature_c', label: '온도', unit: '°C'},
];

export function ResourceTrend({history}) {
  const [selected, setSelected] = useState('cpu_percent');
  const metric = metrics.find(item => item.key === selected);
  const state = history.error ? '지표를 가져오지 못했습니다.' : history.data?.database === 'unavailable' ? '데이터베이스를 사용할 수 없습니다.' : !history.data ? '지표를 불러오는 중입니다.' : null;
  const samples = (history.data?.samples || []).slice(0, 60).reverse();
  const values = samples.map(sample => typeof sample[selected] === 'number' && Number.isFinite(sample[selected]) ? sample[selected] : null);
  const valid = values.filter(value => value !== null);
  const min = metric.fixed ? metric.fixed[0] : valid.length ? Math.floor(Math.min(...valid) - 2) : 0;
  const max = metric.fixed ? metric.fixed[1] : valid.length ? Math.ceil(Math.max(...valid) + 2) : 1;
  const points = values.map((value, index) => value === null ? null : `${20 + (samples.length === 1 ? 0 : index * 560 / (samples.length - 1))},${110 - (value - min) / (max - min || 1) * 90}`);
  // Split gaps instead of drawing invented values through missing measurements.
  // 한글: 측정 누락 구간은 임의의 값으로 연결하지 않고 선을 끊는다.
  const segments = [];
  for (const point of points) {
    if (point === null) segments.push([]);
    else { if (!segments.length) segments.push([]); segments[segments.length - 1].push(point); }
  }
  return <section className="panel trend-panel"><div className="panel-head"><div><h3>시스템 자원 추이</h3><p>최근 최대 60개 기록 · 오래된 순서부터</p></div><span className="panel-symbol" aria-hidden="true">⌁</span></div>
    <div className="trend-tabs" role="group" aria-label="표시할 지표">{metrics.map(item => <button type="button" key={item.key} className={selected === item.key ? 'trend-tab selected' : 'trend-tab'} aria-pressed={selected === item.key} onClick={() => setSelected(item.key)}>{item.label}</button>)}</div>
    {state ? <p className="empty-state" role="status">{state}</p> : !valid.length ? <p className="empty-state">표시할 {metric.label} 기록이 없습니다.</p> : <><div className="trend-stats"><div><small>최근 기록</small><strong>{values.at(-1) == null ? '—' : `${values.at(-1).toFixed(1)}${metric.unit}`}</strong></div><div><small>최저 / 최고</small><b>{Math.min(...valid).toFixed(1)} / {Math.max(...valid).toFixed(1)} {metric.unit}</b></div></div><svg className="trend-chart" viewBox="0 0 600 130" preserveAspectRatio="none" role="img" aria-label={`${metric.label} 기록 ${valid.length}개, 최저 ${Math.min(...valid).toFixed(1)}${metric.unit}, 최고 ${Math.max(...valid).toFixed(1)}${metric.unit}`}><line x1="20" y1="20" x2="580" y2="20"/><line x1="20" y1="65" x2="580" y2="65"/><line x1="20" y1="110" x2="580" y2="110"/>{segments.map((segment, index) => segment.length > 1 ? <polyline key={index} points={segment.join(' ')}/> : segment.length ? <circle key={index} cx={segment[0].split(',')[0]} cy={segment[0].split(',')[1]} r="3"/> : null)}</svg><div className="trend-axis"><span>오래된 기록</span><span>최신 기록</span></div><p className="record-note">측정 순서 기준 표시 · 기록 간 간격이 일정하지 않을 수 있습니다.</p></>}
  </section>;
}

export function MonitoringSummary({data, statusError, monitoring, batteryAge, streamAge}) {
  if (!data && !statusError) return <section className="overview-notice" role="status">상태를 확인하고 있습니다.</section>;
  const notices = [];
  if (statusError) notices.push('서버 연결 끊김');
  if (!statusError && data?.database !== 'connected') notices.push('데이터베이스 연결 미확인');
  if (!monitoring) notices.push('ROS 모니터 미확인');
  if (monitoring) {
    if (batteryAge == null) notices.push('배터리 측정값 미확인');
    const missing = [['imu', 'IMU'], ['scan', 'LiDAR'], ['camera', '카메라']].filter(([key]) => streamAge(data?.robot?.streams?.[key]?.age_seconds) == null).map(([, label]) => label);
    if (missing.length) notices.push(`${missing.join(' · ')} 수신 미확인`);
  }
  return <section className={notices.length ? 'overview-notice attention' : 'overview-notice'} aria-label="연결 상태 요약"><span className="notice-icon" aria-hidden="true">{notices.length ? '!' : '✓'}</span><div><b>{notices.length ? '확인이 필요한 항목' : '현재 연결된 항목을 수신 중입니다'}</b><p>{notices.length ? notices.join('  /  ') : '서버, 데이터베이스와 모니터링 데이터가 응답하고 있습니다.'}</p></div><span className="notice-label">상태 요약</span></section>;
}
