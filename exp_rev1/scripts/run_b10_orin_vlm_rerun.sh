#!/bin/bash
# B10 (Orin): re-run of the two image runs after two harness fixes.
#  - qwen2.5vl-3b: the first run warmed up on item 1's image, so item 1 reused the
#    encoded image; kept as invalid_warmupcache_qwen2.5vl-3b.
#  - moondream: the ollama-template run failed because this server build uses a
#    random media marker (read from /props now); kept as invalid_marker_moondream.
cd ~/rev1/out
mv qwen2.5vl-3b invalid_warmupcache_qwen2.5vl-3b && mv log_qwen2.5vl-3b.txt invalid_warmupcache_log_qwen2.5vl-3b.txt
mv moondream invalid_marker_moondream && mv log_moondream.txt invalid_marker_log_moondream.txt
cd ~/rev1
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --name moondream --model models/moondream2-text.gguf \
  --mmproj models/moondream2-mmproj.gguf --pixel --ollama-moondream --laptop-key moondream > out/log_moondream.txt 2>&1
python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --name qwen2.5vl-3b --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf \
  --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel --laptop-key qwen2.5vl-3b > out/log_qwen2.5vl-3b.txt 2>&1
echo done > out/RERUN_DONE
