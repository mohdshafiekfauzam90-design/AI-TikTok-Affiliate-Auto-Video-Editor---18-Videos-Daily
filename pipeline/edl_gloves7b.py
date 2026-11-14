"""Edit decision list for the MUROH DOOH work gloves (touchscreen fingertips, 6 / 12 pairs), presenter on camera, 1:11 - v2.
v2: "zoom bagi nampak elok-elok" was his note to the editor, not part of the pitch: cut, and shown as a push-in instead.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: his gloved finger sliding the phone screen (45.00-49.80) under his line "jadi kalau korang tengah buat kerja nak
  jawab call memang tak ada masalah, tak perlu nak buka glove" (47.36-52.16, J-cut; not repeated later).
Dropped: the unfinished "lepas tu satu lagi untuk glove ni" lead-ins, the silent glove-on stretch, "korang boleh tengok kita
boleh slide telefon, nampak" (the hook shows it), "yang tu yang paling bagus lah", the "so yang mana" stumble and the
long pauses. He never says "beg dekat bawah", so the CTA card says it.
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
    (0.00, 12.20, "exact", "Yang ni glove ni dia disediakan dengan 2 pilihan tau, 6 pasang dengan 12 pasang. Kalau korang ada bajet terus ambil 12 pasang, harga pun murah je. Sekali korang beli ni memang boleh pakai lama."),
    (12.22, 17.94, "exact", "Untuk glove ni kalau korang nak buat ... motor, nak buat apa, berkebun ke, memang sangat sesuai."),
    (18.00, 22.64, "exact", "Yang ni size dia, untuk size dia dia ada satu size sahaja, size 8."),
    (37.30, 40.48, "exact", "Ok korang boleh tengok, untuk glove ni dia boleh slide tau.", {"edge": "keep"}),
    (59.00, 69.26, "exact", "Jadi yang mana korang tengah mencari glove nak buat kerja-kerja heavy duty, nak buat berkebun ke, boleh sangat beli yang ni, nak jimat terus ambil 12 pasang.", {"edge": "keep"}),
    (69.30, 70.10, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(45.00, 49.80), voice=(47.36, 52.16), drill_gain=0.0)

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
