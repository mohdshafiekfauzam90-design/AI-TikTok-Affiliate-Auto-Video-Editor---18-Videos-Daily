"""Generate the HyperFrames project (edit/) for the MUROH DOOH hammer-drill TikTok.

Inputs (pipeline/data):
  spine_transcript.json  whisper large-v3 word timings measured on the cut spine (output time)
  spine_map.json         where every cut lands in output time
Outputs: edit/index.html + edit/compositions/*.html

Every on-screen claim below is something the speaker says in the recording; nothing is
invented (no price, no discount, no specs that are not spoken).
"""
import json, html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDIT = os.path.join(ROOT, "edit")
DATA = os.path.join(ROOT, "pipeline", "data")
W, H, FPS = 1080, 1920, 30
DUR = 69.4                       # spine (68.2 s) + 1.2 s held last frame under the CTA

tx = json.load(open(os.path.join(DATA, "spine_transcript.json")))
cmap = json.load(open(os.path.join(DATA, "spine_map.json")))
CUTS = [s["out_in"] for s in cmap["segments"]] + [cmap["duration"]]

# --------------------------------------------------------------------------- captions
words, SEG_START = [], set()
for seg in tx["segments"]:
    SEG_START.add(len(words)); words.extend(seg["words"])
# ASR slips checked against two passes on the original audio + standard Malay spelling.
FIX = {8: "konkrit", 110: "dia", 172: "drill", 177: "beg"}
W_ = []
for i, w in enumerate(words):
    t = FIX.get(i, w["word"].strip())
    if t.startswith("-") and W_:                       # "lama" "-lama" -> "lama-lama"
        W_[-1]["text"] += t; W_[-1]["end"] = w["end"]; W_[-1]["punct"] = bool(re.search(r"[.,!?]$", t)); continue
    W_.append({"i": i, "seg0": i in SEG_START, "text": t, "start": w["start"], "end": w["end"], "punct": bool(re.search(r"[.,!?]$", t))})
for w in W_:
    w["text"] = re.sub(r"[.,!?]+$", "", w["text"]).upper()
    if w["end"] - w["start"] > 0.6 and not w["text"][0].isdigit():                   # whisper folds pauses into a word's start
        w["start"] = round(w["end"] - 0.42, 2)
HOOK_END = 4.4
cap_words = [w for w in W_ if w["start"] >= HOOK_END]   # hook line is kinetic type instead

# A new sentence starts a new group: whisper segment starts + Malay sentence openers.
OPENERS = {"SO", "UNTUK", "CONTOH", "NANTI", "JANGAN", "LEPAS", "BOLEH", "HARGA", "SATU"}
for k, w in enumerate(cap_words):
    w["new"] = w["seg0"] or w["text"] in OPENERS
groups, cur = [], []
for k, w in enumerate(cap_words):
    cur.append(w)
    nxt = cap_words[k + 1] if k + 1 < len(cap_words) else None
    chars = sum(len(x["text"]) for x in cur)
    if (nxt is None or w["punct"] or len(cur) >= 3 or chars >= 16
            or nxt["start"] - w["end"] >= 0.15 or nxt["new"]):
        groups.append(cur); cur = []
# No orphan single words: an opener joins the next group, anything else the previous one.
merged = []
k = 0
while k < len(groups):
    g = groups[k]
    if len(g) == 1 and g[0]["text"] in OPENERS and k + 1 < len(groups) and len(groups[k + 1]) <= 3:
        groups[k + 1] = g + groups[k + 1]
    elif len(g) == 1 and merged and len(merged[-1]) <= 3 and g[0]["start"] - merged[-1][-1]["end"] < 0.45:
        merged[-1] = merged[-1] + g
    else:
        merged.append(g)
    k += 1
groups = merged
caps = []
for g in groups:
    caps.append({"start": round(g[0]["start"] - 0.04, 2), "end": round(g[-1]["end"] + 0.12, 2), "words": g})
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

