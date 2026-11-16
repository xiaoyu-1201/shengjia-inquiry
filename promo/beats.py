# 配樂節拍分析：解出單聲道 → 低頻能量的起音曲線 → 在估計 BPM 附近找最準的拍長和相位 → 找最適合當開頭的小節
import subprocess, sys, json, numpy as np
import os
FF = os.environ.get('FFMPEG', 'ffmpeg')
SR = 11025
def load(p):
    raw = subprocess.run([FF, '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
def analyse(p, bpm_guess, need=30.0):
    x = load(p); hop = 110; win = 512                      # 每 10ms 一點
    n = (len(x) - win) // hop
    fr = np.lib.stride_tricks.sliding_window_view(x, win)[::hop][:n] * np.hanning(win)
    mag = np.abs(np.fft.rfft(fr, axis=1))
    low = mag[:, 1:int(150 / (SR / win))].sum(1)             # 150Hz 以下＝大鼓
    onset = np.maximum(0, np.diff(np.log1p(low * 10), prepend=0))
    fps = SR / hop
    best = None
    for bpm in np.arange(bpm_guess - 3, bpm_guess + 3, 0.01):
        per = fps * 60 / bpm
        for ph in np.arange(0, per, 0.5):
            idx = (ph + np.arange(0, (len(onset) - ph) / per) * per).astype(int)
            sc = onset[idx].mean()
            if best is None or sc > best[0]: best = (sc, bpm, ph / fps)
    _, bpm, phase = best
    beat = 60 / bpm
    rms = np.sqrt((x[:len(x) // SR * SR].reshape(-1, SR) ** 2).mean(1))   # 每秒音量
    # 找開頭：小節線（每 4 拍）上，往後 need 秒平均音量最大、而且一開頭就有力
    cands = []
    t = phase
    while t + need < len(x) / SR:
        s = int(t); e = int(t + need)
        cands.append((rms[s:e].mean() * 0.7 + rms[s:s + 3].mean() * 0.3, t)); t += beat * 4
    start = max(cands)[1]
    return dict(file=p, bpm=round(bpm, 3), beat=beat, phase=round(phase, 3), start=round(start, 3), dur=len(x) / SR,
                loud=[round(float(v), 3) for v in rms])
out = {}
B = os.environ.get('BGM_DIR', 'bgm')
for name, g in (('house-vibez', 123), ('cat-walk', 129)):
    r = analyse(rf'{B}\{name}.mp3', g); out[name] = r
    print(name, 'bpm', r['bpm'], 'phase', r['phase'], 'start', r['start'], 'loud/s', r['loud'][:40])
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'beats.json'), 'w'), indent=1)
