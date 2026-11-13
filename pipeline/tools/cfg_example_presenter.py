name, proj, data, title = "work_light6", "work-light-6", "work_light_6", "Black Dog COB light (armband / head strap / magnet), take 2"
DUR = 56.167; cap0 = 6; capstart = 2.967; CTA_START = 52.3; C0 = 52.3; BRAND0 = 2.967
FIX = '''# ASR slips, checked with prompted + unprompted passes on the original: "stripe" = "strap", "type C" = "Type-C";
# "tu je" (42-43) is the tail of "bukan setakat tu je" before the cut, left out of the caption.
FIX = {14: "terbaru.", 42: "", 43: "", 56: "strap", 91: "melekat.", 101: "Type-C", 102: "", 103: "sahaja."}'''
GROUPS = '''[(6, 11), (12, 14), (15, 19), (20, 21), (22, 23), (24, 26), (27, 29), (30, 33), (34, 37), (38, 41), (42, 46),
    (47, 52), (53, 59), (60, 62), (63, 65), (66, 71), (72, 77), (78, 81), (82, 85), (86, 88), (89, 91), (92, 95), (96, 98),
    (99, 103), (104, 106), (107, 110), (111, 114), (115, 119), (120, 124), (125, 127)]'''
FLASHES = "[2.967]"
REVEALS = '{0.0: (1.12, 1.03, 2.967, "power2.out"), 2.967: (1.16, 1.0, 0.6, "expo.out")}'
EMPH = '''{2.967: [(5.4, 1.08, 0.35, "power3.out")], 9.467: [(10.3, 1.08, 0.35, "power3.out")], 16.9: [(18.4, 1.1, 0.35, "power3.out")],
        25.867: [(26.6, 1.08, 0.35, "power3.out")], 33.1: [(35.1, 1.1, 0.35, "power3.out")], 40.633: [(43.2, 1.08, 0.35, "power3.out")]}'''
SCENES = r'''# ------------------------------------------------------------------ 1. HOOK (0 - 2.97, in sync): stuck on by the magnet, "melekat"
HK = 2.967
hook_html = f"""    <div id="hook-top" class="clip" data-start="0" data-duration="{HK}" data-track-index="1">
      <div id="hook-title"><span class="hf-stroke">LETAK JE, MELEKAT!</span></div>
      <div id="hook-tag">LAMPU BLACK DOG</div>
    </div>
"""
hook_css = """
      #hook-top { position:absolute; left:40px; right:40px; top:1250px; text-align:center; }
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:104px; line-height:1.02; color:var(--yellow); text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-tag { display:inline-block; margin-top:14px; background:var(--red); color:var(--white); padding:10px 28px;
        border-radius:14px; transform:rotate(-3deg); font-family:'Archivo Black','Inter',sans-serif; font-size:52px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.14, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "expo.out" }, 0.02);
    tl.fromTo("#hook-tag", { scale: 0.6, rotation: -14, opacity: 0 }, { scale: 1, rotation: -3, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }, 0.35);
"""
hosts.append(scene("hook", 0, HK, hook_html, hook_css, hook_js, 10))

LOW_CARD_CSS = CARD_CSS.replace(".band { position:absolute; left:48px; bottom:735px; width:620px; }",
                                ".band { position:absolute; left:48px; bottom:375px; width:620px; }")
assert LOW_CARD_CSS != CARD_CSS
card_scene("intro", 2.967, 9.4, 11, [
    ("in", 3.2, 9.35, '<div class="k">LAMPU BLACK DOG</div><div class="v">MODEL TERBARU</div>', []),
], css=LOW_CARD_CSS)
card_scene("modes", 9.467, 20.65, 12, [
    ("md", 9.6, 15.1, '<div class="k">LAMPU</div><div class="v">3 MODE</div>', []),
    ("cl", 15.25, 20.6, '<div class="k">WARNA</div><div class="v">MERAH &amp; BIRU</div>', []),
], css=LOW_CARD_CSS)
card_scene("sensor", 20.7, 23.0, 13, [
    ("ss", 20.8, 22.95, '<div class="k">SATU LAGI</div><div class="v">ADA SENSOR</div>', []),
], css=LOW_CARD_CSS)
card_scene("wear", 23.033, 33.05, 14, [
    ("dh", 23.2, 28.2, '<div class="k">LEKAT DEKAT</div><div class="v">DAHI PUN BOLEH</div>', []),
    ("st", 28.3, 33.0, '<div class="k">SIAP STRAP</div><div class="v">ATAS KEPALA</div>', []),
], css=LOW_CARD_CSS)
card_scene("magnet", 33.1, 40.6, 15, [
    ("mg", 33.3, 40.55, '<div class="k">BELAKANG ADA</div><div class="v">MAGNET</div><div id="mg-c" class="chip">MELEKAT DI BESI</div>', [("mg-c", 37.1)]),
], css=LOW_CARD_CSS)
card_scene("charge", 40.633, 45.0, 16, [
    ("cg", 40.8, 44.95, '<div class="k">CHARGE</div><div class="v">KABEL TYPE-C</div>', []),
], css=LOW_CARD_CSS)
card_scene("use", 45.033, 52.25, 17, [
    ("us", 47.9, 52.2, '<div class="k">SESUAI UNTUK</div><div class="v">OUTDOOR</div><div class="chips"><div id="us-j" class="chip">JOGGING</div>'
     '<div id="us-m" class="chip">MANCING</div></div>', [("us-j", 48.5), ("us-m", 49.8)]),
], css=LOW_CARD_CSS)
from toons import toon, TOP_RIGHT
TOONS = [("t-beam", "light_beam", 10.3, 2.0, TOP_RIGHT),     # "ni mode yang pertama..."
         ("t-mag", "magnet", 35.1, 2.0, TOP_RIGHT),          # "dia ada magnet tau"
         ("t-cable", "energy_cable", 43.1, 1.8, TOP_RIGHT)]  # "kabel Type-C"
for k, (tid, kind, t0, d, pos) in enumerate(TOONS):
    th, tc, tj = toon(kind, tid, d)
    hosts.append(scene(tid, t0, d, th, tc + pos.format(tid=tid), tj, 21 + k))

'''
SFX = '''[
    (0.0, "whoosh-short", 0.2), (1.3, "impact-bass-1", 0.12), (2.87, "whoosh-cinematic", 0.24),
    (3.18, "pop", 0.42), (9.58, "whoosh-short", 0.22), (10.28, "sparkle", 0.16), (15.23, "pop", 0.38), (20.78, "pop", 0.38),
    (23.18, "whoosh-short", 0.22), (28.28, "pop", 0.38), (33.28, "whoosh-short", 0.22), (35.08, "sparkle", 0.16), (37.08, "pop", 0.36),
    (40.78, "whoosh-short", 0.22), (43.08, "sparkle", 0.16), (47.88, "whoosh-short", 0.22), (48.48, "pop", 0.34), (49.78, "pop", 0.34),
    (52.28, "sparkle", 0.28), (53.0, "impact-bass-2", 0.07),
]'''
