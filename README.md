# AI TikTok Affiliate Auto Video Editor (HyperFrames)

Pipeline that turns a raw TikTok Shop affiliate recording into a finished
1080 × 1920, 9:16, 30 fps MP4, built with [HyperFrames](https://hyperframes.heygen.com)
(HTML + GSAP rendered to video).

First edit: **MUROH DOOH: Rotary Hammer Drill 2200W** (127 s raw → 69.4 s final).

## Pipeline

| Step | File | What it does |
| --- | --- | --- |
| 1. Transcribe | `pipeline/data/original_transcript.json` | Whisper large-v3, `language=ms`, word timestamps. Key figures (2200 watt, 2 mode, 6 batang, 1 carbon) confirmed by a second, unprompted pass. |
| 2. Cut list | `pipeline/edl.py` | Removes dead air (pauses > 0.30 s shrunk to 0.14 s), repeated lines and fillers; every cut snapped to the quietest 10 ms. Builds the hook (J-cut). |
| 3. Spine | `pipeline/build_spine.py` | Cuts the original 4K HEVC to a 1080×1920/30 fps spine, original voice kept, 8 ms fades on every cut. Voice loudness-normalised to about −14 LUFS. |
| 4. Verify | `pipeline/data/spine_transcript.json` | Re-transcribes the cut spine to confirm no word was clipped, and gives caption timing in output time. |
| 5. Compose | `pipeline/gen.py` → `edit/` | Generates the HyperFrames project: captions, hook, motion graphics, SFX, camera moves, colour grade. |
| 6. Render | `cd edit && npx hyperframes render -q delivery` | Final MP4. |

## Edit decisions (hammer drill video)

- **Hook (0–4.4 s):** brick-breaking demo with the speaker's own line
  *"Kalau korang nak buat tebuk dinding, nak pecah konkrit ke… semua boleh!"* laid over it,
  plus a "HAMMER DRILL / 2200 WATT" headline on frame 0.
- **Removed:** "hammer drill" said 3× (kept once), the repeated "dapat mata dia",
  the doubled grease instructions, the "carbon" stumble, a hesitation before "6 batang", and all long pauses.
- **Motion graphics (spoken facts only):** Rotary Hammer Drill, Harga Bajet, 2200 Watt counter,
  2 Mode (Hacking / Tebuk Dinding), Plug 3 Pin, kit checklist (Casing, Mata ×6 batang,
  Minyak grease, 1 Carbon), carbon-change and grease tips, Sesuai untuk tukang & contractor.
- **Camera:** settle-in zooms on the 3 scene reveals, alternating 0/+6 % framing on jump cuts,
  pushes on "2200 watt" and "6 batang", slow push under the CTA.
- **Transitions:** 2 white flashes (product reveal, case reveal) + whooshes; hard cuts elsewhere.
- **Grade:** HyperFrames *Product Polish* treatment, slightly brighter (exposure +0.06, shadows +0.09, vibrance +0.05).
- **CTA:** "KLIK BEG KAT BAWAH" + bag icon + bouncing arrow + MUROH DOOH sign-off, over the speaker's own "boleh tengok dekat beg dekat bawah".
- **Captions:** Malay, 2–4 words, active-word highlight; also exported as `edit/captions_ms.srt`.
- **Music:** none. A music bed needs a HeyGen sign-in (`npx hyperframes auth login`) or your own track.

## Re-run

```bash
npm install                      # hyperframes CLI
pip install openai-whisper       # + torch
python3 pipeline/edl.py audio16k.wav build/edl.json
python3 pipeline/build_spine.py raw.mp4 build/edl.json build/spine.mp4
python3 pipeline/gen.py
cd edit && npx hyperframes check && npx hyperframes render -q delivery -o final.mp4
```

Large media (`*.mp4`, `*.wav`) are git-ignored; `edit/assets/video/spine.mp4` must be rebuilt (steps 2–3) on a fresh clone.
