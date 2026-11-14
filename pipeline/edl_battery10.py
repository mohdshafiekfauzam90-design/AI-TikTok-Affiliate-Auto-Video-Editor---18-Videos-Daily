"""Edit decision list for the MUROH DOOH Santino backpack battery (powers Makita-base tools), presenter on camera, 2:05.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the angle grinder running off the pack (20.60-23.12) under his line "bila korang guna ni boleh guna berjam-jam"
  (110.48-113.00, J-cut, grinder kept low under it; not repeated later).
Dropped: his spoken notes to the editor ("zoom dekat sikit bateri ni", "zoom angle grinder ni", "zoom blower ni",
"zoom dekat sini": shown as camera push-ins instead), "ok korang boleh tengok haa ni", the repeated "dia datang dengan
backpack" and "boleh check bateri indicator dia", "korang akan dapat free" (unfinished), "maknanya semua", "apa lagi kita nak on" and "jadi kalau korang nak guna untuk jangka masa yang lama", most of the
tool run-ups and the long pauses.
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
    (0.00, 3.40, "exact", "Yang ni bateri daripada Santino."),
    (11.40, 14.00, "exact", "Chainsaw dia boleh on."),
    (16.90, 18.30, "exact", "Angle grinder.", {"edge": "keep"}),
    (24.70, 26.90, "demo", "grinder running"),
    (29.70, 32.90, "exact", "On blower, blower ada kat depan."),
    (39.80, 41.30, "demo", "blower running"),
    (48.20, 53.20, "exact", "Untuk bateri Santino ni, yang ni dia datang dengan backpack tau."),
    (55.60, 59.58, "exact", "Macam ni, jadi korang boleh pikul dekat belakang."),
    (64.06, 68.10, "exact", "So lepas korang guna ni korang boleh check bateri indicator dia.", {"edge": "keep"}),
    (74.10, 79.98, "exact", "Lepas tu untuk kabel dia, dia datang dengan panjang dia lebih kurang dalam 1 meter."),
    (83.06, 89.12, "exact", "Untuk bateri ni korang boleh guna dekat semua power tools jenis tapak Makita.", {"edge": "keep"}),
    (93.68, 109.24, "exact", "Korang boleh beli satu bateri ni, sesuai lah untuk nak buat potong-potong pokok kan guna chainsaw ataupun korang nak buat mesin rumput, boleh ambil bateri ni, harga pun tak mahal mana."),
    (113.12, 115.86, "exact", "Jadi kalau korang boleh tengok dekat beg dekat bawah.", {"edge": "keep"}),
    (115.90, 116.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(20.60, 23.12), voice=(110.48, 113.00), drill_gain=0.35)

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
