"""Edit decision list for the MUROH DOOH Santino 10-inch cordless work light (presenter on camera).

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, kind, note[, opts]).
Owner's rule: 30 s - 1 min, key points only. Dropped: the long, repeated level-1 vs level-2 explanation
(18-30.6 s; its clean summary at 30.7 s is kept) and the closing "penuh dengan..." tail.
- Hook: the lamp switched on, facing the camera (22.95-25.45), under his opening line
  "nak buat kerja tak cukup pencahayaan" (0.12-2.62, J-cut, original sound muted under it).
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

# (src_in, src_out, kind, note[, opts])  kind: demo = keep exactly as given (no snap, no pause trim; use it for a
# line whose speaker pauses inside a number), exact = trim inner pauses but keep the given edges, speech = both
# opts: {"speed": x} speeds picture+sound, {"gain": 0} mutes a repeated line under a demo shot.
KEEPS = [
    (2.68, 12.40, "speech", "Ni dia korang boleh beli satu work light daripada Santino. Yang ni size 10 inci, dia ada 2 level, pakai bateri jenis tapak Makita."),
    (12.40, 18.15, "speech", "Ni nak adjust level dia dekat sini, korang boleh tengok dekat belakang tu. Memang terang tau."),
    (30.70, 35.85, "speech", "Untuk level 1 dia kurang kembang, level 2 dia lagi luas pembukaan dia gang."),
    (37.45, 45.95, "speech", "Lepas tu yang ni boleh adjust ni tapak dia, boleh adjust, korang boleh pilih lah mengikut kesesuaian kerja korang."),
    (45.95, 53.17, "speech", "Jadi untuk yang ni kalau korang nak jadikan power bank pun boleh, dia ada 2 port USB, jadi korang boleh charge telefon."),
    (53.22, 60.65, "speech", "Yang mana korang buat kerja tak cukup pencahayaan tu, boleh beli satu lampu cordless daripada Santino ni."),
    (60.65, 63.80, "exact", "Size 10 inci, full LED tau."),
    (65.45, 66.15, "demo", "end plate under CTA (silent; 63.8-65.2 is \"penuh dengan...\")"),
]
MANUAL_CUTS = []
HOOK = dict(video=(22.95, 25.45), voice=(0.12, 2.62), drill_gain=0.0)

segs = []
for k in KEEPS:
    s, e, kind, note = k[:4]; opts = k[4] if len(k) > 4 else {}
    s2 = s if kind in ("demo", "exact") else snap(s)
    if segs and s2 < segs[-1][1]: s2 = segs[-1][1]   # never replay frames
    e2 = e if kind in ("demo", "exact") else snap(e)
    if kind not in ("speech", "exact"):
        segs.append([s2, e2, opts]); continue
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
                segs.append([cur, round(gs + half, 2), {}]); cur = round(ge - half, 2)
            j = k
        else:
            j += 1
    segs.append([cur, e2, {}])

for c0, c1 in MANUAL_CUTS:
    out = []
    for a, b, o in segs:
        if a < c0 < b and a < c1 < b: out += [[a, c0, o], [c1, b, o]]
        else: out.append([a, b, o])
    segs = out

hook_len = round(HOOK["video"][1] - HOOK["video"][0], 2)
t = hook_len; tmap = []
for s, e, o in segs:
    tmap.append({"src_in": s, "src_out": e, "out_in": round(t, 3), **o}); t += (e - s) / o.get("speed", 1)
json.dump({"hook": HOOK, "hook_len": hook_len, "segments": tmap, "total": round(t, 3)},
          open(OUT, "w"), indent=1)
print(f"{len(tmap)} segments, output {t:.2f}s")
