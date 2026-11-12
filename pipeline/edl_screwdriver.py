"""Edit decision list for the MUROH DOOH Keelat mini cordless screwdriver (hands-only, motorcycle screw demo).

Times are seconds in the ORIGINAL recording. Each keep is (src_in, src_out, kind, note[, opts]).
- Hook: the screwdriver driving a motorcycle screw, motor running (30.0-33.05), under his own line
  "kalau korang nak buat pasang skru, buka skru dengan cepat" (85.22-88.27, J-cut; not repeated later).
- Torque: he says "lima Nm" (3.5 s) and later "lima puluh Nm" (18.6 s); every pass, prompted either way,
  keeps each as heard, so the speaker contradicts himself. Both torque lines are cut and no torque is shown
  until the owner confirms the real figure.
- Cut as unclear or repeated: "nak guna buat keluar je mata bit dia" (said again fully at 9.7 s), "Ok",
  "kalau korang nak buat pasal suhu/skru kawasan motor, apa, nak buat" (passes disagree; camera wanders),
  the first closing take ("boleh beli satu mini screwdriver daripada cordless").
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
    (0.00, 3.50, "exact", "Yang ni mini screwdriver, daripada Keelat."),
    (9.70, 17.15, "speech", "Kalau korang nak guna, nak guna mata bit dia, buat keluar, masuk sahaja, terus boleh guna."),
    (20.65, 21.70, "speech", "Jom kita tengok."),
    (23.20, 29.85, "speech", "Macam korang nak buat pasang skru, buka skru tu memang mudah. Nampak? Ha memang mudah kan."),
    (45.92, 50.70, "exact", "(unclear word cut) Pasal-pasal perabot dekat rumah, haa memang boleh sangat pakai yang ni."),
    (50.66, 54.30, "speech", "So kalau dah tak nak guna, kita boleh simpan."),
    (54.26, 63.85, "speech", "So yang ni kalau korang nak jadikan lurus pun boleh, tekan, pusing. Nampak? Nak jadikan bentuk asal balik, pusing, tekan, pusing."),
    (64.85, 70.75, "speech", "Yang ni dia datang dengan 30 pieces, korang tengok lah mata bit dia ni banyak macam-macam bentuk ada."),
    (71.35, 76.45, "speech", "Lepas tu ni cable yang dia bagi untuk charge pakai cable type C."),
    (77.05, 85.05, "speech", "Datang dengan casing macam ni. Yang ni brand daripada Keelat, sebelum ni dah habis stock, dah agak lama, sekarang baru restock."),
    (95.05, 97.62, "exact", "Boleh beli satu mini screwdriver ni."),
    (97.62, 98.40, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(30.00, 33.05), voice=(85.22, 88.27), drill_gain=0.5)

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
