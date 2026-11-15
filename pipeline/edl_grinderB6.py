"""Edit decision list for the MUROH DOOH cordless brushless angle grinders 4" and 5" (presenter on camera), 0:59.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "korang boleh tengok perbezaan dia, yang ni size 4 inci, yang ni size 5 inci" (2.16-7.24).
Dropped: "ok", the doubled "tapak" and "harga bajet je", the closing "terima kasih" and the long pauses.
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
    (7.24, 18.90, "exact", "Dua-dua brushless motor. Jadi kalau korang nak size besar sikit, korang terus ambil yang ni, 5 inci, boleh adjust 4 level. Model ni tak boleh nak adjust level.", {"edge": "keep"}),
    (21.00, 33.60, "exact", "So korang boleh dengar bunyi motor dia. Adjust level dia dekat sini, ni level 1, level 2, level 3, level 4.", {"edge": "keep"}),
    (34.50, 41.46, "exact", "Untuk bateri dia ni jenis tapak Makita, jadi mana-mana jenama pun boleh je masuk, janji tapak yang sama.", {"edge": "keep"}),
    (42.26, 44.40, "exact", "Barang dia ni geng, harga bajet je.", {"edge": "keep"}),
    (45.30, 49.88, "exact", "Untuk 5 inci ni, handle ni korang boleh letak kiri dan kanan."),
    (49.90, 57.70, "exact", "Jadi kalau korang tengah mencari angle grinder, nak size mata besar sikit, special sikit, boleh ambil yang ni, boleh tengok dekat beg dekat bawah."),
    (57.74, 58.50, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(2.16, 7.24), voice=None, drill_gain=1.0)

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
