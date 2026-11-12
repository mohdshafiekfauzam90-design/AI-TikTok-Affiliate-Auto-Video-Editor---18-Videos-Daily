#!/usr/bin/env python3
"""MUROH DOOH Auto Video Editor — TikTok affiliate edit (Gaya A + B).

Pipeline (semua tempatan, ffmpeg + Whisper + Pillow + numpy):
  1. normalise  -> 1080x1920 9:16, 30fps, audio asal dikekalkan
  2. transcribe -> Whisper (Bahasa Melayu) dengan cap masa setiap perkataan
  3. subtitles  -> ASS beranimasi, perkataan aktif membesar, kata kunci berwarna
  4. hook       -> teks hook 3 saat pertama (pop + goncang)
  5. zoom       -> zoom in / zoom out lancar pada bahagian penting
  6. graphics   -> kad callout produk (PNG) yang meluncur masuk
  7. sfx        -> kesan bunyi disintesis (whoosh, pop, boom, ding)
  8. cta        -> kad CTA di penghujung video
  9. render     -> MP4 H.264 High, CRF rendah, AAC 320k, +faststart

Guna:
  python3 muroh_dooh_editor.py configs/ryoku_impact_wrench.json
  python3 muroh_dooh_editor.py configs/x.json --transcribe-only   # semak transkrip dahulu
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SR = 48000
FONT_BLACK = "Inter Black"
FONT_FILE_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_FILE_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


# ----------------------------------------------------------------- utilities
def run(cmd: list[str]) -> None:
    print("  $", " ".join(str(c) for c in cmd)[:300], flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def find_font(preferred: str) -> str:
    if Path(preferred).exists():
        return preferred
    out = subprocess.run(["fc-match", "-f", "%{file}", "Inter:black"],
                         capture_output=True, text=True).stdout
    return out or "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def ass_color(h: str, alpha: int = 0) -> str:
    r, g, b = hex_to_rgb(h)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def ass_time(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{(cs // 6000) % 60:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


_FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def text_width(text: str, size: int) -> int:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = ImageFont.truetype(find_font(FONT_FILE_BLACK), size)
    b = _FONT_CACHE[size].getbbox(text)
    return b[2] - b[0]


def fit_size(text: str, size: int, max_w: int = 960) -> int:
    """Kecilkan saiz fon supaya teks muat dalam lebar skrin (selamat UI TikTok)."""
    while size > 30 and text_width(text, size) > max_w:
        size -= 2
    return size


def display_word(w: str) -> str:
    if re.match(r"^\d+nm", w.lower()):
        return re.sub(r"(?i)nm", "Nm", w)
    return w.upper()


# ------------------------------------------------------------- 1. normalise
def normalise(src: Path, dst: Path) -> None:
    if dst.exists():
        print(f"[1] base video sedia ada: {dst}")
        return
    # Base disimpan pada 2x (2160x3840) jika sumber 4K, supaya zoom kekal tajam;
    # output akhir tetap 1080x1920.
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)],
                         capture_output=True, text=True, check=True).stdout
    sw, sh = sorted(int(x) for x in out.strip().split(",")[:2])
    k = 2 if sw >= 2 * W else 1
    print(f"[1] Normalise -> {W * k}x{H * k} 9:16 @{FPS}fps (output akhir {W}x{H})")
    vf = (f"scale={W * k}:{H * k}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={W * k}:{H * k},fps={FPS},setsar=1")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0",
         "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "12",
         "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", str(SR), dst])


# ------------------------------------------------------------ 2. transcribe
def transcribe(base: Path, out_json: Path, cfg: dict) -> list[dict]:
    if out_json.exists():
        print(f"[2] transkrip sedia ada: {out_json}")
        return json.loads(out_json.read_text())["words"]
    wcfg = cfg.get("whisper", {})
    lang = wcfg.get("language", "ms")
    wav = out_json.with_suffix(".wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", base, "-vn", "-ac", "1", "-ar", "16000",
         "-af", "highpass=f=80,loudnorm", wav])
    ggml = wcfg.get("ggml_model")
    if ggml:
        # Backend 1: whisper.cpp (pywhispercpp) dengan model Whisper OpenAI ditukar ke ggml
        from pywhispercpp.model import Model

        ggml = os.path.expanduser(ggml)
        print(f"[2] Whisper (whisper.cpp) model={Path(ggml).name} bahasa={lang}")
        model = Model(ggml, n_threads=os.cpu_count() or 4, print_progress=False,
                      print_realtime=False)
        # segmen 1 perkataan = cap masa perkataan
        segs = model.transcribe(str(wav), language=lang, token_timestamps=True,
                                max_len=1, split_on_word=True,
                                initial_prompt=wcfg.get("initial_prompt", ""),
                                temperature=0.0)
        words = [{"word": s.text.strip(), "start": s.t0 / 100.0, "end": s.t1 / 100.0}
                 for s in segs if s.text.strip()]
        text = " ".join(w["word"] for w in words)
    else:
        # Backend 2: pakej openai-whisper (PyTorch)
        import whisper

        model_name = wcfg.get("model", "medium")
        print(f"[2] Whisper '{model_name}' bahasa={lang}")
        model = whisper.load_model(model_name)
        res = model.transcribe(str(wav), language=lang, task="transcribe",
                               word_timestamps=True, fp16=False, temperature=0.0,
                               initial_prompt=wcfg.get("initial_prompt"),
                               condition_on_previous_text=False)
        words = [{"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])}
                 for seg in res["segments"] for w in seg.get("words", []) if w["word"].strip()]
        text = res["text"]
    out_json.write_text(json.dumps({"text": text, "words": words}, ensure_ascii=False, indent=1))
    return words


def apply_corrections(words: list[dict], cfg: dict) -> list[dict]:
    """Betulkan ejaan Whisper (cth. 'rioku' -> 'RYOKU') dari config."""
    corr = {k.lower(): v for k, v in cfg.get("corrections", {}).items()}
    out = []
    for w in words:
        core = re.sub(r"[^\w%]", "", w["word"].lower())
        if core in corr:
            if corr[core] == "":
                continue
            punct = re.search(r"[.,!?]*$", w["word"]).group(0)
            w = {**w, "word": corr[core] + punct}
        out.append(w)
    # gantian ikut julat masa (cth. nama jenama yang Whisper terlepas)
    for ov in cfg.get("word_overrides", []):
        out = [w for w in out if not (ov["from"] <= w["start"] < ov["to"])]
        out += [dict(x) for x in ov["words"]]
    out.sort(key=lambda w: w["start"])
    return out


# -------------------------------------------------------------- 3. subtitles
def chunk_words(words: list[dict], max_words: int = 3, max_chars: int = 16,
                max_gap: float = 0.6) -> list[list[dict]]:
    chunks, cur = [], []
    for w in words:
        text_len = sum(len(x["word"]) + 1 for x in cur) + len(w["word"])
        gap = w["start"] - cur[-1]["end"] if cur else 0
        ends_sentence = bool(cur) and re.search(r"[.!?,]$", cur[-1]["word"])
        if cur and (len(cur) >= max_words or text_len > max_chars or gap > max_gap
                    or ends_sentence):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def keyword_color(word: str, cfg: dict) -> str | None:
    core = re.sub(r"[^\w%]", "", word.lower())
    for color, kws in cfg.get("keyword_colors", {}).items():
        for kw in kws:
            if core == kw.lower() or (len(kw) > 3 and core.startswith(kw.lower())):
                return color
    if re.search(r"\d", core):
        return cfg.get("number_color", "#FFE600")
    return None


def build_ass(words: list[dict], cfg: dict, duration: float, out: Path) -> None:
    st = cfg.get("subtitle_style", {})
    sub_y = st.get("y", 1330)
    font_size = st.get("font_size", 86)
    active_col = st.get("active_color", "#FFE600")
    hook = cfg["hook"]
    cta = cfg["cta"]
    cta_start = duration - cta.get("duration", 4.0)

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT_BLACK},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,4,5,40,40,0,1
Style: Hook,{FONT_BLACK},104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,26,0,5,60,60,0,1
Style: HookTop,{FONT_BLACK},62,&H00000000,&H00000000,&H0000E6FF,&H00000000,-1,0,0,0,100,100,0,0,3,18,0,5,60,60,0,1
Style: CTA,{FONT_BLACK},92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,5,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev: list[str] = []

    def add(layer, t0, t1, style, text):
        ev.append(f"Dialogue: {layer},{ass_time(t0)},{ass_time(t1)},{style},,0,0,0,,{text}")

    # ---- animated subtitles (karaoke pop: perkataan aktif kuning + besar)
    chunks = chunk_words(words, st.get("max_words", 3), st.get("max_chars", 16))
    for ci, ch in enumerate(chunks):
        c_start = ch[0]["start"]
        nxt = chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else duration
        c_end = min(ch[-1]["end"] + 0.35, nxt)
        for wi, w in enumerate(ch):
            t0 = c_start if wi == 0 else w["start"]
            t1 = ch[wi + 1]["start"] if wi + 1 < len(ch) else c_end
            if t1 - t0 < 0.02:
                continue
            parts = []
            for wj, x in enumerate(ch):
                txt = ass_escape(display_word(x["word"]))
                kc = keyword_color(x["word"], cfg)
                if wj == wi:
                    col = kc or active_col
                    parts.append(
                        f"{{\\c{ass_color(col)}\\3c&H000000&\\fscx112\\fscy112"
                        f"\\t(0,90,\\fscx122\\fscy122)\\t(90,180,\\fscx112\\fscy112)}}"
                        f"{txt}{{\\r}}")
                elif kc:
                    parts.append(f"{{\\c{ass_color(kc)}}}{txt}{{\\r}}")
                else:
                    parts.append(txt)
            intro = ("\\fscx80\\fscy80\\t(0,120,\\fscx100\\fscy100)"
                     if wi == 0 else "")
            plain = " ".join(display_word(x["word"]) for x in ch)
            fs = fit_size(plain, int(font_size * 1.12), 1000)
            fs = min(font_size, int(fs / 1.12))
            add(10, t0, t1, "Sub", f"{{\\pos({W // 2},{sub_y})\\fs{fs}{intro}}}" + " ".join(parts))

    # ---- HOOK (0 - 3 s): label + 2 baris besar, pop + goncang
    hd = hook.get("duration", 3.0)
    add(20, 0.0, hd, "HookTop",
        f"{{\\pos({W // 2},300)\\fs{fit_size(hook['label'], 62, 900)}\\fscx0\\fscy0\\t(0,180,\\fscx110\\fscy110)"
        f"\\t(180,260,\\fscx100\\fscy100)\\fad(0,200)}}{ass_escape(hook['label'])}")
    for i, line in enumerate(hook["lines"]):
        y = 470 + i * 150
        col = hook.get("colors", ["#FFFFFF", "#FFE600"])[i % 2]
        delay = 150 + i * 220
        shake = "".join(
            f"\\t({delay + 260 + k * 60},{delay + 290 + k * 60},\\frz{(-2.5 if k % 2 else 2.5)})"
            for k in range(4)) + f"\\t({delay + 500},{delay + 540},\\frz0)"
        add(20, 0.0, hd, "Hook",
            f"{{\\pos({W // 2},{y})\\fs{fit_size(line, 104, 900)}\\c{ass_color(col)}"
            f"\\3c{ass_color(hook.get('box_color', '#E0102E'))}"
            f"\\fscx0\\fscy0\\t({delay},{delay + 160},\\fscx118\\fscy118)"
            f"\\t({delay + 160},{delay + 260},\\fscx100\\fscy100){shake}\\fad(0,200)}}"
            f"{ass_escape(line)}")

    # ---- CTA (penghujung)
    for i, line in enumerate(cta["lines"]):
        y = cta.get("y", 560) + i * 125
        col = cta.get("colors", ["#FFFFFF", "#FFE600", "#39FF14"])[i % 3]
        d = 250 + i * 250
        pulse = "".join(
            f"\\t({d + 400 + k * 600},{d + 700 + k * 600},\\fscx108\\fscy108)"
            f"\\t({d + 700 + k * 600},{d + 1000 + k * 600},\\fscx100\\fscy100)"
            for k in range(6))
        add(30, cta_start, duration, "CTA",
            f"{{\\pos({W // 2},{y})\\fs{fit_size(line, 92, 960)}\\c{ass_color(col)}\\fscx0\\fscy0"
            f"\\t({d},{d + 180},\\fscx115\\fscy115)\\t({d + 180},{d + 300},\\fscx100\\fscy100){pulse}}}"
            f"{ass_escape(line)}")

    out.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    print(f"[3] ASS: {len(chunks)} chunk subtitle -> {out}")


# ------------------------------------------------------------ 6. graphics
def rounded_card(w: int, h: int, r: int, fill, outline=None, ow=0) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=ow)
    return img


def render_callout(c: dict, path: Path) -> tuple[int, int]:
    fb = ImageFont.truetype(find_font(FONT_FILE_BLACK), c.get("title_size", 92))
    fs = ImageFont.truetype(find_font(FONT_FILE_BOLD), c.get("sub_size", 40))
    accent = hex_to_rgb(c.get("color", "#39FF14"))
    title, sub = c["title"], c.get("subtitle", "")
    tb = fb.getbbox(title)
    sb = fs.getbbox(sub) if sub else (0, 0, 0, 0)
    pad_x, pad_y, bar = 42, 30, 18
    cw = max(tb[2], sb[2]) + pad_x * 2 + bar
    ch = (tb[3] - tb[1]) + ((sb[3] - sb[1]) + 18 if sub else 0) + pad_y * 2
    margin = 30
    img = Image.new("RGBA", (cw + margin * 2, ch + margin * 2), (0, 0, 0, 0))
    # bayang lembut
    shadow = rounded_card(cw, ch, 28, (0, 0, 0, 170)).filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(shadow, (margin + 6, margin + 12))
    card = rounded_card(cw, ch, 28, (12, 14, 18, 235), outline=accent + (255,), ow=5)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, bar + 14, ch - 1), 28, fill=accent + (255,))
    d.rectangle((bar, 0, bar + 14, ch - 1), fill=(12, 14, 18, 235))
    d.text((bar + pad_x - tb[0], pad_y - tb[1]), title, font=fb, fill=accent + (255,))
    if sub:
        d.text((bar + pad_x - sb[0], pad_y + (tb[3] - tb[1]) + 18 - sb[1]), sub,
               font=fs, fill=(255, 255, 255, 255))
    img.alpha_composite(card, (margin, margin))
    # badge kecil (cth. "✓", "NEW")
    if c.get("badge"):
        bf = ImageFont.truetype(find_font(FONT_FILE_BLACK), 30)
        bb = bf.getbbox(c["badge"])
        bw, bh = bb[2] - bb[0] + 30, bb[3] - bb[1] + 18
        badge = rounded_card(bw, bh, bh // 2, (224, 16, 46, 255))
        ImageDraw.Draw(badge).text((15 - bb[0], 9 - bb[1]), c["badge"], font=bf, fill="white")
        big = Image.new("RGBA", (img.width + 20, img.height + 20), (0, 0, 0, 0))
        big.alpha_composite(img, (0, 20))
        big.alpha_composite(badge, (big.width - bw - 30, 8))
        img = big
    img.save(path)
    return img.size


def render_cta_panel(cfg: dict, path: Path) -> None:
    """Panel gelap separa telus + butang 'beg kuning' + anak panah ke bawah."""
    cta = cfg["cta"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # gradien gelap atas -> bawah supaya teks CTA jelas
    for y in range(H):
        a = int(150 * (0.55 + 0.45 * math.sin(math.pi * min(1, y / H))))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    # butang
    bf = ImageFont.truetype(find_font(FONT_FILE_BLACK), 64)
    label = cta.get("button", "BELI SEKARANG")
    bb = bf.getbbox(label)
    bw, bh = bb[2] - bb[0] + 150, 150
    bx, by = (W - bw) // 2, cta.get("button_y", 1020)
    glow = rounded_card(bw + 40, bh + 40, 95, (255, 214, 0, 140)).filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow, (bx - 20, by - 20))
    btn = rounded_card(bw, bh, 75, (255, 214, 0, 255), outline=(255, 255, 255, 255), ow=6)
    bd = ImageDraw.Draw(btn)
    # ikon beg (troli) ringkas
    cx, cy = 62, bh // 2
    bd.rounded_rectangle((cx - 28, cy - 18, cx + 28, cy + 32), 8, fill=(20, 20, 20, 255))
    bd.arc((cx - 16, cy - 40, cx + 16, cy - 4), 180, 360, fill=(20, 20, 20, 255), width=7)
    bd.text((110 - bb[0], (bh - (bb[3] - bb[1])) // 2 - bb[1]), label, font=bf, fill=(20, 20, 20, 255))
    img.alpha_composite(btn, (bx, by))
    # anak panah ke bawah-kiri (ke arah beg kuning TikTok)
    ax, ay = cta.get("arrow_x", 150), by + bh + 70
    for k in range(3):
        y0 = ay + k * 70
        d.polygon([(ax - 55, y0), (ax + 55, y0), (ax, y0 + 55)],
                  fill=(255, 214, 0, 255 - k * 70))
    img.save(path)


# -------------------------------------------------------------------- 7. sfx
def _env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.exp(-np.linspace(0, 6, r))
    return e


def sfx_whoosh(d=0.45):
    n = int(d * SR)
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(n)
    # sapuan band-pass ringkas menggunakan FFT bergerak
    t = np.linspace(0, 1, n)
    out = np.zeros(n)
    seg = 1024
    for i in range(0, n, seg // 2):
        blk = noise[i:i + seg]
        if len(blk) < 16:
            break
        f = np.fft.rfft(blk * np.hanning(len(blk)))
        freqs = np.fft.rfftfreq(len(blk), 1 / SR)
        centre = 300 + 4500 * math.sin(math.pi * t[min(i, n - 1)])
        f *= np.exp(-((freqs - centre) / (centre * 0.6)) ** 2)
        out[i:i + len(blk)] += np.fft.irfft(f, len(blk))
    env = np.sin(np.pi * t) ** 1.5
    out = out * env
    return out / (np.abs(out).max() + 1e-9) * 0.8


def sfx_pop(d=0.14):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 900 * np.exp(-t * 18) + 250
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    return s * 0.8


def sfx_boom(d=0.9):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 6) + 42
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    click = np.random.default_rng(2).standard_normal(n) * np.exp(-t * 120) * 0.5
    s = np.tanh((s + click) * 2.2)
    return s * 0.9


def sfx_ding(d=1.1):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1318.5 * t) + 0.6 * np.sin(2 * np.pi * 1975.5 * t)
         + 0.3 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 4)
    s2 = np.zeros(n)
    off = int(0.11 * SR)
    s2[off:] = (np.sin(2 * np.pi * 1760 * t[:n - off]) * np.exp(-t[:n - off] * 3.5))
    s = s + 0.8 * s2
    return s / np.abs(s).max() * 0.7


def sfx_riser(d=0.8):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 200 + 1600 * (t / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2
    noise = np.random.default_rng(3).standard_normal(n) * (t / d) ** 3 * 0.25
    return (s * 0.5 + noise) * 0.7


SFX = {"whoosh": sfx_whoosh, "pop": sfx_pop, "boom": sfx_boom, "ding": sfx_ding,
       "riser": sfx_riser}


def build_sfx_track(events: list[dict], duration: float, out: Path) -> None:
    n = int((duration + 2) * SR)
    track = np.zeros((n, 2))
    cache: dict[str, np.ndarray] = {}
    for e in events:
        kind = e["type"]
        if kind not in cache:
            cache[kind] = SFX[kind]()
        s = cache[kind] * e.get("gain", 1.0)
        i = int(max(0.0, e["t"] - e.get("lead", 0.0)) * SR)
        j = min(n, i + len(s))
        pan = e.get("pan", 0.0)
        track[i:j, 0] += s[:j - i] * (1 - max(0, pan))
        track[i:j, 1] += s[:j - i] * (1 + min(0, pan))
    track = np.clip(track, -1, 1)
    pcm = (track * 32767).astype(np.int16)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"[7] SFX: {len(events)} kesan bunyi -> {out}")


# ------------------------------------------------------------------- 5. zoom
def zoom_expr(zooms: list[dict]) -> str:
    """z(t) = 1 + Σ (scale-1) * smoothstep(ramp in) * smoothstep(ramp out)."""
    terms = []
    for z in zooms:
        a, b, s = z["start"], z["end"], z["scale"]
        ri, ro = z.get("ramp_in", 0.35), z.get("ramp_out", 0.45)
        r = f"clip((t-{a})/{ri},0,1)*clip(({b}-t)/{ro},0,1)"
        terms.append(f"{s - 1:.3f}*(({r})*({r})*(3-2*({r})))")
    return "1+" + "+".join(terms) if terms else "1"


# ----------------------------------------------------------------- 9. render
def render(cfg: dict, base: Path, ass: Path, sfx: Path, work: Path, out: Path,
           duration: float) -> None:
    hook_d = cfg["hook"].get("duration", 3.0)
    cta_start = duration - cfg["cta"].get("duration", 4.0)
    zexpr = zoom_expr(cfg.get("zooms", []))

    inputs = ["-i", base, "-i", sfx]
    filters = [
        # zoom: besarkan setiap frame ikut z(t) kemudian potong tengah 1080x1920
        f"[0:v]scale=w='trunc({W}*({zexpr})/2)*2':h='trunc({H}*({zexpr})/2)*2'"
        f":eval=frame:flags=bicubic,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})*0.45',"
        f"eq=contrast=1.06:saturation=1.18:brightness=0.01,unsharp=5:5:0.6,"
        # flash putih ringkas pada permulaan hook (gaya B)
        f"fade=t=in:st=0:d=0.25:color=white[v0]",
    ]
    last = "v0"
    idx = 2
    # kad callout (PNG) – meluncur masuk dari sisi
    for i, c in enumerate(cfg.get("callouts", [])):
        png = work / f"callout_{i}.png"
        cw, chh = render_callout(c, png)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{duration:.3f}", "-i", png]
        a, b = c["start"], c["end"]
        y = c.get("y", 760)
        if c.get("side", "left") == "left":
            x_final, x_off = 24, -cw
        else:
            x_final, x_off = W - cw - 24, W
        xe = (f"if(lt(t,{a}+0.28),{x_off}+({x_final}-({x_off}))*(1-pow(1-(t-{a})/0.28,3)),"
              f"if(gt(t,{b}-0.22),{x_final}+({x_off}-({x_final}))*pow((t-({b}-0.22))/0.22,2),{x_final}))")
        filters.append(f"[{idx}:v]format=rgba[c{i}]")
        filters.append(f"[{last}][c{i}]overlay=x='{xe}':y={y}:enable='between(t,{a},{b})'"
                       f":eof_action=pass[v{i + 1}]")
        last = f"v{i + 1}"
        idx += 1
    # [enhancement] Minimal Smart Animation – widget kartun kecil 1–3 s (jika ON)
    for i, a in enumerate(cfg.get("_anims", [])):
        inputs += ["-i", a["mov"]]
        filters.append(f"[{idx}:v]format=rgba,setpts=PTS-STARTPTS+{a['start']}/TB[an{i}]")
        filters.append(f"[{last}][an{i}]overlay=x={a['x']}:y={a['y']}:eof_action=pass:"
                       f"enable='between(t,{a['start']},{a['end']})'[va{i}]")
        last = f"va{i}"
        idx += 1
    # panel CTA
    panel = work / "cta_panel.png"
    render_cta_panel(cfg, panel)
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{duration:.3f}", "-i", panel]
    filters.append(f"[{idx}:v]format=rgba,fade=t=in:st={cta_start:.3f}:d=0.35:alpha=1[cta]")
    filters.append(f"[{last}][cta]overlay=0:0:enable='gte(t,{cta_start:.3f})'[vc]")
    # gelapkan sedikit latar semasa hook supaya teks menonjol
    filters.append(f"[vc]drawbox=x=0:y=200:w={W}:h=560:color=black@0.28:t=fill:"
                   f"enable='lt(t,{hook_d})'[vh]")
    ass_path = str(ass).replace(":", "\\:").replace("'", "\\'")
    filters.append(f"[vh]ass='{ass_path}',format=yuv420p[vout]")
    # audio: suara asal dikekalkan 100%, SFX dicampur di bawahnya
    sfx_gain = cfg.get("sfx_volume", 0.55)
    filters.append(
        f"[0:a]aresample={SR},highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,"
        f"volume=1.6[voice];[1:a]volume={sfx_gain}[fx];"
        f"[voice][fx]amix=inputs=2:normalize=0:duration=first,"
        f"alimiter=limit=0.95:level=disabled,loudnorm=I=-14:TP=-1.0:LRA=11[aout]")

    graph = work / "filter_graph.txt"
    graph.write_text(";\n".join(filters))
    print("[9] Render MP4 akhir")
    run(["ffmpeg", "-v", "error", "-stats_period", "15", "-stats", "-y", *inputs,
         "-filter_complex_script", graph, "-map", "[vout]", "-map", "[aout]",
         *(["-ss", str(cfg["_ss"])] if cfg.get("_ss") else []),
         "-t", f"{cfg['_len'] or duration:.3f}",
         "-c:v", "libx264", "-preset", cfg.get("preset", "slow"), "-crf", str(cfg.get("crf", 16)),
         "-profile:v", "high", "-level:v", "4.2", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-g", str(FPS * 2), "-bf", "2", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "320k", "-ar", str(SR),
         "-metadata", "title=" + cfg.get("title", "MUROH DOOH edit"), out])


# ------------------------------------------------------------------ main
def auto_sfx(cfg: dict, duration: float) -> list[dict]:
    ev = [{"type": "boom", "t": 0.02, "gain": 0.9},
          {"type": "whoosh", "t": 0.0, "gain": 0.7}]
    for i, _ in enumerate(cfg["hook"]["lines"]):
        ev.append({"type": "pop", "t": 0.15 + i * 0.22, "gain": 0.8})
    ev.append({"type": "whoosh", "t": cfg["hook"].get("duration", 3.0) - 0.15, "gain": 0.6})
    for c in cfg.get("callouts", []):
        ev.append({"type": "whoosh", "t": c["start"], "gain": 0.7,
                   "pan": -0.4 if c.get("side", "left") == "left" else 0.4})
        ev.append({"type": "pop", "t": c["start"] + 0.27, "gain": 0.7})
    for z in cfg.get("zooms", []):
        if z.get("sfx", True):
            ev.append({"type": "riser" if z["scale"] >= 1.3 else "whoosh",
                       "t": z["start"], "lead": 0.45 if z["scale"] >= 1.3 else 0.1,
                       "gain": 0.45})
    cta_start = duration - cfg["cta"].get("duration", 4.0)
    ev += [{"type": "whoosh", "t": cta_start - 0.1, "gain": 0.7},
           {"type": "ding", "t": cta_start + 0.3, "gain": 0.8},
           {"type": "pop", "t": cta_start + 0.55, "gain": 0.6},
           {"type": "pop", "t": cta_start + 0.8, "gain": 0.6}]
    return ev + cfg.get("extra_sfx", [])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--transcribe-only", action="store_true")
    ap.add_argument("--preview", action="store_true", help="render pantas kualiti rendah")
    ap.add_argument("--start", type=float, help="(preview) mula pada saat ini")
    ap.add_argument("--length", type=float, help="(preview) panjang klip")
    ap.add_argument("--smart-anim", choices=["on", "off"],
                    help="Minimal Smart Animation (override config smart_animation.enabled)")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = json.loads(cfg_path.read_text())
    root = cfg_path.parent.parent
    src = Path(os.path.expanduser(cfg["input"]))
    src = src if src.is_absolute() else root / src
    work = root / cfg.get("work_dir", "work") / cfg_path.stem
    work.mkdir(parents=True, exist_ok=True)
    out = root / cfg.get("output", f"output/{cfg_path.stem}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)

    g = cfg.get("whisper", {}).get("ggml_model")
    if g and not Path(os.path.expanduser(g)).is_absolute():
        cfg["whisper"]["ggml_model"] = str(root / g)

    base = work / "base.mov"
    normalise(src, base)
    words = transcribe(base, work / "transcript.json", cfg)
    if args.transcribe_only:
        for w in words:
            print(f"{w['start']:6.2f}-{w['end']:6.2f} {w['word']}")
        return
    words = apply_corrections(words, cfg)
    duration = cfg.get("duration") or probe_duration(base)

    ass = work / "subs.ass"
    build_ass(words, cfg, duration, ass)
    sfx_ev = auto_sfx(cfg, duration)

    # [enhancement] Minimal Smart Animation (90% video asal + ≤10% animasi)
    sa = cfg.setdefault("smart_animation", {})
    enabled = sa.get("enabled", False) if args.smart_anim is None else args.smart_anim == "on"
    if enabled:
        import smart_anim

        SFX.update(smart_anim.SFX_EXTRA)
        anims = smart_anim.plan_animations(words, cfg, duration)
        size = sa.get("size", 320)
        smart_anim.place(anims, cfg, size, W)
        for i, a in enumerate(anims):
            a["mov"] = str(smart_anim.render_animation(a, work / f"anim_{i}_{a['type']}.mov", size))
        (work / "anim_plan.json").write_text(json.dumps(anims, ensure_ascii=False, indent=1))
        cfg["_anims"] = anims
        out = out.with_name(out.stem + "_smartanim.mp4")
        sfx_ev += smart_anim.sfx_events(anims, sa.get("sfx_gain", 0.35))
    else:
        print("[A] Smart animation: OFF")

    sfx = work / "sfx.wav"
    build_sfx_track(sfx_ev, duration, sfx)
    if args.preview:
        cfg["preset"], cfg["crf"] = "ultrafast", 26
        out = out.with_name(out.stem + "_preview.mp4")
    cfg["_ss"], cfg["_len"] = args.start, args.length
    render(cfg, base, ass, sfx, work, out, duration)
    print(f"\nSIAP -> {out}")


if __name__ == "__main__":
    sys.exit(main())
