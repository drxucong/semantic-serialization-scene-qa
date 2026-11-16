"""2026-11-16, offline (no board, no language model): the fixed rule of
exp2_option_baselines.py (baseline B1, Supplement Table S4), applied without change to the
perceived states that the one-pass detector pair produced ON THE BOARD
(exp_rev1/b10_boards/orin_nano_fullbank/states_confirm_light1_orin.json, copied from the board,
md5 6afa4f75b6e2436588255d7cc943a071).

Why: an internal review of the final manuscript asked why the table of the board has no row for
the rule without a language model, which on the full-stack states of the laptop scores 0.8027 on
the confirmatory bank (above both readers) and 0.3479 on the reworded bank N1.

The rule was fixed on the development bank with the full-stack states; nothing is fitted here.
Checks: (a) the same code on the full-stack confirmatory states must reproduce 0.8027;
(b) the questions and their order are those of the board run (the items of the 3B reader run).

The script runs in two layouts: the authors' tree (scripts/rev1/) and the public repository
(exp_rev1/scripts/), where the bank, the states and the rule are in banks/, states/, analysis/
and serializer/.
Output: exp_rev1/b10_boards/orin_nano_fullbank/rule_on_board_states.json
usage: python b10_rule_on_board_states.py
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if (ROOT / "scripts/paper/exp2_option_baselines.py").exists():        # authors' tree
    sys.path.insert(0, str(ROOT / "scripts/paper"))
    QA, ST_FULL = "outputs/coda/qa_confirm.jsonl", "outputs/coda/states_confirm_v9.json"
else:                                                                  # public repository
    for p in ("serializer", "analysis"):
        sys.path.insert(0, str(ROOT / p))
    QA, ST_FULL = "banks/qa_confirm.jsonl", "states/states_confirm_v9.json"
import exp2_option_baselines as B  # noqa: E402
B.ROOT = ROOT

OBD = ROOT / "exp_rev1/b10_boards/orin_nano_fullbank"
ST_BOARD = "exp_rev1/b10_boards/orin_nano_fullbank/states_confirm_light1_orin.json"
FAMS = ("counting", "direction", "nearest_class", "nearest_dist", "path_object")


def run(states_rel):
    items = B.load_bank(QA, states_rel)
    preds = {}
    for it, fch, fans, st in items:
        f = B.state_facts(st, it["category"], it["question"])
        preds[it["qa_id"]] = {"pred": B.rule_pick(it["category"], fch, f), "gold": fans, "family": it["category"],
                              "recording": it["scene_name"]}
    return preds


def summary(preds, ids):
    acc = sum(preds[i]["pred"] == preds[i]["gold"] for i in ids) / len(ids)
    fam = {f: sum(preds[i]["pred"] == preds[i]["gold"] for i in ids if preds[i]["family"] == f) / max(1, sum(preds[i]["family"] == f for i in ids))
           for f in FAMS}
    return {"n": len(ids), "acc": acc, "n_correct": sum(preds[i]["pred"] == preds[i]["gold"] for i in ids), "family": fam}


def main():
    board_ids = [json.loads(l)["qa_id"] for l in open(OBD / "full-qwen2.5-3b/items.jsonl", encoding="utf-8")]
    assert len(board_ids) == 1328 and len(set(board_ids)) == 1328
    full = run(ST_FULL)
    board = run(ST_BOARD)
    missing_full = [i for i in board_ids if i not in full]
    missing_board = [i for i in board_ids if i not in board]
    out = {"states_board_md5": "6afa4f75b6e2436588255d7cc943a071",
           "n_questions_board_run": len(board_ids), "missing_in_full_states": len(missing_full), "missing_in_board_states": len(missing_board)}
    if not missing_full:
        out["full_stack_laptop_states"] = summary(full, board_ids)
    if not missing_board:
        out["one_pass_board_states"] = summary(board, board_ids)
        out["preds_board"] = {i: board[i] for i in board_ids}
    json.dump(out, open(OBD / "rule_on_board_states.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "preds_board"}, indent=1))


if __name__ == "__main__":
    main()
