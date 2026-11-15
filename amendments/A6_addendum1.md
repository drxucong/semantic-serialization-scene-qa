# Amendment A6, addendum 1 (written 2026-11-15, before any run on the new nuScenes bank)

## An error in the first nuScenes check, found while preparing the serializer for release

The serializer writes the image sector of an object ("on the left side", "in the center",
"on the right side") from the image column `u` of the object and the image width. The image
width is a constant of the camera. In the source it is fixed at 1224 pixels, the width of the
CODa camera (`IMG_W` in `run_serializer_v12.py`; the thresholds 408 and 816 in
`run_coda_text_v9.py`).

The first nuScenes check (`exp_rev1/c1_nusc/`, the ten scenes of v1.0-mini) passed states
whose `u` is in pixels of the 1600-pixel nuScenes image, and left the constant at 1224. The
question bank of that check defines the sectors by thirds of 1600 pixels. The serializer
therefore placed the sector boundaries at 408 and 816 pixels, and the bank at 533 and 1067.
With the annotated objects as input, the serializer gives a sector that differs from the
gold sector in 11 of the 64 direction questions of that bank. The error works against the
serialized route. It does not affect any result on CODa.

## What is done about it (fixed here, before the runs)

- On nuScenes, the states handed to the serializer carry `u` multiplied by 1224/1600, so
  that the serializer, byte for byte the shipped code, places its boundaries at thirds of the
  nuScenes image. Nothing else in a state is changed. This sets a camera constant; it uses no
  answer and no result.
- New bank (A6, Part 2): criterion E1 and E2 and every serialized arm of Part 2 use these
  states. In addition the serialized route is run once at each size on the states with the
  original `u` (the configuration of the first check), and both are reported.
- First check (v1.0-mini): the serialized arms (perceived objects and annotated objects, 3B
  and 7B) are run again with the corrected states. The manuscript and the Supplement report
  the corrected values, state the error, and give the values of the first run next to them.
  The mini bank is not used for any criterion.
- The response to the reviewers lists the error among the corrections.
