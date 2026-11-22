import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createServer} from 'vite';

const vite = await createServer({server: {middlewareMode: true}, appType: 'custom', logLevel: 'silent'});
try {
  const {Dashboard} = await vite.ssrLoadModule('/src/App.jsx');
  const robot = {status: 'monitoring', snapshot_age_seconds: 1, battery_voltage: 12.3, battery_age_seconds: 2,
    streams: {imu: {hz: 10, age_seconds: 1}, scan: {hz: null, age_seconds: 2}, camera: {hz: null, age_seconds: null}}};
  const data = {robot, database: 'connected', host: {timestamp: '2026-11-15T00:00:00Z', cpu_percent: 10, memory_percent: 20, memory_used_gb: 1, memory_total_gb: 8, disk_percent: 30, disk_free_gb: 5, temperature_c: 40}};
  const ok = {data: {database: 'connected', events: [], samples: []}, error: false};
  const render = overrides => renderToStaticMarkup(React.createElement(Dashboard, {data, statusError: false, events: ok, history: ok, now: 100000, receivedAt: 100000, ...overrides}));
  const {default: Knowledge} = await vite.ssrLoadModule('/src/Knowledge.jsx');
  const operatorKnowledge = renderToStaticMarkup(React.createElement(Knowledge, {role: 'operator'}));
  const viewerKnowledge = renderToStaticMarkup(React.createElement(Knowledge, {role: 'viewer'}));
  assert.ok(operatorKnowledge.includes('EXAONE 외부 답변'));
  assert.ok(operatorKnowledge.includes('색인 백업'));
  assert.ok(!viewerKnowledge.includes('EXAONE 외부 답변'));
  assert.ok(!viewerKnowledge.includes('색인 백업'));
  const {InspectionDiagnostics} = await vite.ssrLoadModule('/src/Missions.jsx');
  const diagnosticHtml = renderToStaticMarkup(React.createElement(InspectionDiagnostics, {diagnostics: {
    received: 12, window_frames: 3, invalid_time: 2, gap_resets: 1, invalid_format: 0,
    color_reasons: {red: 'fixture_not_found'},
  }}));
  for (const value of ['수신 영상 12개', '시각 오류 2개', '시험판의 위치']) assert.ok(diagnosticHtml.includes(value), value);
  const {RobotMicrophone} = await vite.ssrLoadModule('/src/Voice.jsx');
  const robotOperator = renderToStaticMarkup(React.createElement(RobotMicrophone, {role: 'operator'}));
  const robotViewer = renderToStaticMarkup(React.createElement(RobotMicrophone, {role: 'viewer'}));
  assert.ok(robotOperator.includes('Hello Hiwonder') && robotOperator.includes('>듣기 시작</button>'));
  assert.ok(!robotViewer.includes('>듣기 시작</button>') && robotViewer.includes('운영자만'));
  const missionPage = render({page: 'missions'});
  for (const label of ['임무 관리', '시뮬레이션 전용', '임무 생성']) assert.ok(missionPage.includes(label), label);
  const robotPage = render({page: 'robot'});
  for (const label of ['카메라 미리보기', '저장된 지도', '실제 로봇 임무 관리자는 연결되지 않았습니다']) assert.ok(robotPage.includes(label), label);
  const normal = render({});
  for (const value of ['12.30 V', '10 Hz', '주기 계산 중', '수신 미확인', '표시할 지표 기록이 없습니다', '표시할 운영 기록이 없습니다']) assert.ok(normal.includes(value), value);
  const stale = render({now: 110000, statusError: true});
  assert.ok(stale.includes('서버 연결 끊김'));
  assert.ok(stale.includes('이전 값'));
  assert.ok(!stale.includes('12.30 V'));
  assert.ok(!stale.includes('10 Hz'));
  const failed = render({events: {data: {database: 'unavailable', events: []}, error: false}, history: {data: null, error: true}});
  assert.ok(failed.includes('데이터베이스를 사용할 수 없습니다'));
  assert.ok(failed.includes('데이터를 가져오지 못했습니다'));
  const restored = render({history: {data: {database: 'connected', samples: [{recorded_at: '2026-11-15T01:00:00', cpu_percent: 15, memory_percent: 20, disk_percent: 30, temperature_c: null}]}, error: false}});
  assert.ok(restored.includes('15%'));
  assert.ok(restored.includes('DB 기록 시각의 시간대는 미확인'));
  console.log('Dashboard rendering: normal, stale, failure, and recovery cases passed');
} finally {
  await vite.close();
}
