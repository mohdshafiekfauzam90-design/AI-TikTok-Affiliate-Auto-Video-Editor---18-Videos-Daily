"""Generate the HyperFrames project (projects/screwdriver/) for the MUROH DOOH Keelat mini cordless screwdriver TikTok.

Inputs (pipeline/data/screwdriver):
  spine_transcript.json  whisper large-v3 word timings measured on the cut spine (output time)
  spine_map.json         where every cut lands in output time
Outputs: projects/screwdriver/index.html + compositions/*.html

Every on-screen claim below is something the speaker says in the recording; nothing is
invented (no price, no discount, no specs that are not spoken).
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT = os.path.join(ROOT, "projects", "screwdriver")
DATA = os.path.join(ROOT, "pipeline", "data", "screwdriver")
W, H, FPS = 1080, 1920, 30
DUR = 56.6                       # spine (55.4 s) + 1.2 s held last frame under the CTA

tx = json.load(open(os.path.join(DATA, "spine_transcript.json")))
cmap = json.load(open(os.path.join(DATA, "spine_map.json")))
CUTS = [s["out_in"] for s in cmap["segments"]] + [cmap["duration"]]

# --------------------------------------------------------------------------- captions
words, SEG_START = [], set()
for seg in tx["segments"]:
    SEG_START.add(len(words)); words.extend(seg["words"])
# ASR slips checked against two passes on the original audio + standard Malay spelling.
# ASR slips, checked on prompted + unprompted passes: "ke" = "tu" (buka skru tu), "big" = "bit",
# "Kilat" = "Keelat" (the brand on the label), "restart" = "restock". "Pasang-pasang perabot" confirmed by the owner.
FIX = {44: "tu", 104: "bit", 134: "Keelat", 145: "restock"}
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
cap_words = [w for w in W_ if w["i"] >= 11]  # words 0-10 = hook line, shown as kinetic type

# Caption groups set by hand for this video (spine word indices, inclusive): natural Malay
# phrases, a number always with "STEP", the hook line left to the kinetic type.
MANUAL_GROUPS = [(11, 14), (15, 16), (17, 20), (21, 25), (26, 27), (28, 29), (30, 32), (33, 35), (36, 39), (40, 43),
    (44, 46), (47, 48), (49, 51), (52, 54), (55, 56), (57, 59), (60, 62), (63, 68), (69, 71), (72, 76), (77, 80),
    (81, 83), (84, 84), (85, 89), (90, 92), (93, 97), (98, 99), (100, 102), (103, 106), (107, 111), (112, 115),
    (116, 118), (119, 124), (125, 129), (130, 134), (135, 139), (140, 142), (143, 145), (146, 151)]
groups = [[w for w in W_ if a <= w["i"] <= b] for a, b in MANUAL_GROUPS]
groups = [g for g in groups if g]
assert sum(len(g) for g in groups) == len(cap_words), "every caption word in exactly one group"
caps = []
for g in groups:
    caps.append({"start": round(g[0]["start"] - 0.04, 2), "end": round(g[-1]["end"] + 0.12, 2), "words": g})
caps[0]["start"] = max(caps[0]["start"], 3.09)        # after the hook's kinetic line
CTA_START = 52.1                                       # the CTA card says the closing line itself
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
      .band { position:absolute; left:48px; top:250px; width:640px; }
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

# ------------------------------------------------------------------ 1. HOOK (0 - 3.067): screw driven in, motor running
HK = 3.067
hook_html = f"""    <div id="hook-top" class="clip" data-start="0" data-duration="{HK}" data-track-index="1">
      <div id="hook-title"><span class="hf-stroke">MINI SCREWDRIVER</span></div>
      <div id="hook-tag">CORDLESS &middot; KEELAT</div>
    </div>
    <div id="hook-b0" class="clip hook-beat" data-start="2.45" data-duration="{r(HK-2.45)}" data-track-index="2"><span class="hf-stroke">CEPAT!</span></div>
"""
hook_css = """
      #hook-top { position:absolute; left:0; right:0; top:1150px; text-align:center; }   /* screws + screwdriver fill the top of the hook */
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:100px; line-height:1.02; text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-tag { display:inline-block; margin-top:12px; background:var(--red); color:var(--white); padding:10px 28px;
        border-radius:14px; transform:rotate(-3deg); font-family:'Archivo Black','Inter',sans-serif; font-size:50px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
      .hook-beat { position:absolute; left:40px; right:40px; top:1480px; text-align:center; font-family:'Archivo Black','Inter',sans-serif;
        font-size:160px; line-height:1; color:var(--yellow); }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.12 }, { scale: 1, duration: 0.5, ease: "expo.out" }, 0);
    tl.fromTo("#hook-tag", { scale: 0.6, rotation: -14 }, { scale: 1, rotation: -3, duration: 0.45, ease: "back.out(2.2)" }, 0.1);
    tl.fromTo("#hook-b0 span", { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.24, ease: "expo.out" }, 2.45);
