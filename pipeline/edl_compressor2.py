"""Edit decision list for the MUROH DOOH silent air compressor, take 2 (hands only, 1:38).

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the compressor running (44.00-46.70) under his line "jenis silent, memang tak mengganggu jiran-jiran"
  (90.10-92.75, J-cut, machine low under it; not repeated later).
Dropped: the opening tank-size attempt (he says on camera "yang tadi tu delete"), "dia ada 3 model tank berbeza
size", "angin dia kuat", the second "memang tak bising", "kategori laju", the 8-litre "carburetor / poman motor"
line (unclear) and the duplicated "satu set".
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
    (12.05, 25.16, "exact", "Untuk kapasiti tank dia, dia ada 3 model. Yang saya pegang ni, yang kat depan saya ni size 8 liter, satu lagi korang boleh pilih 30 liter, satu lagi 50 liter."),
    (28.66, 38.60, "exact", "Jadi untuk yang ni jenis silent, free oil, tak perlu pun nak jaga minyak. Jadi senang cerita, jenis free maintenance lah. Korang boleh dengar bunyi dia, memang tak bising."),
    (50.50, 58.06, "exact", "Untuk saiz 8 liter ni dia nak ambil masa penuh satu tank ni lebih kurang dalam 1 minit."),
    (59.24, 67.56, "exact", "Jadi kalau korang beli, korang juga akan dapat sekali dengan nozzle dia, satu set lah, satu set korang akan dapat semuanya, balik terus boleh guna."),
    (77.22, 86.16, "exact", "Tapi kalau korang ada bajet, terus ambil yang 30 ataupun 50 liter, nak buat cat motor, cat kereta, 30 ke atas lah, lagi sesuai."),
    (86.18, 89.18, "exact", "Harga tak mahal mana, kualiti cantik je kan."),
    (93.12, 95.64, "exact", "Jadi kalau korang berminat boleh tengok dekat beg dekat bawah."),
    (96.00, 96.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(44.00, 46.70), voice=(90.10, 92.75), drill_gain=0.4)

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
