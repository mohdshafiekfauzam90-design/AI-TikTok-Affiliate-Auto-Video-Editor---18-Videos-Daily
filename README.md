# MUROH DOOH Auto Video Editor — TikTok Affiliate (Gaya A + B)

Editor video automatik untuk video affiliate TikTok. Satu config JSON → satu MP4 sedia muat naik.

| # | Ciri | Cara |
|---|------|------|
| 1 | Format 1080×1920 (9:16), 30fps | ffmpeg scale + crop (base disimpan 2160×3840 jika sumber 4K supaya zoom tajam) |
| 2 | Rakaman & suara asal dikekalkan | audio asal 100% + compressor ringan + loudnorm −14 LUFS (standard TikTok) |
| 3 | Subtitle Bahasa Melayu automatik | Whisper large-v3 (whisper.cpp) dengan cap masa setiap perkataan |
| 4 | Hook 3 saat pertama | label + 2 baris besar, pop-in + goncang, flash putih, zoom-out |
| 5 | Subtitle animasi + kata kunci berwarna | ASS karaoke: perkataan aktif membesar; produk=hijau, nombor=kuning, faedah=merah jambu, kegunaan=cyan |
| 6 | Zoom in / zoom out | ekspresi zoom lancar (smoothstep) per frame pada bahagian penting |
| 7 | Sound effect | disintesis (tiada aset luar): boom, whoosh, pop, riser, ding |
| 8 | Grafik & callout produk | kad PNG (Pillow) dengan badge, meluncur masuk dari sisi |
| 9 | CTA di penghujung | teks berdenyut + butang "TEKAN BEG KUNING" + anak panah |
| 10 | MP4 kualiti tinggi | H.264 High@4.2, CRF 16 preset slow, AAC 320k 48kHz, +faststart |

## Pemasangan

```bash
sudo apt install ffmpeg fonts-inter
pip install -r requirements.txt
```

Model Whisper: muat turun `large-v3.pt` rasmi OpenAI dan tukar ke ggml (tanpa PyTorch):

```bash
curl -L -o large-v3.pt https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt
pip download --no-deps --no-binary :all: openai-whisper && tar xzf openai_whisper-*.tar.gz   # untuk mel_filters + tokenizer
python3 tools/convert_pt_to_ggml.py large-v3.pt openai_whisper-*/whisper/assets models/ggml-large-v3.bin
```

## Guna

```bash
# 1. letak video asal dalam input/, salin config contoh
python3 muroh_dooh_editor.py configs/ryoku_impact_wrench.json --transcribe-only   # semak transkrip + masa
# 2. sunting hook / callouts / zooms / cta dalam config ikut masa transkrip
python3 muroh_dooh_editor.py configs/ryoku_impact_wrench.json --preview --start 0 --length 15
python3 muroh_dooh_editor.py configs/ryoku_impact_wrench.json                      # render akhir -> output/
```

Transkrip disimpan dalam `work/<config>/transcript.json` (cache). Pembetulan ejaan Whisper diletak dalam `"corrections"`.

## Contoh: `configs/ryoku_impact_wrench.json`
Review RYOKU 20V Brushless Impact Wrench 500Nm (78 s): hook "SKRU KETAT? SETTLE 1 SAAT!", 7 callout
(Impact Wrench, 500 Nm, 1/2" Drive, Set Lengkap, 2x Bateri, Sesuai Untuk, Model Terkini), 9 zoom, CTA beg kuning.
