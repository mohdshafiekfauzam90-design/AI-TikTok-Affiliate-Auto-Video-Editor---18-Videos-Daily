"""Edit decision list for the MUROH DOOH folding ladder (3rd ladder video: storage + safety lock).

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
    (10.60, 14.75, "speech", "Sama je yang panjang ke yang pendek ke, sama sahaja."),
    (16.95, 19.15, "speech", "Korang boleh sandar je dekat dinding."),
    (22.40, 23.25, "exact", "Nampak?"),
    (24.05, 28.42, "speech", "So yang ni tangga ni dia ada banyak pilihan tau, korang boleh pilih:"),
    (29.55, 33.65, "demo", "yang ada 4, 5, 6, 7 dengan 8 step."),   # list of sizes, pauses kept
    (39.55, 41.48, "exact", "Yang paling rendah 4 step."),
    (48.30, 56.05, "speech", "Kalau korang nak simpan atau ambil barang dalam kabinet dapur korang tu yang tinggi-tinggi tu, korang ambil je 4 step, cukup geng cukup."),
    (84.65, 93.35, "exact", "Lepas korang buka ni, make sure korang lock dulu dekat belakang ni, ha ni untuk safety lah, jadi dia masa korang panjat tu dia tak terbuka."),
    (94.20, 101.80, "speech", "Yang ni harga bajet je. Korang boleh survei dulu harga dekat luar, confirm tak sama dekat harga beg dekat bawah."),
    (101.68, 106.25, "speech", "Jadi kalau korang berminat kan dengan tangga lipat yang jimat ruang macam ni,"),
    (106.70, 108.62, "speech", "boleh tengok dekat beg dekat bawah."),
    (108.62, 109.40, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
# Hook: in sync - he folds the ladder: "korang boleh tengok lah kalau nak simpan ni, nak simpan dia memang tak makan ruang".
HOOK = dict(video=(0.00, 6.25), voice=None, drill_gain=1.0)

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