# ------------------------------------------------------------------ 1. HOOK (0 - 4.4)
# Frame 0 already carries the headline (thumbnail + hook). The speaker's own line plays
# over the brick-breaking demo; its three beats land as kinetic type on the words.
hook_beats = [("TEBUK DINDING?", 1.26), ("PECAH KONKRIT?", 2.46), ("SEMUA BOLEH!", 3.48)]
hook_html = """    <div id="hook-top" class="clip" data-start="0" data-duration="4.4" data-track-index="1">
      <div id="hook-kicker">REVIEW JUJUR &middot; MUROH DOOH</div>
      <div id="hook-title"><span class="hf-stroke">HAMMER DRILL</span></div>
      <div id="hook-watt"><span>2200</span>WATT</div>
    </div>
""" + "".join(
    f'    <div id="hook-b{k}" class="clip hook-beat" data-start="{t - 0.06:.2f}" data-duration="{(hook_beats[k+1][1] if k < 2 else 4.4) - t + 0.06:.2f}" data-track-index="2">'
    f'<span class="hf-stroke">{html.escape(txt)}</span></div>\n' for k, (txt, t) in enumerate(hook_beats))
hook_css = """
      #hook-top { position:absolute; left:0; right:0; top:206px; text-align:center; }
      #hook-kicker { display:inline-block; background:var(--yellow); color:var(--ink); font-weight:900;
        font-size:34px; letter-spacing:.04em; padding:10px 22px; border-radius:10px; }
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:118px; line-height:1.02;
        margin-top:18px; letter-spacing:-.01em; text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-watt { display:inline-flex; align-items:baseline; gap:14px; margin-top:12px;
        background:var(--red); padding:6px 26px 10px; border-radius:14px; transform:rotate(-3deg);
        font-family:'Archivo Black','Inter',sans-serif; font-size:44px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
      #hook-watt span { font-size:92px; color:var(--yellow); }
      .hook-beat { position:absolute; left:40px; right:40px; top:1060px; text-align:center;
        font-family:'Archivo Black','Inter',sans-serif; font-size:112px; line-height:1; color:var(--white); }
      #hook-b2 { color:var(--yellow); font-size:128px; }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.12 }, { scale: 1, duration: 0.5, ease: "expo.out" }, 0);
    tl.fromTo("#hook-watt", { scale: 0.6, rotation: -14 }, { scale: 1, rotation: -3, duration: 0.45, ease: "back.out(2.2)" }, 0.12);
    tl.fromTo("#hook-kicker", { y: -12 }, { y: 0, duration: 0.4, ease: "power3.out" }, 0);
    tl.to("#hook-top", { y: -26, opacity: 0, duration: 0.22, ease: "power3.in" }, 4.16);
""" + "".join(
    f'    tl.fromTo("#hook-b{k} span", {{ scale: 1.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.24, ease: "expo.out" }}, {t - 0.06:.2f});\n'
    for k, (txt, t) in enumerate(hook_beats)) + """    tl.to("#hook-b2 span", { scale: 1.06, duration: 0.6, ease: "power1.inOut" }, 3.7);
"""
hosts.append(scene("hook", 0, 4.4, hook_html, hook_css, hook_js, 10))

# ------------------------------------------------------------- 2. DEMO (4.4 - 11.8)
demo_html = """    <div id="demo-chip" class="clip" data-start="0.15" data-duration="7.15" data-track-index="1">
      <span class="dot"></span>TEST PECAH BATA
    </div>
"""
demo_css = """
      #demo-chip { position:absolute; left:60px; top:262px; display:flex; align-items:center; gap:16px;
        background:rgba(13,13,13,.78); border:3px solid var(--yellow); color:var(--white); font-weight:900;
        font-size:42px; letter-spacing:.03em; padding:16px 28px; border-radius:16px; }
      #demo-chip .dot { width:22px; height:22px; border-radius:50%; background:var(--red); box-shadow:0 0 0 6px rgba(229,37,42,.3); }
"""
demo_js = """    tl.fromTo("#demo-chip", { x: -60, opacity: 0 }, { x: 0, opacity: 1, duration: 0.4, ease: "power4.out" }, 0.15);
    tl.fromTo("#demo-chip .dot", { scale: 1 }, { scale: 0.6, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 12 }, 0.6);
    tl.to("#demo-chip", { x: -40, opacity: 0, duration: 0.2, ease: "power3.in" }, 7.1);
"""
hosts.append(scene("demo", 4.4, 7.4, demo_html, demo_css, demo_js, 11))

