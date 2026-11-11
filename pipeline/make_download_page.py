"""Build the iPhone download page for a finished MP4, byte-for-byte (no re-encode).

Artifacts serve files up to 15 MB each, so the MP4 is split into 14 MB parts published as
parts/partNN.mp4 next to a page that fetches them, checks every part's SHA-256, joins them
back into the identical file and hands it to the viewer through the `downloads` capability
(on iPhone: the share sheet -> Save Video).

usage: python3 pipeline/make_download_page.py <final.mp4> <out_dir> "<Heading>" "<Title>"
then publish <out_dir>/index.html with the Artifact tool:
  capabilities {"downloads": true}, root=<out_dir>,
  files {"parts/partNN.mp4": {"from": "parts/partNN.bin", "contentType": "video/mp4"}, ...}
  at most 4 parts (56 MB) per publish -> publish the same file_path again with the next 4.
Never modify or delete the source MP4.
"""
import base64, hashlib, json, os, subprocess, sys

src, out, heading, title = sys.argv[1:5]
tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "download_page.html")
os.makedirs(os.path.join(out, "parts"), exist_ok=True)
CHUNK = 14_000_000
meta, h_all = [], hashlib.sha256()
with open(src, "rb") as f:
    i = 0
    while True:
        b = f.read(CHUNK)
        if not b: break
        h_all.update(b)
        open(os.path.join(out, "parts", f"part{i:02d}.bin"), "wb").write(b)
        meta.append({"path": f"parts/part{i:02d}.mp4", "size": len(b), "sha": hashlib.sha256(b).hexdigest()})
        i += 1
total = sum(m["size"] for m in meta)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout.strip())
thumb = os.path.join(out, "thumb.jpg")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, dur - 3)), "-i", src, "-frames:v", "1",
                "-vf", "scale=360:640", "-q:v", "6", thumb], check=True)
page = open(tpl).read()
for k, v in {"__THUMB__": base64.b64encode(open(thumb, "rb").read()).decode(), "__PARTS__": json.dumps(meta),
             "__TOTAL__": str(total), "__NAME__": os.path.basename(src), "__TITLE__": title, "__HEADING__": heading,
             "__DUR__": f"{int(dur // 60)} min {round(dur % 60)} s", "__MB__": f"{total / 1e6:.0f}",
             "__FULLSHA__": h_all.hexdigest()}.items():
    page = page.replace(k, v)
open(os.path.join(out, "index.html"), "w").write(page)
print(json.dumps({"parts": len(meta), "bytes": total, "sha256": h_all.hexdigest(),
                  "files": {m["path"]: {"from": m["path"].replace(".mp4", ".bin"), "contentType": "video/mp4"} for m in meta}}, indent=1))
