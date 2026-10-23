"""A9 (Access resubmission, R2-6 "YOLO overfits"): evaluate each per-fold
detector on (a) the frames of its *held-out* fold sequences (true out-of-fold)
and (b) its own training split, so the paper can report the train/held-out
gap instead of the results.csv 'val' number (which is a random 10 % of the
training sequences and therefore not out-of-fold).

Frames and labels: outputs/coda/detset_kf/{images,labels}/all (the 1,366
development-bank frames with GT-projected 2D boxes, 21 classes). Fold
membership: outputs/coda/kfold/folds.json. Detectors:
runs/detect/outputs/coda/detrun_kf/kf{f}_{11l,11m}/weights/best.pt.

Resume-safe: a (fold, model, split) whose result json exists is skipped.
Inference settings match perception (imgsz 1280); NMS/conf are ultralytics
val defaults (conf 0.001, iou 0.7) as is standard for mAP.
"""
import json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DSET = ROOT / "outputs/coda/detset_kf"
OUT = ROOT / "exp_rev1/a9_detmap"
OUT.mkdir(parents=True, exist_ok=True)
FOLDS = json.load(open(ROOT / "outputs/coda/kfold/folds.json"))["folds"]
NAMES = [l.split(":", 1)[1].strip() for l in open(DSET / "dataset_f0.yaml") if re.match(r"\s+\d+:", l)]


def write_list(name, paths):
    p = OUT / f"{name}.txt"
    p.write_text("\n".join(paths) + "\n")
    y = OUT / f"{name}.yaml"
    y.write_text(f"path: {DSET.as_posix()}\ntrain: {p.as_posix()}\nval: {p.as_posix()}\nnames:\n"
                 + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))
    return y


def seq_of(p):
    return re.search(r"/(\d+)_\d+\.png$", p.replace("\\", "/")).group(1)


def main():
    from ultralytics import YOLO
    all_imgs = sorted((DSET / "images/all").glob("*.png"))
    all_imgs = [p.as_posix() for p in all_imgs]
    for f in range(4):
        held = set(FOLDS[str(f)])
        oof = [p for p in all_imgs if seq_of(p) in held]
        train = [l.strip() for l in open(DSET / f"train_f{f}.txt") if l.strip()]
        assert not (held & {seq_of(p) for p in train}), f"fold {f}: held-out seq leaked into train list"
        lists = {"heldout": write_list(f"f{f}_heldout", oof),
                 "train": write_list(f"f{f}_train", train)}
        for tag in ("11l", "11m"):
            w = ROOT / f"runs/detect/outputs/coda/detrun_kf/kf{f}_{tag}/weights/best.pt"
            for split, yaml in lists.items():
                res_p = OUT / f"kf{f}_{tag}_{split}.json"
                if res_p.exists():
                    print(f"[skip] {res_p.name}", flush=True); continue
                t0 = time.time()
                m = YOLO(str(w))
                r = m.val(data=str(yaml), imgsz=1280, batch=8, device=0, plots=False, verbose=False,
                          project=str(OUT / "runs"), name=f"kf{f}_{tag}_{split}", exist_ok=True)
                out = {"fold": f, "model": tag, "split": split, "n_images": sum(1 for l in open(OUT / f"f{f}_{split}.txt") if l.strip()),  # paths contain spaces: count lines, not tokens
                       "heldout_seqs": sorted(held), "mAP50": float(r.box.map50), "mAP50_95": float(r.box.map),
                       "precision": float(r.box.mp), "recall": float(r.box.mr),
                       "per_class_mAP50": {NAMES[i]: float(v) for i, v in zip(r.box.ap_class_index, r.box.ap50)},
                       "wall_s": time.time() - t0}
                json.dump(out, open(res_p, "w"), indent=1)
                print(f"[done] kf{f}_{tag}_{split}: mAP50={out['mAP50']:.4f} mAP50-95={out['mAP50_95']:.4f} "
                      f"n={out['n_images']} ({out['wall_s']:.0f}s)", flush=True)
    (OUT / "A9_COMPLETE.marker").write_text("done\n")
    print("all done", flush=True)


if __name__ == "__main__":
    main()
