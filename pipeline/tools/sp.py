import json,sys
v=sys.argv[1]; B=f"{v}/build/"
d=json.load(open(B+'spine_tx.json')); m=json.load(open(B+'spine_map.json'))
print([s['out_in'] for s in m['segments']], m['duration'])
i=0
for s in d['segments']:
    print(" ".join(f"{i+k}:{w['word'].strip()}[{w['start']:.2f}]" for k,w in enumerate(s['words']))); i+=len(s['words'])
