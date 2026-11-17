import React, {useEffect, useRef, useState} from 'react';

export const labels = {created: '생성됨', queued: '시작 대기', running: '모의 실행 중', cancel_requested: '취소 요청됨', succeeded: '모의 성공', failed: '모의 실패', canceled: '취소 완료', interrupted: '중단됨'};
export const missionLabel = (state, mode) => mode === 'gazebo' ? ({running: 'Gazebo 실행 중', succeeded: 'Gazebo 성공', failed: 'Gazebo 실패'}[state] || labels[state]) : labels[state];
const reasons = {nav2_succeeded: 'Gazebo 주행 성공', nav2_action_unavailable: 'Gazebo Nav2 주행 서버가 준비되지 않았습니다.', inspection_observed: '가상 경광등 관측 완료', inspection_unconfirmed: '카메라 영상 또는 경광등 상태를 확인하지 못했습니다.', inspection_result_unconfirmed: '점검 결과를 확인하지 못했습니다.', inspection_canceled: '점검 취소가 확인되었습니다.', gazebo_start_pose_mismatch: 'Gazebo 로봇을 시작 위치로 초기화해야 합니다.', gazebo_pose_unavailable: 'Gazebo 위치를 확인할 수 없습니다.', gazebo_unavailable_or_unconfirmed: 'Gazebo 연결 또는 결과를 확인할 수 없습니다.', gazebo_result_unconfirmed: 'Gazebo 결과를 확인할 수 없습니다.', timeout_cancel_confirmed: '시간 초과로 Gazebo 주행이 취소되었습니다.', cancel_confirmed: 'Gazebo 주행 취소가 확인되었습니다.', manager_restarted: '관리자 재시작으로 중단되었습니다.'};
Object.assign(reasons, {gazebo_environment_busy: '다른 시뮬레이터가 실행 중입니다. 기존 시뮬레이터를 종료한 뒤 다시 시도하세요.', gazebo_start_failed: 'Gazebo 환경을 시작하지 못했습니다.', gazebo_start_timeout: 'Gazebo 환경 준비 시간이 초과됐습니다.', gazebo_fixture_unavailable: '가상 경광등 시험판을 준비하지 못했습니다.', gazebo_cleanup_unconfirmed: 'Gazebo 종료를 확인하지 못했습니다.', gazebo_preparation_canceled: 'Gazebo 환경 준비를 취소했습니다.', canceled_before_goal: '주행 목표 전송 전에 취소했습니다.'});
const errors = {mission_busy: '다른 모의 임무가 실행 중입니다.', invalid_transition: '현재 상태에서는 요청할 수 없습니다.', manager_unavailable: '모의 임무 관리자를 사용할 수 없습니다.', database_unavailable: '모의 임무 저장소를 사용할 수 없습니다.', origin_denied: '현재 접속 주소에서는 요청할 수 없습니다.'};
const kinds = {simulation: {mode: 'simulation', kind: 'inspection_demo'}, gazebo: {mode: 'gazebo', kind: 'navigate_demo'}, gazebo_inspection: {mode: 'gazebo', kind: 'inspect_stack_light'}};
export const missionName = item => item.kind === 'inspect_stack_light' ? 'Gazebo 경광등 점검' : item.mode === 'gazebo' ? 'Gazebo 주행' : '모의 점검';
const colorNames = {red: '빨강', yellow: '노랑', green: '초록'};
const colorStates = {on: '켜짐', off: '꺼짐', blinking: '깜빡임', unknown: '미확인'};
export const stageLabel = stage => ({simulated_inspection: '모의 점검', gazebo_preparing: 'Gazebo 환경 준비 중', gazebo_navigation: 'Gazebo 주행', gazebo_inspection: '경광등 점검'}[stage] || '—');

