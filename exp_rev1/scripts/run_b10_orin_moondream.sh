#!/bin/bash
# B10 (Orin): moondream re-run with ollama's moondream prompt template (see
# --ollama-moondream in b10_board_bench.py). The first run through the chat endpoint
# produced an immediate end-of-text on every item; it is kept, renamed, as
# invalid_chattemplate_moondream. Starts after the main sequence has finished.
cd ~/rev1
while [ ! -f out/ALL_DONE ]; do sleep 20; done
[ -d out/moondream ] && mv out/moondream out/invalid_chattemplate_moondream && mv out/log_moondream.txt out/invalid_chattemplate_log_moondream.txt
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --name moondream --model models/moondream2-text.gguf \
  --mmproj models/moondream2-mmproj.gguf --pixel --ollama-moondream --laptop-key moondream > out/log_moondream.txt 2>&1
echo done > out/MOONDREAM_DONE
