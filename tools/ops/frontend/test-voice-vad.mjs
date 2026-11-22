import assert from 'node:assert/strict';
import {VoiceVad, MonoResampler, pcmWav} from './src/voiceVad.js';
const vad = new VoiceVad();
const silence = new Float32Array(320), speech = new Float32Array(320).fill(0.1);
for (let i = 0; i < 60; i++) assert.equal(vad.push(silence), null);
for (let i = 0; i < 30; i++) assert.equal(vad.push(speech), null);
let segment = null; for (let i = 0; i < 40; i++) segment = vad.push(silence) || segment;
assert.ok(segment && segment.length >= 4800 && segment.length <= 160000);
const wav = new DataView(pcmWav(segment)); assert.equal(wav.getUint32(24, true), 16000); assert.equal(wav.getUint16(22, true), 1);
const resampler = new MonoResampler(48000); let count = 0;
for (let i = 0; i < 12; i++) count += resampler.push(new Float32Array(4000)).reduce((n, f) => n + f.length, 0);
assert.equal(count, 16000);
// A 12 kHz tone would alias to 4 kHz without the low-pass; 1 kHz speech-band tone must pass.
// 한글: 12kHz 톤은 저역 통과가 없으면 4kHz로 접힌다. 1kHz 음성 대역 톤은 유지돼야 한다.
function toneRms(freq) {
  const r = new MonoResampler(48000), input = Float32Array.from({length: 48000}, (_, i) => Math.sin(2 * Math.PI * freq * i / 48000));
  const out = r.push(input).flatMap(f => Array.from(f)).slice(400);
  return Math.sqrt(out.reduce((n, v) => n + v * v, 0) / out.length);
}
assert.ok(toneRms(12000) < 0.02, 'alias tone suppressed'); assert.ok(toneRms(1000) > 0.65, 'speech band kept');
const bounded = new VoiceVad({maxFrames: 50}); let cut = null;
for (let i = 0; i < 60; i++) cut = bounded.push(speech) || cut;
assert.ok(cut && cut.length <= 50 * 320);
console.log('voice VAD: silence, endpoint, anti-alias resampling, WAV and length passed');
