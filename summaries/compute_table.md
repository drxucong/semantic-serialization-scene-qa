# 计算对照表(Phase 2 第 7 步,M4 回应;全部实测,2026-08-10)

测量环境:RTX 5090 Laptop 24 GB,单流,GPU 独占(sweep 结束后测)。
延迟:感知栈在 200 张 confirmatory 帧上逐模块计时(`exp2_runs/perception_bench.json`);
reader/VLM 经 ollama(Q4_K_M 量化)、连接池、3 次预热后 30 题取样
(`exp2_runs/llm_bench.json`)。参数量:感知模块 torch numel 实数,
LLM/VLM 为 ollama `general.parameter_count` 实数(`exp2_runs/model_params.json`)。

## 1. 模块参数量

| 模块 | 参数 | 备注 |
|---|---|---|
| YOLO11l(fine-tuned,kf0) | 25.3 M | 双检测器之一,全帧+2×2 tile |
| YOLO11m(fine-tuned,kf0) | 20.1 M | 双检测器之二 |
| LLMDet(swin-base) | 233.0 M | 零样本开放词表,absence recovery only |
| UniDepthV2(vitl14) | 353.8 M | 单目测距第 4 路 |
| 立体 SGBM(OpenCV) | 0(无参) | CPU |
| 序列化器 | ≈0 | 确定性规则 |
| **感知栈合计** | **≈0.63 B** | |
| qwen2.5 0.5b / 1.5b / 3b / 7b | 0.494 / 1.544 / 3.086 / 7.616 B | 文本 reader |
| qwen2.5vl 3b / 7b | 3.755 / 8.292 B | 其中 ViT ≈0.67 B(官方架构,未单独实测) |
| moondream | 1.418 B(实测;宣传 1.8B) | 含 SigLIP 视觉编码器 |
| llava-phi3 | 3.821 B | 含 CLIP-L 视觉编码器(≈0.30 B,官方架构) |
| qwen3-vl:2b(偏离臂) | 2.128 B | |

## 2. 单流延迟(mean / median / P95)

### 感知栈(逐模块,200 帧)

| 模块 | mean | median | P95 |
|---|---|---|---|
| YOLO 全帧 ×2 | 62.5 ms | 58.2 | 63.0 |
| YOLO tile ×2(2×2) | 221.3 ms | 221.6 | 230.3 |
| LLMDet | 298.0 ms | 298.5 | 325.4 |
| UniDepthV2 | 98.7 ms | 96.5 | 102.4 |
| 立体 SGBM(CPU) | 267.7 ms | 268.2 | 271.9 |
| 序列化器 D0 | 0.1 ms | 0.1 | 0.1 |
| **串行合计** | **≈0.95 s/帧** | | (SGBM 在 CPU,可与 GPU 模块重叠;按串行计为保守值) |

峰值显存(逐模块独测):YOLO 2.72 GiB、LLMDet 3.40 GiB、UniDepth 4.20 GiB。
注:UniDepth 未编译 cuda patch 算子(与正式感知 run 同环境,如实记录)。

### reader / VLM 单题(T=0、8 token;30 题)

| 模型 | mean | median | P95 |
|---|---|---|---|
| qwen2.5:0.5b | 0.151 s | 0.151 | 0.176 |
| qwen2.5:1.5b | 0.181 s | 0.175 | 0.208 |
| qwen2.5:3b | 0.196 s | 0.195 | 0.246 |
| qwen2.5:7b | 0.241 s | 0.230 | 0.328 |
| moondream | 0.294 s | 0.294 | 0.329 |
| llava-phi3 | 0.348 s | 0.345 | 0.383 |
| qwen2.5vl:3b | 0.972 s | 0.970 | 1.022 |
| qwen2.5vl:7b | 1.109 s | 1.102 | 1.198 |
| qwen3-vl:2b(偏离:256 thinking) | 1.183 s | 1.307 | 1.449 |

测量勘误(已记 LOG):第一遍 7B/7C 用 urllib 逐调用建连,Windows 代理解析引入
~2.1 s/call 常数开销(0.5B 与 7B 同为 ~2.3 s 露馅),作废重测;本表为连接池数字。
同因:各 pixel 正式 run 的墙钟吞吐不得用作延迟证据。

## 3. 端到端,同帧 Q 题(实测)

| 条件 | Q=1 | Q=2 | Q=5 | Q=10 |
|---|---|---|---|---|
| 文本臂 qwen2.5:3b(感知 0.95 s 一次 + Q×0.184 s) | 1.13 s | 1.32 | 1.87 | 2.79 |
| 文本臂 qwen2.5:7b(感知 0.95 s 一次 + Q×0.232 s) | 1.18 s | 1.41 | 2.11 | 3.27 |
| VLM qwen2.5vl:7b,每题全新编码 | 0.96 s | 1.92 | 4.80 | 9.60 |
| VLM qwen2.5vl:7b,同图会话缓存(实测逐轮 0.32–0.47 s) | 0.44 s | 0.82 | 1.86 | 3.70 |
| VLM moondream,每题全新编码 | 0.28 s | 0.57 | 1.42 | 2.84 |
| VLM moondream,同图会话缓存 | 0.24 s | 0.42 | 0.96 | 1.84 |

会话缓存条件通过 ollama 单会话多轮实现(图像只在第 1 轮发送),缓存生效
(qwen2.5vl:7b 逐轮 0.37 s vs 全新编码 0.96 s),两种条件均如实报告。
