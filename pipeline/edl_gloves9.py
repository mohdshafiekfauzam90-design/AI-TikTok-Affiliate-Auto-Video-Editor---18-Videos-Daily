"""Edit decision list for the MUROH DOOH heavy-duty touchscreen work gloves, take 3 (presenter on camera), 1:06.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "korang tengok ni guys, glove ni dia boleh touch tau" (0.00-3.22), the phone demo.
Dropped: the repeated oil line ("jenis kalau untuk glove ni kalau main dengan minyak takde masalah lah, okey sahaja"),
and the long pauses.
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
    (3.80, 9.96, "exact", "Jadi senang lah bila korang buat kerja tu nak jawab orang call, tak perlu buka glove ni."),
    (9.96, 20.12, "exact", "Yang ni glove jenis heavy duty, sesuai untuk abang-abang pomen, abang-abang nak buat berkebun, jenis kerja-kerja lasak lah, boleh beli glove ni."),
    (20.12, 23.22, "exact", "Yang atas ni jenis kain, dekat bawah ni jenis bergetah."),
    (23.22, 26.04, "exact", "Yang ni kalau untuk berminyak ke takde masalah.", {"edge": "keep"}),
    (31.10, 38.98, "exact", "So untuk yang ni dia datang dengan 2 set tau, 6 pasang dengan 12 pasang. Kalau korang nak jimat terus ambil 12 pasang."),
    (38.98, 44.88, "exact", "Untuk sepasang ni kan kalau korang pakai memang boleh pakai lama. Dia susah nak koyak, jenis tahan lasak."),
    (45.40, 48.30, "exact", "So korang boleh tengok lah kualiti dia pun cantik."),
    (50.46, 53.40, "exact", "Untuk yang ni dia ada satu saiz sahaja. Saiz 8."),
    (55.46, 63.92, "exact", "So yang mana korang tengah mencari glove untuk nak buat kerja pomen, berkebun ke, aktiviti lasak, boleh pakai glove ni."),
    (63.96, 64.80, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(0.00, 3.22), voice=None, drill_gain=1.0)

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
