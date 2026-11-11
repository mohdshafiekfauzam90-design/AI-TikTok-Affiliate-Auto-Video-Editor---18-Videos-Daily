"""Edit decision list for the MUROH DOOH Santino 21V backpack battery, 2nd video ("dah restock", closed bag).

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, kind, note[, opts]).
- Cuts are snapped to the quietest 10 ms frame within +-SNAP s, so no word is clipped.
- Pauses longer than MAX_GAP inside speech keeps are shrunk to KEEP_GAP (dead air removal).
- Hook: the chainsaw running off the battery cable (54.8-59.1) under his own line
  "macam korang nak buat mesin rumput, nak guna lama kan, berjam-jam" (J-cut; not repeated later).
- Repeats dropped: "dekat atas ni dia ada span" (said twice), "voltage/wattage dia pun tinggi"
  (passes disagree; the clean retake "watt dia pun tinggi" is kept), the first CTA attempt.
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
    (0.00, 5.20, "exact", "Yang ni bateri daripada Santino, sekarang dah restock."),
    (5.75, 9.80, "speech", "Ni dia, dia datang sekali dengan bag tau."),
    (9.76, 16.20, "speech", "Sebelum ni bag dia ni jenis apa, transparent, sekarang dia tertutup habis, tapi dekat atas ni dia ada span ni."),
    (20.68, 23.10, "speech", "Jadi kita boleh masuk macam ni."),
    (23.75, 28.90, "speech", "Contoh nak masuk... masuk je macam ni."),
    (30.90, 36.05, "speech", "Lepas tu korang jangan risaulah, dia cun-cun lubang dia ni, kiri kanan ni cun-cun lubang dia."),
    (36.90, 41.95, "speech", "Nak masuk korang tarik je yang ni, terus boleh masuk."),
    (44.70, 51.10, "speech", "Lepas tu kat sini dia ada bateri indicator dia, jadi senang korang nak monitor, korang boleh tengok ni."),
    (51.05, 54.45, "exact", "Untuk kabel dia ni lebih kurang dalam 1 meter."),
    (59.15, 64.47, "exact", "Untuk bateri ni sesuai untuk semua power tools jenis tapak Makita."),
    (68.28, 72.98, "speech", "Boleh beli bateri ni, yang ni daripada Santino."),
    (72.90, 79.97, "speech", "Jadi kalau korang nak guna untuk mesin rumput, pakai bateri ni memang sangat sesuai, memang boleh guna lama."),
    (79.97, 88.47, "exact", "Lepas tu ni charger dia tau, charger dia datang macam ni, saiz besar; kalau pakai charger biasa tu tak tahu bila lah nak penuh kan."),
    (91.00, 93.85, "exact", "Yang ni dia bagi charger ni, watt dia pun tinggi."),
    (96.95, 101.35, "exact", "Jadi kalau korang berminat bateri daripada Santino ni, boleh tengok dekat beg dekat bawah."),
    (101.35, 102.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(54.80, 59.10), voice=(64.45, 68.20), drill_gain=0.35)

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
