"""Edit decision list for the MUROH DOOH Bosch GWS 700 corded angle grinder (presenter on camera).

Times are seconds in the ORIGINAL recording (2:23). Owner's rule: 30 s - 1 min, key points only.
- Hook: the grinder running (63.20-66.90) under his line "memang padu kan, nak buat potong besi tebal-tebal
  selamba" (68.80-72.50, J-cut, motor kept low under it; not repeated later).
Dropped: the stumbling opening (0-13 s), the long "dulu gemuk, sekarang slim" back-and-forth (one line kept),
the repeated "plug 3 pin" line, the first handle description (the clearer one at 100 s is kept), the repeated
"package" lines and the repeated "kerja seharian" lead-ins.
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
    (13.35, 23.18, "speech", "Angle grinder daripada Bosch, model yang latest, GWS 700, 710W, boleh pergi sampai 12000 RPM."),
    (23.18, 27.36, "exact", "Dia tak sama dengan model yang sebelum ni, design dia lain sikit."),
    (38.15, 41.45, "exact", "Yang ni dia dah slim, motor dia pun power."),
    (47.20, 51.68, "speech", "Bila kita pegang ni memang selesa, lagi grip daripada sebelum ni."),
    (73.65, 76.95, "speech", "Size 4 inci, dia pakai plug 3 pin"),
    (79.12, 80.95, "exact", "yang biasa kita guna je."),
    (100.20, 105.15, "speech", "Untuk handle ni korang boleh pasang kiri dan kanan mengikut kesesuaian kerja korang."),
    (105.12, 107.75, "speech", "Lepas tu cover, cover pun tebal."),
    (108.55, 111.20, "speech", "Lepas tu satu lagi, pembuka dia."),
    (124.08, 134.62, "speech", "Kalau korang nak pakai lama, nak buat kerja untuk seharian, boleh beli angle grinder ni, memang tahan lasak, je nama Bosch ni memang dah terkenal dengan tahan lasak dia."),
    (134.60, 137.70, "speech", "Jadi kalau korang berminat boleh tengok dekat beg dekat bawah."),
    (138.30, 139.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(63.20, 66.90), voice=(68.80, 72.50), drill_gain=0.35)

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
