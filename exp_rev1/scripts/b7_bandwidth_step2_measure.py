"""B7 step 2 (vlbase env: transformers 5.x, PIL): for every confirmatory item
  - text tokens of the Scoped / Flat serialized state (Qwen2.5 tokenizer;
    identical vocabulary across 0.5B-7B)
  - keyframe bytes: PNG as stored (what the pixel arm sent), JPEG q90 / q75 at
    native 1224x1024, and JPEG q75 at 640 px wide (a plausible low-bandwidth
    setting)
  - visual tokens the Qwen2.5-VL processor produces for the native keyframe
    under its default pixel budget (image_grid_thw -> tokens after 2x2 merge)
Writes step2_measurements.csv and a summary json with medians / means / p95.
"""
import csv, io, json, statistics as S, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_rev1/b7_bandwidth"
rows = [json.loads(l) for l in open(OUT / "step1_serialized.jsonl", encoding="utf-8")]

from transformers import AutoTokenizer, AutoProcessor  # noqa: E402
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
proc = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")
merge = getattr(proc.image_processor, "merge_size", 2)


def jpeg_bytes(im, q, width=None):
    if width:
        im = im.resize((width, round(im.height * width / im.width)), Image.BICUBIC)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q); return b.tell()


res = []
cache = {}
for r in rows:
    p = ROOT / r["image"]
    if r["sample_id"] not in cache:
        im = Image.open(p).convert("RGB")
        enc = proc.image_processor(images=im, return_tensors="pt")
        t, h, w = enc["image_grid_thw"][0].tolist()
        cache[r["sample_id"]] = {"png_bytes": p.stat().st_size, "jpeg90_bytes": jpeg_bytes(im, 90),
                                 "jpeg75_bytes": jpeg_bytes(im, 75), "jpeg75_640_bytes": jpeg_bytes(im, 75, 640),
                                 "visual_tokens": t * h * w // (merge * merge), "img_w": im.width, "img_h": im.height}
    c = cache[r["sample_id"]]
    res.append({**{k: r[k] for k in ("qa_id", "sample_id", "seq", "family", "n_objects", "scoped_bytes", "flat_bytes", "question_bytes")},
                "scoped_tokens": len(tok(r["scoped_text"])["input_ids"]),
                "flat_tokens": len(tok(r["flat_text"])["input_ids"]), **c})

with open(OUT / "step2_measurements.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)


def summ(k):
    v = sorted(x[k] for x in res)
    return {"median": S.median(v), "mean": S.mean(v), "p95": v[int(0.95 * len(v)) - 1], "min": v[0], "max": v[-1]}


summary = {k: summ(k) for k in ("scoped_bytes", "flat_bytes", "scoped_tokens", "flat_tokens", "png_bytes",
                                "jpeg90_bytes", "jpeg75_bytes", "jpeg75_640_bytes", "visual_tokens", "n_objects")}
summary["per_family_scoped_bytes_median"] = {fam: S.median([x["scoped_bytes"] for x in res if x["family"] == fam])
                                            for fam in sorted({x["family"] for x in res})}
summary["per_family_scoped_tokens_median"] = {fam: S.median([x["scoped_tokens"] for x in res if x["family"] == fam])
                                             for fam in sorted({x["family"] for x in res})}
summary["n_items"] = len(res); summary["n_frames"] = len(cache)
summary["vl_processor_defaults"] = {"min_pixels": getattr(proc.image_processor, "min_pixels", None),
                                    "max_pixels": getattr(proc.image_processor, "max_pixels", None),
                                    "size": getattr(proc.image_processor, "size", None), "merge_size": merge}
json.dump(summary, open(OUT / "step2_summary.json", "w"), indent=1, default=str)
for k, v in summary.items():
    print(k, v)
