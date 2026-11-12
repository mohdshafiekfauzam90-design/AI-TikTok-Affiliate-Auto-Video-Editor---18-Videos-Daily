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
              "".join(f'    tl.fromTo("#{p}-s{i}", {{ opacity: 0, scale: 0.2, svgOrigin: "170 126" }}, {{ opacity: 1, scale: 1, duration: 0.16, ease: "power2.out" }}, {round(0.25 + 0.3 * k + 0.05 * i, 3)});\n'
                      f'    tl.to("#{p}-s{i}", {{ opacity: 0, duration: 0.12 }}, {round(0.41 + 0.3 * k + 0.05 * i, 3)});\n'
                      for k in range(int((dur - 0.6) / 0.3)) for i in range(6)))
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
    else:
        raise ValueError(kind)
    html = f'    <div class="toon"><svg viewBox="0 0 320 200" aria-hidden="true">{svg}</svg></div>\n'
    return html, BASE_CSS, _pop(tid, dur) + js
