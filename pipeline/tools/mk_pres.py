"""mk_pres.py <config.py>: build pipeline/gen_<name>.py from gen_work_light3.py (presenter on camera)."""
import sys, runpy
C = runpy.run_path(sys.argv[1])
s = open('pipeline/gen_work_light3.py').read()
def R(a_, b_):
    global s
    assert a_ in s, a_[:90]; s = s.replace(a_, b_)
R('"""Generate the HyperFrames project (projects/work-light-3/) for the MUROH DOOH Black Dog COB light (armband / head strap) TikTok.',
  f'"""Generate the HyperFrames project (projects/{C["proj"]}/) for the MUROH DOOH {C["title"]} TikTok.')
s = s.replace('pipeline/data/work_light_3', f'pipeline/data/{C["data"]}').replace('projects/work-light-3/', f'projects/{C["proj"]}/')
R('"projects", "work-light-3"', f'"projects", "{C["proj"]}"'); R('"data", "work_light_3"', f'"data", "{C["data"]}"')
R('DUR = 49.5                       # spine (48.3 s) + 1.2 s held last frame under the CTA', f'DUR = {C["DUR"]}                      # spine + 1.2 s held last frame under the CTA')
R('cap_words = [w for w in W_ if w["i"] >= 10]  # words 0-9', f'cap_words = [w for w in W_ if w["i"] >= {C["cap0"]}]  # earlier words = hook line')
R('caps[0]["start"] = max(caps[0]["start"], 4.12)', f'caps[0]["start"] = max(caps[0]["start"], {C["capstart"]})')
R('CTA_START = 42.1 ', f'CTA_START = {C["CTA_START"]} ')
a = s.index('# ASR slips, checked with prompted'); b = s.index('W_ = []')
s = s[:a] + C["FIX"].strip() + "\n" + s[b:]
a = s.index('MANUAL_GROUPS = ['); b = s.index('groups = [[w for w in W_')
s = s[:a] + "MANUAL_GROUPS = " + C["GROUPS"].strip() + "\n" + s[b:]
a = s.index('# ------------------------------------------------------------------ 1. HOOK'); b = s.index('# ------------------------------------------------------------- 7. CTA')
s = s[:a] + C["SCENES"] + s[b:]
R('''    hi = ' style="top:1580px"' if 34.7 <= g["start"] < 42.1 else ""   # strap demo mid-frame''', "    " + C.get("HI", 'hi = ""'))
C0 = C["C0"]
for a_, b_ in [('C0 = 42.333; CD = r(DUR - C0)', f'C0 = {C0}; CD = r(DUR - C0)'),
 ('{LC(42.65)}', f'{{LC({C0+0.3:.3f})}}'), ('{LC(43.1)}', f'{{LC({C0+0.75:.3f})}}'), ('{LC(43.45)}', f'{{LC({C0+1.1:.3f})}}'),
 ('{LC(43.8)}', f'{{LC({C0+1.45:.3f})}}'), ('bounce_t = LC(44.0)', f'bounce_t = LC({C0+1.65:.3f})'),
 ('data-start="4.1" data-duration="{r(C0 - 4.1)}"', f'data-start="{C["BRAND0"]}" data-duration="{{r(C0 - {C["BRAND0"]})}}"'),
 ('FLASHES = [4.1]', f'FLASHES = {C["FLASHES"]}'),
 ('REVEALS = {0.0: (1.12, 1.03, 4.1, "power2.out"), 4.1: (1.2, 1.0, 0.6, "expo.out")}', 'REVEALS = ' + C["REVEALS"]),
 ('CTA_FROM = 42.333 ', f'CTA_FROM = {C0} '),
 ('EMPH = {14.667: [(17.7, 1.1, 0.35, "power3.out")], 19.933: [(21.9, 1.1, 0.35, "power3.out")],\n        27.267: [(30.9, 1.1, 0.35, "power3.out")], 35.133: [(36.7, 1.08, 0.35, "power3.out")]}', 'EMPH = ' + C["EMPH"]),
 ('one punch-in per key point (merah, sensor, magnet, kepala)', 'one punch-in per key point')]:
    R(a_, b_)
if "CTA_TOP" in C:
    R('#cta-box { position:absolute; left:0; right:0; top:860px;', f'#cta-box {{ position:absolute; left:0; right:0; top:{C["CTA_TOP"]}px;')
a = s.index('SFX = ['); b = s.index('SFX_LEN = {')
s = s[:a] + "SFX = " + C["SFX"].strip() + "\n" + s[b:]
open(f'pipeline/gen_{C["name"]}.py', 'w').write(s); print('ok', C["name"])
