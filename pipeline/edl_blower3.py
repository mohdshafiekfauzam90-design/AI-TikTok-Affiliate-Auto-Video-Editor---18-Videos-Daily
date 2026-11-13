"""Edit decision list for the MUROH DOOH EB260 26cc leaf blower, take 3 (presenter, "kenapa susah nak hidup", 2:31).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the blower running (40.00-43.40) under his opening line "kenapa saya beli susah nak hidup" (0.00-3.40,
  J-cut, engine low under it).
Dropped: the repeated "susah nak hidup / awal-awal" lead-ins, the engine run, "habuk siling jatuh", the
"mungkin korang tak pump dulu" recap, the mixing measure example (petrol 5 / 2T 5) and the long run of
"jadi yang mana korang ada halaman besar" false starts before the closer; the closing "terima kasih" is invented.
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
    (8.74, 29.34, "exact", "Kalau susah nak hidup awal-awal tu, abang pump dulu bang, kat bawah ni bang, dekat bawah ni dia ada satu balon tau, abang tekan, pump pump pump pump, bagi minyak naik dulu, baru senang nak hidup. Ni macam ni, kalau dah minyak naik sekali start je, terus hidup."),
    (78.84, 96.88, "exact", "Yang ni model EB260, 26cc. Kalau korang beli korang akan dapat satu set macam ni lah, nozzle, lepas tu blower, satu lagi korang akan dapat dia punya tong yang ini untuk bancuh dia ni, yang kecil ni korang masuk 2T, yang besar ni korang masuk petrol."),
    (104.12, 107.95, "exact", "Korang boleh bancuh, ha settle, senang sangat-sangat."),
    (134.00, 145.54, "exact", "Jadi yang mana korang nak buat bersih halaman rumah tu, daun kering, rumput kering, nak buat bersih kebun, boleh je pakai yang ni, harga murah je. Kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (145.80, 146.50, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(40.00, 43.40), voice=(0.00, 3.40), drill_gain=0.4)

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
