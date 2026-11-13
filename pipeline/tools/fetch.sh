#!/bin/bash
# fetch.sh vNN : download the Drive video, 16 kHz wav, frame sheet, then queue the transcript
SP=$(dirname "$0"); v=$1; cd $SP/$v; id=$(cat src/id.txt)
curl -sSL -o src/raw.mp4 "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact src/raw.mp4 > src/probe.txt 2>&1
ffmpeg -v error -y -i src/raw.mp4 -ac 1 -ar 16000 src/a16.wav
nice ffmpeg -v error -y -i src/raw.mp4 -map 0:v:0 -vf "fps=1/4,scale=120:-1,tile=15x3" -frames:v 1 tx/sheet.jpg
echo FETCHED
$SP/wq.sh python3 tx/run.py src/a16.wav tx/orig.json > tx/log.txt 2>&1
