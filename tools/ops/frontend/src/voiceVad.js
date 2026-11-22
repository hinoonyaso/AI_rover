// Segment bounded 16 kHz mono speech using RMS and trailing silence.
// 한글: RMS와 뒤따르는 무음으로 16kHz 모노 발화를 제한된 길이로 나눈다.
export class VoiceVad {
  constructor({threshold = 0.015, startFrames = 3, endFrames = 40, maxFrames = 450} = {}) {
    this.threshold = threshold; this.startFrames = startFrames; this.endFrames = endFrames; this.maxFrames = maxFrames; this.reset();
  }
  reset() { this.active = false; this.loud = 0; this.silent = 0; this.frames = []; this.lead = []; }
  push(frame) {
    const copy = Float32Array.from(frame);
    const rms = Math.sqrt(copy.reduce((sum, value) => sum + value * value, 0) / copy.length);
    if (!this.active) {
      this.lead.push(copy); if (this.lead.length > 12) this.lead.shift();
      this.loud = rms >= this.threshold ? this.loud + 1 : 0;
      if (this.loud < this.startFrames) return null;
      this.active = true; this.frames = this.lead; this.lead = []; this.silent = 0;
    } else { this.frames.push(copy); this.silent = rms < this.threshold ? this.silent + 1 : 0; }
    if (this.silent < this.endFrames && this.frames.length < this.maxFrames) return null;
    const frames = this.frames; const total = frames.reduce((n, item) => n + item.length, 0);
    const output = new Float32Array(total); let at = 0;
    for (const item of frames) { output.set(item, at); at += item.length; }
    this.reset(); return output.length >= 4800 ? output : null;
  }
}

// Windowed-sinc low-pass taps below the 8 kHz output Nyquist limit.
// 한글: 16kHz 출력의 나이퀴스트(8kHz) 아래로 자르는 윈도 sinc 저역 통과 계수.
export function lowPassTaps(rate, cutoff = 7200, count = 63) {
  const taps = new Float32Array(count), middle = (count - 1) / 2, fc = cutoff / rate;
  let sum = 0;
  for (let i = 0; i < count; i++) {
    const x = i - middle, sinc = x === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * x) / (Math.PI * x);
    taps[i] = sinc * (0.54 - 0.46 * Math.cos(2 * Math.PI * i / (count - 1))); sum += taps[i];
  }
  for (let i = 0; i < count; i++) taps[i] /= sum;
  return taps;
}

// Preserve filter history and resampling phase across callbacks; no recording is saved locally.
// Decimating without a low-pass folds 8-24 kHz content into speech (aliasing).
// 한글: 콜백 사이 필터 이력과 리샘플 위상을 보존하며 녹음은 로컬에 저장하지 않는다.
// 한글: 저역 통과 없이 솎아내면 8~24kHz 성분이 음성 대역으로 접혀 들어온다(앨리어싱).
export class MonoResampler {
  constructor(rate) {
    this.rate = rate; this.phase = 0; this.pending = [];
    this.taps = rate > 16000 ? lowPassTaps(rate) : null;
    this.history = this.taps ? new Float32Array(this.taps.length) : null; this.at = 0;
  }
  reset() { this.phase = 0; this.pending = []; if (this.history) { this.history.fill(0); this.at = 0; } }
  filter(value) {
    if (!this.taps) return value;
    const n = this.taps.length; this.history[this.at] = value;
    let out = 0;
    for (let i = 0; i < n; i++) out += this.taps[i] * this.history[(this.at - i + n) % n];
    this.at = (this.at + 1) % n;
    return out;
  }
  push(input) {
    const frames = [];
    for (const raw of input) {
      // Filter every input sample so the history stays continuous.
      // 한글: 이력이 끊기지 않도록 모든 입력 표본을 거른다.
      const value = this.filter(raw);
      this.phase += 16000;
      if (this.phase >= this.rate) { this.phase -= this.rate; this.pending.push(value); }
      if (this.pending.length === 320) { frames.push(Float32Array.from(this.pending)); this.pending = []; }
    }
    return frames;
  }
}

export function pcmWav(samples) {
  const buffer = new ArrayBuffer(44 + samples.length * 2), view = new DataView(buffer);
  const write = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  write(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); write(8, 'WAVE');
  write(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  write(36, 'data'); view.setUint32(40, samples.length * 2, true);
  samples.forEach((s, i) => view.setInt16(44 + i * 2, Math.round(Math.max(-1, Math.min(1, s)) * (s < 0 ? 32768 : 32767)), true));
  return buffer;
}
