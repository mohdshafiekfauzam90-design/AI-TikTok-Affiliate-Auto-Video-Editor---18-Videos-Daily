"""Edit decision list for the MUROH DOOH Sonco 580Nm brushless impact wrench kit (presenter on camera), 1:04.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "580Nm torque daripada Sonco" (6.06-10.72).
Dropped: "ok", "nampak", "motherboard, flexible shaft, semua adalah" and "kat depan ni kan korang boleh masuk motherboard
hexagon" (unclear in the pass, cut rather than guessed), the unfinished "dia datang dengan" and the long pauses.
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
    (1.04, 5.66, "exact", "Sekadar korang nak buat repair motor, korang terus ambil model ni je."),
    (10.72, 22.42, "exact", "Brushless motor, tak perlu nak tukar carbon, free maintenance. Bateri dia jenis tapak Makita, jadi mana-mana je jenama pun boleh je masuk, janji tapak yang sama. Bateri dia pun ada bateri indicator."),
    (23.10, 29.12, "exact", "Lepas tu untuk torque dia juga boleh adjust, nak maximum torque atau perlu torque, perhatikan je dekat atas ni."),
    (31.00, 35.30, "exact", "Jadi untuk package ni kan dia datang sekali dengan socket."),
    (43.32, 48.28, "exact", "Jadi kalau korang nak buat pasang skru buka skru senang, maknanya impact wrench ni 2 dalam 1.", {"edge": "keep"}),
    (49.00, 52.72, "exact", "Nak buat pomen motor boleh, nak buat pasang skru buka skru pun boleh.", {"edge": "keep"}),
    (56.08, 63.06, "exact", "Dia datang dengan casing macam ni kan. So yang ni harga tak mahal mana, mampu milik je, kalau korang nak boleh tengok dekat beg dekat bawah.", {"edge": "keep"}),
    (63.10, 63.90, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(6.06, 10.72), voice=None, drill_gain=1.0)

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
