# D-Ladder 序列化器实现规范

你在自己的代码库里改序列化器,按本规范逐字对齐输出格式。所有臂共享 SCOPED 的结构
(selection 行、runner-up、按 family scope、置信度分裂计数),**只改距离字段的表示**。
方位词 (left/center/right) 全部臂不动。

## D0 = SCOPED(现状,参照,不改)
```
nearest pedestrian: under 5 m (runner-up: bicycle, 5 to 15 m)
```

## D1 = NUMERIC
- 所有距离一律数值,一位小数,单位 " m"(空格+m)。
- 删除全部 ε borderline flags(数值本身携带边界邻近信息)。
- selection 与 runner-up 结构保留。
```
nearest pedestrian: 4.7 m (runner-up: bicycle, 8.2 m)
forward-path nearest object: car, 11.3 m (runner-up: pedestrian, 14.9 m)
```
- counting 家族的 per-object 行同样数值化:
```
pedestrian #1: 4.7 m, left, confident
pedestrian #2: 16.2 m, center, uncertain
```

## D2 = NUMERIC + ALT
- 在 D1 每个数值后追加异词表异边界标签,边界 4/12 m,词表:
  - r < 4 m        -> "close range"
  - 4 <= r <= 12 m -> "mid range"
  - r > 12 m       -> "far range"
```
nearest pedestrian: 4.7 m, mid range (runner-up: bicycle, 8.2 m, mid range)
```
- 断言检查:输出中不得出现 "under 5"、"5 to 15"、"over 15" 任何子串(自动 grep 校验)。

## D3 = ALT-ONLY(负控制)
- 仅标签无数值:
```
nearest pedestrian: mid range (runner-up: bicycle, mid range)
```

## 实现与校验清单
1. 四个臂由同一份代码走配置开关生成,禁止四份复制粘贴的序列化器。
2. 对 development bank 全量 1366 帧生成四臂输出,跑三条自动断言:
   - D1/D2/D3 输出不含任何 β 词表子串("under 5 m" 等);
   - D1 与 D0 在删除距离字段后逐字节相同(证明单变量);
   - D2 标签与数值一致(按 4/12 边界反查)。
3. 断言全过之后才允许在 confirmatory bank 上运行。confirmatory 输出只生成一次,
   与预测 CSV 一起存档。

## 需要报告的对比(全部走 analysis_bootstrap.py)
| 对比 | 检验内容 |
|---|---|
| D1 vs PIXEL(总体 + counting + nearest-distance) | P1 |
| D0 vs D1 | 分档词表本身值多少(泄漏上界) |
| D2 vs D1 | 离散化预计算是否有词表之外的价值 |
| D3 vs PIXEL | 负控制(预期变差或无优势) |
| D0 vs PIXEL on N1 | P2(与 confirmatory 原值比衰减率) |
| D1 vs PIXEL on N2、D0 vs PIXEL on N2 | P3 + SCOPED 在词表外判定上的表现 |
