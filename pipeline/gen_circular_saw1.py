"""Generate the HyperFrames project (projects/circular-saw-1/) for the MUROH DOOH cordless brushless circular saw (take 1) TikTok.

Inputs (pipeline/data/circular_saw_1):
  spine_transcript.json  whisper large-v3 word timings measured on the cut spine (output time)
  spine_map.json         where every cut lands in output time
Outputs: projects/circular-saw-1/index.html + compositions/*.html

Every on-screen claim below is something the speaker says in the recording; nothing is
invented (no price, no discount, no specs that are not spoken).
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT = os.path.join(ROOT, "projects", "circular-saw-1")
DATA = os.path.join(ROOT, "pipeline", "data", "circular_saw_1")
W, H, FPS = 1080, 1920, 30
DUR = 53.23                      # spine + 1.2 s held last frame under the CTA

tx = json.load(open(os.path.join(DATA, "spine_transcript.json")))
cmap = json.load(open(os.path.join(DATA, "spine_map.json")))
CUTS = [s["out_in"] for s in cmap["segments"]] + [cmap["duration"]]

# --------------------------------------------------------------------------- captions
words, SEG_START = [], set()
for seg in tx["segments"]:
    SEG_START.add(len(words)); words.extend(seg["words"])
# ASR slips checked against two passes on the original audio + standard Malay spelling.
# ASR slips, checked with prompted + unprompted passes: "cyclosaw"/"C-Closer" = "circular saw", "papa" = "papan".
FIX = {26: "circular saw", 64: "papan", 134: "circular saw", 135: ""}
W_ = []
for i, w in enumerate(words):
    t = FIX.get(i, w["word"].strip())
    if t == "": continue                                # merged into the previous fix
    if t.startswith("-") and W_:                       # "lama" "-lama" -> "lama-lama"
        W_[-1]["text"] += t; W_[-1]["end"] = w["end"]; W_[-1]["punct"] = bool(re.search(r"[.,!?]$", t)); continue
    W_.append({"i": i, "seg0": i in SEG_START, "text": t, "start": w["start"], "end": w["end"], "punct": bool(re.search(r"[.,!?]$", t))})
for w in W_:
    w["text"] = re.sub(r"[.,!?]+$", "", w["text"]).upper()
    if w["text"] and w["end"] - w["start"] > 0.6 and not w["text"][0].isdigit():                   # whisper folds pauses into a word's start
        w["start"] = round(w["end"] - 0.42, 2)
HOOK_END = 2.3
cap_words = [w for w in W_ if w["i"] >= 7]  # earlier words = hook line = hook line, shown as kinetic type

# Caption groups set by hand for this video (spine word indices, inclusive): natural Malay
# phrases, a number always with "STEP", the hook line left to the kinetic type.
MANUAL_GROUPS = [(7, 9), (10, 13), (14, 19), (20, 23), (24, 26), (27, 29), (30, 34), (35, 40), (41, 45), (46, 51), (52, 55),
    (56, 60), (61, 64), (65, 66), (67, 71), (72, 73), (74, 78), (79, 82), (83, 85), (86, 88), (89, 92), (93, 96),
    (97, 99), (100, 102), (103, 104), (105, 106), (107, 111), (112, 113), (114, 118), (119, 122), (123, 125), (126, 127),
    (128, 132), (133, 135), (136, 137), (138, 143)]
groups = [[w for w in W_ if a <= w["i"] <= b] for a, b in MANUAL_GROUPS]
groups = [g for g in groups if g]
assert sum(len(g) for g in groups) == len(cap_words), "every caption word in exactly one group"
caps = []
for g in groups:
    caps.append({"start": round(g[0]["start"] - 0.04, 2), "end": round(g[-1]["end"] + 0.12, 2), "words": g})
caps[0]["start"] = max(caps[0]["start"], 2.44)        # after the hook's kinetic line
CTA_START = 49.4                                       # the CTA card says the closing line itself
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

# Info cards sit just above the captions, anchored at the bottom so they grow upwards (y ~980-1185),
# chips in a row to stay short: in this video's close-ups the face fills the upper half, so nothing
# is drawn above y ~950 except the hook title and the brand tag.
CARD_CSS = """
      .band { position:absolute; left:48px; bottom:735px; width:620px; }
      .card { display:inline-flex; flex-direction:column; align-items:flex-start; gap:8px; background:rgba(13,13,13,.84);
        border-left:10px solid var(--yellow); border-radius:20px; padding:14px 22px; box-shadow:0 16px 36px rgba(0,0,0,.35); }
      .card .k { font-weight:900; font-size:30px; letter-spacing:.08em; color:var(--yellow); }
      .card .v { font-family:'Archivo Black','Inter',sans-serif; font-size:56px; line-height:1; }
      .card .big { font-family:'Archivo Black','Inter',sans-serif; font-size:84px; line-height:.95; color:var(--yellow); }
      .chips { display:flex; flex-wrap:wrap; gap:10px; }
      .chip { display:inline-flex; align-items:center; gap:10px; background:var(--yellow); color:var(--ink); font-weight:900;
        font-size:34px; padding:8px 18px; border-radius:12px; opacity:0; }
      .chip.dark { background:var(--white); }
