"""Cut the original recording into the 1080x1920 / 30 fps spine following build/edl.json.
Each segment is rendered on its own (frame-accurate seek, re-encode), then concatenated,
so memory stays flat. Original voice kept; the hook = demo picture + the speaker's own
line over ducked drill sound (or, with "voice": null, a plain in-sync shot). Every audio
piece gets 8 ms fades so jump cuts never click. A segment may carry "speed" (picture and
sound sped up together, pitch kept) and "gain" (0 mutes a repeated line under a demo)."""
import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
src, edl, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(edl)); tmp = os.path.join(os.path.dirname(out), "segs"); os.makedirs(tmp, exist_ok=True)
V = "scale=1080:1920:flags=lanczos,fps=30,setsar=1,format=yuv420p"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p",
       "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]

def run(cmd): subprocess.run(["ffmpeg", "-v", "error", "-y", "-threads", "2"] + cmd, check=True)

def hook():
    if not d["hook"].get("voice"):                    # in-sync hook: an ordinary segment
        return seg(0, {"src_in": d["hook"]["video"][0], "src_out": d["hook"]["video"][1]})
    hv0, hv1 = d["hook"]["video"]; ha0, ha1 = d["hook"]["voice"]; L = round(hv1 - hv0, 3)
    g = d["hook"]["drill_gain"]
    run(["-ss", str(hv0), "-t", str(L), "-i", src, "-ss", str(ha0), "-t", str(ha1 - ha0), "-i", src,
         "-filter_complex",
         f"[0:v]{V}[v];[0:a]volume={g}[d];[1:a]afade=t=in:d=0.03,apad=whole_dur={L}[s];"
         f"[d][s]amix=inputs=2:normalize=0,atrim=0:{L},afade=t=out:st={L-0.04}:d=0.04[a]",
         "-map", "[v]", "-map", "[a]", "-t", str(L)] + ENC + [f"{tmp}/s000.mov"])
    return f"{tmp}/s000.mov"

def seg(i, s):
    a, b = s["src_in"], s["src_out"]; dur = round(b - a, 3); o = f"{tmp}/s{i:03d}.mov"
    sp, g = s.get("speed", 1), s.get("gain", 1)
    od = round(dur / sp, 3)                           # output length
    vf = (f"setpts=PTS/{sp}," if sp != 1 else "") + V
    af = (f"atempo={sp}," if sp != 1 else "") + (f"volume={g}," if g != 1 else "") + \
         f"afade=t=in:d=0.008,afade=t=out:st={od-0.008:.3f}:d=0.008"
    run(["-ss", str(a), "-t", str(dur), "-i", src, "-vf", vf, "-af", af, "-t", str(od)] + ENC + [o])
    return o

with ThreadPoolExecutor(2) as ex:
    futs = [ex.submit(hook)] + [ex.submit(seg, i + 1, s) for i, s in enumerate(d["segments"])]
    files = [f.result() for f in futs]
lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "medium", "-crf", "16",
     "-g", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
print("wrote", out)

# Record where every segment really lands (frame-rounded) for overlays and punch-ins.
def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=nb_frames", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()) / 30
t, cuts = 0.0, []
srcs = [tuple(d["hook"]["video"])] + [(s["src_in"], s["src_out"]) for s in d["segments"]]
for f, (a, b) in zip(files, srcs):
    cuts.append({"out_in": round(t, 3), "src_in": a, "src_out": b}); t += dur(f)
json.dump({"duration": round(t, 3), "segments": cuts}, open(out.rsplit(".", 1)[0] + "_map.json", "w"), indent=1)
print("map written, duration", round(t, 3))
