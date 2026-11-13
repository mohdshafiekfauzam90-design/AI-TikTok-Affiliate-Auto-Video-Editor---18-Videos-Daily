import json,sys
d=json.load(open(sys.argv[1]))
for s in d['segments']:
    print(" ".join(f"{w['word'].strip()}[{w['start']:.2f}-{w['end']:.2f}]" for w in s['words']))