"""
def card_in(sel, t):  return f'    tl.fromTo("{sel}", {{ x: -70, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {r(t)});\n'
def card_out(sel, t): return f'    tl.to("{sel}", {{ x: -40, opacity: 0, duration: 0.2, ease: "power3.in" }}, {r(t)});\n'
def chip_in(sel, t):  return f'    tl.fromTo("{sel}", {{ scale: 0.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.4)" }}, {r(t)});\n'

TOP_CARD_CSS = None   # defined after CARD_CSS, before the scenes

def card_scene(cid, s0, s1, track, cards, css=None):
    """cards: list of (id, t_in, t_out, inner_html, [(chip_id, t), ...])"""
    def L(t): return r(t - s0)
    body, js = "", ""
    for cid2, t0, t1, inner, chips in cards:
        body += f'    <div id="{cid2}" class="clip band" data-start="{L(t0)}" data-duration="{r(L(t1) - L(t0))}" data-track-index="1"><div class="card">{inner}</div></div>\n'
        js += card_in("#" + cid2, L(t0)) + "".join(chip_in("#" + c, L(t)) for c, t in chips) + card_out("#" + cid2, L(t1) - 0.2)
    hosts.append(scene(cid, s0, r(s1 - s0), body, css or CARD_CSS, js, track))

# ------------------------------------------------------------------ 1. HOOK (in sync 0 - 9.93; title over the first line)
HK = 2.6
hook_html = f"""    <div id="hook-top" class="clip" data-start="0" data-duration="{HK}" data-track-index="1">
      <div id="hook-title"><span class="hf-stroke">TAK PAYAH CAKAP BANYAK!</span></div>
      <div id="hook-tag">CIRCULAR SAW BRUSHLESS</div>
    </div>
"""
hook_css = """
      #hook-top { position:absolute; left:40px; right:40px; top:1250px; text-align:center; }
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:96px; line-height:1.02; color:var(--yellow); text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-tag { display:inline-block; margin-top:14px; background:var(--red); color:var(--white); padding:10px 28px;
        border-radius:14px; transform:rotate(-3deg); font-family:'Archivo Black','Inter',sans-serif; font-size:50px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.25, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "expo.out" }, 0.05);
    tl.fromTo("#hook-tag", { scale: 0.6, rotation: -14, opacity: 0 }, { scale: 1, rotation: -3, opacity: 1, duration: 0.45, ease: "back.out(2.2)" }, 0.5);
    tl.to("#hook-top", { y: -20, opacity: 0, duration: 0.2, ease: "power3.in" }, 2.38);
