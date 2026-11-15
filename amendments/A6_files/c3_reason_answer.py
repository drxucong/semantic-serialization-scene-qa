"""C3 (second revision): the 'reason, then answer' protocol (protocol R).

The shipped arms let the model write at most 8 tokens and ask for the option letter
only. Protocol R gives both routes room to reason before they answer:

  --route vlm    image + question, Qwen2.5-VL (the shipped VLM arm, protocol R)
  --route text   Scoped serialized text + question, Qwen2.5 (the shipped reader arm,
                 protocol R; the text is produced by the same code path as the shipped
                 arm, run_serializer_dladder.serialize_dl(..., 'd0'))

Protocol R, identical for the two routes:
  * system prompt = the shipped system prompt of the route, with its last sentence
    ('Reply with ONLY the option letter.') replaced by R_SYSTEM_TAIL;
  * user prompt = the shipped user prompt of the route, with its last line
    ('Answer with ONLY the option letter.') replaced by R_USER_TAIL;
  * temperature 0, at most MAX_TOKENS output tokens;
  * the answer is the letter of the LAST 'Answer: X' in the output; if the text after
    the last 'Answer:' is not a letter but is exactly the text of one option, that
    option; if there is no 'Answer:' and the last non-empty line has at most 20
    characters, the letter found in that line; otherwise the output counts as
    unparsed, and unparsed counts as wrong;
  * serving faults are not scored as answers: if the server returns an error and no
    text, the model is unloaded and the question is asked again (at most three
    times); in addition the reload rule of the shipped VLM arm applies (four unparsed
    outputs in a row -> unload the model, ask the question once more).

The full output text is stored. Resume-safe by qa_id.
"""
import argparse, base64, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_pilot_pixel_ollama as PX  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402

LETTER_ONLY_SYS = "Reply with ONLY the option letter."
LETTER_ONLY_USER = "Answer with ONLY the option letter."
R_SYSTEM_TAIL = ("First reason step by step in a few sentences. Then give the final answer on a "
                 "new last line in the form 'Answer: X', where X is the option letter.")
R_USER_TAIL = "Reason step by step, then end with a line of the form 'Answer: X'."
MAX_TOKENS = 512
ANS = re.compile(r"ANSWER\s*(?:IS)?\s*[:：]?\s*\**\s*\(?([A-D])(?![A-Z])")


def r_system(shipped):
    assert shipped.endswith(LETTER_ONLY_SYS), shipped
    return shipped[: -len(LETTER_ONLY_SYS)] + R_SYSTEM_TAIL


def r_user(shipped):
    assert shipped.endswith(LETTER_ONLY_USER), shipped
    return shipped[: -len(LETTER_ONLY_USER)] + R_USER_TAIL


