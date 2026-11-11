"""Edit decision list for the MUROH DOOH Santino 4-in-1 jump starter with air pump video.

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
    (4.40, 9.10, "speech", "nak jumpstart kereta pun boleh, nak jadikan powerbank pun boleh."),
    (9.04, 15.45, "speech", "Kalau bateri ni habis, boleh cucuk juga dekat dalam kereta, pump ni juga boleh on."),
    (15.30, 20.55, "speech", "Dekat depan ni dia ada lampu suluh, kat sini siap boleh pegang macam ni."),
    (20.48, 27.05, "speech", "Memang cukup function, 4 in 1 jumpstarter daripada Santino."),
    (26.94, 37.00, "speech", "Jadi yang mana korang tak kisah sangat dari segi harga, tengah mencari jumpstart yang jenis berkualiti, boleh cuba brand daripada Santino ni."),
    (36.98, 42.72, "demo", "Yang ni 16000 mAh geng, memang bateri dia besar."),   # pause inside "16000 ... mAh"
    (48.30, 56.55, "speech", "Nak on dia dekat sini, tekan je lama-lama, dia akan keluar paparan dia macam ni. Jadi untuk U ni untuk adjust unit dia,"),
    (56.90, 63.55, "speech", "macam korang nak PSI, korang nak kPa ataupun kilogram, yang awal-awal ni bar."),
    (63.40, 74.35, "speech", "So untuk yang sebelah dia ni untuk adjust macam korang nak pump kereta, pump basikal, pump motor ataupun pump bola. Tambah tolak ni untuk adjust tekanan angin tayar."),
    (74.20, 79.55, "speech", "Lepas tu satu lagi untuk lampu dia pun terang tau, dia ada 3 mode:"),
    (79.50, 83.30, "demo", "ni mode yang pertama, yang kedua, ni yang ketiga (light modes shown)."),
    (84.80, 92.50, "speech", "So kalau ada in case malam-malam kereta problem ke, boleh guna lampu ni. Barang dia cantik."),
    (92.50, 104.20, "speech", "So kalau korang nak jadikan powerbank, ni dia, dia ada 3 port dekat sini tau: 2 port USB, 1 port untuk kabel type C. Ni kabel untuk charge dia pun dia dah bagi siap-siap."),
    (112.85, 115.10, "exact", "Yang ni dia datang dengan kotak macam ni,"),
    (115.00, 118.95, "speech", "jadi nak simpan dalam kereta boleh simpan guna kotak ni lah."),
    (124.20, 136.32, "exact", "Jadi yang mana korang nak standby satu letak dekat dalam kereta ke, nak standby satu letak dekat rumah ke, boleh je jump start with air pump ni daripada Santino, 4 dalam 1."),
    (136.40, 140.40, "exact", "Jadi kalau korang nak boleh tengok dekat beg dekat bawah, harga pun mampu milik je."),
]
MANUAL_CUTS = []
# Hook: in sync - the opening line while he holds it up: "korang boleh tengok, nak pump pun boleh".
HOOK = dict(video=(0.85, 4.42), voice=None, drill_gain=1.0)

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
