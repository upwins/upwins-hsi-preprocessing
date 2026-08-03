#!/usr/bin/env python3
"""
batch_convert_reflectance.py
============================

Batch companion to notebook 02: convert every raw image in a directory to
reflectance using the gain/offset from notebook 01, then bad-band removal and
spatial smoothing. Reflectance images are written next to each input as
`<name>_ref.img/.hdr`, where `<name>` drops any ENVI data extension: a
`raw_5.bin` input yields `raw_5_ref.img`, not `raw_5.bin_ref.img`.

Paths and parameters come from config.yaml. The script resolves config.yaml
(and the paths inside it) from the repo root, so it runs from any directory:
    python scripts/batch_convert_reflectance.py
"""
import os
import gc
import time
from pathlib import Path
import numpy as np
import spectral
import yaml

from upwins_hsi import utils  # spatial_smoothing, ENVI path helpers

# ---- Configuration ----
# config.yaml lives at the repo root and its paths are relative to it. Walk up
# from this script's location to find the repo root, then absolutize every path
# in the `paths` section against it.
REPO_ROOT = Path(__file__).resolve().parent
while not (REPO_ROOT / "config.yaml").exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent
with open(REPO_ROOT / "config.yaml") as f:
    CONFIG = yaml.safe_load(f)
for _key, _val in CONFIG.get("paths", {}).items():
    if isinstance(_val, str):
        CONFIG["paths"][_key] = str(REPO_ROOT / _val)

# batch.input_dir is a path (absolutize it); batch.ends_with is a filename
# suffix, NOT a path, so it must be left alone.
data_dir = str(REPO_ROOT / CONFIG["batch"]["input_dir"])
ends_with_text = CONFIG["batch"]["ends_with"]
smoothing_level = CONFIG["reflectance"]["smoothing_level"]
bbl_wl_ranges = CONFIG["reflectance"]["bbl_wl_ranges"]

# Calibration coefficients from notebook 01 (loaded once, subset per image).
# Read this collection's bundle from calibration_dir. Nothing ships in the repo:
# run notebook 01 for THIS collection first so calibration_dir holds
# gain.npy/offset.npy. Never point calibration_dir at another collection's
# bundle -- gain/offset absorb that collection's illumination and exposure and
# are not valid for another.
_cal_dir = CONFIG["paths"]["calibration_dir"]
_gain = os.path.join(_cal_dir, "gain.npy")
_offset = os.path.join(_cal_dir, "offset.npy")
print(f"Using calibration from: {_cal_dir}")
gain_full = np.load(_gain)
offset_full = np.load(_offset)

# ---- Collect the images to process ----
# Skip this script's own products. `_ref` outputs land next to their inputs, so
# an `ends_with` that also matches them (e.g. ".img") would re-convert them on
# the next run and write <name>_ref_ref.img, applying the calibration twice.
fnames = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
          if f.endswith(ends_with_text)
          and not utils.envi_basename(f).endswith("_ref")
          and not f.endswith(".hdr")]
print(f"Found {len(fnames)} image(s) ending with '{ends_with_text}' in {data_dir}")

for count, file_name in enumerate(fnames, start=1):
    gc.collect()
    start_time = time.time()
    print(f"\nProcessing image {count} of {len(fnames)}: {file_name}")

    # Accept either header convention: <file>.hdr or <base>.hdr. This script
    # used to assume the first, while config.yaml's image pairs use the second,
    # so a .bin collection one entry point accepted the other rejected.
    fname_hdr = utils.find_envi_header(file_name)
    im = spectral.envi.open(fname_hdr, file_name)
    wl = np.asarray(im.bands.centers)

    # Band-grid guard (B2): coefficients are position-indexed and valid only for
    # the band configuration they were fit on. Skip any image whose band count
    # does not match, rather than misaligning silently or IndexError-ing below.
    # (A batch skips the offending image and keeps going instead of aborting.)
    if len(gain_full) != len(wl):
        print(f"  SKIP: calibration has {len(gain_full)} bands but this image "
              f"has {len(wl)}; re-run notebook 01 for this collection.")
        continue

    # Good-band indices (outside the bad-band ranges)
    indices = []
    for i in range(len(wl)):
        if not any(lo < wl[i] < hi for lo, hi in bbl_wl_ranges):
            indices.append(int(i))
    indices = np.asarray(indices, dtype=np.int16)

    nr, nc, nb = im.nrows, im.ncols, len(indices)
    gain = gain_full[indices]
    offset = offset_full[indices]
    wl_good = wl[indices]

    imRef = np.zeros((nr, nc, nb), dtype=np.float32)
    mask = (im.read_band(0) > 0).astype(np.float32)

    print("Converting to reflectance.")
    # reflectance = gain*counts + offset, matching notebook 01's empirical-line
    # fit (LinearRegression with fit_intercept=True). The * mask is applied
    # OUTSIDE the affine term so no-data pixels stay exactly 0 (offset must not
    # leak into them), preserving the band0>0 mask convention used downstream.
    for i, b in enumerate(indices):
        imRef[:, :, i] = ((gain[i] * np.squeeze(im.read_band(b)) + offset[i]) * mask).astype(np.float32)

    for i in range(smoothing_level):
        print(f"Smoothing, iteration {i + 1}.")
        imRef = utils.spatial_smoothing(imRef, mask=mask).astype(np.float32)

    # Same header handling as notebook 02, which this script is the batch
    # companion to: copy rather than alias the raw metadata, and subset EVERY
    # per-band key (wavelength, fwhm, band names, bbl are positional lists of
    # one entry per band, so each must stay exactly `bands` long). Drop
    # `default bands`, whose band NUMBERS are renumbered by the bad-band removal.
    md = dict(im.metadata)
    for _key in ("fwhm", "band names", "bbl"):
        _vals = md.get(_key)
        if _vals is None:
            continue
        if len(_vals) == len(wl):
            md[_key] = [_vals[b] for b in indices]
        else:
            print(f"  note: header key '{_key}' has {len(_vals)} entries for "
                  f"{len(wl)} bands, so it was already inconsistent; left as is.")
    md["wavelength"] = [str(w) for w in wl_good]
    md.pop("default bands", None)
    out_hdr, _ = utils.reflectance_paths(file_name)
    print(f"Saving {out_hdr}")
    spectral.envi.save_image(out_hdr, imRef, metadata=md, force=True)
    print(f"Done in {time.time() - start_time:.1f}s")
