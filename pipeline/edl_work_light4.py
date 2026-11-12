"""Edit decision list for the MUROH DOOH Santino 10" cordless work light (Makita-type battery base), presenter on camera, 1:24.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the lamp lit up against the wall (27.10-31.00) under his line "dia boleh cover lebih kurang dalam
  10 meter" (21.48-25.38, J-cut, original sound muted; the line is not repeated later).
Dropped: "Yang besar, pembukaan lampu dia. Nampak?" (under the hook picture) and the two repeated USB-port lines,
the first "tapak boleh adjust" and the repeated "untuk tapak dia ni korang boleh adjust" line.
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
    (0.00, 20.05, "exact", "Kalau korang nak jimat boleh beli kepala dia sahaja, make sure korang dah ada bateri jenis tapak Makita dekat rumah. Tak kisah jenama apa, semua boleh masuk jenis tapak Makita. Yang ni guys work light daripada Santino, saiz 10 inci. Korang boleh tengok penuh dengan LED."),
    (31.00, 44.85, "speech", "Dia ada dua level korang boleh adjust. Level satu tu pembukaan dia kecil sikit, level dua tu dia lagi luas. Lepas tu kat sini dia ada dua port USB, kalau korang nak buat charge telefon pun boleh pakai."),
    (61.55, 66.40, "speech", "Tapak dia boleh adjust, macam-macam bentuk, macam-macam kedudukan korang boleh."),
    (70.90, 82.70, "speech", "Jadi yang mana korang tengah mencari work light, nak buat kerja tak cukup pencahayaan, untuk abang-abang tukang, abang-abang kontraktor, boleh beli satu yang ni. Harga tak mahal mana pun. Boleh tengok dekat beg dekat bawah."),
    (82.90, 83.60, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(27.10, 31.00), voice=(21.48, 25.38), drill_gain=0.0)

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
                segs.append([cur, round(gs + tail, 2), {}]); cur = round(ge - lead, 2)
            j = k
        else:
            j += 1
    segs.append([cur, e2, {}])

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
