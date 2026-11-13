import json,sys
d=json.load(open(sys.argv[1]))
for s in d['segments']:
    w=s['words']; print(f"{w[0]['start']:.2f}-{w[-1]['end']:.2f} {s['text'].strip()}")
