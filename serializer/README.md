# The serializer (source)

This folder holds the source of the serializer of the manuscript and a script that checks it
against the released logs. It was added with the second revision (2026-11-15). The files
`run_*.py` and `b4*.py` are copies of the files that produced the results; their comments are
the authors' working notes and are left as they were written.

| file | what it holds | name in the manuscript |
|---|---|---|
| `run_serializer_v15.py` | `serialize_v15(state, family)` | Scoped (the serializer of the primary result) |
| `run_serializer_v12.py` | `serialize_v12(state)`: the count line, the forward-path line, the nearest-object line, the line with band and sector of the nearest object of each class | the lines of Scoped |
| `run_serializer_v14.py` | `object_list(state)`: one row per object | the object rows that Scoped writes for counting questions |
| `run_coda_text_v9.py` | `typed_text(state)`; the system prompt and the user prompt of the reader | Flat (the earlier serializer) |
| `run_serializer_dladder.py` | `serialize_dl(state, family, mode)`; mode `d0` is Scoped, `d1` to `d3` change how range is written | the variants with numeric range |
| `b4b_scenegraph_aligned.py`, `b4_scenegraph.py` | the same content as relation triples and as JSON; the object list as triples and as JSON | scene-graph formats |
| `run_pilot_phase0.py` | the two helper functions that the files import (option letters, answer parser) | |
| `c2_rescale_u.py` | sets the image width for a camera other than the CODa camera (see below) | |
| `verify_serializer.py` | the check described next | |
| `serialized_text_confirm.jsonl` | the Scoped and the Flat text of every confirmatory question, written by the check | |

A state is one record of `states/*.json`: a list of objects, each with class, range in meters,
bearing in degrees, image column `u`, and a flag for an uncertain detection. The serializer
reads the state and the question family. It does not read the question, the options, or the
answer.

## Check against the released logs

The runs of the text readers logged, for every question, the number of characters of the text
that the reader received. From the repository root:

    python serializer/verify_serializer.py

serializes the released states again and compares. Result on 2026-11-15: the length is the
same for all 1328 confirmatory questions in the Scoped runs at 0.5B, 1.5B, 3B, and 7B, for all
1366 development questions in the Scoped runs at 3B and 7B, for all 1328 questions in the
Flat runs, and for the runs on ground-truth objects; the five texts of `exemplars/` are
identical character by character; `serialize_dl(..., 'd0')` and `serialize_v15` give the
same text on every question of both banks.

Two further self-checks are part of the original files (give absolute paths, because the
files resolve relative paths against the authors' folder layout):

    python serializer/run_serializer_dladder.py --check --qa <repo>/banks/qa_coda.jsonl --states <repo>/states/states_kf_v9.json
    python serializer/b4b_scenegraph_aligned.py --check --qa <repo>/banks/qa_confirm.jsonl --states <repo>/states/states_confirm_v9.json

## One constant that belongs to the camera

The sector of an object ("on the left side", "in the center", "on the right side") is taken
from its image column and the image width. The width is fixed at 1224 pixels, the CODa
camera (`IMG_W` in `run_serializer_v12.py`; 408 and 816 in `run_coda_text_v9.py`). For
another camera, `c2_rescale_u.py` multiplies the image column of every object by
1224 / (image width) before the state is serialized. The first nuScenes check did not do
this; `amendments/A6_addendum1.md` describes the error and its correction.

## What is still not released

The perception stack (detector training, range cues, fusion), the fine-tuned detector
weights, and the generators of the two CODa question banks. The perceived states that the
serializer read are in `states/`.
