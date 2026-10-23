#!/bin/bash
# B10 (Orin) driver, runs detached on the board: wait for the CUDA build, run the
# readers + moondream, wait for the verified Qwen2.5-VL-3B download, run the VLM.
cd ~/rev1
log () { echo "$(date +%H:%M:%S) $*" >> out/orchestrate.log; }
log start
while [ ! -f BUILD_OK ]; do
  pgrep -f b10_build_llamacpp_orin.sh >/dev/null || { log "BUILD FAILED"; echo fail > out/BUILD_FAILED; exit 1; }
  sleep 20
done
log "build ok; readers"
bash run_b10_orin.sh
log "readers done"
for i in $(seq 1 180); do [ -f FETCH_OK ] && break; sleep 20; done
if [ -f FETCH_OK ]; then log "fetch ok; vlm"; bash run_b10_orin.sh vlm; log "vlm done"; else log "FETCH NOT OK"; fi
echo done > out/ALL_DONE
log all-done
