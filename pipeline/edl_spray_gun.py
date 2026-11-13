"""Edit decision list for the MUROH DOOH electric spray gun (500 W, 32000 RPM, 2.5 mm nozzle, 800 ml), presenter, 1:13.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: in sync, "korang boleh tengok semburan dia ni" over the spray (24.40-26.62).
Dropped: "model elektrik dengan cordless dua-dua dah restock", "tapi korang jangan risau dari segi motor dia, dari
segi watt dia power" (the spec line right after says it), and "jadi kalau korang dah guna spray gun ni, biasanya
lepas korang guna".
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
    (5.70, 14.20, "exact", "Jadi kalau korang nak bajet sikit, boleh ambil yang jenis spray gun elektrik macam ni, yang ni murah sikit daripada cordless."),
    (18.78, 24.38, "exact", "Untuk motor dia 500 watt, untuk RPM dia boleh pergi sampai 32000 RPM."),
    (26.62, 30.95, "exact", "Lepas tu boleh adjust kat depan ni."),
    (33.66, 48.02, "exact", "Untuk nozzle kat depan ni 2.5mm, kapasiti tank dia ni 800ml, boleh buka ni, yang ni boleh buka. Lepas tu dia pakai plug pin yang biasa kita guna je, plug 3 pin."),
    (48.06, 57.16, "exact", "Jadi kalau korang nak buat cat pagar rumah, cat dinding rumah, nak buat kerja dengan cepat, kena ada satu spray gun electric ni geng."),
    (61.62, 66.24, "exact", "Spray gun ni korang akan nampak perbezaan dia, cat korang lagi jimat."),
    (66.80, 71.66, "exact", "Harga tak mahal mana geng, jadi kalau korang berminat boleh tengok dekat beg dekat bawah."),
    (72.30, 73.00, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(24.40, 26.62), voice=None, drill_gain=1.0)

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
