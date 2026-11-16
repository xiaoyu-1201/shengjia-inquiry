# 合成宣傳片：畫面（30fps jpg）＋配樂（從 start 秒開始截）＋音效（照拍點放）→ MP4
# 用法：python mix.py <beat秒> <畫面資料夾> <輸出.mp4> [配樂mp3 起點秒]（沒給配樂＝只有音效版）
import subprocess, sys, os
FF = os.environ.get('FFMPEG', 'ffmpeg')   # 設環境變數 FFMPEG 指到 ffmpeg.exe，或把 ffmpeg 加進 PATH
SFX = os.environ.get('SFX_DIR', 'sfx')     # Mixkit 音效資料夾（video-shotcraft skill 的 assets/audio/sfx）
beat, frames, out = float(sys.argv[1]), sys.argv[2], sys.argv[3]
music = sys.argv[4] if len(sys.argv) > 4 else None
mstart = float(sys.argv[5]) if len(sys.argv) > 5 else 0
b = lambda n: n * beat
dur = len([f for f in os.listdir(frames) if f.endswith('.jpg')]) / 30
SC = [b(n) for n in (0, 8, 16, 24, 32, 40, 50, 60)]
# (秒, 檔案, 音量)：跟 promo.html 的動作時間對齊（Mixkit 免費授權，見 ATTRIBUTION.md）
cues = [
 (0.05, r'transition\air-zoom-vacuum.mp3', .35),
 (1.25, r'text\marker-pen-line.mp3', .55),          # 螢光筆畫「要問價？」
 (b(5), r'transition\sweep-fast-small.mp3', .5),     # 劃掉「一間一間打電話」
 (SC[1] - .45, r'transition\whoosh-fast.mp3', .45),   # 前景鋼瓶掠過
 (SC[1], r'impact\impact-zoom-quick.mp3', .8),       # 重拍 1：Logo 落定
 (SC[1] + .35, r'light\sparkle-touch.mp3', .35),
 (SC[1] + b(2), r'ui\ui-popup-dry.mp3', .45),        # 「線上詢價 上線了」
 (SC[2] - .45, r'transition\whoosh-fast.mp3', .4),
 (SC[2], r'transition\air-zoom-vacuum.mp3', .45),    # 手機升起
 (SC[2] + 1.1, r'counter\clock-knob-spin.mp3', .35), # 數字滾到 4,000
 (SC[3], r'transition\transition-soft.mp3', .4) if os.path.exists(SFX + r'\transition\transition-soft.mp3') else (SC[3], r'transition\air-zoom-vacuum.mp3', .35),
 (SC[3] + b(2), r'ui\pop-electric.mp3', .6),        # 規格標籤三聲，一聲比一聲小
 (SC[3] + b(3), r'ui\pop-electric.mp3', .48),
 (SC[3] + b(4), r'ui\pop-electric.mp3', .38),
 (SC[4], r'transition\sweep-metal-quick.mp3', .4),
 *[(SC[4] + b(2 + i * .5), r'ui\ui-select-click.mp3', .5 - i * .05) for i in range(4)],   # 打 Z B 2 6
 (SC[4] + b(4), r'impact\bass-hit-short.mp3', .7),   # 重拍 2：結果出來
 (SC[4] + b(4) + .05, r'ui\ui-confirm-tone.mp3', .35),
 (SC[5] - .45, r'transition\whoosh-fast.mp3', .4),
 (SC[5], r'transition\air-zoom-vacuum.mp3', .3),
 (SC[5] + b(3.5), r'transition\sweep-fast-small.mp3', .45),   # 品項飛進泡泡
 (SC[5] + b(3.5) + .4, r'ui\ui-message-pop.mp3', .55),        # 訊息送出
 (SC[5] + b(7.2), r'ui\ui-popup-dry.mp3', .5),                # 店家回覆
 (SC[6] - .3, r'light\light-transition-magic.mp3', .3),
 (SC[6], r'impact\impact-cine-big.mp3', .75),        # 重拍 3：結尾大合照
 (SC[6] + .25, r'light\shimmer-sparkle-sweep.mp3', .3),
 (SC[6] + .6, r'ui\ui-popup-dry.mp3', .5),          # 「掃描或點主頁連結」
]
cues = [c for c in cues if c[0] < dur - .3]
import numpy as np
_info = {}
def info(f):  # (起音秒, 峰值振幅)：起音＝第一次超過峰值 30% 的位置
    if f not in _info:
        x = np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', os.path.join(SFX, f), '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
        a = np.abs(x)
        on = float(np.argmax(a > a.max() * .3)) / 16000
        if f.startswith('impact'): on = float(a.argmax()) / 16000   # 重擊類：最響那一下對準拍點（前面的漸強當鋪陳）
        _info[f] = (on, float(a.max()))
    return _info[f]
for _, f, _ in cues:
    assert os.path.exists(os.path.join(SFX, f)), f
cmd = [FF, '-y', '-v', 'error', '-framerate', '30', '-i', os.path.join(frames, '%05d.jpg')]
filt, labels = [], []
n = 1
if music:
    cmd += ['-ss', str(mstart), '-t', str(dur), '-i', music]
    filt.append(f'[{n}:a]volume=0.5,afade=t=in:d=0.3,afade=t=out:st={dur-2.2:.2f}:d=2.2[m]'); labels.append('[m]'); n += 1
for t, f, v in cues:
    on, pk = info(f)
    cmd += ['-i', os.path.join(SFX, f)]
    ms = int(max(0, t - on) * 1000)                 # 讓音效「開始響的那一下」落在 t，不是檔案開頭
    g = 10 ** (-6 / 20) / pk * v                     # 每個音效先統一到 -6 dB 峰值，再乘重要程度
    filt.append(f'[{n}:a]volume={g:.3f},adelay={ms}|{ms}[s{n}]'); labels.append(f'[s{n}]'); n += 1
filt.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f},alimiter=limit=0.7:level=false[a]')
cmd += ['-filter_complex', ';'.join(filt), '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{dur:.3f}', out]
r = subprocess.run(cmd, capture_output=True, text=True)
print('ok' if r.returncode == 0 else r.stderr[-1500:], out, round(os.path.getsize(out) / 1e6, 1) if os.path.exists(out) else '', 'MB', len(cues), 'sfx')
