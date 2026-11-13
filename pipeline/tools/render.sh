#!/bin/bash
# render.sh <project dir> <vNN>: one render at a time (render lock), then probe + freeze check
SP=$(dirname "$0"); P=$1; V=$2
exec 9>$SP/render.lock; flock 9
cd "$P" && timeout 3500 nice npx hyperframes render -q delivery -f 30 -w 2 -o $SP/$V/build/final.mp4 > $SP/$V/render.log 2>&1
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration,size -of compact $SP/$V/build/final.mp4 > $SP/$V/probe.txt 2>&1
ffmpeg -i $SP/$V/build/final.mp4 -vf 'freezedetect=n=-60dB:d=1.6,metadata=mode=print' -an -f null - 2>&1 | grep freeze_ >> $SP/$V/probe.txt
echo END >> $SP/$V/probe.txt