# ------------------------------------------------------ 3. PRODUCT (11.8 - 28.767)
P0 = 11.8; PD = r(CUTS[CUTS.index(28.767)] - P0) if 28.767 in CUTS else 16.967
def L(t): return r(t - P0)       # absolute -> scene-local
prod_html = f"""    <div id="p-name" class="clip" data-start="{L(12.9)}" data-duration="{L(15.75)-L(12.9)}" data-track-index="1">
      <div class="lbl">INI DIA</div>
      <div class="big"><span class="hf-stroke">ROTARY</span><br><span class="hf-stroke">HAMMER DRILL</span></div>
    </div>
    <div id="p-bajet" class="clip sticker" data-start="{L(14.22)}" data-duration="{L(15.75)-L(14.22)}" data-track-index="2">HARGA BAJET</div>
    <div id="p-watt" class="clip" data-start="{L(16.2)}" data-duration="{L(18.45)-L(16.2)}" data-track-index="1">
      <div class="num"><span id="p-watt-n" class="hf-stroke">2200</span></div>
      <div class="unit">WATT</div>
    </div>
    <div id="p-mode" class="clip" data-start="{L(18.45)}" data-duration="{L(26.5)-L(18.45)}" data-track-index="1">
      <div class="head"><span class="n">2</span> MODE <span class="sub">BOLEH ADJUST</span></div>
      <div class="chips">
        <div id="p-mode-1" class="chip"><b>1</b>HACKING</div>
        <div id="p-mode-2" class="chip"><b>2</b>TEBUK DINDING</div>
      </div>
    </div>
    <div id="p-plug" class="clip" data-start="{L(27.6)}" data-duration="{L(28.767)-L(27.6)}" data-track-index="2">
      <span class="ic">&#9889;</span>PLUG 3 PIN
    </div>
"""
prod_css = """
      #p-name { position:absolute; left:60px; right:60px; top:256px; }
      #p-name .lbl { display:inline-block; background:var(--yellow); color:var(--ink); font-weight:900; font-size:34px;
        padding:8px 18px; border-radius:10px; letter-spacing:.05em; }
      #p-name .big { font-family:'Archivo Black','Inter',sans-serif; font-size:96px; line-height:1.0; margin-top:14px; }
      .sticker { position:absolute; right:70px; top:520px; background:var(--red); color:var(--white);
        font-family:'Archivo Black','Inter',sans-serif; font-size:56px; padding:14px 28px; border-radius:16px;
        border:5px solid var(--white); box-shadow:0 14px 30px rgba(0,0,0,.4); }
      #p-watt { position:absolute; left:0; right:0; top:262px; text-align:center; }
      #p-watt .num { font-family:'Archivo Black','Inter',sans-serif; font-size:230px; line-height:.95; color:var(--yellow);
        text-shadow:0 14px 40px rgba(0,0,0,.45); }
      #p-watt .unit { display:inline-block; margin-top:4px; background:var(--ink); color:var(--white); font-weight:900;
        font-size:64px; letter-spacing:.3em; padding:6px 10px 6px 30px; border-radius:12px; }
      #p-mode { position:absolute; left:60px; right:60px; top:256px; }
      #p-mode .head { font-family:'Archivo Black','Inter',sans-serif; font-size:96px; line-height:1; paint-order:stroke fill; -webkit-text-stroke:14px var(--ink); }
      #p-mode .head .sub { -webkit-text-stroke:0; }
      #p-mode .head .n { color:var(--yellow); }
      #p-mode .head .sub { display:inline-block; vertical-align:middle; font-family:'Inter'; font-weight:900;
        font-size:30px; background:var(--white); color:var(--ink); padding:8px 14px; border-radius:10px; margin-left:8px; }
      #p-mode .chips { display:flex; flex-direction:column; gap:18px; margin-top:26px; align-items:flex-start; }
      #p-mode .chip { display:flex; align-items:center; gap:18px; background:rgba(13,13,13,.82); border:3px solid var(--yellow);
        font-weight:900; font-size:50px; padding:14px 30px 14px 16px; border-radius:18px; opacity:0; }
      #p-mode .chip b { display:inline-flex; align-items:center; justify-content:center; width:62px; height:62px;
        border-radius:12px; background:var(--yellow); color:var(--ink); font-size:40px; }
      #p-plug { position:absolute; left:60px; top:262px; display:flex; align-items:center; gap:14px; background:var(--yellow);
        color:var(--ink); font-weight:900; font-size:58px; padding:14px 30px; border-radius:16px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
      #p-plug .ic { font-size:52px; }
"""
prod_js = f"""    tl.fromTo("#p-name .lbl", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {L(12.9)});
    tl.fromTo("#p-name .big", {{ y: 40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {L(12.98)});
    tl.to("#p-name", {{ opacity: 0, y: -20, duration: 0.2, ease: "power3.in" }}, {L(15.5)});
    tl.fromTo("#p-bajet", {{ scale: 0.2, rotation: -24 }}, {{ scale: 1, rotation: -6, duration: 0.42, ease: "back.out(2.4)" }}, {L(14.22)});
    tl.to("#p-bajet", {{ scale: 0.4, opacity: 0, duration: 0.18, ease: "power3.in" }}, {L(15.55)});
    tl.fromTo("#p-watt", {{ scale: 0.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "expo.out" }}, {L(16.2)});
    tl.fromTo("#p-watt-n", {{ textContent: 0 }}, {{ textContent: 2200, duration: 1.4, ease: "power2.out", snap: {{ textContent: 10 }} }}, {L(16.26)});
    tl.fromTo("#p-watt .unit", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power3.out" }}, {L(17.74)});
    tl.to("#p-watt", {{ opacity: 0, scale: 0.92, duration: 0.18, ease: "power3.in" }}, {L(18.25)});
    tl.fromTo("#p-mode .head", {{ x: -80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {L(18.45)});
    tl.fromTo("#p-mode-1", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, {L(23.1)});
    tl.fromTo("#p-mode-2", {{ x: -60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, {L(25.0)});
    tl.to("#p-mode-1", {{ opacity: 0.55, duration: 0.2 }}, {L(25.0)});
    tl.to("#p-mode", {{ opacity: 0, x: -30, duration: 0.2, ease: "power3.in" }}, {L(26.28)});
    tl.fromTo("#p-plug", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, {L(27.6)});
"""
hosts.append(scene("product", P0, PD, prod_html, prod_css, prod_js, 12))

