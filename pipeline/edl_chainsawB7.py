"""Edit decision list for the MUROH DOOH 52cc 2-stroke petrol chainsaw, 18 / 20 / 22" (presenter crouching, take 2), 1:24.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "yang macam kat depan saya ni, yang paling panjang 22 inci" (29.70-34.28, his second take).
Dropped: "ok gang", the two fumbled "untuk yang ni chainsaw harga bajet" starts (the third is kept), the first "yang macam saya
pegang ni yang paling panjang" take, "dah boleh nampak", "jadi kat sini, jadi" and the long pauses.
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
    (17.44, 27.46, "exact", "Chainsaw harga bajet, dia ada 3 size korang boleh pilih, 18 inci, 20 inci dengan 22 inci.", {"edge": "keep"}),
    (35.66, 40.36, "exact", "So yang ni jenis 2 stroke, 52cc.", {"edge": "keep"}),
    (45.94, 64.74, "exact", "Kat sini tempat nak masuk minyak hitam, function dia untuk basahkan rantai ni, jadi dia bagi pelincir dekat rantai ni, rantai pun boleh pakai lama. Lepas tu yang ni untuk masuk petrol, kat sini on off dia, lepas tu kat sini choke dia gang.", {"edge": "keep"}),
    (65.40, 81.92, "exact", "Jadi yang mana korang tengah mencari chainsaw nak buat trim pokok dekat kebun ke dekat rumah ke, nak cari yang harga bajet, serious korang boleh sangat pakai yang ni, murah je gang, murah je, jadi kalau korang berminat boleh tengok dekat beg dekat bawah."),
    (81.96, 82.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(29.70, 34.28), voice=None, drill_gain=1.0)

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
