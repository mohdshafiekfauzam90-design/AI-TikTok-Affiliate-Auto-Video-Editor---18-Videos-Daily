"""Edit decision list for the MUROH DOOH Santino 10" cordless work light, hands-only take (1:15).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the lamp lit against the wall during the level demo (7.50-10.05) under his line "serius, lampu dia memang
  terang" (67.10-69.64, J-cut, original sound muted; cut from the closer so it is not heard twice).
Dropped: the first "level 1, level 2, nampak perbezaan" lines (under the hook picture), the "bateri jenis power
tool" false start, the repeated "untuk tapak dia ni korang boleh adjust" line.
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
    (10.40, 28.40, "exact", "Kalau level 2 ni pembukaan dia lagi luas sikit lah, level 1 dia kecil sikit. So yang ni work light daripada Santino saiz 10 inci. Jadi yang mana korang buat kerja tak cukup pencahayaan, tengah mencari lampu kerja, boleh ambil yang ni."),
    (28.30, 33.30, "exact", "Tak pakai wire, senang nak bawa ke mana-mana. Dia pakai bateri jenis tapak Makita."),
    (37.40, 47.48, "exact", "Kalau kat rumah korang dah ada bateri jenis tapak Makita, boleh beli kepala dia saja. Kalau tak ada bateri lagi, beli sekali dengan bateri."),
    (48.50, 52.55, "exact", "Masuk je dekat belakang ni, terus boleh guna."),
    (53.75, 56.86, "exact", "Untuk tapak dia ni macam-macam bentuk boleh adjust tau."),
    (61.85, 67.06, "exact", "Jadi yang mana korang tengah mencari work light, boleh beli satu yang ni."),
    (69.66, 72.05, "exact", "Kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (72.30, 73.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(7.50, 10.05), voice=(67.10, 69.64), drill_gain=0.0)

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
