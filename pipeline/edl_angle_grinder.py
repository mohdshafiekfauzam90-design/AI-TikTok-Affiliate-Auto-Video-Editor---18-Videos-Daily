"""Edit decision list for the MUROH DOOH Soarfly cordless angle grinder (hands-only demo, no presenter on camera).

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, kind, note[, opts]).
- Cuts are snapped to the quietest 10 ms frame within +-SNAP s, so no word is clipped.
- Pauses longer than MAX_GAP inside speech keeps are shrunk to KEEP_GAP (dead air removal).
- The hook is the opening shot in sync ("rate power 1400W, putaran per minit dia 12 ribu").
- The closing pitch ("jadi yang mana korang tengah mencari...", "yang ni 1400W 12000 RPM") is said
  two or three times with stumbles in between (whisper mis-hears the numbers as "RM14,000"); one clean
  take of each is kept. "tebal-tebal" vs "tempat-tempat" (10.8 s): three passes hear "tempat-tempat".
"""
import json, sys, wave, numpy as np

AUDIO = sys.argv[1]          # 16 kHz mono wav of the original
OUT = sys.argv[2]
SNAP, MAX_GAP, KEEP_GAP, THR_DB = 0.12, 0.30, 0.14, -38.0

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
    (7.62, 18.70, "speech", "Power gang. Yang ni kalau korang nak buat potong besi [unclear word cut] pun takde masalah. Angle grinder daripada Soarfly brushless motor, boleh adjust 3 level."),
    (18.70, 20.70, "demo", "presses the speed button (motor)", {"speed": 1.6}),
    (20.70, 24.55, "exact", "Level 1, level 2, level 3."),
    (24.85, 37.90, "speech", "Untuk yang ni gang korang juga akan dapat. Lepas tu aksesori yang dia bagi pun banyak... semua ada dekat sini."),
    (38.10, 46.30, "speech", "Yang ni handle, yang ni cover dia. Handle ni korang boleh letak kiri dan kanan mengikut kesesuaian kerja korang."),
    (46.85, 51.10, "speech", "Ni korang jangan risau, ni untuk buka mata dia."),
    (52.00, 59.85, "speech", "Satu charger. Bateri dia ni korang boleh pilih nak satu ataupun dua, kalau ada budget terus ambil 2 bateri senang buat extra."),
    (59.90, 66.21, "exact", "Jadi yang mana korang tengah mencari angle grinder cordless, nak yang power, boleh cuba brand daripada Soarfly ni."),
    (81.48, 84.45, "exact", "Yang ni 1400W, 12000 RPM."),
    (84.40, 87.55, "speech", "Jadi kalau korang nak, boleh tengok dekat beg dekat bawah."),
    (87.55, 88.30, "demo", "end plate under CTA"),
]
MANUAL_CUTS = [(10.78, 11.18)]   # "tebal-tebal" / "tempat-tempat": passes disagree, so the word is cut, not guessed
HOOK = dict(video=(0.00, 6.00), voice=None, drill_gain=1.0)

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
                half = KEEP_GAP / 2
                segs.append([cur, round(gs + half, 2), {}]); cur = round(ge - half, 2)
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
