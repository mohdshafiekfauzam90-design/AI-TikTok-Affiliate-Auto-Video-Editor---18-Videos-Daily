"""Edit decision list for the MUROH DOOH Santino backpack battery, take 3 (worn on his back, blower demo), 2:24.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the blower running off the pack on his back (36.00-38.32) under his line "memang korang boleh guna berjam-jam"
  (16.08-18.40, J-cut, blower kept low under it; not repeated later).
Dropped: "ok", the doubled "bila korang dah guna bateri daripada Santino ni" lead-in, "untuk ke gaji ke" (unclear, cut
rather than guessed), the long blower run and "memang kuat geng, nampak", both "cable ... lebih kurang dalam 1 meter" lines (takes 1-2 show the cable),
his notes to the editor ("zoom cable ni", "zoom bagi nampak semua"), the bag and cable handling, "kereta" (unclear),
"satu lagi" (unfinished) and the long pauses.
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
    (0.52, 5.94, "exact", "Korang boleh tengok untuk bateri yang saya pikul ni geng, yang ni brand daripada Santino tau."),
    (18.44, 21.72, "exact", "Untuk blower, untuk mesin rumput,", {"edge": "keep"}),
    (23.88, 30.06, "exact", "janji bateri jenis tapak Makita, boleh guna bateri backpack ni.", {"edge": "keep"}),
    (49.40, 58.14, "exact", "Jadi sesuai lah macam korang nak buat mesin rumput tu kan, yang jenis pakai bateri cordless tu, boleh beli satu bateri ni, dia datang sekali dengan bag."),
    (101.56, 105.26, "exact", "Lepas tu kat sini korang boleh on, dia akan keluar bateri indicator,", {"edge": "keep"}),
    (105.62, 107.82, "exact", "jadi senang korang nak monitor.", {"edge": "keep"}),
    (114.80, 124.66, "exact", "Korang juga akan dapat satu charger dia ni, charger dia, tak boleh pakai charger yang biasa, lambat nak penuh, korang guna charger yang dia bagi ni."),
    (125.50, 139.04, "exact", "So yang mana korang nak guna untuk jangka masa yang lama, nak buat mesin rumput, boleh beli satu bateri ni, harga pun tak mahal mana, mampu milik je, boleh tengok dekat beg dekat bawah."),
    (139.08, 139.90, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(36.00, 38.32), voice=(16.08, 18.40), drill_gain=0.35)

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
