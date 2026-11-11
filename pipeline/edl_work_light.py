"""Edit decision list for the MUROH DOOH Santino 20V work light video.

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
    (1.00, 14.60, "speech", "Yang ni work light daripada Santino. Size 10 inch. Haa ni dia, penuh dengan LED. Yang ni dia ada 2 level korang boleh adjust. Ni level 1. Level 2."),
    (15.90, 22.98, "speech", "Level 2 dia lagi kembang. Untuk yang ni dia dapat cover lebih kurang dalam 10 meter."),
    (27.70, 33.56, "speech", "Dia pakai bateri jenis tapak makita. Kalau korang full charge, kalau korang pakai level 1, dia boleh bertahan"),
    (36.66, 41.92, "speech", "lebih kurang dalam 3 hingga 4 jam untuk satu bateri yang dia bagi."),
    (59.90, 63.80, "demo", "Untuk maksimum power dia, 50W."),   # pause inside "lima puluh watt"
    (68.35, 72.55, "speech", "Yang ni boleh adjust tau, untuk kepala dia ni, untuk angle dia ni boleh."),
    (72.62, 78.40, "demo", "head-angle adjust demo, 2x, muted", {"speed": 2.0, "gain": 0}),
    (79.45, 85.22, "speech", "So untuk tapak dia ni jenis aluminium, jadi memang ringan."),
    (87.98, 94.30, "exact", "Jadi total berat lampu dengan bateri ni lebih kurang dalam 1kg. Ok lah tak berat mana pun."),
    (94.22, 99.25, "speech", "Jadi yang ni kalau korang nak buat aktiviti outdoor, nak pergi camping, nak bawa pergi ni."),
    (108.65, 113.24, "demo", "Lepas tu untuk color temperature dia 6500K."),   # pauses inside the number
    (113.32, 118.58, "speech", "Lepas tu kalau korang nak buat charge telefon pun boleh dekat sini. Dia ada 2 port USB."),
    (118.68, 122.50, "speech", "Maknanya lampu ni boleh dijadikan power bank."),
    (122.58, 133.55, "speech", "Jadi kalau kat rumah korang tu dah ada bateri tapak jenis makita, tak perlu beli sekali dengan bateri. Korang beli je lampu sahaja, lagi jimat."),
    (135.65, 138.05, "speech", "Jadi yang mana korang tengah mencari work light,"),
    (140.90, 143.50, "speech", "boleh beli satu work light daripada Santino."),
]
MANUAL_CUTS = []
# Hook: the light blazing at the camera (flash-forward of the level-2 demo) under the speaker's
# own closing line "korang jangan risau, memang terang, dia boleh cover lebih kurang dalam 10 meter".
HOOK = dict(video=(15.60, 20.32), voice=(143.64, 148.36), drill_gain=0.25)

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