# ---------------------------------------------------------- 4. KIT (28.767 - 41.9)
K0 = 28.767; KD = r(41.9 - K0)
def LK(t): return r(t - K0)
kit_items = [("k1", "CASING", "", 31.85), ("k2", "MATA &times;6 BATANG", "HACKING + TEBUK DINDING", 33.95),
             ("k3", "MINYAK GREASE", "", 39.45), ("k4", "1 CARBON", "", 40.45)]
kit_html = f"""    <div id="kit-panel" class="clip" data-start="{LK(30.45)}" data-duration="{LK(41.9)-LK(30.45)}" data-track-index="1">
      <div class="head">DAPAT SEKALI</div>
""" + "".join(f"""      <div id="{k}" class="item"><span class="tick">&#10003;</span><div><div class="t">{t}</div>{f'<div class="s">{s}</div>' if s else ''}</div></div>
""" for k, t, s, _ in kit_items) + "    </div>\n"
kit_css = """
      #kit-panel { position:absolute; left:56px; top:256px; width:640px; background:rgba(13,13,13,.84);
        border-radius:26px; padding:26px 30px 14px; border-left:12px solid var(--yellow); box-shadow:0 18px 40px rgba(0,0,0,.4); }
      #kit-panel .head { font-family:'Archivo Black','Inter',sans-serif; font-size:52px; color:var(--yellow); margin-bottom:10px; }
      #kit-panel .item { display:flex; align-items:flex-start; gap:18px; padding:10px 0; opacity:0; }
      #kit-panel .tick { flex:none; display:inline-flex; align-items:center; justify-content:center; width:52px; height:52px;
        border-radius:50%; background:var(--yellow); color:var(--ink); font-weight:900; font-size:34px; margin-top:2px; }
      #kit-panel .t { font-weight:900; font-size:48px; line-height:1.1; }
      #kit-panel .s { font-weight:700; font-size:30px; color:#d9d9d9; margin-top:4px; letter-spacing:.02em; }
"""
kit_js = f"""    tl.fromTo("#kit-panel", {{ x: -80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {LK(30.45)});
""" + "".join(f"""    tl.fromTo("#{k}", {{ x: -40, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.32, ease: "back.out(1.7)" }}, {LK(t)});
    tl.fromTo("#{k} .tick", {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: "back.out(3)" }}, {LK(t) + 0.06:.3f});
""" for k, _, _, t in kit_items) + f"""    tl.to("#kit-panel", {{ x: -60, opacity: 0, duration: 0.22, ease: "power3.in" }}, {LK(41.62)});
"""
hosts.append(scene("kit", K0, KD, kit_html, kit_css, kit_js, 13))

