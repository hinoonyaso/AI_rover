import React, {useEffect, useRef, useState} from 'react';
import {VoiceVad, MonoResampler, pcmWav} from './voiceVad';

const jsonHeaders = {'Content-Type': 'application/json'};
async function call(path, options = {}) {
  const response = await fetch(path, {...options, cache: 'no-store'});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.error === 'string' ? data.error : data.error?.message || '요청을 처리하지 못했습니다.');
  return data;
}

export default function Voice({role}) {
  const [listening, setListening] = useState(false), [stage, setStage] = useState('꺼짐');
  const [transcript, setTranscript] = useState(''), [reply, setReply] = useState(''), [error, setError] = useState('');
  const [pending, setPending] = useState(null), [text, setText] = useState(''), [speakEnabled, setSpeakEnabled] = useState(false);
  const audio = useRef(null), epoch = useRef(0), busy = useRef(false), pendingRef = useRef(null), dispatch = useRef(null), speaking = useRef(false), abort = useRef(null), speakRef = useRef(false), actionInFlight = useRef(false);
  pendingRef.current = pending; speakRef.current = speakEnabled;
  function closeMicrophone() {
    epoch.current += 1; abort.current?.abort(); abort.current = null;
    if (audio.current) {
      const {stream, processor, source, context} = audio.current; audio.current = null;
      stream.getTracks().forEach(track => { track.onended = null; track.stop(); });
      processor.disconnect(); source.disconnect(); context.close().catch(() => {});
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    speaking.current = false; if (!actionInFlight.current) busy.current = false; setListening(false); setStage('꺼짐');
  }
  useEffect(() => () => closeMicrophone(), []);
  function speak(message) {
    setReply(message);
    if (!speakRef.current || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel(); speaking.current = true;
    const utterance = new SpeechSynthesisUtterance(message.slice(0, 300)); utterance.lang = 'ko-KR';
    utterance.onend = utterance.onerror = () => { speaking.current = false; };
    window.speechSynthesis.speak(utterance);
  }
  async function confirmAction() {
    const action = pendingRef.current; if (!action || busy.current || actionInFlight.current) return;
    actionInFlight.current = true; busy.current = true; setStage('임무 처리 중'); setError('');
    try {
      if (action.kind === 'start') {
        const created = await call('/api/missions', {method:'POST', headers:jsonHeaders, body:JSON.stringify({request_id:action.requestId, mode:'simulation', kind:'inspection_demo', parameters:{}})});
        await call(`/api/missions/${created.id}/start`, {method:'POST', headers:jsonHeaders, body:'{}'});
        speak(`모의 점검을 시작했습니다. 임무 번호 ${created.id.slice(0, 8)}. 실제 로봇은 움직이지 않습니다.`);
      } else {
        const current = await call(`/api/missions/${action.id}`);
        if (current.mode !== 'simulation' || !['created','queued','running'].includes(current.state)) throw new Error('모의 임무 상태가 바뀌어 취소하지 않았습니다.');
        const result = await call(`/api/missions/${action.id}/cancel`, {method:'POST', headers:jsonHeaders, body:'{}'});
        speak(result.state === 'canceled' ? '모의 임무 취소가 확인되었습니다.' : '모의 임무 취소를 요청했습니다. 상태를 확인하세요.');
      }
      pendingRef.current = null; setPending(null);
    } catch (e) { setError(e.message); }
    finally { actionInFlight.current = false; busy.current = false; setStage(audio.current ? '듣는 중' : '꺼짐'); }
  }
  async function handle(data) {
    setTranscript(data.transcript || ''); setError('');
    if (data.intent === 'sleep') return;
    if (data.intent === 'confirm') { if (pendingRef.current) { busy.current = false; await confirmAction(); } else speak('확인할 모의 임무 요청이 없습니다.'); return; }
    if (data.intent === 'dismiss') { pendingRef.current = null; setPending(null); speak('대기 중인 요청을 취소했습니다.'); return; }
    if (pendingRef.current) { speak('먼저 대기 중인 요청을 확인하거나 취소해 주세요.'); return; }
    if (data.intent === 'wake') { speak('듣고 있습니다. 호출어와 함께 요청해 주세요.'); return; }
    if (data.intent === 'status') {
      const result = await call('/api/status'); const robot = result.robot;
      const battery = robot?.battery_voltage == null ? '배터리 전압은 미확인' : `배터리 전압은 ${robot.battery_voltage.toFixed(2)} 볼트`;
      const streams = ['imu','scan','camera'].map((key, i) => `${['IMU','라이다','카메라'][i]} ${robot?.streams?.[key]?.age_seconds == null ? '수신 미확인' : '수신 중'}`).join(', ');
      speak(`${battery}입니다. ${streams}입니다.`); return;
    }
    if (data.intent === 'knowledge') {
      const result = await call('/api/knowledge/answer?q=' + encodeURIComponent(data.command));
      const first = result.results?.[0]; speak(first ? `문서 근거를 찾았습니다. ${first.source}. 화면에서 원문을 확인하세요.` : result.answer);
      if (first) setReply(result.answer); return;
    }
    if (data.intent === 'mission_status' || data.intent === 'simulation_cancel') {
      const dataList = await call('/api/missions?limit=100');
      if (dataList.next_cursor) { speak('임무 목록이 여러 페이지입니다. 임무 화면에서 직접 선택해 주세요.'); return; }
      const active = dataList.missions.filter(m => m.mode === 'simulation' && ['created','queued','running'].includes(m.state));
      if (data.intent === 'mission_status') { speak(active.length ? `진행 가능한 모의 임무가 ${active.length}개 있습니다.` : '진행 중인 모의 임무가 없습니다.'); return; }
      if (active.length !== 1) { speak('취소할 모의 임무가 한 개로 확인되지 않습니다. 임무 화면에서 직접 선택해 주세요.'); return; }
      const next = {kind:'cancel', id:active[0].id, label:`모의 임무 ${active[0].id.slice(0,8)} 취소`}; pendingRef.current = next; setPending(next); speak(`${next.label} 요청입니다. 확인 또는 취소해 주세요.`); return;
    }
    if (data.intent === 'simulation_start') {
      const next = {kind:'start', requestId:crypto.randomUUID(), label:'모의 점검 임무 생성 및 실행'}; pendingRef.current = next; setPending(next); speak(`${next.label} 요청입니다. 확인 또는 취소해 주세요.`); return;
    }
    speak('지원하지 않는 요청입니다. 상태 조회, 문서 질문, 모의 점검만 사용할 수 있습니다.');
  }
  dispatch.current = async (samples, myEpoch) => {
    if (busy.current || speaking.current || myEpoch !== epoch.current) return;
    busy.current = true; setStage('음성 인식 중'); setError('');
    const controller = new AbortController(); abort.current = controller;
    try {
      const data = await call('/api/voice/transcribe', {method:'POST', headers:{'Content-Type':'audio/wav'}, body:pcmWav(samples), signal:controller.signal});
      if (myEpoch === epoch.current) { setStage('요청 처리 중'); await handle(data); }
    } catch (e) { if (e.name !== 'AbortError' && myEpoch === epoch.current) setError(e.message); }
    finally { if (myEpoch === epoch.current) { abort.current = null; busy.current = false; setStage(audio.current ? '듣는 중' : '꺼짐'); } }
  };
  async function startMicrophone() {
    if (audio.current || busy.current) return;
    const myEpoch = ++epoch.current; setError(''); setStage('마이크 연결 중');
    let stream = null, context = null;
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('이 브라우저에서 HTTPS 마이크 사용을 지원하지 않습니다.');
      stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true}, video:false});
      if (myEpoch !== epoch.current) { stream.getTracks().forEach(track => track.stop()); return; }
      const Audio = window.AudioContext || window.webkitAudioContext; context = new Audio();
      if (context.sampleRate < 16000) { stream.getTracks().forEach(track => track.stop()); await context.close(); throw new Error('마이크 샘플레이트가 16kHz보다 낮습니다.'); }
      const source = context.createMediaStreamSource(stream), processor = context.createScriptProcessor(4096, 1, 1);
      const mute = context.createGain(); mute.gain.value = 0; source.connect(processor); processor.connect(mute); mute.connect(context.destination);
      const vad = new VoiceVad(), resample = new MonoResampler(context.sampleRate);
      processor.onaudioprocess = event => {
        if (busy.current || speaking.current || myEpoch !== epoch.current) { vad.reset(); resample.reset(); return; }
        for (const frame of resample.push(event.inputBuffer.getChannelData(0))) { const segment = vad.push(frame); if (segment) { dispatch.current(segment, myEpoch); break; } }
      };
      audio.current = {stream, source, processor, context};
      stream.getTracks().forEach(track => { track.onended = () => { closeMicrophone(); setError('마이크 연결이 끊겼습니다. 다시 켜 주세요.'); }; });
      await context.resume(); setListening(true); setStage('듣는 중');
    } catch (e) { if (!audio.current) { stream?.getTracks().forEach(track => track.stop()); context?.close().catch(() => {}); } if (myEpoch === epoch.current) { closeMicrophone(); setError(e.message || '마이크를 열지 못했습니다.'); } }
  }
  async function submitText(event) {
    event.preventDefault(); if (busy.current || text.trim().length < 1) return;
    busy.current = true; setStage('요청 처리 중');
    try { const result = await call('/api/voice/interpret', {method:'POST',headers:jsonHeaders,body:JSON.stringify({text})}); await handle(result); }
    catch (e) { setError(e.message); } finally { busy.current = false; setStage(audio.current ? '듣는 중' : '꺼짐'); }
  }
  return <div className="content"><header className="page-header"><div><p className="eyebrow">VOICE ASSISTANT</p><h1>음성 관제<span className="title-dot">.</span></h1><p className="subtitle">호출어를 포함해 상태·문서·모의 점검을 요청합니다.</p></div></header>
    <section className="panel"><div className="panel-head"><div><h3>마이크</h3><p>현재 사용 중인 PC의 마이크 · 음성은 이 서버에서 로컬 인식</p></div><span className="pill neutral" role="status">{stage}</span></div>
    {role !== 'operator' ? <p>음성 인식과 모의 명령은 운영자만 사용할 수 있습니다.</p> : <><button type="button" onClick={listening ? closeMicrophone : startMicrophone}>{listening ? '마이크 끄기' : '마이크 켜기'}</button> <label><input type="checkbox" checked={speakEnabled} onChange={e => setSpeakEnabled(e.target.checked)}/> 이 PC에서 음성 응답</label><p className="record-note">예: “로버 배터리 상태 알려줘”, “로버 모의 점검 시작해”. 호출어만 말한 뒤에는 요청할 때 호출어를 다시 말해 주세요.</p><p className="record-note">발화 구간은 인식을 위해 이 서버로 전송됩니다. 음성 응답 중에는 입력을 무시하지만 완전한 에코 제거는 아닙니다.</p>
    <form onSubmit={submitText}><label htmlFor="voice-text">인식 문장 직접 시험</label><div><input id="voice-text" value={text} maxLength={300} onChange={e => setText(e.target.value)} placeholder="로버 모의 점검 시작해"/></div><button type="submit" disabled={!text.trim()}>문장 해석</button></form></>}
    {error && <p className="warning" role="alert">{error}</p>}{transcript && <p><b>인식:</b> {transcript}</p>}{reply && <p style={{whiteSpace:'pre-wrap'}}><b>응답:</b> {reply}</p>}
    {pending && <div className="warning" role="status"><b>확인 필요: {pending.label}</b><p>실제 로봇은 움직이지 않습니다. “로버 확인” 또는 버튼으로 확인하세요.</p><button type="button" onClick={confirmAction}>확인</button> <button type="button" onClick={() => {pendingRef.current = null; setPending(null); speak('요청을 취소했습니다.');}}>취소</button></div>}</section></div>;
}
