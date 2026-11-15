"""Edit decision list for the MUROH DOOH silent oil-free air compressor, 30 L / 9 L (hands-only), 1:30.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, the compressor running, "memang senyap, memang senyap" (33.10-35.36).
Dropped: "jadi kalau korang nak puas hati terus ambil yang 30 liter" (said again in the closer), "angin dia kuat tak?",
the first "pressure dia ni lebih kurang dalam 1 minit untuk 8 liter" take (the clearer second one is kept), the first
closer with "free oil, free maintenance, tak bisa" and the long pauses.
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
    (0.00, 5.36, "exact", "30 liter, yang ni 9 liter, dua-dua"),
    (5.90, 8.34, "exact", "air compressor ni dah ada stock."),
    (19.46, 25.88, "exact", "Lepas tu satu lagi yang ni jenis silent, free oil, maknanya korang tak perlu pun nak jaga minyak."),
    (28.20, 31.40, "exact", "Korang boleh dengar bunyi dia tu."),
    (38.00, 41.76, "exact", "Bila korang on ni dia akan stop sampai 8 bar.", {"edge": "keep"}),
    (49.60, 57.54, "exact", "Dia ambil masa ni lah macam untuk yang saiz kecil ni, ok untuk ambil masa dia penuh 1 minit untuk 8 liter.", {"edge": "keep"}),
    (57.58, 69.58, "exact", "Jadi yang ni 30 liter memang puas hati kan, kalau korang ada bajet terus ambil yang 30 liter ni, senang nak buat kerja, nak buat pula main motor, pula main kereta, lepas je.", {"edge": "keep"}),
    (70.30, 76.74, "exact", "Untuk yang ni kalau korang beli korang juga akan dapat sekali dengan hose nozzle ni sekali, harga bajet je."),
    (82.38, 88.76, "exact", "Jadi kalau korang berminat dengan air compressor yang macam kat depan saya ni kan, boleh tengok dekat beg dekat bawah, murah je."),
    (88.80, 89.60, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(33.10, 35.36), voice=None, drill_gain=1.0)

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
