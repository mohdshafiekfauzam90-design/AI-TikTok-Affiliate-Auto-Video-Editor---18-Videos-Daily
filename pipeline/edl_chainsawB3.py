"""Edit decision list for the MUROH DOOH 52cc 2-stroke petrol chainsaw, 18 / 20 / 22" bars (presenter, wide shot), 2:26.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "yang macam kat depan saya ni, yang paling panjang 22 inci" (29.66-34.36).
Dropped: the stumbled first size run ("18, 20 tu doktor", unclear), the long off-camera stretch, the repeated "trim pokok /
potong pokok" and "cari chainsaw harga bajet" lead-ins, "kat sini ni normal" (unclear), the first oil line and the repeated
"function dia untuk bagi basahkan rantai", all the repeated bar-change lines (one kept) and the long pauses.
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
    (0.00, 4.14, "exact", "Untuk chainsaw yang kat depan saya ni, yang ni dia ada 3 size tau,", {"edge": "keep"}),
    (26.40, 29.66, "exact", "dia ada 18, 20 dengan 22 inci.", {"edge": "keep"}),
    (34.36, 38.94, "exact", "Untuk kapasiti engine dia 52cc jenis 2 stroke.", {"edge": "keep"}),
    (49.62, 52.90, "exact", "Jadi yang mana korang nak buat trim pokok ke, nak buat potong pokok ke kan,", {"edge": "keep"}),
    (59.60, 61.92, "exact", "boleh sangat ambil yang ni.", {"edge": "keep"}),
    (63.62, 67.70, "exact", "Korang boleh masuk minyak hitam ataupun minyak terpakai,", {"edge": "keep"}),
    (77.12, 80.78, "exact", "function dia untuk pelincir dekat rantai ni.", {"edge": "keep"}),
    (80.78, 87.26, "exact", "Lepas tu dekat belakang ni korang boleh masuk petrol, yang ni korang kena bancuh lah petrol dengan 2T.", {"edge": "keep"}),
    (87.26, 90.98, "exact", "Kat sini on off dia, sebelah sini choke dia.", {"edge": "keep"}),
    (110.98, 116.12, "exact", "Untuk papan dia ni kan, kalau korang nak tukar saiz pendek ke nak saiz panjang ke, boleh sahaja.", {"edge": "keep"}),
    (132.44, 141.34, "exact", "Jadi yang mana korang tengah mencari chainsaw harga bajet, boleh cuba chainsaw yang macam saya pegang ni, boleh tengok dekat beg dekat bawah."),
    (141.38, 142.20, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(29.66, 34.36), voice=None, drill_gain=1.0)

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
