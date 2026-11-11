# TikTok Affiliate Auto Video Editor: standing workflow

The owner (MUROH DOOH, TikTok Shop Affiliate Malaysia) sends a raw product video, usually as a
Google Drive link, and wants it edited. Reply in Bahasa Melayu. Run this whole workflow every
time, without being asked again, unless the owner says otherwise.

## Editing brief (always applies)

1. Remove awkward pauses, long silences and repeated sentences (never cut a word: re-transcribe the cut to check).
2. Transcribe the original Malay speech; captions must match what is said (Whisper large-v3, `language="ms"`).
3. Find the key moments; add animation, sound effects and motion graphics that fit.
4. A strong hook in the first 3 seconds (best visual + the speaker's own strongest line, J-cut).
5. Natural zoom-in/zoom-out and transitions, never excessive.
6. Colour grade: premium, bright, clear (HyperFrames `Product Polish` treatment; keep product colours true).
7. Keep the original voice. Never change facts or product specs.
8. Show product functions and benefits through visual demo moments.
9. An engaging CTA at the end telling viewers to tap the bag below ("KLIK BEG KAT BAWAH").
10. Final: 1080 × 1920, 9:16, MP4 (H.264, 30 fps).

Style: professional, clean, engaging, for TikTok Shop Affiliate Malaysia. Never invent product
visuals, prices, discounts or specs not in the footage or speech. Keep the MUROH DOOH identity
(brand tag + sign-off; palette yellow #FFD21F, red #E5252A, ink #0D0D0D unless the owner gives an official one).
Never put a "REVIEW JUJUR · MUROH DOOH" line (or any "review jujur" kicker) on the hook: the owner asked for it gone.

## Pipeline (see README.md for details)

1. **Get the video**: from a Drive link id, `curl -L -o raw.mp4 "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"` into the scratchpad.
2. **Transcribe**: Whisper large-v3 on a 16 kHz mono wav; check key numbers/specs with a second, unprompted pass.
3. **Cut list**: copy `pipeline/edl_work_light.py` (the newest, most general one) to `pipeline/edl_<video>.py`
   and set `KEEPS`, `MANUAL_CUTS` and `HOOK`. A keep may carry `{"speed": 1.5}` (a slow demo) or `{"gain": 0}`
   (mute a repeated line under a demo shot); `HOOK` with `voice=None` is an in-sync hook shot. Check segment ends
   against the audio level: whisper word ends are often ~0.2 s early, and a clipped last word shows up in step 5.
   Kinds: `speech` (snap edges + trim inner pauses), `exact` (trim pauses, keep the given edges), `demo` (keep exactly):
   use `demo` for a line where the speaker pauses inside a number ("lima puluh… watt", "6500… K"), or the pause
   trim cuts the number apart. When the full-spine transcript disagrees, re-transcribe just that stretch of the
   spine and of the original to tell a real clip from an ASR slip (see `pipeline/edl_work_light.py`).
4. **Spine**: `python3 pipeline/build_spine.py raw.mp4 edl.json spine.mp4` (per-segment encode; never one giant filter graph: it runs out of memory on 4K), then loudnorm to about −14.5 LUFS.
5. **Verify**: re-transcribe the spine; every word must be present.
6. **Compose**: one HyperFrames project per video in `projects/<video>/` (copy `assets/sfx`, `assets/vendor`,
   `hyperframes.json`, `package.json` from `projects/tangga-lipat/`; data in `pipeline/data/<video>/`). Copy
   `pipeline/gen_work_light.py` (newest) to `pipeline/gen_<video>.py` and write the scenes for the spoken facts. Set the
   caption groups by hand (`MANUAL_GROUPS`, natural Malay phrases, a number always with its unit); keep cards off
   the presenter's face, checked on snapshots of the close-ups (the face moves: a side column covered it in the work
   light video, so cards now sit just above the captions, bottom-anchored); keep the CTA below the face; hide
   captions under the CTA. `pipeline/gen_work_light.py` has a compact `card_scene()` helper for spec cards.
   With no presenter on camera (hands-only demo, e.g. `pipeline/gen_table_vice.py`), cards go in a top band over
   the blank background instead. Read a list of sizes as units in captions ("3″ 4″ 5″"), not "3456".
   A source tagged with a rotation (e.g. 3840×2160 with rotation -90) is still portrait: ffmpeg auto-rotates.
   When the product's own screen or label is the subject of a close-up (e.g. the jump starter's pressure display),
   move that scene's cards to the top band (`card_scene(..., css=TOP_CARD_CSS)`) and lift its captions too, so
   the reading stays visible (see `pipeline/gen_jump_starter.py`). Spoken specs a pass mis-hears as a price
   ("RM16,000 mah") must be confirmed with a prompted second pass before they go on screen ("16000 mAh").
   Check the hook title against the presenter's face too: when the face is at the top of the hook shot, drop the
   title to chest height (`#hook-top { top:700px }`, see `pipeline/gen_backpack_battery.py`). Words both passes
   cannot make out ("mesin ropuk", "potash") are cut rather than guessed into a caption.
   `npx hyperframes check`, then a snapshot review. (`edit/` is the first video, the hammer drill.)
7. **Render**: `cd projects/<video> && npx hyperframes render -q delivery -f 30 -w 3 -o <out>.mp4`. GSAP is bundled in `edit/assets/vendor/` (the CDN fails under the render proxy).
8. **Deliver**: copy the result to `output/` (never overwrite or delete earlier outputs).

## Delivering the video to the owner's iPhone (always do this)

The owner downloads to an iPhone. The chat file card has no download button, and Google Drive
uploads from here are capped (create_file about 10 MB, connector requests about 3 MB), so:

- Do NOT upload large videos with Google Drive `create_file` or base64.
- Do NOT re-render or re-compress the final MP4 for delivery.
- DO build the download page: `python3 pipeline/make_download_page.py output/<file>.mp4 <scratch>/dl "<Heading>" "<Title>"`,
  then publish `<scratch>/dl/index.html` with the Artifact tool: `capabilities: {"downloads": true}`,
  `root: <scratch>/dl`, `files` = the map the script prints, at most 4 parts per publish (repeat the publish
  with the same `file_path` for the next 4). Check with `action: "list", scope: "files"` that every part is
  there, and read one part back to compare its SHA-256.
- Give the owner the link and these steps: open it → **1. Sediakan video** (wait for 100%) →
  **2. Simpan ke iPhone** → share sheet **Save Video** → TikTok **+ → Upload**.

## Housekeeping

- Large media (`*.mp4`, `*.wav`) are git-ignored; commit code, captions (`.srt`) and data JSON.
- Work on the session's designated branch and push when done.
