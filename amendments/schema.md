# 输入数据规范(写一个薄适配器把你的格式转成这个)

我没有你的 bank 与 GT 的真实字段名,所以两个生成器都读下面这个规范化 JSON。
你只需要写一个 10 行的适配器脚本把现有数据转过来;如果不想转,把你的真实 schema
发我,我改生成器来适配你。

## bank.jsonl(每行一题,N1 生成器的输入 = confirmatory bank)
```json
{
  "question_id": "seq07_frame01412_q1",
  "sequence_id": "seq07",
  "frame_id": "frame01412",
  "family": "nearest-distance",        // counting | direction | nearest-class | nearest-distance | path-object
  "stem": "How far is the nearest pedestrian?",
  "options": {"A": "under 5 m", "B": "5 to 15 m", "C": "over 15 m"},
  "gold": "A"
}
```

## gt_state.jsonl(每行一帧,N2 生成器的输入 = 视野门控后的 GT 对象集)
```json
{
  "frame_id": "frame01412",
  "sequence_id": "seq07",
  "objects": [
    {"cls": "pedestrian", "theta_deg": 12.4, "range_m": 4.7, "in_forward_path": false},
    {"cls": "car",        "theta_deg": -3.1, "range_m": 11.3, "in_forward_path": true}
  ]
}
```
- objects 必须已经过 V_GT 门控(inFOV、r <= 40 m;若遮挡门控已完成,用门控后的集合,
  N2 就自动继承遮挡修复)。
- theta_deg 正值为左,与论文约定一致。

## 预测输出 predictions.csv(每个臂跑完后交给 analysis_bootstrap.py)
```
question_id,sequence_id,family,arm,correct
seq07_frame01412_q1,seq07,nearest-distance,D1,1
```
- correct: 1/0,unparsed 计 0(与你的 frozen 规则一致)。
