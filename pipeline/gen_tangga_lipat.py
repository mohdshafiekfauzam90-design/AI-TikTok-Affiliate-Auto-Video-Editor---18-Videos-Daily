"""Generate the HyperFrames project (projects/tangga-lipat/) for the MUROH DOOH folding-ladder TikTok.

Inputs (pipeline/data/tangga_lipat):
  spine_transcript.json  whisper large-v3 word timings measured on the cut spine (output time)
  spine_map.json         where every cut lands in output time
Outputs: projects/tangga-lipat/index.html + compositions/*.html

Every on-screen claim below is something the speaker says in the recording; nothing is
invented (no price, no discount, no specs that are not spoken).
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT = os.path.join(ROOT, "projects", "tangga-lipat")
DATA = os.path.join(ROOT, "pipeline", "data", "tangga_lipat")
W, H, FPS = 1080, 1920, 30
DUR = 62.0                       # spine (60.77 s) + 1.2 s held last frame under the CTA

tx = json.load(open(os.path.join(DATA, "spine_transcript.json")))
cmap = json.load(open(os.path.join(DATA, "spine_map.json")))
CUTS = [s["out_in"] for s in cmap["segments"]] + [cmap["duration"]]

# --------------------------------------------------------------------------- captions
words, SEG_START = [], set()
for seg in tx["segments"]:
    SEG_START.add(len(words)); words.extend(seg["words"])
# ASR slips checked against two passes on the original audio + standard Malay spelling.
# 51 "tipas" in context "bersih lampu, tukar kipas"; 90-92 "memang lah wah" = "memang lawa";
# 158-159 "baru minat" = "berminat"; 163 "back" = "beg"; 165 "awah" = "bawah".
FIX = {51: "kipas", 90: "memang", 91: "lawa", 92: "", 158: "berminat", 159: "", 163: "beg", 165: "bawah"}
W_ = []
for i, w in enumerate(words):
    t = FIX.get(i, w["word"].strip())
    if t == "": continue                                # merged into the previous fix
    if t.startswith("-") and W_:                       # "lama" "-lama" -> "lama-lama"
        W_[-1]["text"] += t; W_[-1]["end"] = w["end"]; W_[-1]["punct"] = bool(re.search(r"[.,!?]$", t)); continue
    W_.append({"i": i, "seg0": i in SEG_START, "text": t, "start": w["start"], "end": w["end"], "punct": bool(re.search(r"[.,!?]$", t))})
for w in W_:
    w["text"] = re.sub(r"[.,!?]+$", "", w["text"]).upper()
    if w["end"] - w["start"] > 0.6 and not w["text"][0].isdigit():                   # whisper folds pauses into a word's start
        w["start"] = round(w["end"] - 0.42, 2)
HOOK_END = 2.3
cap_words = [w for w in W_ if w["i"] >= 9]   # words 0-8 = hook line, shown as kinetic type

# Caption groups set by hand for this video (spine word indices, inclusive): natural Malay
# phrases, a number always with "STEP", the hook line left to the kinetic type.
MANUAL_GROUPS = [(9, 12), (13, 15), (16, 19), (20, 21), (22, 24), (25, 27), (28, 29), (30, 33), (34, 35),
    (36, 38), (39, 41), (42, 45), (46, 49), (50, 51), (52, 54), (55, 57), (58, 61), (62, 63), (64, 66),
    (67, 70), (71, 73), (74, 77), (78, 81), (82, 83), (84, 87), (88, 89), (90, 92), (93, 95), (96, 98),
    (99, 101), (102, 103), (104, 107), (108, 110), (111, 114), (115, 116), (117, 119), (120, 122),
    (123, 125), (126, 128), (129, 132), (133, 135), (136, 139), (140, 142), (143, 145), (146, 149),
    (150, 152), (153, 154), (155, 159), (160, 162), (163, 165)]
groups = [[w for w in W_ if a <= w["i"] <= b] for a, b in MANUAL_GROUPS]
groups = [g for g in groups if g]
assert sum(len(g) for g in groups) == len(cap_words), "every caption word in exactly one group"
caps = []
for g in groups:
    caps.append({"start": round(g[0]["start"] - 0.04, 2), "end": round(g[-1]["end"] + 0.12, 2), "words": g})
caps[0]["start"] = max(caps[0]["start"], 2.34)        # after the hook's kinetic line
CTA_START = 57.5                                       # the CTA card says the closing line itself
caps = [c for c in caps if c["start"] < CTA_START - 0.2]
caps[-1]["end"] = min(caps[-1]["end"], CTA_START)
for a, b in zip(caps, caps[1:]):                       # one group on screen at a time
    if a["end"] > b["start"]: a["end"] = b["start"]
    if a["end"] - a["start"] < 0.35: a["end"] = min(a["start"] + 0.35, b["start"])

# ------------------------------------------------------------------------- shared CSS
TOKENS = """
      :root { --yellow:#FFD21F; --red:#E5252A; --ink:#0D0D0D; --white:#FFFFFF; }
"""
TEXT_FX = """
      .hf-stroke { paint-order: stroke fill; -webkit-text-stroke: 14px var(--ink); }
"""

def scene(cid, start, dur, body_html, css, js, track):
    """Write compositions/<cid>.html and return the host tag for index.html."""
    doc = f"""<template>
  <style>
{TOKENS}{TEXT_FX}
      #{cid} {{ position:absolute; inset:0; font-family:'Inter',sans-serif; color:var(--white); }}
{css}
  </style>
  <div id="{cid}" data-composition-id="{cid}" data-width="{W}" data-height="{H}">
{body_html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""
    os.makedirs(os.path.join(EDIT, "compositions"), exist_ok=True)
    open(os.path.join(EDIT, "compositions", f"{cid}.html"), "w").write(doc)
    kind = "captions" if cid == "captions" else "graphics"
    return (f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" '
            f'data-start="{start}" data-duration="{dur}" data-track-index="{track}" data-track-kind="{kind}" '
            f'data-width="{W}" data-height="{H}"></div>')

def r(x): return round(x, 3)

hosts = []

# Info cards live in a band just above the captions (y 840-1110): the presenter's face sits
# in the top half of most shots, so nothing is drawn over it.
CARD_CSS = """
      .band { position:absolute; left:56px; right:150px; top:850px; }
      .card { display:inline-flex; flex-direction:column; gap:10px; background:rgba(13,13,13,.84);
        border-left:12px solid var(--yellow); border-radius:22px; padding:20px 26px; box-shadow:0 16px 36px rgba(0,0,0,.35); }
      .card .k { font-weight:900; font-size:30px; letter-spacing:.08em; color:var(--yellow); }
      .card .v { font-family:'Archivo Black','Inter',sans-serif; font-size:64px; line-height:1; }
      .row { display:flex; flex-wrap:wrap; gap:12px; }
      .chip { display:inline-flex; align-items:center; gap:12px; background:var(--yellow); color:var(--ink); font-weight:900;
        font-size:42px; padding:10px 22px; border-radius:14px; opacity:0; }
      .chip.dark { background:var(--white); }
      .tick { display:inline-flex; align-items:center; justify-content:center; width:46px; height:46px; border-radius:50%;
        background:var(--ink); color:var(--yellow); font-size:28px; }
      .sticker { position:absolute; right:70px; top:700px; background:var(--red); color:var(--white);
        font-family:'Archivo Black','Inter',sans-serif; font-size:58px; padding:14px 28px; border-radius:16px;
        border:5px solid var(--white); box-shadow:0 14px 30px rgba(0,0,0,.4); }
"""
def card_in(sel, t):  return f'    tl.fromTo("{sel}", {{ x: -70, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {r(t)});\n'
def card_out(sel, t): return f'    tl.to("{sel}", {{ x: -40, opacity: 0, duration: 0.2, ease: "power3.in" }}, {r(t)});\n'
def chip_in(sel, t):  return f'    tl.fromTo("{sel}", {{ scale: 0.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.4)" }}, {r(t)});\n'

# ------------------------------------------------------------------ 1. HOOK (0 - 2.333)
HK = 2.333
hook_html = f"""    <div id="hook-top" class="clip" data-start="0" data-duration="{HK}" data-track-index="1">
      <div id="hook-title"><span class="hf-stroke">TANGGA LIPAT</span></div>
      <div id="hook-steps"><span>4&ndash;8</span>STEP</div>
    </div>
    <div id="hook-b0" class="clip hook-beat" data-start="0.26" data-duration="1.32" data-track-index="2"><span class="hf-stroke">JANGAN RISAU!</span></div>
    <div id="hook-b1" class="clip hook-beat" data-start="1.58" data-duration="{r(HK-1.58)}" data-track-index="2"><span class="hf-stroke">TAHAN LASAK!</span></div>
"""
hook_css = """
      #hook-top { position:absolute; left:0; right:0; top:206px; text-align:center; }
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:124px; line-height:1.02; margin-top:0;
        text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-steps { display:inline-flex; align-items:baseline; gap:14px; margin-top:12px; background:var(--red); padding:6px 26px 10px;
        border-radius:14px; transform:rotate(-3deg); font-family:'Archivo Black','Inter',sans-serif; font-size:48px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
      #hook-steps span { font-size:96px; color:var(--yellow); }
      .hook-beat { position:absolute; left:40px; right:40px; top:1080px; text-align:center; font-family:'Archivo Black','Inter',sans-serif;
        font-size:118px; line-height:1; color:var(--white); }
      #hook-b1 { color:var(--yellow); font-size:130px; }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.12 }, { scale: 1, duration: 0.5, ease: "expo.out" }, 0);
    tl.fromTo("#hook-steps", { scale: 0.6, rotation: -14 }, { scale: 1, rotation: -3, duration: 0.45, ease: "back.out(2.2)" }, 0.1);
    tl.fromTo("#hook-b0 span", { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.24, ease: "expo.out" }, 0.26);
    tl.fromTo("#hook-b1 span", { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.24, ease: "expo.out" }, 1.58);
    tl.to("#hook-top", { y: -26, opacity: 0, duration: 0.2, ease: "power3.in" }, 2.11);
"""
hosts.append(scene("hook", 0, HK, hook_html, hook_css, hook_js, 10))

# ------------------------------------------------------------- 2. STEPS (2.333 - 12.3)
S0 = 2.333; SD = r(12.3 - S0)
def LS(t): return r(t - S0)
NUMS = [("4", 8.94), ("5", 9.60), ("6", 10.04), ("7", 10.58), ("8", 11.28)]
steps_html = f"""    <div id="st-8" class="clip band" data-start="{LS(4.88)}" data-duration="{LS(6.55)-LS(4.88)}" data-track-index="1">
      <div class="card"><div class="v">8 STEP</div><div id="st-8k" class="chip">&#9650; PALING TINGGI</div></div>
    </div>
    <div id="st-4" class="clip band" data-start="{LS(7.0)}" data-duration="{LS(8.4)-LS(7.0)}" data-track-index="1">
      <div class="card"><div class="v">4 STEP</div><div id="st-4k" class="chip dark">&#9660; PALING RENDAH</div></div>
    </div>
    <div id="st-all" class="clip band" data-start="{LS(8.42)}" data-duration="{LS(12.25)-LS(8.42)}" data-track-index="1">
      <div class="card"><div class="k">ADA PILIHAN</div><div class="row">""" + "".join(
    f'<div id="st-n{n}" class="chip">{n} STEP</div>' for n, _ in NUMS) + """</div></div>
    </div>
"""
steps_css = CARD_CSS + """
      #st-all .chip { font-size:40px; padding:10px 18px; }
"""
steps_js = (card_in("#st-8", LS(4.88)) + chip_in("#st-8k", LS(5.82)) + card_out("#st-8", LS(6.35)) +
            card_in("#st-4", LS(7.0)) + chip_in("#st-4k", LS(7.68)) + card_out("#st-4", LS(8.2)) +
            card_in("#st-all", LS(8.42)) + "".join(chip_in(f"#st-n{n}", LS(t)) for n, t in NUMS) + card_out("#st-all", LS(12.05)))
hosts.append(scene("steps", S0, SD, steps_html, steps_css, steps_js, 11))

# -------------------------------------------------------------- 3. USES (12.3 - 25.93)
U0 = 12.3; UD = r(25.93 - U0)
def LU(t): return r(t - U0)
uses_html = f"""    <div id="us-8" class="clip band" data-start="{LU(13.3)}" data-duration="{LU(20.68)-LU(13.3)}" data-track-index="1">
      <div class="card"><div class="k">8 STEP UNTUK</div>
        <div id="us-8a" class="chip"><span class="tick">&#10003;</span>BERSIH LAMPU</div>
        <div id="us-8b" class="chip"><span class="tick">&#10003;</span>TUKAR KIPAS</div></div>
    </div>
    <div id="us-4" class="clip band" data-start="{LU(21.6)}" data-duration="{LU(25.88)-LU(21.6)}" data-track-index="1">
      <div class="card"><div class="k">4 STEP UNTUK</div>
        <div id="us-4a" class="chip"><span class="tick">&#10003;</span>SIMPAN BARANG</div>
        <div id="us-4b" class="chip dark">KABINET DAPUR</div></div>
    </div>
"""
uses_js = (card_in("#us-8", LU(13.3)) + chip_in("#us-8a", LU(15.95)) + chip_in("#us-8b", LU(17.84)) + card_out("#us-8", LU(20.48)) +
           card_in("#us-4", LU(21.6)) + chip_in("#us-4a", LU(21.95)) + chip_in("#us-4b", LU(22.88)) + card_out("#us-4", LU(25.68)))
hosts.append(scene("uses", U0, UD, uses_html, CARD_CSS + "      .card .chip { align-self:flex-start; }\n", uses_js, 12))

# -------------------------------------------------------------- 4. LOOKS (25.93 - 35.17)
K0 = 25.93; KD = r(35.17 - K0)
def LK(t): return r(t - K0)
looks_html = f"""    <div id="lk-c" class="clip band" data-start="{LK(26.7)}" data-duration="{LK(31.35)-LK(26.7)}" data-track-index="1">
      <div class="card"><div class="k">WARNA MENARIK</div><div class="row">
        <div id="lk-w" class="chip dark"><span class="sw" style="background:#fff"></span>PUTIH</div>
        <div id="lk-r" class="chip dark"><span class="sw" style="background:#E5252A"></span>MERAH</div></div></div>
    </div>
    <div id="lk-s" class="clip band" data-start="{LK(32.0)}" data-duration="{LK(35.1)-LK(32.0)}" data-track-index="1">
      <div class="card"><div class="v">BESI TEBAL</div><div id="lk-sk" class="chip">&#128170; TAHAN LASAK</div></div>
    </div>
"""
looks_css = CARD_CSS + """
      .sw { width:40px; height:40px; border-radius:50%; border:3px solid var(--ink); }
"""
looks_js = (card_in("#lk-c", LK(26.7)) + chip_in("#lk-w", LK(29.06)) + chip_in("#lk-r", LK(29.78)) + card_out("#lk-c", LK(31.15)) +
            card_in("#lk-s", LK(32.0)) + chip_in("#lk-sk", LK(34.1)) + card_out("#lk-s", LK(34.9)))
hosts.append(scene("looks", K0, KD, looks_html, looks_css, looks_js, 13))

# ------------------------------------------------------------ 5. STORE (35.17 - 47.57)
T0 = 35.17; TD = r(47.57 - T0)
def LT(t): return r(t - T0)
store_html = f"""    <div id="sr-a" class="clip band" data-start="{LT(37.45)}" data-duration="{LT(42.4)-LT(37.45)}" data-track-index="1">
      <div class="card"><div class="k">SENANG SIMPAN</div><div class="v">TAK MAKAN RUANG</div></div>
    </div>
    <div id="sr-b" class="clip band" data-start="{LT(42.6)}" data-duration="{LT(47.4)-LT(42.6)}" data-track-index="1">
      <div class="card"><div class="v">NIPIS JE</div><div id="sr-bk" class="chip"><span class="tick">&#10003;</span>BOLEH SANDAR KAT DINDING</div></div>
    </div>
"""
store_js = (card_in("#sr-a", LT(37.45)) + card_out("#sr-a", LT(42.2)) +
            card_in("#sr-b", LT(43.1)) + chip_in("#sr-bk", LT(45.3)) + card_out("#sr-b", LT(47.2)))
hosts.append(scene("store", T0, TD, store_html, CARD_CSS + "      #sr-bk { font-size:36px; }\n", store_js, 14))

# --------------------------------------------------------------- 6. BUY (47.57 - 57.5)
B0 = 47.57; BD = r(57.5 - B0)
def LB(t): return r(t - B0)
buy_html = f"""    <div id="by-bajet" class="clip sticker" data-start="{LB(50.28)}" data-duration="{LB(52.45)-LB(50.28)}" data-track-index="2">HARGA BAJET</div>
    <div id="by-pick" class="clip band" data-start="{LB(52.5)}" data-duration="{LB(57.45)-LB(52.5)}" data-track-index="1">
      <div class="card"><div class="k">PILIH IKUT KEPERLUAN</div>
        <div id="by-8" class="chip">8 STEP &middot; PALING TINGGI</div>
        <div id="by-4" class="chip dark">4 STEP &middot; PALING RENDAH</div></div>
    </div>
"""
buy_js = (f'    tl.fromTo("#by-bajet", {{ scale: 0.2, rotation: -24 }}, {{ scale: 1, rotation: -6, duration: 0.42, ease: "back.out(2.4)" }}, {LB(50.28)});\n'
          f'    tl.to("#by-bajet", {{ scale: 0.4, opacity: 0, duration: 0.18, ease: "power3.in" }}, {LB(52.25)});\n' +
          card_in("#by-pick", LB(52.5)) + chip_in("#by-8", LB(53.02)) + chip_in("#by-4", LB(55.34)) + card_out("#by-pick", LB(57.25)))
hosts.append(scene("buy", B0, BD, buy_html, CARD_CSS + "      .card .chip { align-self:flex-start; font-size:38px; }\n", buy_js, 15))

# ------------------------------------------------------------- 7. CTA (64.75 - end)
C0 = 57.5; CD = r(DUR - C0)
def LC(t): return r(t - C0)
BAG = """<svg viewBox="0 0 120 120" width="190" height="190" aria-hidden="true">
          <path d="M22 40h76l-6 66a8 8 0 0 1-8 7H36a8 8 0 0 1-8-7z" fill="#FFD21F" stroke="#0D0D0D" stroke-width="6" stroke-linejoin="round"/>
          <path d="M42 46V34a18 18 0 0 1 36 0v12" fill="none" stroke="#0D0D0D" stroke-width="7" stroke-linecap="round"/>
          <circle cx="42" cy="50" r="5" fill="#0D0D0D"/><circle cx="78" cy="50" r="5" fill="#0D0D0D"/>
        </svg>"""
cta_html = f"""    <div id="cta-scrim" class="clip" data-start="0" data-duration="{CD}" data-track-index="1"></div>
    <div id="cta-box" class="clip" data-start="0.05" data-duration="{r(CD-0.05)}" data-track-index="2">
      <div id="cta-bag">{BAG}</div>
      <div id="cta-l1"><span class="hf-stroke">KLIK BEG</span></div>
      <div id="cta-l2"><span class="hf-stroke">KAT BAWAH</span></div>
      <div id="cta-arrow"><svg viewBox="0 0 80 120" width="90" height="135" aria-hidden="true"><path d="M40 6v92M12 70l28 30 28-30" fill="none" stroke="#FFD21F" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
      <div id="cta-brand">MUROH DOOH</div>
    </div>
"""
cta_css = """
      #cta-scrim { position:absolute; inset:0; background:linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,.55) 62%, rgba(0,0,0,.72) 100%); }
      #cta-box { position:absolute; left:0; right:0; top:610px; text-align:center; }
      #cta-bag { display:inline-block; filter:drop-shadow(0 16px 30px rgba(0,0,0,.45)); }
      #cta-l1, #cta-l2 { font-family:'Archivo Black','Inter',sans-serif; line-height:1.0; }
      #cta-l1 { font-size:132px; color:var(--yellow); margin-top:6px; }
      #cta-l2 { font-size:110px; color:var(--white); }
      #cta-arrow { margin-top:6px; }
      #cta-brand { display:inline-block; margin-top:10px; background:var(--red); color:var(--white); font-weight:900; font-size:40px;
        letter-spacing:.14em; padding:10px 26px; border-radius:12px; border:4px solid var(--white); }
"""
cta_js = f"""    tl.fromTo("#cta-scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "power2.out" }}, 0);
    tl.fromTo("#cta-bag", {{ y: -120, scale: 0.4, rotation: -18, opacity: 0 }}, {{ y: 0, scale: 1, rotation: 0, opacity: 1, duration: 0.55, ease: "back.out(2)" }}, 0.05);
    tl.fromTo("#cta-l1", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(57.9)});
    tl.fromTo("#cta-l2", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(58.4)});
    tl.fromTo("#cta-arrow", {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {LC(58.8)});
    tl.fromTo("#cta-brand", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {LC(59.3)});
"""
bounce_t = LC(59.3)
for k in range(5):                                       # finite bounces, seek-safe
    cta_js += f'    tl.to("#cta-arrow", {{ y: 22, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56)});\n'
    cta_js += f'    tl.to("#cta-arrow", {{ y: 0, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56 + 0.28)});\n'
    cta_js += f'    tl.to("#cta-bag", {{ rotation: {(-1)**k * 5}, duration: 0.56, ease: "sine.inOut" }}, {r(bounce_t - 0.2 + k*0.56)});\n'
hosts.append(scene("cta", C0, CD, cta_html, cta_css, cta_js, 16))

# ------------------------------------------------------------- 8. BRAND tag (whole)
brand_html = f"""    <div id="brand-tag" class="clip" data-start="2.333" data-duration="{r(C0 - 2.333)}" data-track-index="1">
      <span class="d"></span>MUROH DOOH
    </div>
"""
brand_css = """
      #brand-tag { position:absolute; right:54px; top:182px; display:flex; align-items:center; gap:10px;
        background:rgba(13,13,13,.6); color:var(--white); font-weight:900; font-size:28px; letter-spacing:.14em;
        padding:9px 18px; border-radius:999px; border:2px solid rgba(255,210,31,.85); }
      #brand-tag .d { width:12px; height:12px; border-radius:50%; background:var(--yellow); }
"""
brand_js = """    tl.fromTo("#brand-tag", { opacity: 0 }, { opacity: 1, duration: 0.4 }, 0);
"""
hosts.append(scene("brand", 0, DUR, brand_html, brand_css, brand_js, 17))

# --------------------------------------------------------------- 9. FX (flashes)
FLASHES = [2.333]
fx_html = "".join(f'    <div id="fx-f{k}" class="clip flash" data-start="{r(t-0.08)}" data-duration="0.4" data-track-index="1"></div>\n'
                  for k, t in enumerate(FLASHES))
fx_css = "      .flash { position:absolute; inset:0; background:#fff; opacity:0; }\n"
fx_js = "".join(f"""    tl.fromTo("#fx-f{k}", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.08, ease: "power2.in" }}, {r(t-0.08)});
    tl.to("#fx-f{k}", {{ opacity: 0, duration: 0.26, ease: "power2.out" }}, {r(t)});
""" for k, t in enumerate(FLASHES))
hosts.append(scene("fx", 0, DUR, fx_html, fx_css, fx_js, 18))

# ------------------------------------------------------------------ 10. CAPTIONS
cap_html, cap_js = [], []
for gi, g in enumerate(caps):
    spans = " ".join(f'<span id="cw{gi}-{wi}" class="w">{html.escape(w["text"])}</span>' for wi, w in enumerate(g["words"]))
    cap_html.append(f'    <div id="cg{gi}" class="clip cg" data-start="{g["start"]}" data-duration="{r(g["end"]-g["start"])}" data-track-index="1"><div class="line">{spans}</div></div>')
    s = g["start"]
    cap_js.append(f'    tl.fromTo("#cg{gi} .line", {{ scale: 0.86, y: 14, opacity: 0 }}, {{ scale: 1, y: 0, opacity: 1, duration: 0.14, ease: "back.out(2)" }}, {s});')
    for wi, w in enumerate(g["words"]):
        cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFD21F" }}, {max(s, w["start"])});')
        if wi < len(g["words"]) - 1:
            cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFFFFF" }}, {g["words"][wi+1]["start"]});')
caps_css = """
      .cg { position:absolute; left:70px; right:150px; top:1150px; text-align:center; overflow:visible; }
      .cg .line { display:inline-block; font-family:'Inter',sans-serif; font-weight:900; font-size:78px; line-height:1.08;
        letter-spacing:-.01em; color:var(--white); paint-order:stroke fill; -webkit-text-stroke:12px var(--ink);
        text-shadow:0 8px 22px rgba(0,0,0,.55); }
"""
caps_js = "\n".join(cap_js) + """
    // fit each group to the caption box
    document.querySelectorAll("#captions .cg .line").forEach((el) => {
      const fit = window.__hyperframes && window.__hyperframes.fitTextFontSize
        ? window.__hyperframes.fitTextFontSize(el.textContent, { fontFamily: "Inter", fontWeight: 900, maxWidth: 820, baseFontSize: 78, minFontSize: 50 })
        : null;
      if (fit && fit.fontSize) el.style.fontSize = fit.fontSize + "px";
    });
"""
hosts.append(scene("captions", 0, DUR, "\n".join(cap_html) + "\n", caps_css, caps_js, 20))

# --------------------------------------------------------------------- SFX bed
# (time, file, volume) - every hit has a cause on screen; peaks land on the picture.
SFX = [
    (0.00, "whoosh-short", 0.28), (0.24, "pop", 0.5), (1.56, "impact-bass-1", 0.11), (2.24, "whoosh-cinematic", 0.28),
    (4.86, "pop", 0.5), (5.80, "ping", 0.55), (6.98, "pop", 0.45), (7.66, "pop", 0.45),
    (8.92, "pop", 0.38), (9.58, "pop", 0.38), (10.02, "pop", 0.38), (10.56, "pop", 0.38), (11.26, "ping", 0.55),
    (13.28, "whoosh-short", 0.22), (15.93, "pop", 0.42), (17.82, "pop", 0.42),
    (21.58, "whoosh-short", 0.22), (21.93, "pop", 0.42), (22.86, "pop", 0.4),
    (29.04, "pop", 0.42), (29.76, "pop", 0.42), (31.98, "impact-bass-2", 0.07), (34.08, "pop", 0.42),
    (37.43, "whoosh", 0.25), (38.40, "whoosh-cinematic", 0.24), (43.08, "whoosh-short", 0.22), (45.28, "pop", 0.42),
    (50.26, "pop", 0.5), (52.98, "pop", 0.42), (55.32, "pop", 0.42), (57.48, "sparkle", 0.28), (58.38, "impact-bass-2", 0.07),
]
SFX_LEN = {"whoosh-short": 0.57, "whoosh": 0.57, "whoosh-cinematic": 2.5, "pop": 0.72, "ping": 1.32,
           "impact-bass-1": 2.1, "impact-bass-2": 2.5, "sparkle": 1.8}
sfx_tags = "\n".join(
    f'      <audio id="sfx{k:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{min(SFX_LEN[f], r(DUR - t))}" '
    f'data-volume="{v}" data-track-index="{40 + k % 3}"></audio>' for k, (t, f, v) in enumerate(SFX))

# ------------------------------------------------------------- camera (root tl)
# Natural moves only, as one non-overlapping chain of (t0, t1, from, to, ease) pieces:
# settle-in zooms on the three scene reveals, alternating 0 / +6% framing on jump cuts
# (hides the cut), one push on "8 step paling tinggi", one on "besi tebal", slow drift elsewhere.
REVEALS = {0.0: (1.18, 1.04, 2.333, "power2.out"), 2.333: (1.2, 1.0, 0.6, "expo.out")}
MERGE_INTO_PREV = set()
CTA_FROM = 57.567                        # one slow push from here to the end
EMPH = {4.133: [(4.92, 1.1, 0.4, "power3.out"), (7.4, 1.02, 0.45, "power2.inOut")],
        30.5: [(32.04, 1.1, 0.35, "power3.out")]}
bounds = [c for c in CUTS if c not in MERGE_INTO_PREV and c < CTA_FROM] + [CTA_FROM, DUR]
pieces, alt = [], 0
for a, b in zip(bounds, bounds[1:]):
    if a == CTA_FROM:
        pieces.append((a, b, 1.0, 1.08, "sine.inOut")); continue
    if a in REVEALS:
        s0, s1, d, e = REVEALS[a]; d = min(d, b - a)
        pieces.append((a, a + d, s0, s1, e))
        if b - a - d > 0.05: pieces.append((a + d, b, s1, s1 + 0.03, "none"))
        alt = 0; continue
    base = 1.0 if alt % 2 == 0 else 1.06; alt += 1
    t, s = a, base
    for (te, target, d, e) in EMPH.get(a, []):
        if te > t + 0.01: pieces.append((t, te, s, s + 0.01, "none")); s += 0.01
        pieces.append((te, te + d, s, target, e)); t, s = te + d, target
    pieces.append((t, b, s, s + 0.02, "none"))
cam = []
for t0, t1, s0, s1, e in pieces:
    cam.append(f'    tl.set("#cam", {{ scale: {r(s0)} }}, {r(t0)});')
    cam.append(f'    tl.to("#cam", {{ scale: {r(s1)}, duration: {r(t1 - t0 - 0.001)}, ease: "{e}" }}, {r(t0)});')

GRADE = json.dumps({"intensity": 0.8, "adjust": {"exposure": 0.06, "contrast": 0.08, "highlights": -0.1, "shadows": 0.09,
                    "whites": 0.03, "blacks": -0.03, "vibrance": 0.05, "saturation": 0.03}})

index = f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:100%; height:100%; overflow:hidden; background:#000; }}
      #cam {{ position:absolute; inset:0; transform-origin:50% 46%; }}
      #spine {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; object-fit:cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
      <div id="cam">
        <video id="spine" class="clip" src="assets/video/spine.mp4" data-start="0" data-duration="{DUR}" data-track-index="0"
          playsinline data-has-audio="true" data-volume="1"
          data-color-grading='{GRADE}'></video>
      </div>
{chr(10).join(hosts)}
{sfx_tags}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cam)}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(os.path.join(EDIT, "index.html"), "w").write(index)
json.dump([{"start": c["start"], "end": c["end"], "text": " ".join(w["text"] for w in c["words"])} for c in caps],
          open(os.path.join(DATA, "captions.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(caps)} caption groups, {len(SFX)} sfx, {len(hosts)} scenes")
