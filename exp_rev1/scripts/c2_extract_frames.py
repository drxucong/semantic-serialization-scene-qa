"""C2: extract from the nuScenes keyframe archives only the front-camera frames that the
bank uses. Reads every archive once as a stream; writes nothing else and deletes nothing.

Usage: python c2_extract_frames.py --qa outputs/nusc_ext2/qa_nusc2.jsonl
       --archives F:/datasets/nuscenes_trainval_keyframes/archives
       --root F:/datasets/nuscenes_trainval_keyframes/raw
"""
import argparse, json, tarfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True)
    ap.add_argument("--archives", required=True)
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    root = Path(a.root)
    need = set()
    for l in open(ROOT / a.qa, encoding="utf-8"):
        p = json.loads(l)["cam_front"].replace("\\", "/")
        assert p.startswith(a.root.replace("\\", "/").rstrip("/") + "/"), p
        need.add(p[len(a.root.rstrip("/")) + 1:])
    have = {n for n in need if (root / n).exists() and (root / n).stat().st_size > 0}
    print(f"[extract] frames needed {len(need)}; already there {len(have)}", flush=True)
    for arc in sorted(Path(a.archives).glob("*.tgz")):
        if len(have) == len(need):
            break
        # completeness of every archive is checked beforehand by c2_verify_archives.py
        # (multipart ETag of the bucket and gzip CRC); see VERIFY.txt next to the archives
        t0 = time.time(); got = 0
        with tarfile.open(arc, "r|gz") as tf:
            for m in tf:
                if m.isfile() and m.name in need and m.name not in have:
                    dst = root / m.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dst.with_suffix(dst.suffix + ".part")
                    with open(tmp, "wb") as f:
                        f.write(tf.extractfile(m).read())
                    tmp.replace(dst)
                    have.add(m.name); got += 1
        print(f"[extract] {arc.name}: {got} frames ({(time.time()-t0)/60:.1f} min); total {len(have)}/{len(need)}", flush=True)
    miss = sorted(need - have)
    print(f"[extract] done: {len(have)}/{len(need)} frames; missing {len(miss)}", flush=True)
    if miss:
        print("[extract] first missing:", miss[:3], flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
