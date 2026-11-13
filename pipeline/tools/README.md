# Batch helpers (one working folder per session)

Copy this folder to a working directory (the session scratchpad), e.g. `cp pipeline/tools/* $W/`, then run
everything from the repo root. Every video lives in `$W/vNN/` (`src/`, `tx/`, `build/`).

| step | command | notes |
|---|---|---|
| fetch | `mkdir -p $W/vNN/src $W/vNN/tx; echo <DRIVE_ID> > $W/vNN/src/id.txt; cp <a run.py> $W/vNN/tx/; $W/fetch.sh vNN` | download, 16 kHz wav, frame sheet, then the Whisper transcript (`tx/orig.json`, queued) |
| read words | `python3 $W/words.py $W/vNN/tx/orig.json` | word times for the cut list |
| second pass | write `tx/v2.py` (prompted + unprompted, see any `vNN/tx/v2.py`), run it with `$W/wq.sh` | confirms specs and spellings |
| cut list | copy `pipeline/edl_work_light6.py` (latest) to `pipeline/edl_<name>.py`, set `KEEPS` / `HOOK` | check edges with the audio level, never cut a word |
| spine | `$W/build.sh vNN <name>` | tail guard, loudnorm, then the spine transcript (`build/spine_tx.json`, queued) |
| verify | `python3 $W/sp.py $W/vNN` (run from `$W`: `cd $W && python3 sp.py vNN`) | every word, and the last word of every phrase, must be there |
| compose | write `cfg_<name>.py` (copy `cfg_example_presenter.py` or `cfg_example_hands_only.py`), `$W/proj.sh vNN <proj> <data> cfg_<name>.py` | builds `pipeline/gen_<name>.py` from `gen_work_light3.py`; print the captions and read every word |
| check | `cd projects/<proj> && npx hyperframes snapshot --at ... -o $W/vNN/snap` | cards off the face / label, captions not over a card |
| render | `$W/render.sh projects/<proj> vNN` | one render at a time (`render.lock`), writes `vNN/probe.txt` |
| deliver | `python3 pipeline/make_download_page.py output/<file>.mp4 $W/dlNN "<Heading>" "<Title>"` + Artifact publish | see CLAUDE.md |
| captions | `python3 pipeline/srt_from_captions.py <data> <proj>` | commit the `.srt` |

Whisper large-v3 needs about 7 GB: only one at a time (`wq.sh` holds a lock). A model id that begins with a
letter-number code (e.g. "GSR 120-LI") gets its caption start pulled late by the long-word rule in the generator;
patch the generated `gen_<name>.py` as in `gen_bosch_drill2.py` (`startswith("GSR")`).
