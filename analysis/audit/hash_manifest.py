"""Evidence-chain hash manifest (moat P4).

Pins every reviewer-facing artifact with sha256 + size + mtime so numbers in
the papers are tied to immutable file states. Re-run after any regeneration;
manifests are timestamped, never overwritten (evidence_manifest_<n>.json).
"""
import hashlib, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    "outputs/rebuild/qa_tv_v3.jsonl", "outputs/rebuild/scenes_tv_v3c.jsonl",
    "outputs/rebuild/qa_womd_v3.jsonl", "outputs/rebuild/qa_womd_v4.jsonl",
    "outputs/rebuild/scenes_womd_v3.jsonl", "outputs/coda/qa_coda.jsonl",
    "outputs/coda/states_kf_v9.json", "outputs/coda/states_coda.json",
    "outputs/matrix360/corpus_c/train_a1.jsonl",
    "outputs/matrix360/corpus_c/eval_nusc.jsonl",
    "outputs/matrix360/corpus_c/eval_womd.jsonl",
    "outputs/matrix360/corpus_c2/train_a1.jsonl",
    "outputs/matrix360/corpus_ct/train_a1.jsonl",
    "outputs/matrix360/eval/summary_a1.json",
    "outputs/matrix360/eval/summary_a1_scratch.json",
    "outputs/matrix360/eval/summary_a2.json",
    "outputs/matrix360/eval/summary_c1.json",
    "outputs/matrix360/eval/summary_c2.json",
    "outputs/anchor/anchor_analysis.json",
    "outputs/anchor_womd/teacher_analysis.json",
    "outputs/labels3/teacher_labels_32b.jsonl",
    "outputs/labels3/teacher_labels_womd_32b.jsonl",
    "outputs/surplus/coda_items.jsonl", "outputs/surplus/rule_preds.jsonl",
]


def sha(p, blk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(blk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    man = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "files": {}}
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            man["files"][rel] = None
            continue
        st = p.stat()
        man["files"][rel] = {"sha256": sha(p), "bytes": st.st_size,
                             "mtime": int(st.st_mtime)}
    n = 0
    while (ROOT / f"outputs/evidence_manifest_{n}.json").exists():
        n += 1
    out = ROOT / f"outputs/evidence_manifest_{n}.json"
    json.dump(man, open(out, "w"), indent=1)
    ok = sum(1 for v in man["files"].values() if v)
    print(f"[manifest] {ok}/{len(TARGETS)} files pinned -> {out.name}",
          flush=True)


if __name__ == "__main__":
    main()
