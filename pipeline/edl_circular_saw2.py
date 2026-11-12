"""Edit decision list for the MUROH DOOH cordless brushless circular saw, take 2 (presenter on camera).

Times are seconds in the ORIGINAL recording (1:51). Owner's rule: 30 s - 1 min, key points only.
- Hook: in sync, "so yang ni brushless motor, korang boleh dengar motor dia" running into the motor and
  "power kan eh, 1800" (63.28-73.75).
Dropped: the opening "ni korang boleh nampak", "banyak dah", the first "harga bajet" pitch (the CTA repeats it),
"1800W brushless" (said in the hook), "normal lah untuk circular saw biasa", the lock aside and the battery aside.
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
    (2.90, 7.08, "speech", "Sebelum ni dah habis stock geng, sekarang dah restock."),
    (16.05, 18.95, "speech", "Angle depan ni boleh adjust 45 darjah."),
    (24.65, 28.12, "speech", "Jadi kalau korang nak potong sudut, senang adjust je dekat depan ni."),
    (28.12, 31.30, "speech", "Lepas tu yang ni dia ada satu cover, safety cover dia lah."),
    (39.22, 48.32, "speech", "Korang jangan terbuka macam ni pula, takut kena tangan budak-budak. Jadi kalau korang nak guna biar je tertutup macam ni, bila korang potong tu dia akan terangkat automatic."),
    (73.75, 82.10, "speech", "Nak buat potong, nak buat potong plywood, memang takde masalah."),
    (82.10, 90.70, "speech", "Yang ni dia ada 3 level korang boleh adjust, adjust level dia dekat sini, level 1, level 2, level 3."),
    (101.50, 109.00, "speech", "Yang mana tengah mencari circular saw jenis cordless harga budget, boleh ambil yang ni, boleh tengok dekat beg dekat bawah."),
    (109.30, 110.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(63.28, 73.75), voice=None, drill_gain=1.0)

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
