#!/bin/bash
# B10: build a fully static aarch64 llama-server at the SAME commit as the
# Orange Pi's build (11fe021), for the Agilex 5 HPS (Yocto scarthgap, no C++
# compiler on target). Generic armv8.2-a+dotprod so one binary serves both the
# A55 and A76 cores. Runs in WSL.
set -euo pipefail
SRC=/root/rev1_llamacpp
OUT=/root/rev1_llamacpp/build-aarch64-static
if [ ! -d "$SRC/.git" ]; then
  git clone --filter=blob:none https://github.com/ggml-org/llama.cpp "$SRC"
fi
cd "$SRC"
git fetch --quiet origin 2>/dev/null || true
git checkout --quiet 11fe021
echo "commit: $(git log -1 --format='%h %cd')"
cat > /root/rev1_aarch64.cmake <<'EOF'
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
set(CMAKE_FIND_ROOT_PATH /usr/aarch64-linux-gnu)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
EOF
cmake -S . -B "$OUT" -G Ninja -DCMAKE_TOOLCHAIN_FILE=/root/rev1_aarch64.cmake \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DGGML_STATIC=ON \
  -DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH=armv8.2-a+dotprod -DGGML_OPENMP=OFF \
  -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
  -DCMAKE_EXE_LINKER_FLAGS="-static" > /tmp/rev1_cmake.log 2>&1 || { tail -30 /tmp/rev1_cmake.log; exit 1; }
cmake --build "$OUT" --target llama-server llama-bench -j 16 > /tmp/rev1_build.log 2>&1 || { tail -40 /tmp/rev1_build.log; exit 1; }
file "$OUT/bin/llama-server" "$OUT/bin/llama-bench"
ls -la "$OUT/bin/llama-server" "$OUT/bin/llama-bench"