"""
hosts.append(scene("hook", 0, HK, hook_html, hook_css, hook_js, 10))

# Hands-only demo, no presenter: cards in the top band (CARD_CSS .band top:250px), except the motorcycle
# screw demo, where the screws sit at the top of frame: there the card goes low (LOW_CARD_CSS).
LOW_CARD_CSS = CARD_CSS.replace(".band { position:absolute; left:48px; top:250px; width:640px; }",
                                ".band { position:absolute; left:48px; top:1370px; width:640px; }")
assert LOW_CARD_CSS != CARD_CSS
# ------------------------------------------------ 2. INTRO + BITS
card_scene("intro", 3.067, 11.833, 11, [
    ("in-a", 3.1, 5.95, '<div class="k">MINI SCREWDRIVER</div><div class="v">KEELAT</div>', []),
    ("in-b", 6.0, 11.8, '<div class="k">MATA BIT</div><div class="v">KELUAR &middot; MASUK</div><div id="in-c" class="chip">TERUS BOLEH GUNA</div>', [("in-c", 10.7)]),
])
# ------------------------------------------------ 3. DEMO on the motorcycle (screws at the top: card low)
card_scene("demo", 11.833, 19.267, 12, [
    ("dm-a", 12.9, 19.2, '<div class="k">PASANG &amp; BUKA SKRU</div><div class="v">MEMANG MUDAH</div>', []),
], css=LOW_CARD_CSS)
# ------------------------------------------------ 4. FURNITURE + STORE
card_scene("use", 19.267, 23.733, 13, [      # still the screw demo shot: card low
    ("us-a", 19.3, 23.65, '<div class="k">SESUAI JUGA</div><div class="v">PASANG PERABOT</div>', []),
], css=LOW_CARD_CSS)
card_scene("store", 23.733, 27.233, 16, [
    ("us-b", 24.3, 27.2, '<div class="k">DAH TAK GUNA</div><div class="v">BOLEH SIMPAN</div>', []),
])
# ------------------------------------------------ 5. STRAIGHT / PISTOL
card_scene("pivot", 27.233, 34.6, 14, [
    ("pv-a", 27.6, 34.55, '<div class="k">TEKAN &amp; PUSING</div><div class="v">BOLEH JADI LURUS</div><div id="pv-b" class="chip">BALIK BENTUK ASAL PUN BOLEH</div>', [("pv-b", 31.8)]),
])
# ------------------------------------------------ 6. 30 PIECES + TYPE C + CASING + RESTOCK
card_scene("box", 34.6, 52.3, 15, [
    ("bx-a", 34.7, 40.45, '<div class="k">DATANG DENGAN</div><div class="big">30 PIECES</div><div id="bx-b" class="chip">MATA BIT MACAM-MACAM BENTUK</div>', [("bx-b", 38.35)]),
    ("bx-c", 40.55, 44.8, '<div class="k">CHARGE GUNA</div><div class="v">CABLE TYPE C</div>', []),
    ("bx-d", 44.85, 47.3, '<div class="k">DATANG DENGAN</div><div class="v">CASING</div>', []),
    ("bx-e", 47.4, 52.25, '<div class="k">BRAND KEELAT</div><div class="v">DAH RESTOCK</div><div id="bx-f" class="chip dark">SEBELUM NI HABIS STOCK</div>', [("bx-f", 48.8)]),
])
# ------------------------------------------------------------- 6c. TOONS (key points only, 1-3 s)
from toons import toon, TOP_RIGHT, BOTTOM_RIGHT
LOW_RIGHT = "      #{tid} .toon {{ left:680px; top:1330px; }}\n"     # beside the low demo card
TOONS = [("t-bolt", "bolt_tighten", 14.7, 2.4, LOW_RIGHT),   # "pasang skru, buka skru tu memang mudah"
         ("t-piv", "pivot_fold", 29.6, 2.6, TOP_RIGHT),      # "jadikan lurus pun boleh, tekan, pusing"
         ("t-chg", "fast_charge", 43.0, 2.3, TOP_RIGHT)]     # "untuk charge pakai cable type C"
for k, (tid, kind, t0, d, pos) in enumerate(TOONS):
    th, tc, tj = toon(kind, tid, d)
    hosts.append(scene(tid, t0, d, th, tc + pos.format(tid=tid), tj, 21 + k))

# ------------------------------------------------------------- 7. CTA (64.75 - end)
C0 = 52.3; CD = r(DUR - C0)
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
      #cta-box { position:absolute; left:0; right:0; top:1000px;   /* below the KEELAT logo on the case */ text-align:center; }
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
    tl.fromTo("#cta-l1", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(52.6)});
    tl.fromTo("#cta-l2", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(53.05)});
    tl.fromTo("#cta-arrow", {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {LC(53.4)});
    tl.fromTo("#cta-brand", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {LC(53.75)});
"""
bounce_t = LC(53.95)
for k in range(5):                                       # finite bounces, seek-safe
    cta_js += f'    tl.to("#cta-arrow", {{ y: 22, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56)});\n'
    cta_js += f'    tl.to("#cta-arrow", {{ y: 0, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56 + 0.28)});\n'
    cta_js += f'    tl.to("#cta-bag", {{ rotation: {(-1)**k * 5}, duration: 0.56, ease: "sine.inOut" }}, {r(bounce_t - 0.2 + k*0.56)});\n'
