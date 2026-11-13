#!/bin/bash
# whisper queue: run "$@" holding the GPU-less memory lock (one large-v3 at a time)
exec flock $(dirname "$0")/wq.lock "$@"
