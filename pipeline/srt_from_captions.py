"""Write projects/<proj>/captions_ms.srt from pipeline/data/<data>/captions.json (the burned-in caption groups).
    python3 pipeline/srt_from_captions.py <data> <proj>"""
import json, sys
data, proj = sys.argv[1:3]
def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
g = json.load(open(f"pipeline/data/{data}/captions.json"))
open(f"projects/{proj}/captions_ms.srt", "w").write("".join(
    f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n\n" for i, c in enumerate(g, 1)))
print(len(g), "captions")
