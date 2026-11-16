"""Audit of the answer key of the nearest-distance family (added 2026-11-15 after a simulated
review asked how the key is defined and whether it depends on that definition).

Key as generated (both datasets): ground distance from the sensor origin to the CENTER of the
annotated 3D box of the nearest visible object. CODa: origin of the LiDAR frame in which the
boxes are annotated. nuScenes: origin of the front camera. Bands: under 5 m, 5 to 15 m, over
15 m; questions within 0.8 m of a boundary are not generated.

This script recomputes, for every nearest-distance question of the confirmatory bank and of
the second nuScenes bank, the ground distance to the NEAREST POINT of the footprint of the same
box, and writes both distances and both bands. A question whose band is the same under the two
definitions has a key that does not depend on the choice of the box point.

Reads annotations only. Writes exp_rev1/key_audit/nearest_dist_key_audit.jsonl.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_rev1/key_audit"; OUT.mkdir(parents=True, exist_ok=True)


def band(d):
    return "under 5 meters away" if d < 5 else "5 to 15 meters away" if d < 15 else "over 15 meters away"


def seg_dist(p, a, b):
    """distance from point p to segment ab (2D)"""
    ab = b - a; t = float(np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-12), 0.0, 1.0))
    return float(np.linalg.norm(p - (a + t * ab)))


def poly_dist(corners):
    """ground distance from the origin to a convex quadrilateral given by its 4 corners (2D)"""
    o = np.zeros(2); n = len(corners)
    return min(seg_dist(o, corners[i], corners[(i + 1) % n]) for i in range(n))


rows = []

# ------------------------------------------------------------------ CODa, confirmatory bank
qa = [json.loads(l) for l in open(ROOT / "outputs/coda/qa_confirm.jsonl", encoding="utf-8")]
gt = json.load(open(ROOT / "outputs/coda/states_confirm_gt.json", encoding="utf-8"))
miss = 0
for it in qa:
    if it["category"] != "nearest_dist":
        continue
    seq, fr = it["sample_id"].split("_")
    key = gt[it["sample_id"]]["agents"][0]                  # nearest visible object; the question names its class
    boxes = json.load(open(ROOT / f"data/coda_sm/CODa_sm/3d_bbox/os1/{seq}/3d_bbox_os1_{seq}_{fr}.json"))["3dbbox"]
    cand = [b for b in boxes if b["classId"] == key["cls"] and abs(round(math.hypot(b["cX"], b["cY"]), 2) - key["dist"]) < 0.011]
    if len(cand) < 1:
        miss += 1; continue
    b = cand[0]
    c, s = math.cos(b["y"]), math.sin(b["y"])
    half = np.array([[b["l"] / 2, b["w"] / 2], [b["l"] / 2, -b["w"] / 2], [-b["l"] / 2, -b["w"] / 2], [-b["l"] / 2, b["w"] / 2]])
    R = np.array([[c, -s], [s, c]])
    corners = half @ R.T + np.array([b["cX"], b["cY"]])
    dc = math.hypot(b["cX"], b["cY"]); dn = poly_dist(corners)
    rows.append({"bank": "confirm", "qa_id": it["qa_id"], "cls": key["cls"], "d_center": round(dc, 3), "d_nearest": round(dn, 3),
                 "band_center": band(dc), "band_nearest": band(dn), "gold": it["choices"][it["answer"]]})
print(f"[key-audit] CODa: {sum(r['bank'] == 'confirm' for r in rows)} nearest-distance questions, {miss} boxes not matched", flush=True)

# ------------------------------------------------------------------ nuScenes, second bank
from nuscenes.nuscenes import NuScenes  # noqa: E402
from nuscenes.utils.geometry_utils import BoxVisibility  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts/rev1"))
from c2_make_nusc_qa import CLS_MAP  # noqa: E402
qa2 = [json.loads(l) for l in open(ROOT / "outputs/nusc_ext2/qa_nusc2.jsonl", encoding="utf-8")]
gt2 = json.load(open(ROOT / "outputs/nusc_ext2/states_nusc2_gt.json", encoding="utf-8"))
nusc = NuScenes(version="v1.0-trainval", dataroot=str(ROOT / "data/nuscenes/raw"), verbose=False)
miss2 = 0
for it in qa2:
    if it["category"] != "nearest_dist":
        continue
    key = gt2[it["sample_id"]]["agents"][0]
    s = nusc.get("sample", it["sample_id"])
    _, boxes, _ = nusc.get_sample_data(s["data"]["CAM_FRONT"], box_vis_level=BoxVisibility.ANY)
    cand = []
    for b in boxes:
        ann = nusc.get("sample_annotation", b.token)
        if CLS_MAP.get(ann["category_name"]) != key["cls"]:
            continue
        x, y, z = b.center
        if abs(round(math.hypot(x, z), 2) - key["dist"]) < 0.011:
            cand.append(b)
    if not cand:
        miss2 += 1; continue
    b = cand[0]
    bc = b.bottom_corners()                                  # 3 x 4, camera frame: x right, y down, z forward
    corners = np.stack([bc[0], bc[2]], axis=1)               # ground plane = (x, z)
    x, y, z = b.center
    dc = math.hypot(x, z); dn = poly_dist(corners)
    rows.append({"bank": "nusc2", "qa_id": it["qa_id"], "cls": key["cls"], "d_center": round(dc, 3), "d_nearest": round(dn, 3),
                 "band_center": band(dc), "band_nearest": band(dn), "gold": it["choices"][it["answer"]]})
print(f"[key-audit] nuScenes: {sum(r['bank'] == 'nusc2' for r in rows)} nearest-distance questions, {miss2} boxes not matched", flush=True)

with open(OUT / "nearest_dist_key_audit.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
for bank in ("confirm", "nusc2"):
    rs = [r for r in rows if r["bank"] == bank]
    ok = sum(r["gold"] == r["band_center"] for r in rs); same = sum(r["band_center"] == r["band_nearest"] for r in rs)
    print(f"[key-audit] {bank}: key equals the band of the center distance in {ok} of {len(rs)}; "
          f"band unchanged with the nearest point of the box in {same} of {len(rs)}; "
          f"median (center - nearest point) = {np.median([r['d_center'] - r['d_nearest'] for r in rs]):.2f} m", flush=True)
