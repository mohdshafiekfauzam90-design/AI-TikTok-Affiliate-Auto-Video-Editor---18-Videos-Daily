"""Edit decision list for the MUROH DOOH Bosch GWS 700 corded angle grinder, third take (presenter on camera, 1:45).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the grinder running (33.15-36.75) under his line "kualiti dia memang sangat-sangat cantik"
  (29.25-32.85, J-cut, motor low under it; not repeated later).
Dropped: the "nak pakai seharian, nak guna seharian" stumble at the start, the doubled "memanglah harga dia"
price line, "barang memang cantik", the "gigi-gigi ... memang tune/cute" line (both passes disagree), the second
"pembuka" and the box line, and the first of the two "jadi yang mana korang tengah mencari" closers.
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
    (15.90, 20.50, "exact", "Untuk abang-abang tukang, abang-abang kontraktor, nak beli sekali, nak pakai lama,"),
    (21.35, 24.62, "exact", "korang boleh pakai brand daripada Bosch ni."),
    (38.15, 51.35, "exact", "Yang ni model GWS 700, 710W, dia boleh pergi sampai 12000 RPM. Untuk saiz dia ni 4 inci. (motor still running under the first words)"),
    (52.97, 57.35, "exact", "Yang ni original daripada Bosch."),
    (59.17, 63.40, "exact", "Yang ni model latest tau, model terbaru angle grinder."),
    (67.47, 72.98, "exact", "Lepas tu korang juga akan dapat satu handle, handle ni korang boleh letak kiri dan kanan, dia ada cop Bosch tau."),
    (75.05, 81.10, "exact", "Lepas tu korang juga akan dapat cover dengan pembuka dia. Ni cover dia, cover pun tebal."),
    (96.55, 103.95, "exact", "Jadi yang mana korang tengah mencari angle grinder nak pakai lama, terus ambil brand ... Bosch."),
    (104.30, 105.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(33.15, 36.75), voice=(29.25, 32.85), drill_gain=0.35)

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
                segs.append([cur, round(gs + tail, 2), {}]); cur = round(ge - lead, 2)
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
