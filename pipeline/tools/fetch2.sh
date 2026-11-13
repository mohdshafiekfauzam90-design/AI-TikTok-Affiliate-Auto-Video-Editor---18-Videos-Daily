#!/bin/bash
# fetch2.sh vNN : like fetch.sh but resumes (uses src/orig.mp4 if it is there) and does NOT queue the transcript
SP=$(dirname "$0"); v=$1; cd $SP/$v; id=$(cat src/id.txt)
[ -s src/orig.mp4 ] || curl -sSL -o src/orig.mp4 "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t"
nice ffmpeg -v error -y -threads 2 -i src/orig.mp4 -map 0:v:0 -map 0:a:0 -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p -c:a aac -b:a 256k src/raw.mp4 && rm -f src/orig.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 src/raw.mp4 > src/probe.txt 2>&1
ffmpeg -v error -y -i src/raw.mp4 -ac 1 -ar 16000 src/a16.wav
nice ffmpeg -v error -y -i src/raw.mp4 -vf "fps=1/4,scale=120:-1,tile=15x3" -frames:v 1 tx/sheet.jpg
echo FETCHED