# ---------------------------------------------------------- 5. TIPS (41.9 - 59.5)
T0 = 41.9; TD = r(59.5 - T0)
def LT(t): return r(t - T0)
tips_html = f"""    <div id="tip1" class="clip tip" data-start="{LT(42.0)}" data-duration="{LT(50.6)-LT(42.0)}" data-track-index="1">
      <div class="tag">TIP</div>
      <div class="h">TUKAR CARBON SENANG</div>
      <div id="tip1-a" class="b">Tukar kat bawah je &mdash; tak perlu buka sampai dalam</div>
      <div id="tip1-b" class="b2">Ada kiri &amp; kanan</div>
    </div>
    <div id="tip2" class="clip tip" data-start="{LT(50.75)}" data-duration="{LT(57.3)-LT(50.75)}" data-track-index="1">
      <div class="tag">TIP</div>
      <div class="h">DAH GUNA BANYAK KALI?</div>
      <div class="b">Letak grease balik kat atas</div>
    </div>
    <div id="tip3" class="clip" data-start="{LT(57.95)}" data-duration="{LT(59.45)-LT(57.95)}" data-track-index="2">
      <span class="tick">&#10003;</span>MINYAK GREASE DISERTAKAN
    </div>
"""
tips_css = """
      .tip { position:absolute; left:56px; right:120px; top:256px; background:var(--white); color:var(--ink);
        border-radius:26px; padding:26px 32px 28px; box-shadow:0 18px 40px rgba(0,0,0,.35); }
      .tip .tag { display:inline-block; background:var(--red); color:var(--white); font-weight:900; font-size:30px;
        letter-spacing:.12em; padding:6px 16px; border-radius:8px; }
      .tip .h { font-family:'Archivo Black','Inter',sans-serif; font-size:58px; line-height:1.05; margin-top:12px; }
      .tip .b { font-weight:800; font-size:40px; line-height:1.2; margin-top:12px; color:#222; }
      .tip .b2 { display:inline-block; font-weight:900; font-size:36px; margin-top:16px; background:var(--yellow);
        padding:8px 18px; border-radius:10px; opacity:0; }
      #tip3 { position:absolute; left:56px; top:262px; display:flex; align-items:center; gap:16px; background:rgba(13,13,13,.84);
        border:3px solid var(--yellow); font-weight:900; font-size:44px; padding:16px 28px; border-radius:16px; }
      #tip3 .tick { display:inline-flex; align-items:center; justify-content:center; width:50px; height:50px; border-radius:50%;
        background:var(--yellow); color:var(--ink); font-size:32px; }
"""
tips_js = f"""    tl.fromTo("#tip1", {{ y: -40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {LT(42.0)});
    tl.fromTo("#tip1-a", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {LT(42.3)});
    tl.fromTo("#tip1-b", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, {LT(45.75)});
    tl.to("#tip1", {{ y: -30, opacity: 0, duration: 0.2, ease: "power3.in" }}, {LT(50.35)});
    tl.fromTo("#tip2", {{ y: -40, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "expo.out" }}, {LT(50.75)});
    tl.to("#tip2", {{ y: -30, opacity: 0, duration: 0.2, ease: "power3.in" }}, {LT(57.05)});
    tl.fromTo("#tip3", {{ x: -50, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, {LT(57.95)});
    tl.to("#tip3", {{ opacity: 0, duration: 0.15 }}, {LT(59.28)});
"""
hosts.append(scene("tips", T0, TD, tips_html, tips_css, tips_js, 14))

