"""A9c: per-fold detector mAP on held-out sequences AND own training split,
against a chosen label set (detset_kf = as-trained labels; detset_vis1 /
detset_vis2 = visible-scope labels from a9b). Same val settings as a9.
Usage: python a9c_eval_labelset.py vis1 [vis2 ...]
Resume-safe per (labelset, fold, model, split).
"""
import json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_rev1/a9_detmap"
FOLDS = json.load(open(ROOT / "outputs/coda/kfold/folds.json"))["folds"]
KF = ROOT / "outputs/coda/detset_kf"
NAMES = [l.split(":", 1)[1].strip() for l in open(KF / "dataset_f0.yaml") if re.match(r"\s+\d+:", l)]


def seq_of(p):
    return re.search(r"/(\d+)_\d+\.png$", p.replace("\\", "/")).group(1)


def main(labelsets):
    from ultralytics import YOLO
    for ls in labelsets:
        dset = ROOT / f"outputs/coda/detset_{ls}"
        imgs = sorted(p.as_posix() for p in (dset / "images/all").glob("*.png"))
        for f in range(4):
            held = set(FOLDS[str(f)])
            train_names = {Path(l.strip()).name for l in open(KF / f"train_f{f}.txt") if l.strip()}
            splits = {"heldout": [p for p in imgs if seq_of(p) in held],
                      "train": [p for p in imgs if Path(p).name in train_names]}
            for split, paths in splits.items():
                lst = OUT / f"{ls}_f{f}_{split}.txt"; lst.write_text("\n".join(paths) + "\n")
                y = OUT / f"{ls}_f{f}_{split}.yaml"
                y.write_text(f"path: {dset.as_posix()}\ntrain: {lst.as_posix()}\nval: {lst.as_posix()}\nnames:\n"
                             + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))
                for tag in ("11l", "11m"):
                    res_p = OUT / f"{ls}_kf{f}_{tag}_{split}.json"
                    if res_p.exists():
                        print(f"[skip] {res_p.name}", flush=True); continue
                    t0 = time.time()
                    r = YOLO(str(ROOT / f"runs/detect/outputs/coda/detrun_kf/kf{f}_{tag}/weights/best.pt")).val(
                        data=str(y), imgsz=1280, batch=8, device=0, plots=False, verbose=False,
                        project=str(OUT / "runs"), name=f"{ls}_kf{f}_{tag}_{split}", exist_ok=True)
                    out = {"labelset": ls, "fold": f, "model": tag, "split": split, "n_images": len(paths),
                           "heldout_seqs": sorted(held), "mAP50": float(r.box.map50), "mAP50_95": float(r.box.map),
                           "precision": float(r.box.mp), "recall": float(r.box.mr),
                           "per_class_mAP50": {NAMES[i]: float(v) for i, v in zip(r.box.ap_class_index, r.box.ap50)},
                           "wall_s": time.time() - t0}
                    json.dump(out, open(res_p, "w"), indent=1)
                    print(f"[done] {res_p.name}: mAP50={out['mAP50']:.4f} mAP50-95={out['mAP50_95']:.4f} n={len(paths)}", flush=True)
    (OUT / f"A9C_{'_'.join(labelsets)}_COMPLETE.marker").write_text("done\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["vis1", "vis2"])
