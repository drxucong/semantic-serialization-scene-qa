#!/bin/bash
# B10 on the Jetson Orin Nano 8 GB (JetPack 6, L4T R36.4.4, power mode 25W):
# same probe set, same Q4_K_M files as the paper (readers and moondream byte-identical
# to the ollama blobs), llama.cpp 11fe021 built with CUDA, all layers on the GPU.
# No cgroup cap (Jetson GPU memory is shared system RAM and is not charged to the
# cgroup). Order protects the key comparison: small readers and moondream first;
# then the Qwen2.5-VL-3B run; the 7B reader last, since it is the run most likely
# to exhaust memory.
# usage: bash ~/rev1/run_b10_orin.sh [vlm]
cd ~/rev1
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
run () { python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none "$@" > "out/log_$2.txt" 2>&1; }
if [ "${1:-}" != "vlm" ]; then
  run --name qwen2.5-0.5b --model models/qwen2.5-0.5b-q4km.gguf
  run --name qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf
  run --name qwen2.5-3b   --model models/qwen2.5-3b-q4km.gguf
  run --name moondream    --model models/moondream2-text.gguf --mmproj models/moondream2-mmproj.gguf --pixel --laptop-key moondream
  echo done > out/DONE_readers
else
  run --name qwen2.5vl-3b --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf \
      --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel --laptop-key qwen2.5vl-3b
  run --name qwen2.5-7b   --model models/qwen2.5-7b-q4km.gguf
  echo done > out/DONE_vlm
fi