def parse_r(raw, valid, options=None):
    if not raw or raw.startswith("__ERROR__"):
        return None
    hits = ANS.findall(raw.upper())
    if hits:
        return hits[-1] if hits[-1] in valid else None
    if options and "ANSWER" in raw.upper():
        tail = raw[raw.upper().rindex("ANSWER") + 6:]
        def norm(t):
            for ch in "*'\":.":
                t = t.replace(ch, " ")
            return " ".join(t.lower().split())
        same = [k for k, v in options.items() if norm(v) == norm(tail)]
        if len(same) == 1:
            return same[0]
    lines = [x.strip() for x in raw.splitlines() if x.strip()]
    if lines and len(lines[-1]) <= 20:
        return parse_letter(lines[-1], valid)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", choices=("vlm", "text"), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--qa", default="outputs/coda/qa_confirm.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_confirm_v9.json")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    from openai import OpenAI
    client = OpenAI(base_url=a.base_url, api_key="ollama")
    items = [json.loads(l) for l in open(ROOT / a.qa, encoding="utf-8")]
    if a.limit:
        items = items[: a.limit]
    states = None
    if a.route == "text":
        from run_serializer_dladder import serialize_dl
        states = json.load(open(ROOT / a.states, encoding="utf-8"))
    system = r_system(PX.SYSTEM if a.route == "vlm" else V9.SYSTEM)
    outdir = ROOT / a.out; outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / f"reason_{a.route}__clean__forced.jsonl"
    done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")} if fp.exists() else set()
    f = open(fp, "a", encoding="utf-8")
    cache = {}; consec_null = 0; t_start = time.time(); n_run = 0; n_fault = 0

    def call(content):
        t0 = time.time()
        try:
            r = client.chat.completions.create(model=a.model, temperature=0, max_tokens=MAX_TOKENS, timeout=600,
                                               messages=[{"role": "system", "content": system},
                                                         {"role": "user", "content": content}])
            return r.choices[0].message.content or "", r.choices[0].finish_reason, time.time() - t0
        except Exception as e:  # noqa: BLE001
            return f"__ERROR__ {e}", "error", time.time() - t0

    def unload_model():
        try:
            req = urllib.request.Request(a.base_url.replace("/v1", "") + "/api/generate",
                                         data=json.dumps({"model": a.model, "keep_alive": 0}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:  # noqa: BLE001
            print(f"[guard] unload failed: {e}", flush=True)
        time.sleep(8)

    for it in items:
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        sid = it["sample_id"]
        if a.route == "vlm":
            if sid not in cache:
                cache = {sid: base64.b64encode((ROOT / it["cam_front"]).read_bytes()).decode()}
            content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{cache[sid]}"}},
                       {"type": "text", "text": r_user(PX.build_prompt(it, fch))}]
        else:
            if sid not in states:
                continue
            scene = serialize_dl(states[sid], it["category"], "d0")
            content = r_user(V9.build_prompt(scene, it, fch))
        raw, fin, dt = call(content)
        waited = 0
        while raw.startswith("__ERROR__") and ("Connection" in raw or "connect" in raw.lower()) and waited < 7200:
            if waited == 0:
                print(f"[guard] ollama unreachable ({raw[:60]!r}); waiting", flush=True)
            time.sleep(30); waited += 30
            raw, fin, dt = call(content)
        tries = 0
        while raw.startswith("__ERROR__") and tries < 3:      # serving fault, not an answer
            tries += 1; n_fault += 1
            unload_model()
            raw, fin, dt = call(content)
        pred = parse_r(raw, set(fch), fch)
        if pred is None:
            consec_null += 1
            if consec_null >= 4:
                print(f"[guard] {consec_null} consecutive unparsed (last raw={raw[:20]!r}); reloading model", flush=True)
                unload_model()
                raw, fin, dt = call(content)
                pred = parse_r(raw, set(fch), fch)
                consec_null = 0 if pred is not None else consec_null
        else:
            consec_null = 0
        f.write(json.dumps({"qa_id": it["qa_id"], "sample_id": sid, "scene_name": it["scene_name"],
                            "category": it["category"], "arm": f"reason_{a.route}", "protocol": "clean",
                            "track": "forced", "model": a.model, "pred": pred, "answer": fans,
                            "correct": pred == fans, "finish": fin, "raw": raw, "latency_s": round(dt, 2)}) + "\n")
        f.flush(); n_run += 1
        if n_run % 100 == 0:
            print(f"[reason {a.route}|{a.model}] {n_run} new ({(time.time()-t_start)/60:.1f} min)", flush=True)
    f.close()
    recs = [json.loads(l) for l in open(fp, encoding="utf-8")]
    n = len(recs); c = sum(r["correct"] for r in recs); par = sum(r["pred"] is not None for r in recs)
    trunc = sum(r["finish"] == "length" for r in recs)
    print(f"[reason {a.route}|{a.model}] {c}/{n} = {c/max(n,1):.4f}; parsed {par}; truncated {trunc}; serving faults retried in this run {n_fault} -> {fp}", flush=True)


if __name__ == "__main__":
    main()
