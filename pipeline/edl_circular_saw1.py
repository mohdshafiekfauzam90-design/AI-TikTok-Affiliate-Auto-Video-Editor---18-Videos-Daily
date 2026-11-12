"""Edit decision list for the MUROH DOOH cordless brushless circular saw, take 1 (presenter on camera).

Times are seconds in the ORIGINAL recording (1:32). Owner's rule: 30 s - 1 min, key points only.
- Hook: in sync, his opening "tak payah cakap banyak, memang lain kan kalau brushless motor, bunyi dia memang
  lain, ni korang boleh dengar bunyi dia" running into 3.4 s of the motor itself (1.28-11.20).
Dropped: "ni korang boleh nampak 5 inci" (repeat), the battery aside (said twice), "lepas tu special",
the repeated "adjust angle dekat depan ni", and the silent stretches.
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
    (15.70, 20.05, "speech", "Seronok tau bunyi dia. Yang ni circular saw size 5 inci."),
    (23.05, 26.50, "speech", "Yang ni kalau korang beli, mata ni pun korang akan dapat sekali."),
    (27.50, 31.98, "speech", "Bila dah brushless macam ni, senang nak bawa ke mana-mana, tak serabut dengan wire."),
    (43.85, 51.62, "speech", "Jadi yang ni kalau korang nak buat potong papan, potong plywood, nak buat kerja-kerja DIY dekat rumah, nak buat pasang kabinet ke, sesuai pakai yang ni."),
    (53.40, 58.45, "speech", "Satu lagi yang special, dia boleh adjust tiga level. Nak adjust level dia dekat sini kan."),
    (59.70, 64.10, "demo", "Ni level 1, level 2, level 3 (motor running)."),
    (70.50, 74.38, "speech", "Jadi kalau korang nak adjust angle dia, boleh pusing dekat depan ni."),
    (80.20, 83.65, "exact", "Maximum dia boleh potong sudut dia 45 darjah."),
    (84.40, 90.85, "speech", "Jadi yang mana korang tengah mencari circular saw harga bajet, boleh cuba brand daripada ST ni."),
    (91.00, 91.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(1.28, 11.20), voice=None, drill_gain=1.0)

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
