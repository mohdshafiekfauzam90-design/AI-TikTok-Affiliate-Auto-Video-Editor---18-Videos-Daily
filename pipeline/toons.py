"""Small cartoon explainer animations ("toons") for key points, 1-3 s each.

The owner's rule: a short, clean cartoon only where a point needs explaining, never over the
product or the real demo. Each toon is a 364x236 badge (dark glass panel, yellow border, ink
outlines in the MUROH DOOH palette) placed in a free corner, popping in and out on its own clip.

    html, css, js = toon(kind, tid, dur)
    hosts.append(scene(tid, t0, dur, html, css + pos_css, js, track))

`js` uses times relative to the toon's own start (the scene's local timeline), finite tweens only
(seek-safe). Kinds:
    battery_fill   bars of a battery light up one by one, then a bolt  (indicator / capacity)
    energy_cable   energy pulses run along a cable from a battery to a tool  (cable / powers tools)
    long_runtime   a clock hand spins twice beside a full battery  ("boleh guna lama", "berjam-jam")
    fast_charge    a plug pushes energy into a battery that fills fast  (charger / high watt)
    sparks         a grinder disc spins and throws sparks off a steel bar  (grinder cutting)
    drill_wall     a drill bit pushes through a wall, dust flying out  (drill)
    bolt_tighten   a bolt turns and drives into a plate  (impact wrench)
    wind_flow      curved air lines stream out of a fan  (fan)
    pivot_fold     a pistol-grip screwdriver's handle swings round to straight  ("tekan, pusing", lurus)
    light_beam     a work lamp switches on and throws a fan of light  (work light: terang, mod cahaya)
    magnet         a horseshoe magnet pulls a light bar onto it  ("ada magnet", lekat dekat besi)
    saw_cut        a circular-saw blade spins across a plank, cutting it with sawdust flying  (circular saw: potong papan)
    chain_run      a chainsaw bar with its chain running drops through a log, chips flying  (chainsaw: potong kayu / pokok)
    oil_drop       oil drips from a can onto a running chain, which turns glossy  (minyak rantai: basahkan rantai)
    fuel_mix       petrol and 2T oil pour into one can and swirl together  (petrol bancuh 2T)
    touch_screen   a gloved finger taps a phone screen, ripples answer  (sarung tangan boleh guna skrin sentuh)
    glove_shield   a glove with a shield badge, hits bounce off it  (lindung tangan, tahan lasak)
    leaf_blow      a blower nozzle pushes air lines that sweep leaves away  (blower: tiup daun / habuk)
"""
INK, YEL, RED, WHITE = "#0D0D0D", "#FFD21F", "#E5252A", "#FFFFFF"

BASE_CSS = """
      .toon { position:absolute; width:364px; height:236px; border-radius:28px; background:rgba(13,13,13,.74);
        border:4px solid var(--yellow); box-shadow:0 18px 40px rgba(0,0,0,.4); display:flex; align-items:center; justify-content:center; }
      .toon svg { width:344px; height:215px; overflow:visible; }
"""
TOP_RIGHT = "      #{tid} .toon {{ left:680px; top:250px; }}\n"         # beside a top-band card
BOTTOM_RIGHT = "      #{tid} .toon {{ left:680px; top:949px; }}\n"      # beside a bottom-band card (ends y 1185)


def _battery(p, x, y, w, h, bars_on=False):
    pad, gap = 10, 6
    bw = (w - 2 * pad - 3 * gap) / 4
    bars = "".join(
        f'<rect id="{p}-b{i}" x="{x + pad + i * (bw + gap):.1f}" y="{y + pad}" width="{bw:.1f}" height="{h - 2 * pad}" rx="5" '
        f'fill="{YEL}" stroke="{INK}" stroke-width="3"{"" if bars_on else " opacity=\"0\""}/>' for i in range(4))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{WHITE}" stroke="{INK}" stroke-width="7"/>'
            f'<rect x="{x + w + 2}" y="{y + h * 0.3:.1f}" width="14" height="{h * 0.4:.1f}" rx="4" fill="{INK}"/>' + bars)


def _bolt(pid, cx, cy, s=1.0, fill=RED):
    pts = [(4, -30), (-14, 4), (0, 4), (-6, 30), (14, -6), (0, -6)]
    d = "M" + " L".join(f"{cx + px * s:.1f} {cy + py * s:.1f}" for px, py in pts) + " Z"
    return f'<path id="{pid}" d="{d}" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'


