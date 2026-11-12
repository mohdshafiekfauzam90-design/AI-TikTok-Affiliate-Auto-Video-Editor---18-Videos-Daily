"""Edit decision list for the MUROH DOOH Bosch GWS 700 corded angle grinder, second take (presenter on camera, 1:43).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the grinder close-up with the motor running (14.30-17.60) under his line "boleh pergi sampai 12,000 RPM"
  (8.22-11.42, J-cut, motor low under it; not repeated later).
Dropped: the repeated "model Bosch / model latest" lead-ins, the body-shape aside, the three repeated
"datang dengan kotak" lines (one kept), the repeated "kalau korang nak pakai lama" and "kerja seharian" lead-ins.
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
    (0.00, 7.55, "exact", "Yang ni model GWS 700, 710W, angle grinder daripada Bosch."),
    (13.05, 14.35, "exact", "Power tau. (motor running under it)"),
    (26.45, 33.15, "exact", "Untuk angle grinder ni model latest, korang boleh tengok lah design dia pun berlainan sikit daripada sebelum ni."),
    (40.40, 42.20, "speech", "Yang ni original."),
    (44.15, 49.75, "exact", "Dia pakai plug pin yang biasa kita guna je, dia datang dengan kotak macam ni tau."),
    (61.15, 72.00, "exact", "Dekat dalam dia korang akan dapat aksesori dia macam ni, handle ni dia ada tulisan Bosch, lepas tu pembuka dia, ni cover dia, cover pun tebal."),
    (79.37, 89.45, "exact", "(edge keep: \"pakai lama\" ends just before) Jadi yang mana korang nak buat kerja lasak, nak guna seharian tu, boleh beli yang ni geng, memang tahan lasak untuk jenama Bosch.", {"edge": "keep"}),
    (96.00, 102.50, "speech", "Terus beli brand daripada Bosch, harga sekarang pun tak mahal mana, mampu milik je, boleh tengok dekat beg dekat bawah."),
    (102.60, 103.30, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(14.30, 17.60), voice=(8.22, 11.42), drill_gain=0.35)

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
