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

## Pipeline (see README.md for details)

1. **Get the video**: from a Drive link id, `curl -L -o raw.mp4 "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"` into the scratchpad.
2. **Transcribe**: Whisper large-v3 on a 16 kHz mono wav; check key numbers/specs with a second, unprompted pass.
3. **Cut list**: copy `pipeline/edl_tangga_lipat.py` (the newest, most general one) to `pipeline/edl_<video>.py`
   and set `KEEPS`, `MANUAL_CUTS` and `HOOK`. A keep may carry `{"speed": 1.5}` (a slow demo) or `{"gain": 0}`
   (mute a repeated line under a demo shot); `HOOK` with `voice=None` is an in-sync hook shot. Check segment ends
   against the audio level (whisper word ends are often early): a clipped last word shows up in step 5.
4. **Spine**: `python3 pipeline/build_spine.py raw.mp4 edl.json spine.mp4` (per-segment encode; never one giant filter graph: it runs out of memory on 4K), then loudnorm to about −14.5 LUFS.
5. **Verify**: re-transcribe the spine; every word must be present.
6. **Compose**: one HyperFrames project per video in `projects/<video>/` (copy `assets/sfx`, `assets/vendor`,
   `hyperframes.json`, `package.json` from `projects/tangga-lipat/`; data in `pipeline/data/<video>/`). Copy
   `pipeline/gen_tangga_lipat.py` to `pipeline/gen_<video>.py` and write the scenes for the spoken facts. Set the
   caption groups by hand (`MANUAL_GROUPS`, natural Malay phrases, a number always with its unit); keep cards off
   the presenter's face (band just above the captions on talking-head shots); hide captions under the CTA.
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