"""
hosts.append(scene("hook", 0, HK, hook_html, hook_css, hook_js, 10))

LOW_CARD_CSS = CARD_CSS.replace(".band { position:absolute; left:48px; bottom:735px; width:620px; }",
                                ".band { position:absolute; left:48px; bottom:375px; width:620px; }")
RIGHT_TOP_CSS = CARD_CSS.replace(".band { position:absolute; left:48px; bottom:735px; width:620px; }",
                                 ".band { position:absolute; right:40px; top:250px; width:620px; text-align:right; }")
assert LOW_CARD_CSS != CARD_CSS and RIGHT_TOP_CSS != CARD_CSS
# ------------------------------------------------ 2. SIZE + BLADE + CORDLESS (presenter: bottom band)
card_scene("intro", 9.933, 22.3, 11, [
    ("sz", 11.1, 14.0, '<div class="k">CIRCULAR SAW</div><div class="big">5 INCI</div>', []),
    ("bl", 14.1, 17.75, '<div class="k">BELI SEKALI</div><div class="v">DAPAT MATA</div>', []),
    ("cl", 17.9, 22.25, '<div class="k">BRUSHLESS</div><div class="v">TAK SERABUT WIRE</div><div id="cl-c" class="chip">SENANG BAWA</div>', [("cl-c", 19.6)]),
])
# ------------------------------------------------ 3. USES
card_scene("uses", 22.367, 29.5, 12, [
    ("us", 22.5, 29.45, '<div class="k">SESUAI UNTUK</div><div class="chips"><div id="us-1" class="chip">POTONG PAPAN</div>'
     '<div id="us-2" class="chip">PLYWOOD</div><div id="us-3" class="chip">DIY</div><div id="us-4" class="chip">PASANG KABINET</div></div>',
     [("us-1", 24.1), ("us-2", 24.78), ("us-3", 26.2), ("us-4", 27.46)]),
])
# ------------------------------------------------ 4. 3 LEVELS (button close-up at 34.6: card low)
card_scene("levels", 29.6, 38.7, 13, [
    ("lv", 30.4, 38.65, '<div class="k">BOLEH ADJUST</div><div class="v">3 LEVEL</div><div class="chips"><div id="lv-1" class="chip">LEVEL 1</div>'
     '<div id="lv-2" class="chip">LEVEL 2</div><div id="lv-3" class="chip">LEVEL 3</div></div>', [("lv-1", 35.36), ("lv-2", 36.88), ("lv-3", 38.3)]),
], css=LOW_CARD_CSS)
# ------------------------------------------------ 5. ANGLE (saw base fills the middle: card top right over the sky)
card_scene("angle", 39.3, 45.4, 14, [
    ("an", 39.4, 45.35, '<div class="k">ADJUST ANGLE DEPAN</div><div class="v">MAKSIMUM 45 DARJAH</div>', []),
], css=RIGHT_TOP_CSS)
# ------------------------------------------------ 6. PRICE
card_scene("price", 45.467, 49.4, 15, [
    ("pr", 46.3, 49.35, '<div class="k">CIRCULAR SAW</div><div class="v">HARGA BAJET</div>', []),
])
# ------------------------------------------------------------- 6c. TOONS (key points only, 1-3 s)
from toons import toon, TOP_RIGHT
TOONS = [("t-saw", "saw_cut", 24.0, 2.4, TOP_RIGHT)]     # "potong papan, potong plywood"
for k, (tid, kind, t0, d, pos) in enumerate(TOONS):
    th, tc, tj = toon(kind, tid, d)
    hosts.append(scene(tid, t0, d, th, tc + pos.format(tid=tid), tj, 21 + k))

# ------------------------------------------------------------- 7. CTA (64.75 - end)
C0 = 49.467; CD = r(DUR - C0)
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
      #cta-box { position:absolute; left:0; right:0; top:860px; text-align:center; }
      #cta-bag svg { width:140px; height:140px; }
      #cta-arrow svg { width:64px; height:92px; }
      #cta-bag { display:inline-block; filter:drop-shadow(0 16px 30px rgba(0,0,0,.45)); }
      #cta-l1, #cta-l2 { font-family:'Archivo Black','Inter',sans-serif; line-height:1.0; }
      #cta-l1 { font-size:132px; color:var(--yellow); margin-top:6px; }
      #cta-l2 { font-size:110px; color:var(--white); }
      #cta-arrow { margin-top:6px; }
      #cta-price { display:inline-block; margin-top:14px; background:var(--yellow); color:var(--ink); font-weight:900; font-size:40px;
        padding:8px 22px; border-radius:12px; }
      #cta-brand { display:inline-block; margin-top:10px; background:var(--red); color:var(--white); font-weight:900; font-size:40px;
        letter-spacing:.14em; padding:10px 26px; border-radius:12px; border:4px solid var(--white); }
"""
cta_js = f"""    tl.fromTo("#cta-scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "power2.out" }}, 0);
    tl.fromTo("#cta-bag", {{ y: -120, scale: 0.4, rotation: -18, opacity: 0 }}, {{ y: 0, scale: 1, rotation: 0, opacity: 1, duration: 0.55, ease: "back.out(2)" }}, 0.05);
    tl.fromTo("#cta-l1", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(49.767)});
    tl.fromTo("#cta-l2", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(50.217)});
    tl.fromTo("#cta-arrow", {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {LC(50.567)});
    tl.fromTo("#cta-brand", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {LC(50.917)});
"""
bounce_t = LC(51.117)
for k in range(5):                                       # finite bounces, seek-safe
    cta_js += f'    tl.to("#cta-arrow", {{ y: 22, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56)});\n'
    cta_js += f'    tl.to("#cta-arrow", {{ y: 0, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56 + 0.28)});\n'
    cta_js += f'    tl.to("#cta-bag", {{ rotation: {(-1)**k * 5}, duration: 0.56, ease: "sine.inOut" }}, {r(bounce_t - 0.2 + k*0.56)});\n'
hosts.append(scene("cta", C0, CD, cta_html, cta_css, cta_js, 16))

