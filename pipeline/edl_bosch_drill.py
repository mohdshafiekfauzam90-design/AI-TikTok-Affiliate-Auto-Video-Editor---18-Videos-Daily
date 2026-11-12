"""Edit decision list for the MUROH DOOH Bosch GSR 120-LI cordless drill (hands-only unboxing).

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, kind, note[, opts]).
Owner's rule: 30 s - 1 min, key points only. Dropped: the contractor aside (19.9-24.7, its shot is the hook),
the DIY lead-in, the repeated "kepala bateri tak sama" explanation, the "ambil 2 bateri" aside and "package
ketiga" preamble.
- Hook: the drill in its case, BOSCH label up (19.90-22.24), under his line "Brand Bosch ni gang, tak perlu
  cerita lebih-lebih lah" (12.78-15.12, J-cut, original sound muted under it; not repeated later).
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
    (0.00, 6.75, "exact", "Yang ni drill cordless daripada Bosch original, model GSR 120-LI."),
    (7.75, 12.76, "exact", "So yang ni kalau korang nak buat pasal skru, buka skru, tebuk kayu, tebuk besi, boleh pakai yang ni."),
    (15.14, 19.50, "speech", "Memang dah terkenal gang dengan kualiti dia, tahan lasaknya."),
    (30.00, 32.80, "speech", "Nak pakai lama, boleh ambil brand Bosch ni."),
    (32.80, 38.25, "demo", "Yang ni dia ada 20 speed torque, lepas tu bateri dia ni jenis 12V."),
    (38.22, 41.60, "exact", "Bateri dia ni tak sama geng dengan bateri (Dray) yang biasa,"),
    (46.82, 50.90, "exact", "korang boleh tengok ni, kepala dia pun dah lain, memang tak boleh tukar-tukar lah."),
    (60.88, 66.98, "speech", "Ini untuk charger dia. Charger dia jenis fast charger, pakai plug 3 pin yang biasa kita guna je."),
    (67.62, 69.68, "speech", "Dia datang dengan casing macam ni."),
    (72.50, 78.85, "speech", "Kalau package ketiga ni, dia ada manual book, satu bateri, satu drill, satu charger."),
    (79.00, 84.45, "speech", "Jadi kalau korang berminat dengan drill daripada Bosch ni, boleh tengok dekat beg dekat bawah. Yang penting original kan."),
    (84.45, 85.20, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(19.90, 22.24), voice=(12.78, 15.12), drill_gain=0.0)

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
