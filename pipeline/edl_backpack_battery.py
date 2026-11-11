"""Edit decision list for the MUROH DOOH Santino 21V backpack battery video.

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
    (10.80, 22.70, "speech", "Contoh kalau korang nak buat kerja untuk jangka masa yang lama, pakai bateri macam ni memang sekejap je lah habis kan, tak lama, mungkin 40 minit, 1 jam kan."),
    (23.40, 28.90, "speech", "Korang boleh beli bateri yang saya pikul ni, sekejap lagi saya tunjuk dekat dalam dia macam mana."),
    (30.10, 36.60, "exact", "Ni dia datang siap dengan apa dia punya kabel dah ni, panjang dia ni lebih kurang dalam 1 meter."),
    (37.85, 39.30, "speech", "Masuk je dekat sini."),
    (53.45, 56.25, "speech", "Yang ni brand daripada Santino."),
    (56.16, 61.25, "speech", "Jom saya tunjuk macam mana dekat dalam. Kat dalam dia macam ni, yang ni"),
    (63.95, 66.85, "speech", "korang jangan risaulah, untuk bag dia ni dia dah bagi siap-siap."),
    (71.40, 73.35, "speech", "Dia punya cable ni korang boleh buka,"),
    (75.45, 77.82, "exact", "dia plug macam ni, plug 3 pin."),
    (92.40, 95.10, "demo", "battery indicator lighting up (fillers muted, 1.3x)", {"speed": 1.3, "gain": 0}),
    (95.10, 98.10, "exact", "Jadi untuk bila korang guna, dia pun keluar bateri indicator dia."),
    (99.60, 100.45, "exact", "Nampak kat sini."),
    (108.55, 112.50, "speech", "Kalau pakai bateri yang biasa tu cepat habis, korang boleh upgrade bateri ni."),
    (114.30, 118.25, "speech", "Korang juga akan dapat sekali dengan apa? Bag dia ni."),
    (118.50, 120.28, "exact", "Satu lagi charger."),
    (121.58, 126.95, "speech", "Lepas tu untuk charger dia tak sama tau macam yang biasa tu, ni dia besar sikit."),
    (136.75, 141.25, "speech", "Nak buat kerja untuk jangka masa yang lama, kena ada bateri ni satu."),
    (141.45, 143.10, "speech", "Boleh tengok dekat beg dekat bawah."),
    (143.10, 143.75, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
# Hook: the chainsaw running off the backpack battery, then the backpack shown, under his own line
# "jadi yang ni memang boleh ambil masa yang lama lah, berjam-jam korang boleh guna" (motor kept low under it).
HOOK = dict(video=(40.00, 45.20), voice=(47.30, 52.50), drill_gain=0.35)

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
