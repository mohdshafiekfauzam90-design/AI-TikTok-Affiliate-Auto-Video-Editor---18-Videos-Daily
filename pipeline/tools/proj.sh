#!/bin/bash
# proj.sh vNN proj data cfg : project folder + data from the built spine, then generate
set -e
REPO=/home/user/AI-TikTok-Affiliate-Auto-Video-Editor---18-Videos-Daily; SP=$(dirname "$0"); v=$1; proj=$2; data=$3; cfg=$4
cd $REPO; B=$SP/$v/build
mkdir -p projects/$proj/assets/video pipeline/data/$data
cp -r projects/tangga-lipat/assets/sfx projects/tangga-lipat/assets/vendor projects/$proj/assets/
cp projects/tangga-lipat/hyperframes.json projects/tangga-lipat/package.json projects/$proj/
cp $B/spine_n.mp4 projects/$proj/assets/video/spine.mp4
cp $B/spine_map.json $B/edl.json pipeline/data/$data/
cp $B/spine_tx.json pipeline/data/$data/spine_transcript.json
cp $SP/$v/tx/orig.json pipeline/data/$data/original_transcript.json
python3 $SP/mk_pres.py $SP/$cfg
python3 pipeline/gen_$(python3 -c "import runpy;print(runpy.run_path('$SP/$cfg')['name'])").py
