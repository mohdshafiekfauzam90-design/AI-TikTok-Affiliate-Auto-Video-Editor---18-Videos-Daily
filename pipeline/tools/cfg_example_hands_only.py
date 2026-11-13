name, proj, data, title = "work_light5", "work-light-5", "work_light_5", "Santino 10\" cordless work light (hands-only take)"
DUR = 51.433; cap0 = 5; capstart = 2.567; CTA_START = 46.7; C0 = 46.7; BRAND0 = 2.567
FIX = '''# ASR slips, checked with prompted + unprompted passes on the original: "Wall light" = "work light", "Size" = "saiz",
# "perbukaan" = "pembukaan", "luar" = "luas", "percayaan" = "pencahayaan", "tampak" = "tapak", "betul" (spine pass)
# = "bentuk" (unprompted original pass), "bag" = "beg".
FIX = {9: "pembukaan", 23: "work", 27: "saiz", 38: "pencahayaan,", 95: "tapak", 100: "bentuk", 122: "beg"}'''
GROUPS = '''[(5, 8), (9, 14), (15, 19), (20, 22), (23, 26), (27, 29), (30, 35), (36, 38), (39, 42), (43, 46), (47, 49),
    (50, 55), (56, 61), (62, 65), (66, 71), (72, 76), (77, 81), (82, 85), (86, 90), (91, 93), (94, 97), (98, 102),
    (103, 105), (106, 110), (111, 115), (116, 124)]'''
FLASHES = "[2.567]"
REVEALS = '{0.0: (1.1, 1.0, 2.567, "sine.inOut"), 2.567: (1.16, 1.0, 0.6, "expo.out")}'
EMPH = '''{2.567: [(4.0, 1.08, 0.35, "power3.out"), (12.2, 1.1, 0.35, "power3.out")], 20.567: [(20.7, 1.08, 0.3, "power3.out"), (24.3, 1.1, 0.35, "power3.out")],
        29.267: [(30.0, 1.08, 0.35, "power3.out")], 39.733: [(40.3, 1.08, 0.35, "power3.out")]}'''
SCENES = r'''# ------------------------------------------------------------------ 1. HOOK (0 - 2.57): the lamp lighting the wall, "memang terang"
HK = 2.567
hook_html = f"""    <div id="hook-top" class="clip" data-start="0" data-duration="{HK}" data-track-index="1">
      <div id="hook-title"><span class="hf-stroke">SERIUS TERANG!</span></div>
      <div id="hook-tag">WORK LIGHT SANTINO 10&Prime;</div>
    </div>
"""
hook_css = """
      #hook-top { position:absolute; left:40px; right:40px; top:1060px; text-align:center; }   /* light spot above, lamp below */
      #hook-title { font-family:'Archivo Black','Inter',sans-serif; font-size:120px; line-height:1.02; color:var(--yellow); text-shadow:0 10px 30px rgba(0,0,0,.45); }
      #hook-tag { display:inline-block; margin-top:14px; background:var(--red); color:var(--white); padding:10px 28px;
        border-radius:14px; transform:rotate(-3deg); font-family:'Archivo Black','Inter',sans-serif; font-size:50px; box-shadow:0 12px 30px rgba(0,0,0,.35); }
"""
hook_js = """    tl.fromTo("#hook-title", { scale: 1.3, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "expo.out" }, 0.02);
    tl.fromTo("#hook-tag", { scale: 0.6, rotation: -14, opacity: 0 }, { scale: 1, rotation: -3, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }, 0.3);
"""
hosts.append(scene("hook", 0, HK, hook_html, hook_css, hook_js, 10))

# hands-only, lamp low and mid-frame: cards in the top band over the bare wall
TOPL_CSS = CARD_CSS.replace(".band { position:absolute; left:48px; bottom:735px; width:620px; }",
                            ".band { position:absolute; left:48px; top:230px; width:600px; }")
assert TOPL_CSS != CARD_CSS
card_scene("level", 2.567, 8.6, 11, [
    ("lv", 2.7, 8.55, '<div class="k">LEVEL 2</div><div class="v">LAGI LUAS</div><div id="lv-1" class="chip">LEVEL 1 &middot; KECIL</div>', [("lv-1", 6.44)]),
], css=TOPL_CSS)
card_scene("spec", 8.6, 20.5, 12, [
    ("sp", 9.6, 13.9, '<div class="k">WORK LIGHT SANTINO</div><div class="v">SAIZ 10 INCI</div>', []),
    ("wk", 14.0, 20.45, '<div class="k">KERJA TAK CUKUP CAHAYA?</div><div class="v">LAMPU KERJA</div>', []),
], css=TOPL_CSS)
card_scene("batt", 20.567, 36.0, 13, [
    ("wr", 20.7, 22.85, '<div class="k">CORDLESS</div><div class="v">TAK PAKAI WIRE</div>', []),
    ("bt", 22.9, 30.9, '<div class="k">BATERI</div><div class="v">TAPAK MAKITA</div><div id="bt-c" class="chip">BELI KEPALA SAHAJA</div>', [("bt-c", 29.0)]),
    ("bs", 31.0, 35.95, '<div class="k">TAK ADA BATERI?</div><div class="v">BELI SEKALI</div>', []),
], css=TOPL_CSS)
card_scene("plug", 36.05, 39.2, 14, [
    ("pl", 36.1, 39.15, '<div class="k">MASUK DEKAT BELAKANG</div><div class="v">TERUS GUNA</div>', []),
], css=TOPL_CSS)
card_scene("base", 39.733, 42.45, 15, [
    ("bs2", 39.85, 42.4, '<div class="k">TAPAK</div><div class="v">BOLEH ADJUST</div>', []),
], css=TOPL_CSS)
from toons import toon, TOP_RIGHT
TOONS = [("t-beam", "light_beam", 4.0, 2.0, TOP_RIGHT),      # "level 2 ni pembukaan dia lagi luas"
         ("t-batt", "battery_fill", 24.3, 2.0, TOP_RIGHT),   # "bateri jenis tapak Makita"
         ("t-fold", "pivot_fold", 40.3, 2.0, TOP_RIGHT)]     # "tapak ... boleh adjust"
for k, (tid, kind, t0, d, pos) in enumerate(TOONS):
    th, tc, tj = toon(kind, tid, d)
    hosts.append(scene(tid, t0, d, th, tc + pos.format(tid=tid), tj, 21 + k))

'''
SFX = '''[
    (0.0, "whoosh-short", 0.2), (0.3, "impact-bass-1", 0.12), (2.47, "whoosh-cinematic", 0.24),
    (2.68, "pop", 0.42), (3.98, "sparkle", 0.16), (6.42, "pop", 0.36), (9.58, "whoosh-short", 0.22), (13.98, "pop", 0.38),
    (20.68, "whoosh-short", 0.22), (22.88, "pop", 0.38), (24.28, "sparkle", 0.16), (28.98, "pop", 0.36), (30.98, "pop", 0.38),
    (36.08, "whoosh-short", 0.22), (39.83, "whoosh-short", 0.22), (40.28, "sparkle", 0.16), (46.68, "sparkle", 0.28), (47.4, "impact-bass-2", 0.07),
]'''
