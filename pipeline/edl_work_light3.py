"""Edit decision list for the MUROH DOOH Black Dog COB light (armband / head strap; presenter on camera).

Times are seconds in the ORIGINAL recording (2:42). Owner's rule: 30 s - 1 min, key points only.
Kept: jogging armband, the light modes (1st, dim, blink, red on double-click), the front sensor, the magnet,
the Black Dog brand, the head strap, "memang smart", the CTA. Dropped: the opening "bila letak terus melekat",
"sekali lagi kita demo", the duplicate "ni yang pertama", long silent demo stretches (52-89 s), the repeated
sensor line (94.8 s) and the first head-strap mention (13.5 s; the fuller one at 146 s is kept).
- Hook: the light cycling pink/blue (45.9-50.0) under his line "dia ada total semua 8 mood tau, memang
  cantik" (48.10-52.20, J-cut, original sound muted; not repeated later).
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
    (9.55, 13.40, "speech", "Jadi yang mana korang jogging tu, boleh pakai yang ni."),
    (17.80, 21.30, "speech", "So untuk yang ni dia ada banyak pilihan lampu. Ni yang pertama."),
    (24.90, 26.35, "speech", "Kedua dia malap sikit."),
    (27.60, 30.25, "speech", "Ketiga dia klik-klik macam ni."),
    (31.00, 36.95, "speech", "Jadi kalau korang tekan double klik, dia akan nyala warna merah. Nampak?"),
    (89.55, 93.15, "speech", "Lepas tu dekat depan ni juga dia ada sensor tau."),
    (115.40, 121.75, "speech", "Memang senang, nak on tekan, nak off tutup, ada sensor, mudah."),
    (131.95, 140.32, "speech", "Contoh kalau korang nak lekat tempat yang ada besi pun boleh, dia ada magnet, memang cukup function. Brand daripada Black Dog ni gang."),
    (146.30, 152.48, "speech", "Jadi nak gantung dekat kepala pun boleh, korang masuk je tali yang dia bagi ni, boleh gantung dekat kepala macam ni."),
    (154.00, 154.92, "exact", "Memang smart."),
    (155.24, 161.10, "speech", "Jadi kalau korang berminat kan lampu daripada Black Dog ni, harga murah je, boleh tengok dekat beg dekat bawah."),
    (161.10, 161.80, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(45.90, 50.00), voice=(48.10, 52.20), drill_gain=0.0)

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
