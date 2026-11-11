"""Edit decision list for the MUROH DOOH folding-ladder (tangga lipat 4-8 step) video.

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

# (src_in, src_out, kind, note[, opts])  kind: demo = keep as-is, speech = trim inner pauses
# opts: {"speed": x} speeds picture+sound, {"gain": 0} mutes a repeated line under a demo shot.
KEEPS = [
    (0.92, 2.70, "speech", "Korang boleh tengok lah. Untuk tangga ni,"),
    (4.30, 13.10, "speech", "Yang ni 8 step paling tinggi. Yang paling rendah ni 4 step. Dia ada 4, 5, 6, 7 dengan 8."),
    (13.20, 19.45, "speech", "Kalau contoh untuk 8 step ni, kalau korang nak buat bersih lampu dekat rumah, tukar kipas,"),
    (21.90, 23.82, "speech", "lepas je untuk 8 step ni."),
    (23.90, 28.95, "speech", "Macam korang nak simpan barang dalam kabinet dapur ke, korang ambil je yang 4 step ni."),
    (32.50, 36.90, "speech", "Lepas tu untuk warna dia memang sangat-sangat menarik lah, dia ada warna putih, warna merah,"),
    (37.40, 40.05, "speech", "memang lawa. Lepas tu besi dia pun tebal,"),
    (40.90, 42.98, "speech", "memang jenis lasak lah geng."),
    (44.55, 47.80, "speech", "Lepas tu satu lagi, kalau korang simpan, dia tak makan ruang."),
    (47.80, 50.60, "demo", "folding demo (repeat line muted, 1.5x)", {"speed": 1.5, "gain": 0}),
    (52.50, 54.30, "demo", "side view: thin when folded (muted)", {"gain": 0}),
    (54.30, 55.05, "speech", "Kecil je."),
    (59.90, 64.48, "speech", "Ni nipis je, jadi korang boleh sandar dekat dinding."),
    (64.90, 70.30, "speech", "Jadi yang mana korang tengah mencari tangga yang harga bajet, boleh cuba tangga ni."),
    (70.70, 76.62, "speech", "Nak 8 step yang paling tinggi, ataupun nak paling rendah, pakat ambil yang 4 step."),
    (76.90, 79.65, "speech", "Jadi kalau korang berminat, boleh tengok dekat beg dekat bawah."),
    (79.65, 80.10, "demo", "end plate (thumbs up) under CTA"),
]
MANUAL_CUTS = []
# Hook: in sync - he stands on the ladder and says it is tough ("tahan lasak").
HOOK = dict(video=(28.90, 31.22), voice=None, drill_gain=1.0)

segs = []
for k in KEEPS:
    s, e, kind, note = k[:4]; opts = k[4] if len(k) > 4 else {}
    s2 = s if kind == "demo" else snap(s)
    if segs and s2 < segs[-1][1]: s2 = segs[-1][1]   # never replay frames
    e2 = e if kind == "demo" else snap(e)
    if kind != "speech":
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
