"""Edit decision list for the MUROH DOOH step ladder (tangga, 2nd video) edit.

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, label).
- Cuts are snapped to the quietest 10 ms frame within +-SNAP s, so no word is clipped.
- Pauses longer than MAX_GAP inside speech keeps are shrunk to KEEP_GAP (dead air removal).
- The hook plays brick-breaking footage with the speaker's own line laid over it (J-cut);
  that line is NOT repeated later.
Outputs build/edl.json (segments + time map) used by build_spine.sh and captions.py.
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
    (0.00, 2.10, "exact", "Ni tangga yang saya pegang ni yang paling pendek,"),
    (4.45, 9.68, "speech", "sesuai untuk korang nak simpan-simpan barang dalam kabinet dapur ke, boleh pakai yang ni."),
    (11.10, 13.12, "speech", "Korang jangan risaulah, yang ni"),
    (16.55, 18.48, "demo", "standing on the ladder, rocking it (no speech)"),
    (18.45, 30.68, "speech", "goncang-goncang pun tak ada masalah. Lepas tu dia ada banyak warna tau, dia ada banyak pilihan warna, korang boleh pilih lah, nak warna putih ke, nak warna merah ke, ikut budget korang."),
    (34.50, 36.10, "speech", "Ni warna putih ni cantik."),
    (39.08, 41.62, "speech", "Untuk yang paling tinggi ni, yang ni 8 step."),
    (50.72, 56.80, "speech", "Kalau korang nak buat bersih kipas, nak pasang lampu, korang terus ambil yang jenis 8 step macam ni."),
    (57.30, 61.05, "speech", "Yang penting kan harga bajet daripada harga dekat kedai luar."),
    (64.50, 68.75, "exact", "Jadi yang mana korang tengah mencari tangga untuk kerja-kerja DIY dekat rumah,"),
    (69.45, 73.90, "speech", "boleh ambil brand yang macam kat depan saya ni, harga murah je, boleh tengok dekat beg dekat bawah."),
    (73.90, 74.50, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
# Hook: in sync - he stands on the ladder: "memang jenis tahan lasak, korang boleh tengok".
HOOK = dict(video=(13.62, 16.55), voice=None, drill_gain=1.0)

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
