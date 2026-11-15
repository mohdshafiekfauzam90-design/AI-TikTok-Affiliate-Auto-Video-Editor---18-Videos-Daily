"""Edit decision list for the MUROH DOOH cordless brushless angle grinder 5" kit (hands-only), 1:08.

Times are seconds in the ORIGINAL recording. Owner's rule: 30 s - 1 min, key points only, never clip a word ending.
- Hook: the grinder spinning up (19.80-22.70, its own sound muted) under his line "nampak tak perbezaan dia, memang sangat
  ketara" (11.26-14.16, J-cut; not repeated later).
Dropped: "ok", "ok sekarang boleh tengok" (the hook shows it), "lepas tu yang ni" lead-ins and the long pauses.
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
    (0.60, 4.40, "exact", "Yang ni angle grinder size 5 inci,"),
    (4.40, 11.26, "exact", "mata dia besar tau daripada mata angle grinder yang biasa, yang ni yang biasa, yang ni 5 inci.", {"edge": "keep"}),
    (14.18, 18.16, "exact", "Yang ni brushless motor, boleh adjust 4 level."),
    (22.20, 28.22, "exact", "Ni level 1, level 2, level 3, level 4."),
    (30.12, 37.40, "exact", "Untuk handle ni kan korang boleh letak kiri dan kanan mengikut kesesuaian kerja korang. Lepas tu ni accessory yang korang akan dapat."),
    (40.72, 50.24, "exact", "Ni mata-mata yang korang akan dapat, mata potong kayu, mata polish, mata gosok, mata potong besi, semua ada, nampak barang dia ni cun kan, cun."),
    (51.30, 57.76, "exact", "Untuk bateri dia ni korang boleh pilih nak satu ataupun dua, kalau korang ada budget terus ambil dua bateri, senang buat extra."),
    (57.80, 66.88, "exact", "Jadi yang mana korang tengah mencari angle grinder, nak mata saiz besar, boleh ambil yang ni, saiz 5 inci. Jadi kalau korang nak boleh tengok dekat beg dekat bawah."),
    (66.92, 67.70, "demo", "end plate under CTA"),
]
MANUAL_CUTS = []
HOOK = dict(video=(19.80, 22.70), voice=(11.26, 14.16), drill_gain=0.0)

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
