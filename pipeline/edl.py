"""Edit decision list for the MUROH DOOH hammer-drill affiliate video.

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, label).
- Cuts are snapped to the quietest 10 ms frame within +-SNAP s, so no word is clipped.
- Pauses longer than MAX_GAP inside speech keeps are shrunk to KEEP_GAP (dead air removal).
- The hook plays brick-breaking footage with the speaker's own line laid over it (J-cut);
  that line is NOT repeated later.
Outputs build/edl.json (segments + time map) used by build_spine.sh and captions.py.
"""
import json, sys, wave, numpy as np

AUDIO = sys.argv[1]          # 16 kHz mono wav of the original
OUT = sys.argv[2]
SNAP, MAX_GAP, KEEP_GAP, THR_DB = 0.12, 0.30, 0.14, -38.0

w = wave.open(AUDIO); sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop = int(sr * 0.01)
rms = np.array([np.sqrt(np.mean(a[i:i+hop]**2) + 1e-12) for i in range(0, len(a) - hop, hop)])
db = 20 * np.log10(rms)

def snap(t):
    i0, i1 = int((t - SNAP) * 100), int((t + SNAP) * 100)
    i = i0 + int(np.argmin(db[i0:i1]))
    return round(i / 100, 2)

# (src_in, src_out, kind, note)  kind: demo = keep as-is, speech = trim inner pauses
KEEPS = [
    (20.00, 23.00, "demo",   "drill bites into brick"),
    (30.00, 34.40, "demo",   "drill finishes, lifts off"),
    (35.10, 37.95, "speech", "So yang ni kan, rotary hammer drill"),
    (42.30, 43.55, "speech", "Harga bajet"),
    (47.85, 52.45, "speech", "Yang ni 2200 watt. Dia ada 2 mode korang boleh adjust"),
    (53.25, 59.55, "speech", "So nak adjust mode dia dekat sini kan. Untuk yang ni mode hacking. Satu lagi mode ni untuk tebuk dinding"),
    (64.25, 67.30, "speech", "So yang ni dia pakai plug 3 pin"),
    (71.45, 79.45, "speech", "So kalau korang beli dia datang macam ni dengan casing. Korang juga akan dapat mata dia 6 batang"),
    (80.30, 83.10, "speech", "Mata hacking, mata tebuk dinding ada sekali"),
    (83.70, 85.80, "speech", "Lepas tu satu minyak grease"),
    (86.90, 107.25, "speech", "Satu carbon. Untuk carbon ni ... korang masuk grease"),
    (109.38, 111.95, "speech", "Ni minyak yang dia bagi ni"),
    (118.10, 125.55, "speech", "Harga bajet je ... boleh tengok dekat beg dekat bawah"),
    (125.55, 127.30, "demo",   "end-card plate (footage under CTA)"),
]
# Filler sounds (no words) removed by hand inside a keep: (src_from, src_to)
MANUAL_CUTS = [(77.62, 78.28)]   # hesitation between "mata dia" and "6 batang"
# Hook: picture from the demo, sound = speaker's line over ducked drill noise.
HOOK = dict(video=(11.00, 15.40), voice=(43.45, 47.90), drill_gain=0.30)

segs = []
for s, e, kind, note in KEEPS:
    s2 = s if kind == "demo" else snap(s)
    if segs and s2 < segs[-1][1]: s2 = segs[-1][1]   # never replay frames
    e2 = e if kind == "demo" else snap(e)
    if kind != "speech":
        segs.append([s2, e2]); continue
    # split on long inner silences
    i0, i1 = int(s2 * 100), int(e2 * 100)
    quiet = db[i0:i1] < THR_DB
    cur = s2; j = 0
    while j < len(quiet):
        if quiet[j]:
            k = j
            while k < len(quiet) and quiet[k]: k += 1
            gs, ge = (i0 + j) / 100, (i0 + k) / 100
            if ge - gs > MAX_GAP and gs > s2 + 0.05 and ge < e2 - 0.05:
                half = KEEP_GAP / 2
                segs.append([cur, round(gs + half, 2)]); cur = round(ge - half, 2)
            j = k
        else:
            j += 1
    segs.append([cur, e2])

for c0, c1 in MANUAL_CUTS:
    out = []
    for a, b in segs:
        if a < c0 < b and a < c1 < b: out += [[a, c0], [c1, b]]
        else: out.append([a, b])
    segs = out

hook_len = round(HOOK["video"][1] - HOOK["video"][0], 2)
t = hook_len; tmap = []
for s, e in segs:
    tmap.append({"src_in": s, "src_out": e, "out_in": round(t, 3)}); t += e - s
json.dump({"hook": HOOK, "hook_len": hook_len, "segments": tmap, "total": round(t, 3)},
          open(OUT, "w"), indent=1)
removed = 127.34 - (t - hook_len) 
print(f"{len(tmap)} segments, output {t:.2f}s (source 127.34s)")
