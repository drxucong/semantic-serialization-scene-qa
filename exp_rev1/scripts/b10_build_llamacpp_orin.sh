#!/bin/bash
# B10 (Orin): build llama-server / llama-bench natively on the Jetson Orin Nano at
# the SAME commit as the other boards (11fe021, shipped as a git-archive tarball
# because the board has no clone), with CUDA for the Orin GPU (sm_87).
# Runs on the board: bash ~/rev1/b10_build_llamacpp_orin.sh
set -euo pipefail
cd ~/rev1
[ -d llama.cpp-11fe021 ] || tar xzf llama.cpp-11fe021.tar.gz
cd llama.cpp-11fe021
export PATH=/usr/local/cuda/bin:$PATH
echo "nvcc: $(nvcc --version | tail -1)"
cmake -S . -B build-cuda -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87 \
  -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF > ~/rev1/cmake_orin.log 2>&1 \
  || { tail -30 ~/rev1/cmake_orin.log; exit 1; }
cmake --build build-cuda --target llama-server llama-bench -j "$(nproc)" > ~/rev1/build_orin.log 2>&1 \
  || { tail -40 ~/rev1/build_orin.log; exit 1; }
ls -la build-cuda/bin/llama-server build-cuda/bin/llama-bench
echo BUILD_OK > ~/rev1/BUILD_OK
