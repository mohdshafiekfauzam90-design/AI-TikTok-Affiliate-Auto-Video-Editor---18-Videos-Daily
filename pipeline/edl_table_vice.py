"""Edit decision list for the MUROH DOOH table vice (ragum 3-8 inci) video.

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, label).
- Cuts are snapped to the quietest 10 ms frame within +-SNAP s, so no word is clipped.
- Pauses longer than MAX_GAP inside speech keeps are shrunk to KEEP_GAP (dead air removal).
- The hook plays brick-breaking footage with the speaker's own line laid over it (J-cut);
  that line is NOT repeated later.
Outputs build/edl.json (segments + time map) used by build_spine.sh and captions.py.
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
    (1.48, 7.78, "demo", "Untuk table vice ni, yang ni dia ada 3, 4, 5, 6 dengan 8 inci."),   # pauses between sizes kept
    (7.70, 11.85, "speech", "Yang macam saya guna ni, 8 inci yang paling besar."),
    (11.90, 16.55, "speech", "Korang boleh tengok yang ni memang besi padu, bila kita angkat memang terasa berat."),
    (21.05, 23.95, "speech", "Korang longgar je 2 skru dekat sini,"),
    (25.63, 30.50, "demo", "kiri dan kanan ni. Dia boleh pusing... 360 darjah (rotation shown in the pause)."),
    (30.30, 41.80, "speech", "Kat sini normal kan, korang boleh tutup buka. Lepas tu kat sini dia ada satu petak besar untuk ketuk-ketuk. Besi dia memang tebal, korang boleh tengok tu. Kalau korang nak buat ketuk kuat-kuat pun tak ada masalah."),
    (41.58, 44.40, "speech", "Yang ni industri grade, nak letak dekat bengkel,"),
    (47.25, 50.90, "speech", "nak letak dekat rumah, nak buat kerja-kerja DIY."),
    (61.10, 66.35, "speech", "Kalau korang nak menggosok, nak memotong, tak ada orang tolong, boleh beli satu table vice ni geng."),
    (66.15, 74.95, "speech", "Kualiti memang sangat-sangat cantik, harga pun tak mahal mana. Korang boleh survey dulu table vice ni dekat kedai luar, confirm tak dapat harga macam dekat beg saya ni."),
    (75.35, 81.85, "speech", "Jadi korang boleh pilih. Kalau untuk rumah tak perlu ambil sampai 8 inci, korang ambil size 4, 5 pun dah cukup dah."),
    (81.65, 85.05, "speech", "Jadi kalau korang nak, boleh tengok dekat beg dekat bawah, harga murah je."),
    (85.05, 85.80, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
# Hook: the vise swung round on its base (flash-forward of the 360 demo) under his own line
# "yang paling best, yang ni dia boleh pusing 360 darjah".
HOOK = dict(video=(27.00, 31.25), voice=(16.55, 20.80), drill_gain=0.25)

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
