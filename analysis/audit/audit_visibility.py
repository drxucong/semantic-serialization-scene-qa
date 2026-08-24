"""How much of the 'camera-visible' gold set is not actually camera-visible?

The benchmark's visibility gate (make_coda_qa.py) is:

    the 3D centre projects inside the 1224x1024 image, depth > 0.5 m,
    ground distance <= 40 m

That is a frustum test. It says nothing about occlusion, and nothing about
whether an object at 40 m is large enough to see. A pedestrian entirely behind
a parked car passes it, and then counts in the gold answer for a counting
question that neither arm can answer from the image.

This script measures the size of the hole before anyone decides whether to
regenerate the banks. For every object that the current gate admits it reports:

  n_pts      LiDAR returns inside the 3D box            (is it observable at all)
  px_h       projected pixel height of the box          (is it resolvable)
  occ        occlusion ratio: the fraction of the box's image footprint whose
             nearest LiDAR return is at least OCC_M closer than the box's own
             near face                                  (is something in front)

Nothing is modified. Output is one small JSON summary plus a per-object CSV.

Usage (on the machine that has the data):
  python audit_visibility.py --coda data/coda_sm/CODa_sm --sids outputs/coda/qa_confirm_sids.txt --out outputs/coda/visibility_audit_confirm.json
"""
import argparse, glob, json, math, os, sys
import numpy as np
import yaml

OCC_M = 1.0          # a surface this much closer than the box counts as in front
GRID = 4             # image is binned GRID x GRID px for the occlusion test


def load_calib(coda, seq):
    fp = f"{coda}/calibrations/{seq}/calib_os1_to_cam0.yaml"
    return np.array(yaml.safe_load(open(fp))["projection_matrix"]["data"],
                    dtype=np.float64).reshape(3, 4)


def load_points(fp):
    raw = np.fromfile(fp, dtype=np.float32)
    for stride in (4, 5, 6, 3):
        if raw.size % stride == 0:
            p = raw.reshape(-1, stride)[:, :3]
            if np.isfinite(p).all() and np.abs(p).max() < 1e4:
                return p
    return raw.reshape(-1, 4)[:, :3]


def corners(b):
    l, w, h = b["l"], b["w"], b["h"]
    yaw = b.get("yaw", 0.0)
    c, s = math.cos(yaw), math.sin(yaw)
    out = []
    for dx in (-l / 2, l / 2):
        for dy in (-w / 2, w / 2):
            for dz in (-h / 2, h / 2):
                out.append([b["cX"] + dx * c - dy * s,
                            b["cY"] + dx * s + dy * c,
                            b["cZ"] + dz])
    return np.array(out)


def project(P, X):
    h = np.concatenate([X, np.ones((len(X), 1))], 1)
    uvw = h @ P.T
    w = uvw[:, 2]
    ok = w > 1e-6
    uv = np.full((len(X), 2), np.nan)
    uv[ok] = uvw[ok, :2] / w[ok, None]
    return uv, w


