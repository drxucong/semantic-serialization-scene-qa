"""Do the CORRECTED rules match gold better? (offline, zero GPU, discipline 19)

Read out of scripts/coda/make_coda_qa.py, the gold definitions are:

  counting      k = number of visible agents of that class   (GT has no
                confidence notion -- every visible object counts)
  nearest_class ags[0].cls                                   (min dist, all)
  nearest_dist  band(nearest instance of ags[0].cls), <5 / <15 / else
  direction     sector of the IMAGE COLUMN u of that instance,
                u < 1224/3 -> "on the left side", < 2*1224/3 -> "in the center",
                else "on the right side"
  path_object   inpath = {x > 1 and |y| <= 2}; min dist within it

The shipped serializer disagrees with three of them:
  * path_object: it scores lateral + dist/10, a soft score, not a corridor
  * direction:   it sectors the BEARING at +-15 deg, not the image column
  * counting:    it headlines the CONFIDENT count, dropping uncertain detections

Measure each shipped rule and each corrected rule against gold, on the same
perceived states the readers were given.
"""
import json, math, re, collections
from pathlib import Path

UP = Path(".")  # repo root: banks/, states/, results/
ST = json.load(open(UP / "states" / "states_kf_v9.json", encoding="utf-8"))
QA = [json.loads(l) for l in open(UP / "banks" / "qa_coda.jsonl", encoding="utf-8")]


def norm(s): return (s or "").strip().lower()
def gold(it): return norm(it["choices"].get(it["answer"]))
def tgt(it):
    m = re.search(r"'([^']+)'", it["question"]); return m.group(1) if m else None
def xy(g):
    r = math.radians(g["bearing"]); return g["dist"]*math.cos(r), g["dist"]*math.sin(r)
def nearest_by_cls(ags):
    n = {}
    for g in ags: n.setdefault(g["cls"], g)
    return n

# ---- shipped rules ----------------------------------------------------------
def sh_count(it, st):
    k = tgt(it); return str(sum(1 for g in st["agents"] if g["cls"]==k and not g.get("lowconf")))
def sh_dir(it, st):
    g = nearest_by_cls(st["agents"]).get(tgt(it))
    if not g: return None
    b = g["bearing"]; s = "left" if b>15 else ("right" if b<-15 else "center")
    return f"on the {s} side"
def sh_path(it, st):
    a = st["agents"]
    if not a: return None
    f = lambda g: abs(g["dist"]*math.sin(math.radians(g["bearing"]))) + g["dist"]/10.0
    return min(a, key=f)["cls"]

# ---- corrected rules --------------------------------------------------------
def fx_count_all(it, st):
    k = tgt(it); return str(sum(1 for g in st["agents"] if g["cls"]==k))
def fx_dir_u(it, st):
    g = nearest_by_cls(st["agents"]).get(tgt(it))
    if not g or g.get("u") is None: return None
    u = g["u"]
    return ("on the left side" if u < 1224/3 else
            "in the center" if u < 2*1224/3 else "on the right side")
def fx_path_corridor(it, st):
    inp = [g for g in st["agents"] if xy(g)[0] > 1 and abs(xy(g)[1]) <= 2]
    if not inp: return None
    return min(inp, key=lambda g: g["dist"])["cls"]
def fx_path_corridor_wide(it, st, w=3.0):
    inp = [g for g in st["agents"] if xy(g)[0] > 1 and abs(xy(g)[1]) <= w]
    if not inp: return None
    return min(inp, key=lambda g: g["dist"])["cls"]

def score(fam, fn, label):
    ok = tot = miss = 0
    for it in QA:
        if it["category"] != fam: continue
        st = ST.get(it["sample_id"])
        if st is None: continue
        p = fn(it, st); tot += 1
        if p is None: miss += 1; continue
        g = gold(it)
        ok += (norm(p) == g) or (norm(p) in g) or (g in norm(p))
    print(f"  {label:<40} {ok}/{tot} = {ok/tot:.4f}" + (f"   ({miss} no-output)" if miss else ""))
    return ok/tot

print("="*80); print("SHIPPED vs CORRECTED compiled fields, against gold"); print("="*80)
print("path_object:")
a=score("path_object", sh_path, "shipped: lateral + dist/10")
b=score("path_object", fx_path_corridor, "corrected: corridor |y|<=2, x>1, min dist")
score("path_object", lambda i,s: fx_path_corridor_wide(i,s,3.0), "variant: corridor |y|<=3")
score("path_object", lambda i,s: fx_path_corridor_wide(i,s,1.5), "variant: corridor |y|<=1.5")
print(f"  --> gain {b-a:+.4f}")
print("direction:")
c=score("direction", sh_dir, "shipped: bearing sector +-15deg")
d=score("direction", fx_dir_u, "corrected: image-column sector u")
print(f"  --> gain {d-c:+.4f}")
print("counting:")
e=score("counting", sh_count, "shipped: confident only")
f=score("counting", fx_count_all, "corrected: all detections")
print(f"  --> gain {f-e:+.4f}")

# ---------------------------------------------------------------------------
print()
print("="*80)
print("COUNTING: if a perfect reader picked the OPTION CLOSEST to our count")
print("="*80)
def closest_opt(cnt, it):
    best, bd = None, None
    for l, t in it["choices"].items():
        try: v = int(t)
        except (TypeError, ValueError): continue
        d = abs(v - cnt)
        if bd is None or d < bd: bd, best = d, l
    return best

def count_rule_eval(fn, label):
    exact = close = tot = 0
    for it in QA:
        if it["category"] != "counting": continue
        st = ST.get(it["sample_id"])
        if st is None: continue
        c = int(fn(it, st)); tot += 1
        exact += (str(c) == it["choices"][it["answer"]])
        close += (closest_opt(c, it) == it["answer"])
    print(f"  {label:<44} exact {exact/tot:.4f}   closest-option {close/tot:.4f}")
    return close/tot

count_rule_eval(sh_count, "shipped: confident only")
count_rule_eval(fx_count_all, "corrected: all detections")
# recall correction is measured for headroom only; see note below
import json as _j
try:
    nm = _j.load(open(UP.parent / "outputs" / "noise_model_v1.json", encoding="utf-8"))
    rec = nm.get("recall_overall") or nm.get("recall") or 0.669
except Exception:
    rec = 0.669
count_rule_eval(lambda i,s: str(round(int(fx_count_all(i,s))/rec)),
                f"headroom probe: all / recall({rec:.3f})")
print("  NOTE: the recall correction is a headroom probe only -- the recall was")
print("  measured on this same bank, so shipping it would be fitting the test set.")
