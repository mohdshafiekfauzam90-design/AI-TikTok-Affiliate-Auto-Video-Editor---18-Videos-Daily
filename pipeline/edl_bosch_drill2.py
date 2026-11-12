"""Edit decision list for the MUROH DOOH Bosch GSR 120-LI cordless drill with carry case (presenter on camera, 1:58).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the case opened to the drill, batteries and bit set (94.00-98.15) under his line "brand Bosch ni memang
  boleh pakai lama, kita labur sekali" (31.52-35.67, J-cut, original sound muted; not repeated later).
Dropped: "yang biasa tu dia ringan sikit, yang ni berat" (said just before), the repeated "dia ada banyak package" lines, the battery-shape aside, the repeated "ambil 2 bateri",
the "dia datang macam ni" package walk-through (its case is the hook picture), "so kalau korang tengah macam
di-dry" (both passes unclear) and the closing "terima kasih" the first pass invented over silence.
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
    (1.08, 8.62, "exact", "GSR 120-LI, yang ni drill cordless daripada Bosch, original Bosch."),
    (12.95, 25.85, "exact", "Kalau korang pegang drill daripada Bosch ni, mana-mana drill lah, drill ke angle grinder ke tak kisah, korang boleh compare dengan brand yang lain, korang akan rasa beza. Drill ni bila korang pegang akan rasa berat kan."),
    (38.83, 43.42, "exact", "Jadi untuk yang ni dia ada banyak package korang boleh pilih,"),
    (52.88, 58.80, "exact", "nak satu bateri, nak dua bateri, nak dengan set mata bit, korang boleh pilih ikut budget korang."),
    (58.80, 63.20, "exact", "So kalau korang ada budget, saya suggest korang ambil terus dua bateri."),
    (69.47, 75.45, "exact", "Jadi senang lah kalau habis satu korang boleh charge lagi satu, sempat lah boleh tukar-tukar bateri."),
    (81.15, 83.87, "exact", "So untuk charger dia ni jenis fast charger."),
    (105.68, 113.50, "exact", "Nak buat kerja seharian, nak buat pakai lama, terus ambil brand daripada Bosch ni. Kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (114.50, 115.20, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(94.00, 98.15), voice=(31.52, 35.67), drill_gain=0.0)

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
                segs.append([cur, round(gs + tail, 2), {}]); cur = round(ge - lead, 2)
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
