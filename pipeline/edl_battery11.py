"""Edit decision list for the MUROH DOOH Santino backpack battery, take 2 (presenter on camera), 2:40.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the angle grinder running off the pack (55.20-58.54) under his line "korang boleh pakai bateri ni, boleh tahan
  lama" (102.36-105.70, J-cut, grinder kept low under it; not repeated later).
Dropped: "ok", "jadi yang ni yang mana korang ada apa", his note to the editor ("zoom elok-elok bagi nampak bila saya
masuk ni"), the cable plug-in run-up, the air blower / chainsaw run-through and "semua benda yang pakai bateri" (the
Makita-base line covers it), "untuk ke gaji pokok ke" (unclear in the pass, cut rather than guessed), the
"pakai bateri biasa tu mungkin boleh tahan 1 jam 40 minit" comparison (no figure for this pack is given), the bag and
"pikul" handling, "jangan risau untuk lubang-lubang" and the long pauses.
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
    (9.70, 17.12, "exact", "Sebelum ni bateri daripada Santino ni dah habis stock tau, untuk model backpack ni, sekarang dah ada stock."),
    (20.26, 28.40, "exact", "Yang mana korang ada power tools yang jenis tapak Makita, tapak macam ni, boleh guna bateri ni."),
    (28.40, 33.80, "exact", "Yang ni cable yang dia dah bagi siap-siap, panjang kabel ni lebih kurang dalam 1 meter."),
    (46.10, 53.40, "exact", "Terus boleh sambung dekat power tools korang, tak kisahlah janji tapak Makita, contohnya yang ni angle grinder."),
    (86.40, 94.90, "exact", "Jadi untuk yang ni sesuai lah untuk korang nak guna jangka masa yang lama, contohnya untuk mesin rumput ke,"),
    (96.60, 98.30, "exact", "korang nak buat potong-potong pokok kan."),
    (105.72, 111.30, "exact", "Korang juga akan dapat satu charger, charger dia macam ni tau, jenis besar, jenis fast charger.", {"edge": "keep"}),
    (148.50, 155.90, "exact", "Harga dia pun tak mahal mana, jadi kalau korang berminat dengan bateri daripada Santino ni boleh tengok dekat beg dekat bawah, harga murah je."),
    (155.94, 156.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(55.20, 58.54), voice=(102.36, 105.70), drill_gain=0.35)

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
