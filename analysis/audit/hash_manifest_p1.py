"""Evidence-chain hash manifest for PAPER 1 (moat P4, paper-1 scope).

hash_manifest.py pins the shared corpus/training artifacts. It predates the
paper-1 control suite, so none of the arms that carry paper-1's numbers are in
it. This file pins EVERY per-item log a reviewer would need to recompute every
number in the paper, plus the two state files and the question bank, with
sha256 + size + mtime.

New file; hash_manifest.py is untouched. Manifests are timestamped and never
overwritten (evidence_manifest_p1_<n>.json).

Arms are tagged by the role they play in the paper so the manifest doubles as
the released-artifact index:
  headline / control / ladder / ablation / cross-family / log-only
"log-only" arms are released for completeness but are NOT reported as controls
(they differ from their anchor on a second axis; see the paper's reader-family
paragraph).
"""
import hashlib, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = "outputs/phase10/coda/"

TARGETS = {
    # --- bank + states -------------------------------------------------
    "outputs/coda/qa_coda.jsonl": "bank",
    "outputs/coda/states_kf_v9.json": "perceived-state (out-of-fold, K=4)",
    "outputs/coda/states_coda.json": "ground-truth state",
    # --- headline contrast ---------------------------------------------
    P + "results_system9_kf_7b/state_typed__clean__forced.jsonl": "headline v9",
    P + "results_qwen2.5vl_7b/pixel__clean__forced.jsonl": "headline PIXEL 7B",
    P + "results_system8_kf_7b/state_typed__clean__forced.jsonl": "prior v8",
    # --- interface-isolation controls ----------------------------------
    P + "results_ctrlA_vl7b_text/state_typed__clean__forced.jsonl":
        "control A: VL-7B decoder on serialized text",
    "outputs/anno_img/vlm_raw_7b.jsonl": "control B: raw image (within-control anchor)",
    "outputs/anno_img/vlm_anno_7b.jsonl": "control B: GT-annotated image",
    P + "results_gt_v9ser_7b/state_typed__clean__forced.jsonl":
        "control B: GT state through shipped serializer (= oracle .9553)",
    P + "results_qwen2.5_7b/state_typed__clean__forced.jsonl":
        "GT state, previous-generation serializer (.8565)",
    # --- scale x interface ---------------------------------------------
    P + "results_v9_3b/state_typed__clean__forced.jsonl": "real state, 3B reader",
    P + "results_qwen2.5vl_3b/pixel__clean__forced.jsonl": "PIXEL 3B",
    P + "results_qwen2.5_3b/state_typed__clean__forced.jsonl": "GT state, 3B reader",
    # --- 2x2 ablation ---------------------------------------------------
    P + "results_abl_a2_v8st_v9ser/state_typed__clean__forced.jsonl": "a2 v8-state/v9-serializer",
    P + "results_abl_a3_v9st_v3ser/state_typed__clean__forced.jsonl": "a3 v9-state/v3-serializer",
    P + "results_abl_a5_noP3/state_typed__clean__forced.jsonl": "deletion: depth",
    P + "results_abl_a6_noP2/state_typed__clean__forced.jsonl": "deletion: tiling/OV",
    P + "results_abl_a7_noP4/state_typed__clean__forced.jsonl": "deletion: boundary flags",
    # --- cross-family (Mac-internal pairing only) -----------------------
    P + "results_mac_v9_qwen7b/state_typed__clean__forced.jsonl": "Mac anchor qwen2.5:7b",
    P + "results_mac_v9_llama31/state_typed__clean__forced.jsonl": "cross-family llama3.1:8b",
    P + "results_mac_v9_gptoss_fix/state_typed__clean__forced.jsonl": "log-only gpt-oss:20b",
    P + "results_mac_v9_gemma4_fix/state_typed__clean__forced.jsonl": "log-only gemma4:26b",
    P + "results_mac_v9_gptoss_nothink/state_typed__clean__forced.jsonl":
        "log-only gpt-oss think-off (parse rate .000, instrument failure)",
}
# --- serializer-operator ladder ----------------------------------------
for _L in range(7):
    TARGETS[P + f"results_lad_L{_L}/state_typed__clean__forced.jsonl"] = f"ladder L{_L}"


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
           "scope": "paper 1 (encoder-free / semantic serialization), v0.9",
           "note": "role=log-only arms are released for completeness and are "
                   "NOT reported as controls in the paper.",
           "files": {}}
    missing = []
    for rel, role in TARGETS.items():
        p = ROOT / rel
        if not p.exists():
            man["files"][rel] = {"role": role, "status": "MISSING"}
            missing.append(rel)
            continue
        st = p.stat()
        n_lines = sum(1 for _ in open(p, "rb")) if p.suffix == ".jsonl" else None
        man["files"][rel] = {"role": role, "sha256": sha(p),
                             "bytes": st.st_size, "mtime": int(st.st_mtime),
                             "lines": n_lines}
    n = 0
    while (ROOT / f"outputs/evidence_manifest_p1_{n}.json").exists():
        n += 1
    out = ROOT / f"outputs/evidence_manifest_p1_{n}.json"
    json.dump(man, open(out, "w"), indent=1)
    ok = len(TARGETS) - len(missing)
    print(f"[manifest-p1] {ok}/{len(TARGETS)} artifacts pinned -> {out.name}",
          flush=True)
    for rel in missing:
        print(f"[manifest-p1] MISSING {rel}", flush=True)


if __name__ == "__main__":
    main()