hosts.append(scene("cta", C0, CD, cta_html, cta_css, cta_js, 16))

# ------------------------------------------------------------- 8. BRAND tag (whole)
brand_html = f"""    <div id="brand-tag" class="clip" data-start="3.067" data-duration="{r(C0 - 3.067)}" data-track-index="1">
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
FLASHES = [3.067]
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
    # speed-level display close-up (14-21.6 s): captions move up under the top card so the indicator stays clear
    hi = ""
    cap_html.append(f'    <div id="cg{gi}" class="clip cg"{hi} data-start="{g["start"]}" data-duration="{r(g["end"]-g["start"])}" data-track-index="1"><div class="line">{spans}</div></div>')
    s = g["start"]
    cap_js.append(f'    tl.fromTo("#cg{gi} .line", {{ scale: 0.86, y: 14, opacity: 0 }}, {{ scale: 1, y: 0, opacity: 1, duration: 0.14, ease: "back.out(2)" }}, {s});')
    for wi, w in enumerate(g["words"]):
        cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFD21F" }}, {max(s, w["start"])});')
        if wi < len(g["words"]) - 1:
            cap_js.append(f'    tl.set("#cw{gi}-{wi}", {{ color: "#FFFFFF" }}, {g["words"][wi+1]["start"]});')
caps_css = """
      .cg { position:absolute; left:70px; right:150px; top:1205px; text-align:center; overflow:visible; }
      .cg .line { display:inline-block; font-family:'Inter',sans-serif; font-weight:900; font-size:64px; line-height:1.08;   /* owner: subtitles a little smaller */
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
    (0.00, "whoosh-short", 0.22), (2.43, "impact-bass-1", 0.12), (2.97, "whoosh-cinematic", 0.26),
    (3.08, "pop", 0.42), (5.98, "whoosh-short", 0.2), (10.68, "pop", 0.4), (12.88, "whoosh-short", 0.22),
    (14.68, "sparkle", 0.16), (19.28, "whoosh-short", 0.22), (24.28, "pop", 0.4), (27.58, "whoosh-short", 0.22),
    (29.58, "sparkle", 0.16), (31.78, "pop", 0.4), (34.68, "whoosh-short", 0.22), (38.33, "pop", 0.38),
    (40.53, "pop", 0.42), (42.98, "sparkle", 0.16), (44.83, "pop", 0.4), (47.38, "whoosh-short", 0.22), (48.78, "pop", 0.38),
    (52.28, "sparkle", 0.28), (53.03, "impact-bass-2", 0.07),
]
SFX_LEN = {"whoosh-short": 0.57, "whoosh": 0.57, "whoosh-cinematic": 2.5, "pop": 0.72, "ping": 1.32,
           "impact-bass-1": 2.1, "impact-bass-2": 2.5, "sparkle": 1.8}
sfx_tags = "\n".join(
    f'      <audio id="sfx{k:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{min(SFX_LEN[f], r(DUR - t))}" '
    f'data-volume="{v}" data-track-index="{40 + k % 3}"></audio>' for k, (t, f, v) in enumerate(SFX))

# ------------------------------------------------------------- camera (root tl)
# Natural moves only, as one non-overlapping chain of (t0, t1, from, to, ease) pieces:
# settle-in zooms on the three scene reveals, alternating 0 / +6% framing on jump cuts
# (hides the cut), one push into the screw demo, slow drift elsewhere.
REVEALS = {0.0: (1.14, 1.04, 3.067, "power2.out"), 3.067: (1.2, 1.0, 0.6, "expo.out")}
MERGE_INTO_PREV = set()
CTA_FROM = 52.3                        # one slow push from here to the end
EMPH = {12.933: [(14.0, 1.08, 0.35, "power3.out")]}
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
