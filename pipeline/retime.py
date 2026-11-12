"""Carry a finished edit over to a rebuilt spine (same cut list, edges widened by the tail guard).

    python3 pipeline/retime.py OLD_spine_map.json NEW_spine_map.json pipeline/gen_<x>.py pipeline/data/<x>/spine_transcript.json

Every spine time t maps through the source: old segment k holds t at source time src_in + (t - out_in);
the same source moment lands in new segment k at new_out_in + (src - new_src_in). Times before the end of
the hook (which the guard does not touch) stay put. Values that land within 0.06 s of a new cut snap onto it
(EMPH / REVEALS keys, C0 and scene boundaries must equal a cut). In the generator, decimal literals at or
after the hook end are treated as spine times (durations, scales and volumes in this codebase are all
smaller than the shortest hook), and TOONS durations are left alone. Word times in the transcript are
remapped too, so word indices, FIX and MANUAL_GROUPS keep working.
"""
import json, re, sys

old_map, new_map, gen_path, tx_path = sys.argv[1:5]
O = json.load(open(old_map))["segments"]; N = json.load(open(new_map))["segments"]
assert len(O) == len(N), f"segment count changed ({len(O)} -> {len(N)}): rebuild from the same edl.json"
H = N[1]["out_in"] if len(N) > 1 else 0.0          # hook end (segment 0 = hook, untouched)
old_end = json.load(open(old_map))["duration"]; new_end = json.load(open(new_map))["duration"]
CUTS = [s["out_in"] for s in N]

def remap(t):
    if t < H - 1e-6: return t
    if t >= old_end - 1e-6: return round(t - old_end + new_end, 3)        # held last frame, CTA tail
    k = max(i for i, s in enumerate(O) if s["out_in"] <= t + 1e-6)
    src = O[k]["src_in"] + (t - O[k]["out_in"])
    v = N[k]["out_in"] + (src - N[k]["src_in"])
    for c in CUTS:
        if abs(v - c) < 0.06: return round(c, 3)
    return round(v, 3)

# ---- generator literals
g = open(gen_path).read()
a = g.index("def r(x)")                                 # scene code starts after the helpers
head, body = g[:a], g[a:]
toon_ds = set()
for m in re.finditer(r'\("t-[\w-]+", "\w+", [\d.]+, ([\d.]+),', body): toon_ds.add(m.start(1))
def sub(m):
    if m.start(1) in toon_ds: return m.group(0)
    v = float(m.group(1))
    if v < H - 1e-6: return m.group(0)
    return f"{remap(v):g}" if "." in f"{remap(v):g}" else f"{remap(v):.1f}"
body = re.sub(r"(?<![\w.\-#])(\d+\.\d+)(?![\w.%])", sub, body)
head = re.sub(r"^(DUR = )([\d.]+)", lambda m: m.group(1) + f"{remap(float(m.group(2))):.3f}", head, flags=re.M)
head = re.sub(r'(caps\[0\]\["start"\], )([\d.]+)', lambda m: m.group(1) + f"{remap(float(m.group(2)))}", head)
head = re.sub(r"^(CTA_START = )([\d.]+)", lambda m: m.group(1) + f"{remap(float(m.group(2)))}", head, flags=re.M)
open(gen_path, "w").write(head + body)

# ---- transcript word times
d = json.load(open(tx_path))
for s in d["segments"]:
    for w in s["words"]:
        w["start"], w["end"] = remap(w["start"]), remap(w["end"])
    s["start"], s["end"] = remap(s["start"]), remap(s["end"])
d["retimed"] = f"word times carried from {old_map} to {new_map} (tail guard rebuild)"
json.dump(d, open(tx_path, "w"), ensure_ascii=False, indent=1)
print(f"retimed {gen_path}: hook end {H}, duration {old_end} -> {new_end}")
