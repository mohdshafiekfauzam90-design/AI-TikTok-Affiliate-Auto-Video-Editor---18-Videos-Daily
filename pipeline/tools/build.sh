#!/bin/bash
# build.sh vNN edl_name : cut list -> spine (tail guard) -> loudnorm -> queued spine transcript
set -e
REPO=/home/user/AI-TikTok-Affiliate-Auto-Video-Editor---18-Videos-Daily; SP=$(dirname "$0"); v=$1; edl=$2
B=$SP/$v/build; mkdir -p $B; cd $REPO
python3 pipeline/edl_$edl.py $SP/$v/src/a16.wav $B/edl.json
rm -rf $B/segs
nice -n 5 python3 pipeline/build_spine.py $SP/$v/src/raw.mp4 $B/edl.json $B/spine.mp4
nice -n 5 ffmpeg -v error -y -i $B/spine.mp4 -vf "tpad=stop_mode=clone:stop_duration=1.2" -af "loudnorm=I=-14.5:TP=-1.5:LRA=11,apad=pad_dur=1.2" -c:v libx264 -preset medium -crf 16 -g 30 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -movflags +faststart $B/spine_n.mp4
ffmpeg -v error -y -i $B/spine_n.mp4 -ac 1 -ar 16000 $B/s16.wav
rm -rf $B/segs $B/spine.mp4
echo SPINE_OK
cd $SP/$v && $SP/wq.sh python3 tx/run.py build/s16.wav build/spine_tx.json > build/tx.log 2>&1
echo TX_OK
