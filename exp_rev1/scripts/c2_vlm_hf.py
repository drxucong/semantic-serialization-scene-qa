"""C2 (second revision, amendment A6): Qwen2.5-VL run with the Transformers library.

Why. Served by Ollama, Qwen2.5-VL 3B returns a degenerate output on most 1600x900 nuScenes
frames (exp_rev1/c1_nusc/INCIDENTS.md; repeated on 2026-11-15 with Ollama 0.40.16). This
runner uses the weights of the model authors in bfloat16 and the image at its native
resolution, with the SAME system prompt, user prompt, greedy decoding, 8 output tokens and
answer parser as the shipped VLM arm (scripts/pilot/run_pilot_pixel_ollama.py).

  --mode pixel    image + question                          (shipped VLM arm)
  --mode hybrid   image + Scoped text of --states + question (as b123_vlm_aids.py --mode hybrid)
  --mode reason   image + question under protocol R         (as c3_reason_answer.py)

Resume-safe by qa_id.
"""
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper", "scripts/rev1"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_pilot_pixel_ollama as PX  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("pixel", "hybrid", "reason"), required=True)
    ap.add_argument("--model", required=True, help="Hugging Face id or local folder")
    ap.add_argument("--tag", required=True, help="short model name written to the records")
    ap.add_argument("--qa", required=True)
    ap.add_argument("--states", default=None, help="perceived states (hybrid mode)")
    ap.add_argument("--max-pixels", type=int, default=28 * 28 * 2048)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    proc = AutoProcessor.from_pretrained(a.model, max_pixels=a.max_pixels)
    mdl = Qwen2_5_VLForConditionalGeneration.from_pretrained(a.model, device_map="cuda", dtype=torch.bfloat16).eval()

    items = [json.loads(l) for l in open(ROOT / a.qa, encoding="utf-8")]
    if a.limit:
        items = items[: a.limit]
    states = serialize_dl = None
    if a.mode == "hybrid":
        from run_serializer_dladder import serialize_dl
        states = json.load(open(ROOT / a.states, encoding="utf-8"))
    system, max_new = PX.SYSTEM, 8
    if a.mode == "reason":
        import c3_reason_answer as R
        system, max_new = R.r_system(PX.SYSTEM), R.MAX_TOKENS
    outdir = ROOT / a.out; outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / f"{a.mode}_hf__clean__forced.jsonl"
    done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")} if fp.exists() else set()
    f = open(fp, "a", encoding="utf-8")
    t_start = time.time(); n_run = 0
    for it in items:
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        sid = it["sample_id"]
        prompt = PX.build_prompt(it, fch)
        if a.mode == "hybrid":
            if sid not in states:
                continue
            prompt = ("A perception system produced the following description of the same image; it may "
                      "contain errors.\n" + serialize_dl(states[sid], it["category"], "d0") + "\n\n" + prompt)
        elif a.mode == "reason":
            prompt = R.r_user(prompt)
        img = it["cam_front"]
        img = img if Path(img).is_absolute() else str(ROOT / img)
        t0 = time.time(); n_img = None
        try:
            msgs = [{"role": "system", "content": [{"type": "text", "text": system}]},
                    {"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": prompt}]}]
            inputs = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True,
                                              return_dict=True, return_tensors="pt").to("cuda")
            n_img = int(inputs["input_ids"].shape[1])
            with torch.no_grad():
                out = mdl.generate(**inputs, max_new_tokens=max_new, do_sample=False)
            raw = proc.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0]
            fin = "length" if out.shape[1] - inputs["input_ids"].shape[1] >= max_new else "stop"
        except Exception as e:  # noqa: BLE001
            raw, fin = f"__ERROR__ {e}", "error"
        pred = R.parse_r(raw, set(fch), fch) if a.mode == "reason" else parse_letter(raw or "", set(fch))
        rec = {"qa_id": it["qa_id"], "sample_id": sid, "scene_name": it["scene_name"], "category": it["category"],
               "arm": f"{a.mode}_hf", "protocol": "clean", "track": "forced", "model": a.tag, "pred": pred,
               "answer": fans, "correct": pred == fans, "latency_s": round(time.time() - t0, 2), "prompt_tokens": n_img}
        if a.mode == "reason":
            rec["finish"] = fin; rec["raw"] = raw
        else:
            rec["raw_head"] = (raw or "")[:60]
        f.write(json.dumps(rec) + "\n"); f.flush(); n_run += 1
        if n_run % 200 == 0:
            print(f"[{a.mode}_hf|{a.tag}] {n_run} new ({(time.time()-t_start)/60:.1f} min)", flush=True)
    f.close()
    recs = [json.loads(l) for l in open(fp, encoding="utf-8")]
    n = len(recs); c = sum(r["correct"] for r in recs); par = sum(r["pred"] is not None for r in recs)
    print(f"[{a.mode}_hf|{a.tag}] {c}/{n} = {c/max(n,1):.4f}; parsed {par} -> {fp}", flush=True)


if __name__ == "__main__":
    main()
