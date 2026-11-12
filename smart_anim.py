#!/usr/bin/env python3
"""MUROH DOOH – Minimal Smart Animation (enhancement, boleh ON/OFF).

Konsep: 90% video original + 10% animasi.
  * Animasi kartun kecil & kemas (widget sudut ~320px) hanya pada point penting.
  * Setiap animasi 1–3 saat sahaja, tidak menutup produk (diletak di sudut atas,
    bertentangan dengan callout yang sedang aktif).
  * Masa dipilih secara automatik daripada transkrip Whisper: kata kunci diberi
    skor, konteks negatif ditapis ("tak nak guna tenaga" BUKAN tentang bateri),
    bajet masa dihadkan (lalai 10% durasi), ada jarak minimum antara animasi,
    dan zon hook/CTA dielakkan. Tiada point sesuai -> tiada animasi.

Jenis animasi:
  bolt     – bolt berpusing & diketatkan, cincin tork terisi   (impact wrench)
  drill    – mata drill menembusi dinding + serpihan           (drill)
  sparks   – disk grinder memotong besi + percikan api         (grinder)
  airflow  – kipas berpusing + aliran angin                    (kipas / blower)
  energy   – bateri terisi + tenaga mengalir                   (bateri / charger)

Uji sendiri:
  python3 smart_anim.py --demo work/anim_demo     # render kelima-lima animasi ke .mov + .gif
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 30
SR = 48000
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"

# ------------------------------------------------------------ smart planner
# Kata kunci (Bahasa Melayu + istilah biasa) -> berat
TRIGGERS: dict[str, dict[str, float]] = {
    "bolt": {"tork": 3, "torque": 3, "ketat": 3, "ketatkan": 3, "bolt": 3, "nat": 2,
             "skru": 1.5, "wrench": 1, "kuat": 1, "padu": 1, "#NM": 3},
    "drill": {"drill": 3, "gerudi": 3, "tebuk": 3, "tembus": 3, "dinding": 2,
              "lubang": 2, "konkrit": 2, "simen": 2, "batu": 1},
    "sparks": {"grinder": 3, "potong": 3, "percikan": 3, "besi": 2, "asah": 2,
               "cutting": 3, "disc": 2, "mata": 0.5},
    "airflow": {"angin": 3, "kipas": 3, "fan": 3, "blower": 3, "sejuk": 2,
                "aliran": 2, "tiup": 2},
    "energy": {"bateri": 3, "battery": 3, "cas": 2, "charge": 2, "charger": 2.5,
               "tenaga": 1, "volt": 2, "#V": 2, "tahan": 1, "lithium": 2},
}
# Animasi yang relevan untuk setiap jenis produk (yang lain diabaikan)
PRODUCT_ANIMS = {
    "impact_wrench": ["bolt", "energy"],
    "drill": ["drill", "energy"],
    "grinder": ["sparks", "energy"],
    "fan": ["airflow", "energy"],
    "blower": ["airflow", "energy"],
    "battery": ["energy"],
}
PRODUCT_HINTS = {
    "impact_wrench": ["impact", "wrench", "sepana", "tork", "socket"],
    "drill": ["drill", "gerudi", "tebuk"],
    "grinder": ["grinder", "potong", "disc"],
    "fan": ["kipas", "fan", "angin"],
    "battery": ["powerbank", "bateri", "battery"],
}
LABELS = {"bolt": "KETAT & PADU", "drill": "TEMBUS MUDAH", "sparks": "POTONG LAJU",
          "airflow": "ANGIN KUAT", "energy": "TENAGA PENUH"}
ACCENT = {"bolt": (57, 255, 20), "drill": (0, 229, 255), "sparks": (255, 140, 0),
          "airflow": (0, 229, 255), "energy": (255, 230, 0)}
NEGATIONS = {"tak", "tidak", "tanpa", "bukan", "jangan", "x"}


def _core(w: str) -> str:
    return re.sub(r"[^\w%/]", "", w.lower())


def _kw_weight(core: str, table: dict[str, float]) -> float:
    if "#NM" in table and re.match(r"^\d+nm$", core):
        return table["#NM"]
    if "#V" in table and re.match(r"^\d+v$", core):
        return table["#V"]
    best = 0.0
    for kw, wt in table.items():
        if kw.startswith("#"):
            continue
        if core == kw or (len(kw) > 3 and core.startswith(kw)):
            best = max(best, wt)
    return best


def detect_product(words: list[dict], cfg: dict) -> str:
    text = (cfg.get("title", "") + " " + " ".join(w["word"] for w in words)).lower()
    scores = {p: sum(text.count(h) for h in hints) for p, hints in PRODUCT_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def plan_animations(words: list[dict], cfg: dict, duration: float) -> list[dict]:
    """Pilih masa animasi secara 'bijak'. Pulangkan senarai kosong jika tiada point sesuai."""
    sa = cfg.get("smart_animation", {})
    if sa.get("manual"):                       # pengguna tetapkan sendiri
        return [dict(m, reason="manual") for m in sa["manual"]]

    product = sa.get("product_type", "auto")
    if product == "auto":
        product = detect_product(words, cfg)
    allowed = sa.get("types") or PRODUCT_ANIMS.get(product, [])
    if not allowed:
        print(f"[A] Smart animation: produk '{product}' tiada animasi sesuai -> tiada animasi")
        return []

    dur = float(min(3.0, max(1.0, sa.get("duration", 2.0))))
    budget = sa.get("max_ratio", 0.10) * duration
    min_gap = sa.get("min_gap", 10.0)
    min_score = sa.get("min_score", 3.0)
    max_per_type = sa.get("max_per_type", 2)
    t_min = cfg.get("hook", {}).get("duration", 3.0) + 0.6
    t_max = duration - cfg.get("cta", {}).get("duration", 4.0) - 0.4

    cands = []
    cores = [_core(w["word"]) for w in words]
    for i, w in enumerate(words):
        for typ in allowed:
            wt = _kw_weight(cores[i], TRIGGERS[typ])
            if wt <= 0:
                continue
            # konteks negatif: "tak nak guna tenaga" -> bukan point bateri
            prev = set(cores[max(0, i - 3):i])
            if prev & NEGATIONS:
                continue
            # skor tetingkap ±2 s di sekeliling perkataan pencetus
            score, ctx = 0.0, []
            for j in range(len(words)):
                if abs(words[j]["start"] - w["start"]) <= 2.0:
                    s = _kw_weight(cores[j], TRIGGERS[typ])
                    if s and not (set(cores[max(0, j - 3):j]) & NEGATIONS):
                        score += s
                        ctx.append(words[j]["word"])
            if typ == allowed[0]:
                score *= 1.3                   # animasi utama produk diutamakan
            start = round(w["start"] - 0.15, 2)
            if start < t_min or start + dur > t_max or score < min_score:
                continue
            label = LABELS[typ]
            num = next((c for c in ctx if re.match(r"^\d+nm", c.lower())), None)
            if typ == "bolt" and num:
                label = f"{re.sub('(?i)nm', 'Nm', num.strip('.,'))} TORK"
            cands.append({"type": typ, "start": start, "end": round(start + dur, 2),
                          "score": round(score, 2), "label": label,
                          "reason": f"'{w['word']}' @ {w['start']:.2f}s, konteks: {' '.join(ctx)}"})

    cands.sort(key=lambda c: (-c["score"], c["start"]))
    chosen: list[dict] = []
    used = 0.0
    for c in cands:
        if used + dur > budget + 1e-6:
            break
        if any(abs(c["start"] - x["start"]) < min_gap for x in chosen):
            continue
        if sum(x["type"] == c["type"] for x in chosen) >= max_per_type:
            continue
        chosen.append(c)
        used += dur
    chosen.sort(key=lambda c: c["start"])
    print(f"[A] Smart animation: produk={product}, {len(cands)} calon, "
          f"{len(chosen)} dipilih ({used:.1f}s = {100 * used / duration:.1f}% durasi)")
    for c in chosen:
        print(f"    {c['start']:6.2f}-{c['end']:6.2f} {c['type']:8s} skor={c['score']:<5} {c['reason']}")
    return chosen


def place(anims: list[dict], cfg: dict, size: int, W: int = 1080) -> None:
    """Letak widget di sudut atas, bertentangan dengan callout yang aktif."""
    y = cfg.get("smart_animation", {}).get("y", 210)
    for a in anims:
        side = a.get("side")
        if not side:
            busy = {c.get("side", "left") for c in cfg.get("callouts", [])
                    if c["start"] < a["end"] and c["end"] > a["start"]}
            side = "left" if busy == {"right"} else "right"
        a["side"] = side
        a["x"] = 40 if side == "left" else W - size - 40
        a["y"] = a.get("y", y)


# ------------------------------------------------------------- drawing utils
def _ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def _ease_in_out(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _font(px):
    try:
        return ImageFont.truetype(FONT_BLACK, px)
    except OSError:
        return ImageFont.load_default()


def _card(S, accent):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pad = int(S * 0.04)
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad * 2, S - pad, S - pad // 2), S // 7,
                                         fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S // 40)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((pad, pad, S - pad, S - pad), S // 7, fill=(14, 16, 20, 205),
                        outline=accent + (230,), width=max(2, S // 110))
    return img


def _label(img, S, text, accent, alpha=255):
    d = ImageDraw.Draw(img)
    f = _font(int(S * 0.085))
    b = f.getbbox(text)
    tw = b[2] - b[0]
    x, y = (S - tw) // 2, int(S * 0.80)
    d.rounded_rectangle((x - S * 0.04, y - S * 0.02, x + tw + S * 0.04, y + (b[3] - b[1]) + S * 0.035),
                        S // 30, fill=accent + (alpha,))
    d.text((x - b[0], y - b[1]), text, font=f, fill=(12, 12, 12, alpha))


def _poly_rot(cx, cy, r, n, ang):
    return [(cx + r * math.cos(ang + 2 * math.pi * k / n), cy + r * math.sin(ang + 2 * math.pi * k / n))
            for k in range(n)]


# ---------------------------------------------------------------- animations
def draw_bolt(S, t, dur, accent):
    img = _card(S, accent)
    d = ImageDraw.Draw(img)
    cx, cy = S * 0.5, S * 0.43
    p = _ease_out(t / (dur * 0.72))
    done = t >= dur * 0.72
    sink = 1 - 0.08 * p                              # bolt "masuk" sedikit bila ketat
    # plat logam + lubang
    d.ellipse((cx - S * 0.30, cy - S * 0.30, cx + S * 0.30, cy + S * 0.30), fill=(40, 44, 52, 255))
    # cincin tork
    rr = S * 0.33
    d.arc((cx - rr, cy - rr, cx + rr, cy + rr), 0, 360, fill=(70, 74, 82, 255), width=int(S * 0.035))
    if p > 0:
        d.arc((cx - rr, cy - rr, cx + rr, cy + rr), -90, -90 + 360 * p, fill=accent + (255,),
              width=int(S * 0.035))
        a = math.radians(-90 + 360 * p)
        hx, hy = cx + rr * math.cos(a), cy + rr * math.sin(a)
        d.ellipse((hx - S * 0.03, hy - S * 0.03, hx + S * 0.03, hy + S * 0.03), fill=(255, 255, 255, 255))
    # washer
    rw = S * 0.205 * sink
    d.ellipse((cx - rw, cy - rw, cx + rw, cy + rw), fill=(150, 156, 166, 255), outline=(90, 95, 105, 255),
              width=3)
    # kepala bolt heksagon berpusing
    ang = math.radians(1080 * p)
    shake = (math.sin(t * 90) * S * 0.006) if not done else 0
    rh = S * 0.16 * sink
    pts = _poly_rot(cx + shake, cy, rh, 6, ang)
    d.polygon(pts, fill=(205, 210, 218, 255), outline=(70, 74, 82, 255), width=4)
    inner = _poly_rot(cx + shake, cy, rh * 0.62, 6, ang)
    d.polygon(inner, fill=(178, 184, 194, 255))
    for k in range(6):                               # garis tepi untuk ilusi 3D
        d.line([pts[k], inner[k]], fill=(150, 156, 166, 255), width=2)
    # garis hentaman impact semasa berpusing
    if not done and int(t * 20) % 2 == 0:
        for k in range(8):
            a = 2 * math.pi * k / 8 + t * 3
            r1, r2 = S * 0.37, S * 0.42
            d.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)),
                    (cx + r2 * math.cos(a), cy + r2 * math.sin(a))], fill=accent + (200,), width=4)
    # tanda ✓ bila ketat
    if done:
        q = _ease_out((t - dur * 0.72) / 0.18)
        r = S * 0.075 * (0.6 + 0.4 * q)
        bx, by = cx + S * 0.27, cy - S * 0.27
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=accent + (int(255 * q),))
        d.line([(bx - r * 0.45, by), (bx - r * 0.1, by + r * 0.38), (bx + r * 0.5, by - r * 0.35)],
               fill=(12, 12, 12, int(255 * q)), width=max(3, int(S * 0.018)), joint="curve")
    return img


def draw_drill(S, t, dur, accent):
    img = _card(S, accent)
    d = ImageDraw.Draw(img)
    top, bot = S * 0.18, S * 0.70
    wall_x = S * 0.60
    # dinding bata
    d.rectangle((wall_x, top, S * 0.90, bot), fill=(150, 78, 52, 255))
    rows = 6
    for r in range(rows + 1):
        y = top + (bot - top) * r / rows
        d.line([(wall_x, y), (S * 0.90, y)], fill=(210, 190, 170, 255), width=3)
        if r < rows:
            off = 0 if r % 2 else S * 0.07
            x = wall_x + off
            while x < S * 0.90:
                d.line([(x, y), (x, y + (bot - top) / rows)], fill=(210, 190, 170, 255), width=3)
                x += S * 0.14
    cy = (top + bot) / 2
    p = _ease_in_out(t / (dur * 0.8))
    tip = S * 0.47 + (S * 0.80 - S * 0.47) * p
    # lubang
    if tip > wall_x:
        d.rectangle((wall_x - 2, cy - S * 0.045, tip, cy + S * 0.045), fill=(40, 22, 16, 255))
    # mata drill (spiral bergerak = berpusing)
    shaft_l = tip - S * 0.30
    d.rectangle((shaft_l, cy - S * 0.035, tip - S * 0.05, cy + S * 0.035), fill=(196, 202, 212, 255))
    phase = (t * 14) % 1
    x = shaft_l + phase * S * 0.06
    while x < tip - S * 0.06:
        d.line([(x, cy + S * 0.035), (x + S * 0.03, cy - S * 0.035)], fill=(110, 116, 126, 255), width=4)
        x += S * 0.06
    d.polygon([(tip - S * 0.05, cy - S * 0.035), (tip, cy), (tip - S * 0.05, cy + S * 0.035)],
              fill=(230, 234, 240, 255))
    # chuck
    d.rounded_rectangle((shaft_l - S * 0.12, cy - S * 0.07, shaft_l, cy + S * 0.07), 8, fill=(30, 30, 34, 255),
                        outline=accent + (255,), width=3)
    # serpihan
    if tip > wall_x:
        rng = np.random.default_rng(int(t * FPS))
        for _ in range(10):
            ang = rng.uniform(math.pi * 0.6, math.pi * 1.4)
            dist = rng.uniform(0.02, 0.14) * S
            px, py = wall_x - 4 + dist * math.cos(ang), cy + dist * math.sin(ang)
            r = rng.uniform(2, 6)
            d.ellipse((px - r, py - r, px + r, py + r), fill=(205, 160, 120, 230))
    return img


def draw_sparks(S, t, dur, accent):
    img = _card(S, accent)
    d = ImageDraw.Draw(img)
    bar_y = S * 0.56
    d.rectangle((S * 0.10, bar_y, S * 0.90, bar_y + S * 0.08), fill=(120, 126, 136, 255))
    d.line([(S * 0.10, bar_y), (S * 0.90, bar_y)], fill=(190, 196, 206, 255), width=3)
    p = _ease_in_out(t / dur)
    cut_x = S * 0.55
    depth = S * 0.06 * p
    d.rectangle((cut_x - 3, bar_y, cut_x + 3, bar_y + depth), fill=(255, 120, 0, 255))
    # disk grinder berpusing
    r = S * 0.20
    cx, cy = cut_x, bar_y - r + depth
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(60, 62, 70, 255), outline=(30, 30, 34, 255), width=4)
    for k in range(6):
        a = t * 40 + k * math.pi / 3
        d.line([(cx, cy), (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a))],
               fill=(110, 114, 124, 255), width=4)
    d.ellipse((cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2), fill=accent + (255,))
    # pelindung disk
    d.pieslice((cx - r * 1.12, cy - r * 1.12, cx + r * 1.12, cy + r * 1.12), 160, 380,
               fill=(25, 25, 28, 255))
    # percikan api (partikel deterministik)
    ox, oy = cx, bar_y
    for k in range(60):
        rng = np.random.default_rng(k)
        born = rng.uniform(0, dur)
        age = t - born
        life = rng.uniform(0.25, 0.55)
        if age < 0 or age > life:
            continue
        ang = rng.uniform(math.pi * 0.95, math.pi * 1.25)
        v = rng.uniform(1.4, 2.6) * S
        px = ox + v * math.cos(ang) * age
        py = oy + v * math.sin(ang) * age + 1.6 * S * age * age
        f = 1 - age / life
        col = (255, int(200 * f + 80), int(60 * f), int(255 * f))
        tx, ty = px - v * math.cos(ang) * 0.025, py - v * math.sin(ang) * 0.025
        d.line([(tx, ty), (px, py)], fill=col, width=4)
    return img


def draw_airflow(S, t, dur, accent):
    img = _card(S, accent)
    d = ImageDraw.Draw(img)
    cx, cy, r = S * 0.25, S * 0.43, S * 0.14
    d.ellipse((cx - r * 1.25, cy - r * 1.25, cx + r * 1.25, cy + r * 1.25), outline=(200, 205, 215, 255),
              width=5)
    for k in range(3):
        a = t * 25 + k * 2 * math.pi / 3
        pts = [(cx, cy),
               (cx + r * math.cos(a - 0.45), cy + r * math.sin(a - 0.45)),
               (cx + r * 1.05 * math.cos(a), cy + r * 1.05 * math.sin(a)),
               (cx + r * math.cos(a + 0.35), cy + r * math.sin(a + 0.35))]
        d.polygon(pts, fill=(220, 225, 235, 255))
    d.ellipse((cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22), fill=accent + (255,))
    for k in range(4):
        y0 = cy + (k - 1.5) * S * 0.08
        phase = t * 2.2 + k * 0.3
        for seg in range(6):
            u0 = ((seg / 6 + phase) % 1)
            u1 = u0 + 0.09
            if u1 > 1:
                continue
            pts = []
            for u in np.linspace(u0, u1, 8):
                x = S * 0.42 + u * S * 0.46
                y = y0 + math.sin(u * 7 + k) * S * 0.025
                pts.append((x, y))
            a = int(255 * math.sin(math.pi * u0))
            d.line(pts, fill=accent + (a,), width=6, joint="curve")
    return img


def draw_energy(S, t, dur, accent):
    img = _card(S, accent)
    d = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = S * 0.34, S * 0.16, S * 0.66, S * 0.72
    d.rounded_rectangle((S * 0.44, by0 - S * 0.05, S * 0.56, by0 + 4), 6, fill=(200, 205, 215, 255))
    d.rounded_rectangle((bx0, by0, bx1, by1), S // 20, outline=(200, 205, 215, 255), width=6)
    p = _ease_out(t / (dur * 0.75))
    n = 5
    lit = p * n
    gap = S * 0.018
    h = (by1 - by0 - gap * (n + 1)) / n
    for k in range(n):
        y1 = by1 - gap - k * (h + gap)
        y0 = y1 - h
        f = min(1.0, max(0.0, lit - k))
        if f <= 0:
            continue
        col = (int(255 - 200 * (k / n)), 230, int(20 + 20 * k)) if k >= 2 else (255, 200, 0)
        d.rounded_rectangle((bx0 + gap, y0, bx1 - gap, y1), 6, fill=col + (int(255 * f),))
    # kilat
    pulse = 0.9 + 0.1 * math.sin(t * 18)
    cx, cy, s = S * 0.5, (by0 + by1) / 2, S * 0.13 * pulse
    bolt = [(cx + 0.15 * s, cy - s), (cx - 0.45 * s, cy + 0.12 * s), (cx - 0.02 * s, cy + 0.12 * s),
            (cx - 0.2 * s, cy + s), (cx + 0.45 * s, cy - 0.15 * s), (cx + 0.02 * s, cy - 0.15 * s)]
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(bolt, fill=(255, 255, 255, 200))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S // 50)))
    d.polygon(bolt, fill=(255, 255, 255, 255), outline=(20, 20, 20, 255))
    # aliran tenaga (titik bergerak di kedua-dua sisi)
    for side in (S * 0.22, S * 0.78):
        for k in range(5):
            u = (t * 1.4 + k / 5) % 1
            y = by1 - u * (by1 - by0)
            r = S * 0.016 * (1 - abs(u - 0.5))
            d.ellipse((side - r * 1.5, y - r * 1.5, side + r * 1.5, y + r * 1.5), fill=accent + (int(230 * math.sin(math.pi * u)),))
    return img


DRAW = {"bolt": draw_bolt, "drill": draw_drill, "sparks": draw_sparks,
        "airflow": draw_airflow, "energy": draw_energy}


def render_animation(a: dict, out: Path, size: int = 320) -> Path:
    """Render widget animasi (RGBA) ke .mov (qtrle, alfa) untuk overlay ffmpeg."""
    typ = a["type"]
    dur = a["end"] - a["start"]
    accent = ACCENT[typ]
    S = size * 2                                     # lukis 2x -> anti-alias
    nfr = int(round(dur * FPS))
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{size}x{size}",
         "-r", str(FPS), "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", str(out)],
        stdin=subprocess.PIPE)
    for i in range(nfr):
        t = i / FPS
        img = DRAW[typ](S, t, dur, accent)
        # klip semua kandungan dalam bentuk kad (tiada yang terkeluar)
        mask = Image.new("L", (S, S), 0)
        pad = int(S * 0.04)
        ImageDraw.Draw(mask).rounded_rectangle((pad, pad, S - pad, S - pad), S // 7, fill=255)
        img.putalpha(Image.fromarray(np.minimum(np.asarray(img)[..., 3], np.asarray(mask))))
        _label(img, S, a.get("label", LABELS[typ]), accent)
        # masuk: pop + fade 0.22 s, keluar: fade 0.25 s
        fin = _ease_out(t / 0.22)
        fout = min(1.0, (dur - t) / 0.25)
        scale = 0.75 + 0.25 * fin
        img = img.resize((size, size), Image.LANCZOS)
        if scale < 0.999:
            sm = img.resize((max(1, int(size * scale)),) * 2, Image.LANCZOS)
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            img.alpha_composite(sm, ((size - sm.width) // 2, (size - sm.height) // 2))
        arr = np.asarray(img).copy()
        arr[..., 3] = (arr[..., 3] * min(fin, fout)).astype(np.uint8)
        proc.stdin.write(arr.tobytes())
    proc.stdin.close()
    proc.wait()
    return out


# ----------------------------------------------------------------- sfx kecil
def sfx_ratchet(d=0.9):
    """Bunyi impact wrench 'brrrt' – klik pantas yang makin perlahan."""
    n = int(d * SR)
    out = np.zeros(n)
    t, rate = 0.0, 32.0
    rng = np.random.default_rng(5)
    click = rng.standard_normal(int(0.012 * SR)) * np.exp(-np.linspace(0, 8, int(0.012 * SR)))
    while t < d * 0.8:
        i = int(t * SR)
        j = min(n, i + len(click))
        out[i:j] += click[:j - i]
        t += 1 / rate
        rate = max(10.0, rate * 0.985)
    return out / (np.abs(out).max() + 1e-9) * 0.6


def sfx_charge(d=0.9):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 300 + 900 * (t / d)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + 0.25 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)
    return s * np.sin(np.pi * t / d) * 0.6


def sfx_hiss(d=1.2):
    n = int(d * SR)
    s = np.random.default_rng(7).standard_normal(n)
    s = np.diff(s, prepend=0)                        # hi-pass ringkas
    t = np.arange(n) / SR
    return s / np.abs(s).max() * np.sin(np.pi * t / d) * 0.5


def sfx_drill(d=1.2):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * 180 * t)) * 0.3 + np.random.default_rng(9).standard_normal(n) * 0.1
    return s * np.sin(np.pi * t / d) * 0.5


SFX_EXTRA = {"ratchet": sfx_ratchet, "charge": sfx_charge, "hiss": sfx_hiss, "drill": sfx_drill}
TYPE_SFX = {"bolt": "ratchet", "energy": "charge", "sparks": "hiss", "drill": "drill",
            "airflow": "whoosh"}


def sfx_events(anims: list[dict], gain: float = 0.35) -> list[dict]:
    ev = []
    for a in anims:
        ev.append({"type": "pop", "t": a["start"], "gain": gain})
        ev.append({"type": TYPE_SFX[a["type"]], "t": a["start"] + 0.1, "gain": gain,
                   "pan": -0.3 if a.get("side") == "left" else 0.3})
    return ev


# ------------------------------------------------------------------- demo
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", default="work/anim_demo")
    args = ap.parse_args()
    out = Path(args.demo)
    out.mkdir(parents=True, exist_ok=True)
    for typ in DRAW:
        mov = render_animation({"type": typ, "start": 0, "end": 2.0}, out / f"{typ}.mov")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mov, "-vf",
                        "split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse",
                        out / f"{typ}.gif"], check=True)
        print("->", mov)
    print(json.dumps(LABELS, indent=1))
