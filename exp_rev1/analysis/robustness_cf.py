"""A4 robustness checks for the primary contrast (D0 - PIXEL) on the
confirmatory bank, computed from the released per-item log
(exp3_runs/analysis/predictions3_cf_v2.csv; 1328 items x arm, 21 clusters).

Everything here is a *sensitivity analysis* of the pre-registered paired
cluster bootstrap; the pre-registered criterion itself is unchanged.

Outputs (stdout + robustness_cf.json):
  1. paired cluster bootstrap (reproduces the frozen criterion, B=20000)
  2. cluster-level sign-flip permutation test (exact enumeration when 2^21
     is affordable; otherwise Monte Carlo)
  3. leave-one-sequence-out (LOSO): point estimate + bootstrap CI per drop
  4. cluster jackknife SE and CI (delete-one)
  5. per-cluster contribution table (n_q, delta_q, share of total)
  6. cluster-weighted (unweighted-by-size) mean of per-cluster deltas, as a
     check that the result is not carried by the largest sequence
"""
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

B = 20000
SEED = 20260809


def load(csv, sys_arm, pix_arm):
    df = pd.read_csv(csv)
    a = df[df.arm == sys_arm].set_index("question_id")
    b = df[df.arm == pix_arm].set_index("question_id")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    assert (a.sequence_id.values == b.sequence_id.values).all()
    d = pd.DataFrame({"seq": a.sequence_id.values,
                      "diff": a.correct.values.astype(float) - b.correct.values.astype(float)})
    return d


def cluster_stats(d):
    g = d.groupby("seq")["diff"]
    return pd.DataFrame({"n": g.size(), "sum": g.sum(), "mean": g.mean()})


def paired_cluster_bootstrap(cs, B=B, seed=SEED):
    rng = np.random.default_rng(seed)
    k = len(cs)
    sums, ns = cs["sum"].values, cs["n"].values
    idx = rng.integers(0, k, size=(B, k))
    est = sums[idx].sum(1) / ns[idx].sum(1)
    return est


def sign_flip_test(cs, seed=SEED, max_exact=2 ** 22):
    """H0: per-cluster mean difference is symmetric about 0.
    Statistic: pooled delta = sum(sum_q) / sum(n_q). Flip the sign of each
    cluster's sum."""
    sums, ns = cs["sum"].values, cs["n"].values
    k = len(sums)
    obs = sums.sum() / ns.sum()
    if 2 ** k <= max_exact:
        signs = np.array(list(itertools.product([1, -1], repeat=k)), dtype=np.int8)
        stats = (signs * sums).sum(1) / ns.sum()
        p_two = np.mean(np.abs(stats) >= abs(obs) - 1e-12)
        p_one = np.mean(stats >= obs - 1e-12)
        return obs, p_two, p_one, "exact", 2 ** k
    rng = np.random.default_rng(seed)
    signs = rng.choice([1, -1], size=(B, k))
    stats = (signs * sums).sum(1) / ns.sum()
    return obs, float(np.mean(np.abs(stats) >= abs(obs) - 1e-12)), float(np.mean(stats >= obs - 1e-12)), "mc", B


def loso(cs):
    rows = []
    for s in cs.index:
        sub = cs.drop(index=s)
        est = sub["sum"].sum() / sub["n"].sum()
        bs = paired_cluster_bootstrap(sub)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        rows.append({"dropped": int(s), "delta": est, "ci_lo": lo, "ci_hi": hi})
    return pd.DataFrame(rows)


def jackknife(cs):
    sums, ns = cs["sum"].values, cs["n"].values
    k = len(sums)
    full = sums.sum() / ns.sum()
    pseudo = np.array([(sums.sum() - sums[i]) / (ns.sum() - ns[i]) for i in range(k)])
    se = np.sqrt((k - 1) / k * np.sum((pseudo - pseudo.mean()) ** 2))
    return full, se, full - 1.96 * se, full + 1.96 * se


def run(csv, sys_arm, pix_arm):
    d = load(csv, sys_arm, pix_arm)
    cs = cluster_stats(d)
    out = {"sys": sys_arm, "pix": pix_arm, "n_items": int(len(d)), "n_clusters": int(len(cs))}

    delta = d["diff"].mean()
    bs = paired_cluster_bootstrap(cs)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    out["delta"] = delta
    out["paired_cluster_ci"] = [lo, hi]
    out["paired_cluster_p_le0"] = float(np.mean(bs <= 0))

    obs, p2, p1, mode, nperm = sign_flip_test(cs)
    out["signflip"] = {"p_two_sided": p2, "p_one_sided": p1, "mode": mode, "n_perm": int(nperm)}

    full, se, jlo, jhi = jackknife(cs)
    out["jackknife"] = {"se": se, "ci": [jlo, jhi]}

    lo_df = loso(cs)
    out["loso"] = lo_df.to_dict("records")
    out["loso_min_ci_lo"] = {"value": float(lo_df.ci_lo.min()), "dropped": int(lo_df.loc[lo_df.ci_lo.idxmin(), "dropped"])}
    out["loso_n_cross_zero"] = int((lo_df.ci_lo <= 0).sum())

    out["cluster_mean_of_means"] = float(cs["mean"].mean())
    out["clusters_positive"] = int((cs["mean"] > 0).sum())
    out["clusters_negative"] = int((cs["mean"] < 0).sum())
    cs2 = cs.copy()
    cs2["share_of_total"] = cs2["sum"] / cs2["sum"].sum()
    out["per_cluster"] = cs2.reset_index().rename(columns={"seq": "sequence"}).to_dict("records")

    print(f"\n=== {sys_arm} - {pix_arm}  (n={len(d)}, clusters={len(cs)}) ===")
    print(f"delta = {delta:+.4f}   paired-cluster 95% CI [{lo:+.4f}, {hi:+.4f}]   P(bs<=0)={out['paired_cluster_p_le0']:.4f}")
    print(f"sign-flip permutation ({mode}, {nperm}): p_two={p2:.4f}  p_one={p1:.4f}")
    print(f"jackknife SE={se:.4f}  95% CI [{jlo:+.4f}, {jhi:+.4f}]")
    print(f"LOSO: min CI lower {out['loso_min_ci_lo']['value']:+.4f} (drop seq {out['loso_min_ci_lo']['dropped']}); "
          f"{out['loso_n_cross_zero']}/{len(cs)} drops cross zero")
    print(f"per-cluster: mean of means {out['cluster_mean_of_means']:+.4f}; "
          f"{out['clusters_positive']} positive / {out['clusters_negative']} negative")
    print(cs2.sort_values("share_of_total", ascending=False).head(5).to_string())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("robustness_cf.json")))
    a = ap.parse_args()
    res = [run(a.csv, "D0_7b", "PIXEL_7b"), run(a.csv, "D0_3b", "PIXEL_3b")]
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print("\nwrote", a.out)