# --------------------------------------------------------- 6. WHO (59.5 - 64.75)
U0 = 59.5; UD = r(64.75 - U0)
def LU(t): return r(t - U0)
who_html = f"""    <div id="who-bajet" class="clip sticker" data-start="{LU(59.6)}" data-duration="{LU(64.6)-LU(59.6)}" data-track-index="2">HARGA BAJET</div>
    <div id="who-panel" class="clip" data-start="{LU(60.5)}" data-duration="{LU(64.6)-LU(60.5)}" data-track-index="1">
      <div class="h">SESUAI UNTUK</div>
      <div id="who-1" class="row"><span class="tick">&#10003;</span>TUKANG</div>
      <div id="who-2" class="row"><span class="tick">&#10003;</span>CONTRACTOR</div>
    </div>
"""
who_css = """
      .sticker { position:absolute; right:70px; top:270px; background:var(--red); color:var(--white);
        font-family:'Archivo Black','Inter',sans-serif; font-size:56px; padding:14px 28px; border-radius:16px;
        border:5px solid var(--white); box-shadow:0 14px 30px rgba(0,0,0,.4); }
      #who-panel { position:absolute; left:56px; top:420px; }
      #who-panel .h { font-family:'Archivo Black','Inter',sans-serif; font-size:64px; paint-order:stroke fill; -webkit-text-stroke:12px var(--ink); text-shadow:0 8px 24px rgba(0,0,0,.5); }
      #who-panel .row { display:flex; align-items:center; gap:16px; margin-top:16px; background:var(--yellow); color:var(--ink);
        font-weight:900; font-size:56px; padding:12px 30px 12px 14px; border-radius:16px; width:max-content; opacity:0; }
      #who-panel .tick { display:inline-flex; align-items:center; justify-content:center; width:58px; height:58px; border-radius:12px;
        background:var(--ink); color:var(--yellow); font-size:38px; }
"""
who_js = f"""    tl.fromTo("#who-bajet", {{ scale: 0.2, rotation: 20 }}, {{ scale: 1, rotation: 5, duration: 0.42, ease: "back.out(2.4)" }}, {LU(59.6)});
    tl.fromTo("#who-panel .h", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "expo.out" }}, {LU(60.5)});
    tl.fromTo("#who-1", {{ x: -50, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.32, ease: "back.out(1.8)" }}, {LU(61.15)});
    tl.fromTo("#who-2", {{ x: -50, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.32, ease: "back.out(1.8)" }}, {LU(61.95)});
    tl.to(["#who-panel", "#who-bajet"], {{ opacity: 0, duration: 0.18, ease: "power3.in" }}, {LU(64.4)});
"""
hosts.append(scene("who", U0, UD, who_html, who_css, who_js, 15))

