#!/usr/bin/env python3
"""
batch_convert_reflectance.py
============================

Batch companion to notebook 02: convert every raw image in a directory to
reflectance using the gain/offset from notebook 01, then bad-band removal and
spatial smoothing. Reflectance images are written next to each input as
`<name>_ref.img/.hdr`.

Paths and parameters come from config.yaml (run from the repo root):
    python scripts/batch_convert_reflectance.py
"""
import os
import gc
import time
import numpy as np
import spectral
import yaml

import utils  # spatial_smoothing

# ---- Configuration ----
with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

data_dir = CONFIG["batch"]["input_dir"]
ends_with_text = CONFIG["batch"]["ends_with"]
smoothing_level = CONFIG["reflectance"]["smoothing_level"]
bbl_wl_ranges = CONFIG["reflectance"]["bbl_wl_ranges"]

# Calibration coefficients from notebook 01 (loaded once, subset per image).
gain_full = np.load(CONFIG["paths"]["gain"])
offset_full = np.load(CONFIG["paths"]["offset"])

# ---- Collect the images to process ----
fnames = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
          if f.endswith(ends_with_text)]
print(f"Found {len(fnames)} image(s) ending with '{ends_with_text}' in {data_dir}")

for count, file_name in enumerate(fnames, start=1):
    gc.collect()
    start_time = time.time()
    print(f"\nProcessing image {count} of {len(fnames)}: {file_name}")

    fname_hdr = file_name + ".hdr"
    im = spectral.envi.open(fname_hdr, file_name)
    wl = np.asarray(im.bands.centers)

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
    for i, b in enumerate(indices):
        imRef[:, :, i] = (gain[i] * np.squeeze(im.read_band(b) + offset[i]) * mask).astype(np.float32)

    for i in range(smoothing_level):
        print(f"Smoothing, iteration {i + 1}.")
        imRef = utils.spatial_smoothing(imRef, mask=mask).astype(np.float32)

    md = im.metadata
    md["wavelength"] = [str(w) for w in wl_good]
    out_hdr = file_name + "_ref.hdr"
    print(f"Saving {out_hdr}")
    spectral.envi.save_image(out_hdr, imRef, metadata=md, force=True)
    print(f"Done in {time.time() - start_time:.1f}s")
