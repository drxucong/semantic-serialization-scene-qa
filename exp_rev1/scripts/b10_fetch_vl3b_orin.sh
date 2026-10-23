#!/bin/bash
# B10 (Orin): fetch the official llama.cpp-format Qwen2.5-VL-3B files (ggml-org,
# approved by Cong 2026-10-23) and verify them against the Hugging Face LFS SHA-256.
# ollama's qwen2.5vl blob is a combined 'qwen25vl' GGUF that llama.cpp cannot load.
set -u
cd ~/rev1/models
base=https://huggingface.co/ggml-org/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main
cat > vl3b.sha256 <<'EOF'
d02fe9b69ad8cadbbd228e387667af66612c44bed29ffc8eb1e7caf9ac486c12  Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf
b9160fe9d814d1fadf68395677468534778b39ac33c2e7561b7b218626e60d5e  mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf
EOF
for f in Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf; do
  curl -L --fail --retry 3 -C - -o "$f" "$base/$f" || { echo "DOWNLOAD_FAIL $f"; exit 1; }
done
sha256sum -c vl3b.sha256 && echo FETCH_OK > ~/rev1/FETCH_OK
