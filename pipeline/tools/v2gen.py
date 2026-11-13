# v2gen.py vNN "prompt" s-e s-e ... : write vNN/tx/v2.py (prompted + unprompted passes on the given spans)
import sys
v, P, spans = sys.argv[1], sys.argv[2], [tuple(map(float, a.split("-"))) for a in sys.argv[3:]]
open(f"{v}/tx/v2.py", "w").write(f'''import whisper
m = whisper.load_model("large-v3", device="cpu")
a = whisper.load_audio("src/a16.wav")
P = {P!r}
for s,e in {spans!r}:
    for p in [None, P]:
        r = m.transcribe(a[int(s*16000):int(e*16000)], language="ms", temperature=0.0, condition_on_previous_text=False, fp16=False, initial_prompt=p)
        print(f"{{s}}-{{e}} [{{'P' if p else '-'}}] {{r['text']!r}}", flush=True)
''')
