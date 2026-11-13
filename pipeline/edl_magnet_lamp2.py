"""Edit decision list for the MUROH DOOH magnetic work lamp, take 2 (360-degree head, 4 magnets), presenter, 1:12.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "memang kalau dah melekat tu memang susah nak jatuh" (33.64-36.98).
Dropped: "korang main besar lagi magnet dia" (unclear), the repeated "nampak / kuat ni", the second "bateri indicator"
line and the "untuk yang ni kalau korang" false start of the closer.
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
    (0.00, 3.34, "exact", "(Lampu) ni dia boleh pusing 360 darjah, nampak?"),
    (5.00, 16.42, "exact", "Lepas tu dia ada 3 mode korang boleh adjust. Ni mode yang pertama, yang kedua, yang ketiga. Yang kedua tu dia macam kuning-kuning sikit, yang ketiga tu macam warna kuning putih, warna warm-warm sikit."),
    (16.80, 20.50, "exact", "Lepas tu dia ada magnet tau, magnet dia kuat ni."),
    (23.12, 29.14, "exact", "Dia ada 4 biji magnet. Jadi mana-mana tempat yang ada besi, dia boleh melekat."),
    (37.50, 41.00, "exact", "Lepas tu dekat belakang ni dia ada bateri indicator dia."),
    (43.62, 48.62, "exact", "Dia ada 2 port, 1 port USB, 1 port untuk kabel Type-C. Dia ada 2 hook."),
    (48.70, 51.78, "exact", "Yang ni dia ada banyak pilihan warna, dia ada warna merah."),
    (53.24, 70.78, "exact", "Jadi yang mana korang selalu pomen-pomen kereta tu ataupun nak pomen motor, boleh sangat pakai lampu ni. Kalau kereta tu nak baiki engine, boleh letak dekat hood, sebab apa dia ada magnet, memang sangat sesuai. Jadi kalau korang berminat dengan lampu ni, boleh tengok dekat beg dekat bawah, harga murah je."),
    (71.10, 71.80, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(33.64, 36.98), voice=None, drill_gain=1.0)

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