# ------------------------------------------------------------- 7. CTA (64.75 - end)
C0 = 64.75; CD = r(DUR - C0)
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
    tl.fromTo("#cta-l1", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(65.1)});
    tl.fromTo("#cta-l2", {{ scale: 1.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "expo.out" }}, {LC(65.55)});
    tl.fromTo("#cta-arrow", {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {LC(65.9)});
    tl.fromTo("#cta-brand", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "expo.out" }}, {LC(66.3)});
"""
bounce_t = LC(66.3)
for k in range(5):                                       # finite bounces, seek-safe
    cta_js += f'    tl.to("#cta-arrow", {{ y: 22, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56)});\n'
    cta_js += f'    tl.to("#cta-arrow", {{ y: 0, duration: 0.28, ease: "power1.inOut" }}, {r(bounce_t + k*0.56 + 0.28)});\n'
    cta_js += f'    tl.to("#cta-bag", {{ rotation: {(-1)**k * 5}, duration: 0.56, ease: "sine.inOut" }}, {r(bounce_t - 0.2 + k*0.56)});\n'
hosts.append(scene("cta", C0, CD, cta_html, cta_css, cta_js, 16))

# ------------------------------------------------------------- 8. BRAND tag (whole)
brand_html = f"""    <div id="brand-tag" class="clip" data-start="4.4" data-duration="{r(C0 - 4.4)}" data-track-index="1">
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
FLASHES = [11.8, 28.767]
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
    (0.00, "whoosh-short", 0.28), (1.20, "pop", 0.55), (2.40, "pop", 0.55), (3.42, "impact-bass-1", 0.12),
    (4.34, "whoosh", 0.30), (7.34, "whoosh-short", 0.26), (11.62, "whoosh-cinematic", 0.30),
    (12.92, "pop", 0.42), (14.20, "pop", 0.55), (17.72, "ping", 0.75), (18.43, "whoosh-short", 0.22),
    (23.08, "pop", 0.45), (24.98, "pop", 0.45), (27.56, "pop", 0.42), (28.62, "whoosh-cinematic", 0.28),
    (30.42, "whoosh-short", 0.2), (31.82, "pop", 0.4), (33.92, "ping", 0.6), (39.42, "pop", 0.4), (40.42, "pop", 0.4),
    (41.96, "whoosh", 0.24), (45.72, "pop", 0.4), (50.72, "whoosh-short", 0.24), (57.92, "pop", 0.4),
    (59.58, "pop", 0.5), (61.12, "pop", 0.42), (61.92, "pop", 0.42), (64.78, "sparkle", 0.28), (65.08, "impact-bass-2", 0.07),
]
SFX_LEN = {"whoosh-short": 0.57, "whoosh": 0.57, "whoosh-cinematic": 2.5, "pop": 0.72, "ping": 1.32,
           "impact-bass-1": 2.1, "impact-bass-2": 2.5, "sparkle": 1.8}
sfx_tags = "\n".join(
    f'      <audio id="sfx{k:02d}" class="clip" src="assets/sfx/{f}.mp3" data-start="{t}" data-duration="{min(SFX_LEN[f], r(DUR - t))}" '
    f'data-volume="{v}" data-track-index="{40 + k % 3}"></audio>' for k, (t, f, v) in enumerate(SFX))

# ------------------------------------------------------------- camera (root tl)
# Natural moves only, as one non-overlapping chain of (t0, t1, from, to, ease) pieces:
# settle-in zooms on the three scene reveals, alternating 0 / +6% framing on jump cuts
# (hides the cut), one push on "2200 watt", one on "6 batang", slow drift elsewhere.
REVEALS = {0.0: (1.20, 1.04, 4.4, "power2.out"), 11.8: (1.22, 1.0, 0.7, "expo.out"),
           28.767: (1.2, 1.0, 0.55, "expo.out")}
MERGE_INTO_PREV = {12.0}                 # cut inside the reveal move
CTA_FROM = 64.233                        # one slow push from here to the end
EMPH = {15.733: [(16.26, 1.13, 0.4, "power3.out"), (18.3, 1.04, 0.7, "power2.inOut")],
        33.9: [(33.9, 1.12, 0.35, "power3.out")]}
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
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
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
