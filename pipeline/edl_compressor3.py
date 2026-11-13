"""Edit decision list for the MUROH DOOH Re-Aim silent air compressor, take 3 (hands only, 2:02).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "korang boleh dengar bunyi dia, serius, memang senyap je" (12.75-16.60).
Dropped: "nak on dia, tarik je dekat atas ni", the repeated "untuk 8 liter / tengok lah / senyap je", "kalau korang
nak buat komen-komen kan dekat rumah" (unclear), the long run of false starts on the spray line, and the repeated
"oil free" lines.
"""
import json, sys, wave, numpy as np

AUDIO = sys.argv[1]          # 16 kHz mono wav of the original
OUT = sys.argv[2]
SNAP, MAX_GAP, KEEP_GAP, THR_DB = 0.12, 0.40, 0.26, -42.0   # owner: words sounded cut, so pauses keep a fuller tail

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
    (0.00, 10.36, "exact", "Ok, yang ni jenis silent compressor kan, brand daripada Re-Aim. Untuk nozzle dia memang senang, yang ni jenis auto lock, korang tolak je dia akan auto lock."),
    (22.14, 27.62, "exact", "Untuk size 8 liter ni, untuk dia penuh lebih kurang dalam 1 minit."),
    (36.60, 42.54, "exact", "Boleh beli sangat lah air compressor ni, memang tak mengganggu jiran-jiran."),
    (44.70, 48.82, "exact", "Dia akan stop dekat 8 bar, laju je dia naik."),
    (50.55, 57.38, "exact", "Yang ni dia ada 3 size korang boleh pilih, 8 liter, 30 liter dengan 50 liter."),
    (93.57, 103.22, "exact", "Nak buat spray motor ke, saya suggest korang ambil 30 liter ke atas. Nak buat spray kereta, 30 liter pun dah lepas lah. Tapi lagi best ambil 50 liter."),
    (103.30, 109.00, "exact", "Yang ni jenis oil free, tak perlu nak jaga-jaga minyak lah."),
    (114.45, 119.92, "exact", "Harga tak mahal mana, kualiti cantik. Kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (120.40, 121.10, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(12.75, 16.60), voice=None, drill_gain=1.0)

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
                tail, lead = KEEP_GAP * 0.6, KEEP_GAP * 0.4      # more room after a word than before the next
                segs.append([cur, round(gs + tail, 2), dict(opts)]); cur = round(ge - lead, 2)
            j = k
        else:
            j += 1
    segs.append([cur, e2, dict(opts)])

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
