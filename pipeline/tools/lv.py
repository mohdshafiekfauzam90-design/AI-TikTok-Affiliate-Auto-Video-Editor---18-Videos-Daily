import wave,numpy as np,sys
w=wave.open(sys.argv[1]);a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
for sp in sys.argv[2:]:
    s,e=map(float,sp.split('-'))
    print(f"{sp}:"," ".join(f"{t:.2f}:{20*np.log10(np.sqrt(np.mean(a[int(t*16000):int(t*16000)+320]**2))+1e-9):.0f}" for t in np.arange(s,e,0.04)))