# ------------------------------------------------------------- 8. BRAND tag (whole)
brand_html = f"""    <div id="brand-tag" class="clip" data-start="2.6" data-duration="{r(C0 - 2.6)}" data-track-index="1">
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
FLASHES = []
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
    hi = ' style="top:1580px"' if 34.6 <= g["start"] < 38.7 else ""   # speed-button close-up mid-frame
    cap_html.append(f'    <div id="cg{gi}" class="clip cg"{hi} data-start="{g["start"]}" data-duration="{r(g["end"]-g["start"])}" data-track-index="1"><div class="line">{spans}</div></div>')
    s = g["start"]
    cap_js.append(f'    tl.fromTo("#cg{gi} .line", {{ scale: 0.86, y: 14, opacity: 0 }}, {{ scale: 1, y: 0, opacity: 1, duration: 0.14, ease: "back.out(2)" }}, {s});')
    for wi, w in enumerate(g["words"]):
        cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFD21F" }}, {max(s, w["start"])});')
        if wi < len(g["words"]) - 1:
            cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFFFFF" }}, {g["words"][wi+1]["start"]});')
caps_css = """
      .cg { position:absolute; left:70px; right:150px; top:1205px; text-align:center; overflow:visible; }
      .cg .line { display:inline-block; font-family:'Inter',sans-serif; font-weight:900; font-size:64px; line-height:1.08;   /* owner: subtitles a little smaller (was 78) */
        letter-spacing:-.01em; color:var(--white); paint-order:stroke fill; -webkit-text-stroke:10px var(--ink);
        text-shadow:0 8px 22px rgba(0,0,0,.55); }
"""
caps_js = "\n".join(cap_js) + """
    // fit each group to the caption box
    document.querySelectorAll("#captions .cg .line").forEach((el) => {
      const fit = window.__hyperframes && window.__hyperframes.fitTextFontSize
        ? window.__hyperframes.fitTextFontSize(el.textContent, { fontFamily: "Inter", fontWeight: 900, maxWidth: 820, baseFontSize: 64, minFontSize: 44 })
        : null;
      if (fit && fit.fontSize) el.style.fontSize = fit.fontSize + "px";
    });
"""
hosts.append(scene("captions", 0, DUR, "\n".join(cap_html) + "\n", caps_css, caps_js, 20))

# --------------------------------------------------------------------- SFX bed
# (time, file, volume) - every hit has a cause on screen; peaks land on the picture.
SFX = [
    (0.05, "whoosh-short", 0.22), (0.5, "impact-bass-1", 0.1), (9.85, "whoosh-cinematic", 0.24),
    (11.08, "pop", 0.42), (14.08, "pop", 0.4), (17.88, "whoosh-short", 0.22), (19.58, "pop", 0.38),
    (22.48, "whoosh-short", 0.22), (23.98, "sparkle", 0.16), (24.08, "pop", 0.34), (24.76, "pop", 0.34), (26.18, "pop", 0.34), (27.44, "pop", 0.34),
    (30.38, "whoosh-short", 0.22), (35.34, "pop", 0.36), (36.86, "pop", 0.36), (38.28, "ping", 0.42),
    (39.38, "whoosh-short", 0.22), (43.85, "pop", 0.4), (46.28, "whoosh-short", 0.22),
    (49.45, "sparkle", 0.28), (50.2, "impact-bass-2", 0.07),
]
SFX_LEN = {"whoosh-short": 0.57, "whoosh": 0.57, "whoosh-cinematic": 2.5, "pop": 0.72, "ping": 1.32,
           "impact-bass-1": 2.1, "impact-bass-2": 2.5, "sparkle": 1.8}
sfx_tags = "\n".join(
    f'      <audio id="sfx{k:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{min(SFX_LEN[f], r(DUR - t))}" '
    f'data-volume="{v}" data-track-index="{40 + k % 3}"></audio>' for k, (t, f, v) in enumerate(SFX))

# ------------------------------------------------------------- camera (root tl)
# Natural moves only, as one non-overlapping chain of (t0, t1, from, to, ease) pieces:
# settle-in zooms on the three scene reveals, alternating 0 / +6% framing on jump cuts
# (hides the cut), one punch-in per key point, slow drift elsewhere.
REVEALS = {0.0: (1.1, 1.0, 9.9, "sine.inOut"), 9.933: (1.16, 1.0, 0.6, "expo.out")}
MERGE_INTO_PREV = set()
CTA_FROM = 49.467                        # one slow push from here to the end
EMPH = {9.933: [(12.8, 1.1, 0.35, "power3.out")], 22.367: [(24.7, 1.08, 0.35, "power3.out")],
        29.6: [(31.8, 1.1, 0.35, "power3.out")], 42.533: [(43.8, 1.1, 0.35, "power3.out")]}
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