def in_box(pts, b):
    yaw = b.get("yaw", 0.0)
    c, s = math.cos(-yaw), math.sin(-yaw)
    d = pts - np.array([b["cX"], b["cY"], b["cZ"]])
    x = d[:, 0] * c - d[:, 1] * s
    y = d[:, 0] * s + d[:, 1] * c
    return ((np.abs(x) <= b["l"] / 2 + .1) & (np.abs(y) <= b["w"] / 2 + .1)
            & (np.abs(d[:, 2]) <= b["h"] / 2 + .1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coda", required=True)
    ap.add_argument("--sids", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv", default="")
    a = ap.parse_args()

    sids = [l.strip() for l in open(a.sids) if l.strip()]
    recs = []
    missing_pc = 0
    for k, sid in enumerate(sids):
        seq, fr = sid.rsplit("_", 1)
        bb = f"{a.coda}/3d_bbox/os1/{seq}/3d_bbox_os1_{seq}_{fr}.json"
        pc = f"{a.coda}/3d_comp/os1/{seq}/3d_comp_os1_{seq}_{fr}.bin"
        if not os.path.exists(bb):
            continue
        try:
            P = load_calib(a.coda, seq)
        except Exception:
            continue
        boxes = json.load(open(bb))["3dbbox"]
        pts = load_points(pc) if os.path.exists(pc) else None
        if pts is None:
            missing_pc += 1
        if pts is not None and len(pts):
            uvp, wp = project(P, pts)
            keep = (wp > 0.5) & np.isfinite(uvp[:, 0])
            uvp, wp = uvp[keep], wp[keep]
            gu = np.clip((uvp[:, 0] // GRID).astype(int), 0, 1224 // GRID)
            gv = np.clip((uvp[:, 1] // GRID).astype(int), 0, 1024 // GRID)
            key = gu * 10000 + gv
            order = np.argsort(wp)
            depth = {}
            for i in order:                     # nearest return per cell
                kk = key[i]
                if kk not in depth:
                    depth[kk] = wp[i]
        else:
            depth = {}
        for b in boxes:
            uvc, wc = project(P, np.array([[b["cX"], b["cY"], b["cZ"]]]))
            u, v, w = uvc[0, 0], uvc[0, 1], wc[0]
            dist = math.hypot(b["cX"], b["cY"])
            if not (w > 0.5 and 0 <= u < 1224 and 0 <= v < 1024 and dist <= 40):
                continue                        # not in the current gold set
            C = corners(b)
            uvC, wC = project(P, C)
            fin = np.isfinite(uvC[:, 0])
            px_h = float(uvC[fin, 1].max() - uvC[fin, 1].min()) if fin.any() else 0.0
            px_w = float(uvC[fin, 0].max() - uvC[fin, 0].min()) if fin.any() else 0.0
            npts = int(in_box(pts, b).sum()) if pts is not None else -1
            occ = -1.0
            if depth and fin.any():
                u0, u1 = uvC[fin, 0].min(), uvC[fin, 0].max()
                v0, v1 = uvC[fin, 1].min(), uvC[fin, 1].max()
                near = float(wC[fin].min())
                cells, blocked = 0, 0
                for gu_ in range(int(max(0, u0) // GRID),
                                 int(min(1223, u1) // GRID) + 1):
                    for gv_ in range(int(max(0, v0) // GRID),
                                     int(min(1023, v1) // GRID) + 1):
                        d = depth.get(gu_ * 10000 + gv_)
                        if d is None:
                            continue
                        cells += 1
                        if d < near - OCC_M:
                            blocked += 1
                occ = blocked / cells if cells else -1.0
            recs.append({"sid": sid, "cls": b["classId"], "dist": round(dist, 2),
                         "npts": npts, "px_h": round(px_h, 1),
                         "px_w": round(px_w, 1), "occ": round(occ, 3)})
        if (k + 1) % 200 == 0:
            print(f"[vis] {k+1}/{len(sids)} frames, {len(recs)} objects",
                  flush=True)

    n = len(recs)
    def frac(f):
        return round(sum(1 for r in recs if f(r)) / n, 4) if n else None
    have_pts = [r for r in recs if r["npts"] >= 0]
    have_occ = [r for r in recs if r["occ"] >= 0]
    summary = {
        "n_objects_in_current_gold_set": n,
        "frames": len(sids), "frames_without_pointcloud": missing_pc,
        "objects_with_pointcloud": len(have_pts),
        "objects_with_occlusion_estimate": len(have_occ),
        "fraction_npts_lt_1":  frac(lambda r: 0 <= r["npts"] < 1),
        "fraction_npts_lt_5":  frac(lambda r: 0 <= r["npts"] < 5),
        "fraction_npts_lt_20": frac(lambda r: 0 <= r["npts"] < 20),
        "fraction_pxh_lt_10":  frac(lambda r: r["px_h"] < 10),
        "fraction_pxh_lt_20":  frac(lambda r: r["px_h"] < 20),
        "fraction_pxh_lt_30":  frac(lambda r: r["px_h"] < 30),
        "fraction_occ_gt_50":  frac(lambda r: r["occ"] > 0.50),
        "fraction_occ_gt_75":  frac(lambda r: r["occ"] > 0.75),
        "fraction_occ_gt_90":  frac(lambda r: r["occ"] > 0.90),
        "fraction_failing_any": frac(lambda r: (0 <= r["npts"] < 5)
                                     or r["px_h"] < 20 or r["occ"] > 0.75),
        "median_npts": int(np.median([r["npts"] for r in have_pts])) if have_pts else None,
        "median_px_h": float(np.median([r["px_h"] for r in recs])) if n else None,
        "median_occ": float(np.median([r["occ"] for r in have_occ])) if have_occ else None,
    }
    by_cls = {}
    for r in recs:
        d = by_cls.setdefault(r["cls"], {"n": 0, "bad": 0})
        d["n"] += 1
        if (0 <= r["npts"] < 5) or r["px_h"] < 20 or r["occ"] > 0.75:
            d["bad"] += 1
    summary["by_class"] = {c: {"n": d["n"], "bad_frac": round(d["bad"] / d["n"], 3)}
                           for c, d in sorted(by_cls.items(), key=lambda x: -x[1]["n"])}
    json.dump(summary, open(a.out, "w"), indent=1)
    print(json.dumps(summary, indent=1)[:2000])
    if a.csv:
        import csv as _csv
        with open(a.csv, "w", newline="") as fh:
            w_ = _csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
            w_.writeheader(); w_.writerows(recs)
    print(f"[vis] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