async function call(path, options = {}) {
  const response = await fetch(path, {cache: 'no-store', ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(errors[data?.error?.code] || '요청을 처리하지 못했습니다.');
  return data;
}

export default function Missions({role = 'operator'}) {
  const [missions, setMissions] = useState(null);
  const [selected, setSelected] = useState(null);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');
  const [refreshError, setRefreshError] = useState('');
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState('simulation');
  const [pageNumber, setPageNumber] = useState(0);
  const [cursors, setCursors] = useState([null]);
  const [nextCursor, setNextCursor] = useState(null);
  const cursorRef = useRef(null);
  const selectedRef = useRef(null);
  const requestIds = useRef({simulation: null, gazebo: null, gazebo_inspection: null});
  const generation = useRef(0);
  async function refresh() {
    const current = ++generation.current;
    try {
      const query = new URLSearchParams({limit: '50'});
      if (cursorRef.current) query.set('cursor', cursorRef.current);
      const data = await call(`/api/missions?${query}`);
      const id = selectedRef.current;
      const detail = id ? await call(`/api/missions/${id}/events`) : {events: []};
      if (current !== generation.current) return;
      setMissions(data.missions); setNextCursor(data.next_cursor ?? null); setEvents(detail.events); setRefreshError('');
    } catch (failure) { if (current === generation.current) setRefreshError(failure.message); }
  }
  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 2000);
    return () => { generation.current++; clearInterval(timer); };
  }, []);
  function select(id) { selectedRef.current = id; setSelected(id); setEvents([]); refresh(); }
  function page(index, cursor) { cursorRef.current = cursor; setPageNumber(index); selectedRef.current = null; setSelected(null); setEvents([]); refresh(); }
  function nextPage() { if (nextCursor) { setCursors([...cursors.slice(0, pageNumber + 1), nextCursor]); page(pageNumber + 1, nextCursor); } }
  async function create() {
    setBusy(true); setError('');
    try {
      if (!requestIds.current[mode]) requestIds.current[mode] = crypto.randomUUID();
      const data = await call('/api/missions', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({request_id: requestIds.current[mode], ...kinds[mode], parameters: {}})});
      requestIds.current[mode] = null; cursorRef.current = null; setCursors([null]); setPageNumber(0); select(data.id);
    } catch (failure) { setError(failure.message); }
    finally { setBusy(false); }
  }
  async function command(action) {
    if (!selected) return;
    setBusy(true); setError('');
    try { await call(`/api/missions/${selected}/${action}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); await refresh(); }
    catch (failure) { setError(failure.message); }
    finally { setBusy(false); }
  }
  const mission = missions?.find(item => item.id === selected);
  const inspectionColors = mission?.kind === 'inspect_stack_light' && mission.state === 'succeeded' ? mission.result?.colors : null;
  return <div className="content"><header className="page-header"><div><p className="eyebrow"><span/> MISSION CONTROL</p><h1>임무 관리<span className="title-dot">.</span></h1><p className="subtitle">모의 임무와 Gazebo 주행·경광등 점검을 시험합니다.</p></div><div className="header-meta"><div className="badge">시뮬레이션 전용</div><span>실제 로봇은 움직이지 않습니다</span></div></header>
    <div className="overview-notice attention"><span className="notice-icon">!</span><div><b>시뮬레이션 전용</b><p>Gazebo 실행을 누르면 가상 환경을 자동으로 준비하고 완료 후 정리합니다. 실제 로봇은 움직이지 않습니다.</p></div></div>
    {role === 'viewer' && <p className="record-note">조회자 계정은 임무를 조회할 수 있습니다. 임무 생성·실행·취소는 운영자 계정이 필요합니다.</p>}
    {mode === 'gazebo_inspection' && <p className="record-note">Gazebo와 가상 경광등 시험판을 자동으로 준비합니다. 준비에 시간이 걸릴 수 있습니다.</p>}
    {refreshError && <p className="warning" role="status">임무 목록을 갱신하지 못했습니다. {refreshError}</p>}
    {error && <p className="warning" role="alert">{error} <button type="button" className="dismiss-error" onClick={() => setError('')}>닫기</button></p>}
    <div className="mission-layout"><section className="panel"><div className="panel-head"><div><h3>시뮬레이션 임무 목록</h3><p>종류 선택 → 임무 생성 → 상세에서 실행 · 페이지당 50건</p></div><div className="mission-create"><label htmlFor="mission-mode">임무 종류</label><select id="mission-mode" value={mode} disabled={busy} onChange={event => setMode(event.target.value)}><option value="simulation">모의 점검</option><option value="gazebo">Gazebo 주행</option><option value="gazebo_inspection">Gazebo 경광등 점검</option></select><button className="db-button" type="button" disabled={busy || role !== 'operator'} onClick={create}>+ 임무 생성</button></div></div>
      {missions === null ? <p className="empty-state">임무를 불러오는 중입니다.</p> : missions.length === 0 ? <p className="empty-state">생성된 시뮬레이션 임무가 없습니다.</p> : <div className="mission-list">{missions.map(item => <button type="button" key={item.id} className={item.id === selected ? 'mission-item active' : 'mission-item'} onClick={() => select(item.id)}><span><b>{missionName(item)}</b><small>{item.id.slice(0, 8)} · {new Date(item.created_at).toLocaleString('ko-KR')}</small></span><span className="pill neutral">{missionLabel(item.state, item.mode) || '상태 미확인'}</span></button>)}</div>}<div className="mission-actions"><button className="db-button" type="button" disabled={pageNumber === 0} onClick={() => page(pageNumber - 1, cursors[pageNumber - 1])}>이전</button><button className="db-button" type="button" disabled={nextCursor === null} onClick={nextPage}>다음</button></div></section>
      <section className="panel"><div className="panel-head"><div><h3>임무 상세</h3><p>상태와 단계별 기록</p></div>{mission && <span className="pill neutral">{mission.mode === 'gazebo' ? 'GAZEBO' : 'SIMULATION'}</span>}</div>{!mission ? <p className="empty-state">목록에서 임무를 선택하거나 새 임무를 생성하세요.</p> : <><div className="mission-details"><div><span>상태</span><b>{missionLabel(mission.state, mission.mode) || '미확인'}</b></div><div><span>현재 단계</span><b>{stageLabel(mission.stage)}</b></div><div><span>임무 ID</span><b className="mission-id">{mission.id}</b></div><div><span>결과 / 사유</span><b>{(mission.reason ? (reasons[mission.reason] || mission.reason) : null) || (mission.state === 'succeeded' ? (mission.mode === 'gazebo' ? 'Gazebo 주행 완료' : '모의 완료') : '—')}</b></div></div>{['interrupted', 'failed', 'canceled'].includes(mission.state) && <p className="record-note">다시 실행하려면 임무 종류를 선택하고 새 임무를 생성해 주세요.</p>}{mission.kind === 'inspect_stack_light' && <div className="inspection-results"><h4>가상 경광등 관측 결과</h4>{inspectionColors ? <div className="inspection-colors">{Object.entries(colorNames).map(([key, label]) => <div className="inspection-color" key={key}><span className={`inspection-lamp ${key} ${inspectionColors[key]?.state || 'unknown'}`} aria-hidden="true"/><span>{label}</span><b>{colorStates[inspectionColors[key]?.state] || '미확인'}</b></div>)}</div> : <p className="record-note">{mission.state === 'succeeded' ? '점검 결과를 확인할 수 없습니다.' : '확인된 점검 결과가 없습니다.'}</p>}</div>}<div className="mission-actions"><button className="db-button" type="button" disabled={busy || role !== 'operator' || mission.state !== 'created'} onClick={() => command('start')}>{mission.mode === 'gazebo' ? 'Gazebo 실행' : '모의 실행'}</button><button className="db-button" type="button" disabled={busy || role !== 'operator' || !['created', 'queued', 'running'].includes(mission.state)} onClick={() => command('cancel')}>{mission.mode === 'gazebo' ? 'Gazebo 취소' : '모의 취소'}</button></div><h4 className="mission-history-title">상태 이력</h4>{events.length ? <div className="mission-history">{events.map(event => <div key={event.version}><span className="event-dot"/><b>{missionLabel(event.state, mission.mode) || event.state}{event.stage ? ` · ${stageLabel(event.stage)}` : ''}</b><time>{new Date(event.recorded_at).toLocaleString('ko-KR')}</time></div>)}</div> : <p className="record-note">이력을 불러오는 중입니다.</p>}</>}</section></div></div>;
}
