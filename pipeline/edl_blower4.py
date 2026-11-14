"""Edit decision list for the MUROH DOOH cordless air blower (Makita-type battery base, presenter on camera), 1:31.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the blower running flat out at level 3 (44.00-47.40) under his line "serius memang senang bila pakai air blower ni"
  (1.06-4.46, J-cut, blower kept low under it; not repeated later).
Dropped: "bateri tapak Makita macam ni, yang mana tak tahu macam ni", the first "mana-mana jenama ... janji tapak yang sama"
take (the clearer "tak kisah jenama apa pun" is kept), most of the long level-3 run and the angle/nozzle handling, the
repeated "atas", and the long pauses. He never says "beg dekat bawah", so the CTA card says it.
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
    (4.48, 11.12, "exact", "Pakai jenis bateri tapak Makita, tak perlu pakai wire, senang korang nak bawa ke mana-mana."),
    (22.70, 29.36, "exact", "Lepas tu untuk bateri dia pula tak kisah jenama apa pun, kalau tapak Makita boleh je masuk dekat air blower ni."),
    (29.36, 33.20, "exact", "So yang ni dia ada 3 level korang boleh adjust."),
    (35.90, 41.10, "demo", "Ni level 1, level 2, level 3 (blower running)."),
    (51.70, 52.76, "demo", "Kuat kan."),
    (53.88, 56.42, "exact", "Lepas tu untuk angle dia ni boleh adjust."),
    (61.56, 64.56, "exact", "Macam ni ke, macam ni ke, semua boleh adjust."),
    (64.56, 69.20, "exact", "Lepas tu untuk nozzle dia ni boleh buka, bawah ni, atas pun boleh buka."),
    (74.34, 78.10, "exact", "So nozzle dia, dia ada bagi banyak pilihan, bukan satu je."),
    (78.10, 89.80, "exact", "Jadi yang mana korang nak buat bersih daun kering, nak buat bersih rumput kering, nak buat bersih air lepas basuh motor, basuh kereta, nak buat bersih celah-celah sofa, celah-celah almari, boleh je pakai yang ni, harga murah je."),
    (89.82, 90.60, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(44.00, 47.40), voice=(1.06, 4.46), drill_gain=0.35)

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
