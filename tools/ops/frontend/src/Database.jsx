import React, {useEffect, useState} from 'react';

export default function Database() {
  const [tables, setTables] = useState(null);
  const [table, setTable] = useState('system_metrics');
  const [cursors, setCursors] = useState([null]);
  const [page, setPage] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [selectedRow, setSelectedRow] = useState(null);
  const [copyStatus, setCopyStatus] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/database/tables', {signal: controller.signal, cache: 'no-store'}).then(response => {
      if (!response.ok) throw new Error();
      return response.json();
    }).then(data => setTables(data.tables)).catch(err => { if (err.name !== 'AbortError') setTables([]); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(''); setResult(null);
    const params = new URLSearchParams({limit: '50'});
    if (cursors[page] != null) params.set(table === 'missions' || table === 'mission_events' ? 'cursor' : 'before', String(cursors[page]));
    fetch(`/api/database/tables/${encodeURIComponent(table)}/rows?${params}`, {signal: controller.signal, cache: 'no-store'}).then(response => {
      if (!response.ok) throw new Error();
      return response.json();
    }).then(data => { setResult(data); setLoading(false); }).catch(err => {
      if (err.name !== 'AbortError') { setError('데이터를 불러오지 못했습니다. 데이터베이스 연결을 확인해 주세요.'); setLoading(false); }
    });
    return () => controller.abort();
  }, [table, page, revision]);
  const chooseTable = name => { setSelectedRow(null); setTable(name); setCursors([null]); setPage(0); };
  const nextCursor = result?.next_cursor ?? result?.next_before ?? null;
  const next = () => { if (nextCursor != null) { setSelectedRow(null); setCursors(previous => [...previous.slice(0, page + 1), nextCursor]); setPage(page + 1); } };
  return <div className="content"><header className="page-header"><div><p className="eyebrow"><span/> DATA EXPLORER</p><h1>데이터베이스<span className="title-dot">.</span></h1><p className="subtitle">운영 데이터의 테이블과 레코드를 살펴봅니다.</p></div><div className="header-meta"><div className="badge">읽기 전용</div><span>MySQL · jetinspect</span></div></header>
    <div className="db-layout"><aside className="panel db-tables"><div className="section-kicker">DATABASE</div><h3>jetinspect</h3><p>TABLES</p>{tables === null ? <p>테이블 확인 중</p> : tables.length === 0 ? <p>테이블 목록을 불러오지 못했습니다.</p> : tables.map(item => <button type="button" className={item.name === table ? 'db-table active' : 'db-table'} aria-pressed={item.name === table} key={item.name} onClick={() => chooseTable(item.name)}><span aria-hidden="true">▦</span>{item.name}</button>)}</aside>
      <section className="panel db-content"><div className="panel-head"><div><span className="section-kicker">TABLE / DATA</span><h3>{table}</h3><p>{table === 'missions' ? '생성 시각 최신 순' : table === 'mission_events' ? '기록 시각 최신 순' : '최신 ID 순'} · 페이지당 50개</p></div><button className="db-button" type="button" onClick={() => { setSelectedRow(null); setRevision(value => value + 1); }}>새로고침</button></div>
      {loading ? <p className="empty-state" role="status">데이터를 불러오는 중입니다.</p> : error ? <p className="empty-state" role="alert">{error}</p> : result?.rows.length ? <div className="table-wrap db-result"><table><thead><tr>{result.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.map((row, index) => <tr key={row.id ?? `${row.mission_id}-${row.version}-${index}`}>{result.columns.map((column, columnIndex) => <td key={column}>{columnIndex === 0 && <button type="button" className="db-button row-open" onClick={() => { setSelectedRow(row); setCopyStatus(''); }}>상세</button>}{row[column] == null ? <span className="db-null">NULL</span> : column === 'recorded_at' ? String(row[column]).replace('T', ' ') : String(row[column])}</td>)}</tr>)}</tbody></table></div> : <p className="empty-state">이 테이블에 표시할 데이터가 없습니다.</p>}
      {result?.rows.length > 0 && <p className="record-note">행을 선택하면 전체 값을 확인할 수 있습니다.</p>}
      {selectedRow && <section className="row-detail" aria-label="선택한 행 상세"><div className="panel-head"><h3>선택한 행 상세</h3><button className="db-button" type="button" onClick={() => setSelectedRow(null)}>닫기</button></div><pre tabIndex="0">{JSON.stringify(selectedRow, null, 2)}</pre><button className="db-button" type="button" onClick={async () => { try { await navigator.clipboard.writeText(JSON.stringify(selectedRow, null, 2)); setCopyStatus('복사했습니다.'); } catch { setCopyStatus('복사할 수 없습니다. 값을 선택해 직접 복사해 주세요.'); } }}>전체 값 복사</button> <span role="status">{copyStatus}</span></section>}
      <div className="db-pagination"><span>{page + 1} 페이지 · {result?.rows.length ?? 0}개 행</span><div><button className="db-button" type="button" disabled={loading || page === 0} onClick={() => { setSelectedRow(null); setPage(page - 1); }}>이전</button><button className="db-button" type="button" disabled={loading || nextCursor === null} onClick={next}>다음</button></div></div><p className="record-note">DB 기록 시각의 시간대는 미확인 · 데이터를 수정하거나 SQL을 실행할 수 없습니다.</p></section></div></div>;
}
