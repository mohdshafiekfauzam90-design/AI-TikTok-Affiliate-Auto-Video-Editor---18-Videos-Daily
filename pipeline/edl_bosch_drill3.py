"""Edit decision list for the MUROH DOOH Bosch GSR 120-LI cordless drill, second take (presenter on camera, 2:23).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the drill running, LED on (44.55-47.36) under his line "korang jangan risau, brand Bosch ni dah
  terbukti dah" (78.87-81.68, J-cut, motor low under it; not repeated later).
Dropped: the opening "nak guna lama" lead-in and the first "banyak pilihan" (19 s), "dia berbeza tau dengan
drill biasa" and the repeated "bila korang angkat ... berat" line, the muddled "untuk drill ni dekat beg satu"
start of the package line, the battery-shape aside, the two price lines and the "terima kasih" the first pass
invented over the battery close-up.
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
    (19.60, 26.30, "exact", "Yang ni drill daripada Bosch, model GSR 120-LI."),
    (30.80, 35.72, "exact", "Bila kita angkat drill daripada Bosch ni, korang akan rasa berat geng."),
    (55.52, 66.08, "exact", "Dia ada banyak package korang boleh pilih. Korang nak satu bateri, dua bateri, dengan mata bit semua adalah, korang boleh pilih ikut budget korang. Yang ni original daripada Bosch."),
    (68.45, 78.86, "exact", "So yang ni dia ada 20 speed torque, korang boleh adjust. Jadi kalau korang nak buat pasal skru, buka skru, tebuk kayu, tebuk besi, boleh je pakai drill ni. Memang boleh pakai lama kan."),
    (95.50, 98.05, "exact", "Untuk bateri dia jenis 12V kan."),
    (99.42, 102.38, "exact", "Kalau korang ada budget, terus ambil dua bateri."),
    (125.25, 128.42, "exact", "Ni charger dia, yang ni jenis fast charger."),
    (128.44, 141.05, "exact", "So kalau korang tengah mencari drill, nak pakai lama, nak buat kerja untuk seharian, ada budget lebih, terus ambil model ni geng, daripada Bosch. Kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (141.12, 141.42, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(44.55, 47.36), voice=(78.87, 81.68), drill_gain=0.4)

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
