"""A6 addendum 1: set the camera constant of the serializer for nuScenes.

The serializer takes the image sector of an object from its image column `u` and a fixed
image width of 1224 pixels (the CODa camera). nuScenes images are 1600 pixels wide. This
script writes a copy of a state file in which every `u` is multiplied by 1224/1600, so that
the shipped serializer, unchanged, places its sector boundaries at thirds of the nuScenes
image. Nothing else in a state is changed.

Usage: python c2_rescale_u.py IN.json OUT.json
"""
import json, sys

SER_W, CAM_W = 1224.0, 1600.0


def main():
    src, dst = sys.argv[1], sys.argv[2]
    states = json.load(open(src, encoding="utf-8"))
    n = 0
    for st in states.values():
        for g in st["agents"]:
            if g.get("u") is not None:
                g["u"] = round(g["u"] * SER_W / CAM_W, 1); n += 1
    json.dump(states, open(dst, "w", encoding="utf-8"))
    print(f"[rescale-u] {len(states)} frames, {n} objects -> {dst}")


if __name__ == "__main__":
    main()