def _pop(tid, dur):
    return (f'    tl.fromTo("#{tid} .toon", {{ scale: 0.4, opacity: 0, rotation: -6 }}, {{ scale: 1, opacity: 1, rotation: 0, duration: 0.35, ease: "back.out(2.2)" }}, 0);\n'
            f'    tl.to("#{tid} .toon", {{ scale: 0.7, opacity: 0, duration: 0.2, ease: "power3.in" }}, {round(dur - 0.22, 3)});\n')


def _bars_in(p, t0, step):
    return "".join(f'    tl.fromTo("#{p}-b{i}", {{ opacity: 0, scaleY: 0.2, transformOrigin: "50% 100%" }}, '
                   f'{{ opacity: 1, scaleY: 1, duration: 0.18, ease: "back.out(2)" }}, {round(t0 + i * step, 3)});\n' for i in range(4))


def toon(kind, tid, dur):
    p = tid
    if kind == "battery_fill":
        svg = _battery(p, 66, 55, 170, 90) + _bolt(f"{p}-z", 151, 100, 1.25)
        js = _bars_in(p, 0.3, 0.22) + \
             f'    tl.fromTo("#{p}-z", {{ scale: 0, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)" }}, 1.25);\n'
    elif kind == "energy_cable":
        d = "M122 100 C 170 30, 214 170, 258 100"
        svg = (_battery(p, 14, 72, 92, 56, bars_on=True) +
               f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
               f'<path id="{p}-e" d="{d}" fill="none" stroke="{YEL}" stroke-width="6" stroke-linecap="round" stroke-dasharray="12 18"/>'
               f'<circle cx="284" cy="100" r="28" fill="{RED}" stroke="{INK}" stroke-width="6"/>' + _bolt(f"{p}-z", 284, 100, 0.7, WHITE))
        js = (f'    tl.fromTo("#{p}-e", {{ strokeDashoffset: 0 }}, {{ strokeDashoffset: -300, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n'
              f'    tl.fromTo("#{p}-z", {{ scale: 0.6, transformOrigin: "50% 50%" }}, {{ scale: 1.25, duration: 0.25, ease: "power2.out" }}, 0.8);\n'
              f'    tl.to("#{p}-z", {{ scale: 1, duration: 0.25, ease: "power2.in" }}, 1.05);\n'
              f'    tl.to("#{p}-z", {{ scale: 1.25, duration: 0.25, ease: "power2.out" }}, 1.4);\n'
              f'    tl.to("#{p}-z", {{ scale: 1, duration: 0.25, ease: "power2.in" }}, 1.65);\n')
    elif kind == "long_runtime":
        ticks = "".join(f'<line x1="{95 + 50 * c:.1f}" y1="{100 + 50 * s:.1f}" x2="{95 + 58 * c:.1f}" y2="{100 + 58 * s:.1f}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
                        for c, s in [(0, -1), (1, 0), (0, 1), (-1, 0)])
        svg = (f'<circle cx="95" cy="100" r="66" fill="{WHITE}" stroke="{INK}" stroke-width="7"/>' + ticks +
               f'<line id="{p}-h" x1="95" y1="100" x2="95" y2="54" stroke="{RED}" stroke-width="8" stroke-linecap="round"/>'
               f'<line x1="95" y1="100" x2="122" y2="100" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
               f'<circle cx="95" cy="100" r="8" fill="{INK}"/>' + _battery(p, 186, 66, 104, 68, bars_on=True))
        js = (f'    tl.fromTo("#{p}-h", {{ rotation: 0, svgOrigin: "95 100" }}, {{ rotation: 720, duration: {round(dur - 0.5, 3)}, ease: "power1.inOut" }}, 0.2);\n' +
              "".join(f'    tl.fromTo("#{p}-b{i}", {{ opacity: 0.35 }}, {{ opacity: 1, duration: 0.3, repeat: 2, repeatDelay: 0.2, ease: "power1.out" }}, {round(0.4 + 0.08 * i, 3)});\n'
                      for i in range(4)))
    elif kind == "fast_charge":
        svg = (f'<rect x="20" y="72" width="58" height="56" rx="12" fill="{INK}" stroke="{WHITE}" stroke-width="3"/>'
               f'<rect x="2" y="84" width="20" height="9" rx="3" fill="{WHITE}" stroke="{INK}" stroke-width="2"/>'
               f'<rect x="2" y="107" width="20" height="9" rx="3" fill="{WHITE}" stroke="{INK}" stroke-width="2"/>'
               f'<path d="M80 100 L168 100" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
               f'<path id="{p}-e" d="M80 100 L168 100" stroke="{YEL}" stroke-width="6" stroke-linecap="round" stroke-dasharray="10 14" fill="none"/>' +
               _battery(p, 172, 60, 118, 80) + _bolt(f"{p}-z", 231, 100, 1.05))
        js = (f'    tl.fromTo("#{p}-e", {{ strokeDashoffset: 0 }}, {{ strokeDashoffset: -240, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n' +
              _bars_in(p, 0.35, 0.14) +
              f'    tl.fromTo("#{p}-z", {{ scale: 0, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)" }}, 0.95);\n')
    elif kind == "sparks":
        sp = "".join(f'<line id="{p}-s{i}" x1="170" y1="126" x2="{170 + 80 * c:.0f}" y2="{126 + 80 * s:.0f}" stroke="{YEL if i % 2 else RED}" stroke-width="5" stroke-linecap="round"/>'
                     for i, (c, s) in enumerate([(0.95, -0.3), (0.9, -0.1), (0.8, -0.5), (1.0, 0.12), (0.7, -0.65), (0.85, 0.25)]))
        svg = (f'<rect x="20" y="128" width="290" height="26" rx="6" fill="#9AA0A6" stroke="{INK}" stroke-width="6"/>' + sp +
               f'<g id="{p}-d"><circle cx="150" cy="80" r="52" fill="#C9CDD2" stroke="{INK}" stroke-width="7"/>'
               f'<line x1="150" y1="34" x2="150" y2="126" stroke="{INK}" stroke-width="4"/><line x1="104" y1="80" x2="196" y2="80" stroke="{INK}" stroke-width="4"/>'
               f'<circle cx="150" cy="80" r="12" fill="{INK}"/></g>')
        js = (f'    tl.fromTo("#{p}-d", {{ rotation: 0, svgOrigin: "150 80" }}, {{ rotation: 1080, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n' +
              "".join(f'    tl.fromTo("#{p}-s{i}", {{ opacity: 0, scale: 0.2, svgOrigin: "170 126" }}, {{ opacity: 1, scale: 1, duration: 0.15, '
                      f'yoyo: true, repeat: {2 * max(1, int((dur - 0.6) / 0.3)) - 1}, ease: "power2.out" }}, {round(0.25 + 0.05 * i, 3)});\n'
                      for i in range(6)))
    elif kind == "drill_wall":
        dust = "".join(f'<circle id="{p}-p{i}" cx="200" cy="{100 + dy}" r="{r}" fill="#D8C7A8" stroke="{INK}" stroke-width="2" opacity="0"/>'
                       for i, (dy, r) in enumerate([(-18, 6), (14, 5), (-4, 7), (22, 4)]))
        svg = (f'<g id="{p}-b"><rect x="20" y="82" width="90" height="36" rx="10" fill="{YEL}" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M110 92 H190 L206 100 L190 108 H110 Z" fill="#C9CDD2" stroke="{INK}" stroke-width="5"/>'
               f'<path d="M122 92 L132 108 M142 92 L152 108 M162 92 L172 108" stroke="{INK}" stroke-width="3"/></g>'
               f'<rect x="196" y="22" width="96" height="156" fill="#E7DCC8" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M196 70 H292 M196 120 H292 M240 22 V70 M220 70 V120 M262 120 V178" stroke="{INK}" stroke-width="3"/>' + dust)
        js = (f'    tl.fromTo("#{p}-b", {{ x: -40 }}, {{ x: 44, duration: {round(dur - 0.7, 3)}, ease: "power1.inOut" }}, 0.2);\n' +
              "".join(f'    tl.fromTo("#{p}-p{i}", {{ opacity: 0, x: 0, y: 0 }}, {{ opacity: 1, x: {-30 - 12 * i}, y: {(-1) ** i * 24}, duration: 0.4, ease: "power2.out" }}, {round(0.6 + 0.18 * i, 3)});\n'
                      f'    tl.to("#{p}-p{i}", {{ opacity: 0, duration: 0.2 }}, {round(1.0 + 0.18 * i, 3)});\n' for i in range(4)))
    elif kind == "bolt_tighten":
        svg = (f'<rect x="40" y="128" width="240" height="30" rx="6" fill="#9AA0A6" stroke="{INK}" stroke-width="6"/>'
               f'<g id="{p}-n"><polygon points="160,34 196,55 196,97 160,118 124,97 124,55" fill="#C9CDD2" stroke="{INK}" stroke-width="7"/>'
               f'<circle cx="160" cy="76" r="14" fill="{INK}"/></g>'
               f'<path id="{p}-a" d="M214 50 A 62 62 0 0 1 214 104" fill="none" stroke="{YEL}" stroke-width="8" stroke-linecap="round"/>'
               f'<path d="M206 98 L216 110 L226 96" fill="none" stroke="{YEL}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
        js = (f'    tl.fromTo("#{p}-n", {{ rotation: 0, y: -22, svgOrigin: "160 76" }}, {{ rotation: 540, y: 6, duration: {round(dur - 0.6, 3)}, ease: "power2.inOut" }}, 0.2);\n'
              f'    tl.fromTo("#{p}-a", {{ opacity: 0.3 }}, {{ opacity: 1, duration: 0.3, ease: "power1.out" }}, 0.4);\n')
    elif kind == "wind_flow":
        lines = "".join(f'<path id="{p}-w{i}" d="M110 {70 + 30 * i} C 160 {50 + 30 * i}, 210 {90 + 30 * i}, 300 {70 + 30 * i}" fill="none" stroke="{WHITE}" '
                        f'stroke-width="6" stroke-linecap="round" stroke-dasharray="40 30"/>' for i in range(3))
        svg = (lines + f'<g id="{p}-f"><circle cx="64" cy="100" r="52" fill="{YEL}" stroke="{INK}" stroke-width="7"/>' +
               "".join(f'<ellipse cx="64" cy="72" rx="12" ry="26" fill="{WHITE}" stroke="{INK}" stroke-width="4" transform="rotate({a} 64 100)"/>' for a in (0, 120, 240)) +
               f'<circle cx="64" cy="100" r="10" fill="{INK}"/></g>')
        js = (f'    tl.fromTo("#{p}-f", {{ rotation: 0, svgOrigin: "64 100" }}, {{ rotation: 1080, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n' +
              "".join(f'    tl.fromTo("#{p}-w{i}", {{ strokeDashoffset: 0 }}, {{ strokeDashoffset: -280, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n' for i in range(3)))
    elif kind == "pivot_fold":
        svg = (f'<rect x="236" y="90" width="44" height="22" rx="4" fill="#C9CDD2" stroke="{INK}" stroke-width="5"/>'
               f'<path d="M280 90 L304 101 L280 112 Z" fill="#C9CDD2" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
               f'<g id="{p}-h"><rect x="92" y="96" width="40" height="92" rx="14" fill="#2A2A2A" stroke="{INK}" stroke-width="6"/>'
               f'<rect x="102" y="120" width="20" height="44" rx="6" fill="{YEL}"/></g>'
               f'<rect x="106" y="78" width="134" height="48" rx="16" fill="{YEL}" stroke="{INK}" stroke-width="7"/>'
               f'<circle cx="112" cy="102" r="9" fill="{INK}"/>')
        js = (f'    tl.fromTo("#{p}-h", {{ rotation: 0, svgOrigin: "112 102" }}, {{ rotation: 90, duration: 0.6, ease: "back.out(1.6)" }}, 0.45);\n'
              f'    tl.to("#{p}-h", {{ rotation: 0, duration: 0.6, ease: "back.out(1.6)" }}, {round(max(1.3, dur - 1.0), 3)});\n')
    elif kind == "light_beam":
        leds = "".join(f'<circle id="{p}-l{i}" cx="{56 + 18 * (i % 3)}" cy="{78 + 18 * (i // 3)}" r="6" fill="#8A8F96"/>' for i in range(9))
        rays = "".join(f'<path id="{p}-r{i}" d="M120 100 L300 {100 + y0} L300 {100 + y1} Z" fill="{YEL if i % 2 else WHITE}" opacity="0"/>'
                       for i, (y0, y1) in enumerate([(-96, -60), (-46, -14), (0, 34), (48, 84)]))
        svg = (rays + f'<rect x="38" y="60" width="86" height="80" rx="12" fill="{INK}" stroke="{YEL}" stroke-width="8"/>' + leds +
               f'<path d="M48 140 L40 176 M114 140 L122 176 M32 176 H130" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>')
        js = ("".join(f'    tl.to("#{p}-l{i}", {{ attr: {{ fill: "{WHITE}" }}, duration: 0.08 }}, {round(0.35 + 0.03 * i, 3)});\n' for i in range(9)) +
              "".join(f'    tl.fromTo("#{p}-r{i}", {{ opacity: 0, scaleX: 0.2, svgOrigin: "120 100" }}, {{ opacity: 0.85, scaleX: 1, duration: 0.35, ease: "power2.out" }}, {round(0.55 + 0.06 * i, 3)});\n'
                      f'    tl.to("#{p}-r{i}", {{ opacity: 0.45, duration: 0.3, repeat: 2, yoyo: true, ease: "sine.inOut" }}, {round(1.0 + 0.06 * i, 3)});\n' for i in range(4)))
    elif kind == "magnet":
        lines = "".join(f'<path id="{p}-f{i}" d="M150 {64 + 36 * i} Q 178 {82 + 18 * i} 206 {64 + 36 * i}" fill="none" stroke="{WHITE}" '
                        f'stroke-width="5" stroke-linecap="round" stroke-dasharray="8 10" opacity="0"/>' for i in range(3))
        svg = (f'<path d="M140 40 H80 A 60 60 0 0 0 80 160 H140 V124 H80 A 24 24 0 0 1 80 76 H140 Z" fill="{RED}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
               f'<rect x="112" y="40" width="28" height="36" fill="#D9DDE2" stroke="{INK}" stroke-width="5"/>'
               f'<rect x="112" y="124" width="28" height="36" fill="#D9DDE2" stroke="{INK}" stroke-width="5"/>' + lines +
               f'<g id="{p}-b"><rect x="214" y="40" width="40" height="120" rx="14" fill="{INK}" stroke="{YEL}" stroke-width="6"/>'
               f'<rect x="224" y="52" width="20" height="96" rx="8" fill="{WHITE}"/></g>')
        js = ("".join(f'    tl.fromTo("#{p}-f{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {round(0.3 + 0.08 * i, 3)});\n'
                      f'    tl.fromTo("#{p}-f{i}", {{ strokeDashoffset: 0 }}, {{ strokeDashoffset: -54, duration: 0.9, ease: "none" }}, 0.3);\n' for i in range(3)) +
              f'    tl.fromTo("#{p}-b", {{ x: 50, rotation: 10, svgOrigin: "234 100" }}, {{ x: -66, rotation: 0, duration: 0.45, ease: "back.in(1.4)" }}, 0.9);\n' +
              "".join(f'    tl.to("#{p}-f{i}", {{ opacity: 0, duration: 0.15 }}, 1.32);\n' for i in range(3)) +
              f'    tl.fromTo("#{p}-b", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.12, yoyo: true, repeat: 1, transformOrigin: "50% 50%" }}, 1.36);\n')
    elif kind == "saw_cut":
        teeth = " ".join(f"{70 + 52 * __import__('math').cos(k * 0.3927):.1f},{86 + 52 * __import__('math').sin(k * 0.3927):.1f} "
                         f"{70 + 44 * __import__('math').cos(k * 0.3927 + 0.2):.1f},{86 + 44 * __import__('math').sin(k * 0.3927 + 0.2):.1f}" for k in range(16))
        dust = "".join(f'<circle id="{p}-d{i}" cx="70" cy="132" r="{4 + i % 3}" fill="#E8C98E" stroke="{INK}" stroke-width="2" opacity="0"/>' for i in range(5))
        svg = (f'<rect x="10" y="128" width="300" height="34" rx="4" fill="#C8955A" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M30 140 H120 M150 150 H280" stroke="#9C6B36" stroke-width="3"/>'
               f'<rect id="{p}-k" x="20" y="126" width="6" height="38" fill="{INK}"/>' + dust +
               f'<g id="{p}-m"><g id="{p}-w"><polygon points="{teeth}" fill="#C9CDD2" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<circle cx="70" cy="86" r="16" fill="{YEL}" stroke="{INK}" stroke-width="5"/></g>'
               f'<path d="M20 70 A 52 52 0 0 1 120 70" fill="none" stroke="#1FBF8F" stroke-width="14" stroke-linecap="round"/></g>')
        d = round(dur - 0.6, 3)
        js = (f'    tl.fromTo("#{p}-w", {{ rotation: 0, svgOrigin: "70 86" }}, {{ rotation: 1440, duration: {round(dur - 0.3, 3)}, ease: "none" }}, 0.1);\n'
              f'    tl.fromTo("#{p}-m", {{ x: -30 }}, {{ x: 190, duration: {d}, ease: "power1.inOut" }}, 0.25);\n'
              f'    tl.fromTo("#{p}-k", {{ attr: {{ width: 6 }} }}, {{ attr: {{ width: 230 }}, duration: {d}, ease: "power1.inOut" }}, 0.25);\n' +
              "".join(f'    tl.fromTo("#{p}-d{i}", {{ opacity: 0, x: {40 * i}, y: 0 }}, {{ opacity: 1, x: {40 * i - 30 - 6 * i}, y: {-28 - 7 * i}, duration: 0.35, ease: "power2.out" }}, {round(0.45 + 0.25 * i, 3)});\n'
                      f'    tl.to("#{p}-d{i}", {{ opacity: 0, duration: 0.15 }}, {round(0.8 + 0.25 * i, 3)});\n' for i in range(5)))
    elif kind == "chain_run":
        import math
        chips = "".join(f'<rect id="{p}-c{i}" x="200" y="104" width="10" height="6" rx="2" fill="#E8C98E" stroke="{INK}" stroke-width="2" opacity="0"/>' for i in range(5))
        teeth = "".join(f'<rect x="{34 + 18 * k}" y="44" width="9" height="8" fill="{INK}"/>' for k in range(12))
        svg = (f'<ellipse cx="200" cy="150" rx="70" ry="34" fill="#C8955A" stroke="{INK}" stroke-width="6"/>'
               f'<ellipse cx="200" cy="146" rx="46" ry="20" fill="#E3B57A" stroke="#9C6B36" stroke-width="3"/>'
               f'<rect id="{p}-k" x="196" y="118" width="8" height="0" fill="{INK}"/>' + chips +
               f'<g id="{p}-s"><rect x="20" y="50" width="250" height="34" rx="17" fill="#D9DDE2" stroke="{INK}" stroke-width="6"/>'
               f'<g id="{p}-t">{teeth}</g>'
               f'<rect x="250" y="34" width="62" height="64" rx="14" fill="{YEL}" stroke="{INK}" stroke-width="6"/>'
               f'<rect x="262" y="48" width="38" height="14" rx="4" fill="{INK}"/></g>')
        d = round(dur - 0.6, 3)
        js = (f'    tl.fromTo("#{p}-t", {{ x: 0 }}, {{ x: 18, duration: 0.12, repeat: {max(3, int((dur - 0.3) / 0.12))}, ease: "none" }}, 0.1);\n'
              f'    tl.fromTo("#{p}-s", {{ y: -10 }}, {{ y: 46, duration: {d}, ease: "power1.inOut" }}, 0.25);\n'
              f'    tl.fromTo("#{p}-k", {{ attr: {{ height: 0 }} }}, {{ attr: {{ height: 64 }}, duration: {d}, ease: "power1.inOut" }}, 0.25);\n' +
              "".join(f'    tl.fromTo("#{p}-c{i}", {{ opacity: 0, x: 0, y: 0, rotation: 0 }}, {{ opacity: 1, x: {(-1) ** i * (30 + 10 * i)}, y: {-30 - 8 * i}, rotation: {90 * (i + 1)}, duration: 0.35, ease: "power2.out" }}, {round(0.4 + 0.22 * i, 3)});\n'
                      f'    tl.to("#{p}-c{i}", {{ opacity: 0, duration: 0.15 }}, {round(0.75 + 0.22 * i, 3)});\n' for i in range(5)))
    elif kind == "oil_drop":
        teeth = "".join(f'<rect x="{30 + 20 * k}" y="148" width="10" height="9" fill="{INK}"/>' for k in range(13))
        drops = "".join(f'<path id="{p}-d{i}" d="M170 76 C 162 90, 162 98, 170 100 C 178 98, 178 90, 170 76 Z" fill="#3A2A12" stroke="{INK}" stroke-width="3" opacity="0"/>' for i in range(3))
        svg = (f'<g id="{p}-can"><path d="M88 22 H150 V74 H88 Z" fill="{RED}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<path d="M150 40 L182 64 L176 72 L150 56 Z" fill="#C9CDD2" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
               f'<rect x="100" y="36" width="38" height="20" rx="4" fill="{YEL}"/></g>' + drops +
               f'<rect id="{p}-bar" x="20" y="150" width="280" height="30" rx="15" fill="#D9DDE2" stroke="{INK}" stroke-width="6"/>'
               f'<g id="{p}-t">{teeth}</g>'
               f'<rect id="{p}-g" x="26" y="156" width="268" height="6" rx="3" fill="{WHITE}" opacity="0"/>')
        js = (f'    tl.fromTo("#{p}-can", {{ rotation: 0, svgOrigin: "120 74" }}, {{ rotation: 22, duration: 0.3, ease: "power2.out" }}, 0.25);\n'
              f'    tl.fromTo("#{p}-t", {{ x: 0 }}, {{ x: 20, duration: 0.14, repeat: {max(3, int((dur - 0.3) / 0.14))}, ease: "none" }}, 0.1);\n' +
              "".join(f'    tl.fromTo("#{p}-d{i}", {{ opacity: 1, y: 0 }}, {{ opacity: 1, y: 52, duration: 0.32, ease: "power2.in" }}, {round(0.5 + 0.3 * i, 3)});\n'
                      f'    tl.to("#{p}-d{i}", {{ opacity: 0, scaleX: 2, scaleY: 0.3, transformOrigin: "50% 100%", duration: 0.12 }}, {round(0.82 + 0.3 * i, 3)});\n' for i in range(3)) +
              f'    tl.fromTo("#{p}-g", {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.3, repeat: 1, yoyo: true }}, 1.0);\n')
    elif kind == "fuel_mix":
        svg = (f'<g id="{p}-a"><rect x="20" y="30" width="62" height="78" rx="10" fill="#1FBF8F" stroke="{INK}" stroke-width="6"/>'
               f'<text x="51" y="80" text-anchor="middle" font-family="Archivo Black,Inter,sans-serif" font-size="22" fill="{INK}">2T</text>'
               f'<rect x="40" y="16" width="22" height="16" rx="3" fill="{INK}"/></g>'
               f'<g id="{p}-b"><path d="M238 30 H296 V108 H230 V44 Z" fill="{RED}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<path d="M246 22 L262 22 L262 32" fill="none" stroke="{INK}" stroke-width="6"/></g>'
               f'<path id="{p}-sa" d="M86 70 Q 120 90 132 128" fill="none" stroke="#1FBF8F" stroke-width="7" stroke-linecap="round" stroke-dasharray="70" stroke-dashoffset="70"/>'
               f'<path id="{p}-sb" d="M228 70 Q 196 90 186 128" fill="none" stroke="{YEL}" stroke-width="7" stroke-linecap="round" stroke-dasharray="70" stroke-dashoffset="70"/>'
               f'<path d="M110 120 H210 L200 190 H120 Z" fill="{WHITE}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<rect id="{p}-f" x="122" y="186" width="76" height="0" fill="{YEL}"/>'
               f'<path id="{p}-w" d="M130 168 Q 160 150 190 168" fill="none" stroke="#1FBF8F" stroke-width="5" stroke-linecap="round" opacity="0"/>')
        js = (f'    tl.fromTo("#{p}-a", {{ rotation: 0, svgOrigin: "82 70" }}, {{ rotation: 35, duration: 0.3, ease: "power2.out" }}, 0.2);\n'
              f'    tl.fromTo("#{p}-b", {{ rotation: 0, svgOrigin: "230 70" }}, {{ rotation: -35, duration: 0.3, ease: "power2.out" }}, 0.3);\n'
              f'    tl.to("#{p}-sa", {{ strokeDashoffset: 0, duration: 0.3, ease: "none" }}, 0.45);\n'
              f'    tl.to("#{p}-sb", {{ strokeDashoffset: 0, duration: 0.3, ease: "none" }}, 0.55);\n'
              f'    tl.fromTo("#{p}-f", {{ attr: {{ y: 186, height: 0 }} }}, {{ attr: {{ y: 140, height: 46 }}, duration: {round(max(0.6, dur - 1.4), 3)}, ease: "power1.out" }}, 0.6);\n'
              f'    tl.to(["#{p}-sa", "#{p}-sb"], {{ opacity: 0, duration: 0.2 }}, {round(max(1.1, dur - 0.7), 3)});\n'
              f'    tl.fromTo("#{p}-w", {{ opacity: 0, rotation: 0, svgOrigin: "160 160" }}, {{ opacity: 1, rotation: 360, duration: 0.6, ease: "power1.inOut" }}, {round(max(1.1, dur - 0.8), 3)});\n')
    elif kind == "touch_screen":
        rip = "".join(f'<circle id="{p}-r{i}" cx="118" cy="96" r="10" fill="none" stroke="{YEL}" stroke-width="5" opacity="0"/>' for i in range(2))
        svg = (f'<rect x="64" y="14" width="110" height="176" rx="18" fill="{INK}" stroke="{WHITE}" stroke-width="5"/>'
               f'<rect id="{p}-sc" x="74" y="30" width="90" height="144" rx="8" fill="#2E3A48"/>'
               f'<rect x="84" y="44" width="70" height="12" rx="6" fill="#5B6B7E"/><rect x="84" y="64" width="50" height="12" rx="6" fill="#5B6B7E"/>' + rip +
               f'<g id="{p}-h"><path d="M150 108 C 150 96, 166 96, 166 108 L 166 128 L 210 128 C 236 128, 250 146, 250 170 L 250 200 L 168 200 L 136 150 C 130 140, 146 132, 152 140 Z" fill="{RED}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<path d="M150 108 C 150 96, 166 96, 166 108 L 166 124 L 150 124 Z" fill="#2A2A2A" stroke="{INK}" stroke-width="4"/></g>'
               f'<path id="{p}-ok" d="M190 40 L208 58 L240 24" fill="none" stroke="#1FBF8F" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="80" stroke-dashoffset="80"/>')
        js = (f'    tl.fromTo("#{p}-h", {{ x: 40, y: 40 }}, {{ x: -40, y: -10, duration: 0.4, ease: "power2.out" }}, 0.2);\n'
              f'    tl.to("#{p}-h", {{ y: -4, duration: 0.1, yoyo: true, repeat: 3, ease: "power1.inOut" }}, 0.65);\n' +
              "".join(f'    tl.fromTo("#{p}-r{i}", {{ opacity: 1, attr: {{ r: 8 }} }}, {{ opacity: 0, attr: {{ r: 42 }}, duration: 0.45, ease: "power2.out" }}, {round(0.65 + 0.2 * i, 3)});\n' for i in range(2)) +
              f'    tl.to("#{p}-sc", {{ attr: {{ fill: "#3C7BD9" }}, duration: 0.15 }}, 0.7);\n'
              f'    tl.to("#{p}-ok", {{ strokeDashoffset: 0, duration: 0.3, ease: "power2.out" }}, 1.05);\n')
    elif kind == "glove_shield":
        hits = "".join(f'<path id="{p}-x{i}" d="M0 0 L14 8 L4 10 L16 22" fill="none" stroke="{WHITE}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" transform="translate({x} {y})" opacity="0"/>'
                       for i, (x, y) in enumerate([(30, 40), (262, 60), (40, 140)]))
        svg = (f'<g id="{p}-g"><path d="M110 190 L110 110 C 110 100, 124 100, 124 110 L 124 60 C 124 48, 140 48, 140 60 L 140 44 C 140 32, 156 32, 156 44 L 156 52 C 156 40, 172 40, 172 52 L 172 66 C 172 56, 188 56, 188 66 L 188 140 C 188 170, 176 190, 160 190 Z" fill="{RED}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<path d="M110 150 H188" stroke="{INK}" stroke-width="4"/></g>'
               f'<g id="{p}-s"><path d="M210 96 L246 84 L282 96 C 282 134, 266 156, 246 166 C 226 156, 210 134, 210 96 Z" fill="{YEL}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<path d="M230 122 L242 134 L264 108" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></g>' + hits)
        js = (f'    tl.fromTo("#{p}-s", {{ scale: 0, opacity: 0, svgOrigin: "246 125" }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.5)" }}, 0.35);\n' +
              "".join(f'    tl.fromTo("#{p}-x{i}", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.15, yoyo: true, repeat: 1, ease: "power2.out", transformOrigin: "50% 50%" }}, {round(0.8 + 0.22 * i, 3)});\n' for i in range(3)) +
              f'    tl.to("#{p}-g", {{ x: 3, duration: 0.06, yoyo: true, repeat: 5, ease: "none" }}, 0.8);\n')
    elif kind == "leaf_blow":
        leaves = "".join(f'<path id="{p}-l{i}" d="M0 0 C 10 -12, 26 -10, 30 0 C 26 10, 10 12, 0 0 Z" fill="{["#1FBF8F", YEL, "#C8955A", "#1FBF8F"][i]}" stroke="{INK}" stroke-width="3" transform="translate({180 + 22 * i} {120 + (i % 2) * 34})"/>' for i in range(4))
        lines = "".join(f'<path id="{p}-w{i}" d="M120 {84 + 22 * i} H310" fill="none" stroke="{WHITE}" stroke-width="5" stroke-linecap="round" stroke-dasharray="30 26" opacity="0"/>' for i in range(3))
        svg = (lines + leaves +
               f'<path d="M14 70 H70 L120 84 V140 L70 150 H14 Z" fill="#1FBF8F" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
               f'<rect x="20" y="150" width="34" height="40" rx="8" fill="{INK}"/>')
        js = ("".join(f'    tl.fromTo("#{p}-w{i}", {{ opacity: 0, strokeDashoffset: 0 }}, {{ opacity: 1, strokeDashoffset: -224, duration: {round(dur - 0.4, 3)}, ease: "none" }}, 0.2);\n' for i in range(3)) +
              "".join(f'    tl.to("#{p}-l{i}", {{ x: "+=140", y: "-={30 + 18 * i}", rotation: {200 + 60 * i}, opacity: 0, duration: 0.7, ease: "power2.in" }}, {round(0.5 + 0.18 * i, 3)});\n' for i in range(4)))
    else:
        raise ValueError(kind)
    html = f'    <div class="toon"><svg viewBox="0 0 320 200" aria-hidden="true">{svg}</svg></div>\n'
    return html, BASE_CSS, _pop(tid, dur) + js
