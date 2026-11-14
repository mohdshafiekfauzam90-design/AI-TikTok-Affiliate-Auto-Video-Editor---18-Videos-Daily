"""Edit decision list for the MUROH DOOH heavy-duty work gloves, take 2 (presenter on camera), 2:04.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: his gloved finger working the phone screen (86.00-90.50) under his line "untuk sarung tangan ni, kalau korang nak
  buat touch screen telefon pun boleh" (48.90-53.40, J-cut; not repeated later).
Dropped: the "nilik yang tadi tu" restart and the repeated "sarung tangan untuk kerja heavy duty", the repeated "size 8"
lines, the glove-on stretch, "sekejap saya tunjuk dekat korang" and the long phone set-up, the first closer and
"delete yang tadi tu", and the long pauses.
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
    (0.50, 5.14, "exact", "Ok, yang ni sarung tangan untuk kerja heavy duty."),
    (11.56, 17.80, "exact", "Jadi kalau korang nak jimat, korang beli terus 12 pasang macam ni, memang boleh guna lama kan."),
    (17.84, 21.16, "exact", "Lepas tu untuk sarung tangan ni pun jenis tebal tau."),
    (21.80, 25.36, "exact", "Yang ni saiz dia saiz 8, free size."),
    (36.10, 46.74, "exact", "Barang cantik kan. Yang ni kalau korang nak buat berkebun, nak buat pomen motor ke, untuk kerja-kerja heavy duty lah, kerja-kerja lasak, yang ni dia susah nak koyak."),
    (91.30, 97.74, "exact", "Jadi senang lah bila korang buat kerja tu nak jawab call, senang, tak perlu buka glove ni."),
    (107.96, 122.86, "exact", "Jadi yang mana korang tengah mencari glove untuk buat kerja-kerja pomen, kerja-kerja berkebun, kerja-kerja lasak, ni dia, korang boleh ambil yang ni, korang terus beli 12 pasang, jimat geng, kalau korang nak boleh tengok dekat beg dekat bawah.", {"edge": "keep"}),
    (122.90, 123.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(86.00, 90.50), voice=(48.90, 53.40), drill_gain=0.0)

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
