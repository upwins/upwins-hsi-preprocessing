# Data

**Nothing ships in this repo** — no imagery and no calibration. Everything a run
needs is supplied by you and lives under `data/`, which is gitignored in full; a
fresh clone has no `data/` at all. You point `config.yaml` at your files (under
`data/`, or wherever you keep them).

## What you supply

Per data collection:

- **Raw ENVI cubes** (`.img`/no-extension + `.hdr`) whose headers carry the band
  centers:
  - one raw cube containing the calibration tarps (notebook 01 → `cal_image`),
  - one or more raw cubes to convert to reflectance (notebook 02 / the batch
    script → `raw_image` / `batch.input_dir`).
- **The ASD cal-tarp reference library** (`cal_tarp_spectra.sli` + `.hdr`) — the
  tarps' known reflectance (notebook 01 → `cal_library_sli` / `cal_library_hdr`).
- **The cal-panel ROIs** (`CalPanels.pkl`) — drawn on the cal image in notebook
  01's viewer cell and saved (→ `cal_panel_rois`). **Draw these fresh for every
  collection:** the pickle stores measured DN, not a reusable region, so reusing
  another collection's pickle silently re-fits that collection's tarps.

## What the notebooks produce

Notebook 01 writes each collection's calibration bundle — `gain.npy`,
`offset.npy`, and the `panel_*_spectra.npy` intermediates — into that
collection's `calibration_dir` (under `data/`, gitignored). Notebook 02 and the
batch script read `gain.npy`/`offset.npy` back from there, so re-calibrating one
collection never clobbers another's.

Reflectance products are written next to the raw cube with a `.img` extension
(`<raw_image>_ref.img` + `.hdr`). The reflectance images and ROI pickles this
repo produces feed the companion **`upwins-veg-classifier`** training notebook.

## Suggested layout

```
data/                            External, gitignored -- you create this.
└── <collection>/                   <- config.yaml's `collection_dir`
    ├── raw_0_or  / .hdr             raw cube with the cal panels (notebook 01)
    ├── raw_34850_or / .hdr          raw cube to convert (notebook 02)
    ├── cal_tarp_spectra.sli / .hdr  ASD cal-tarp reference library
    ├── CalPanels.pkl                cal-panel ROIs (draw per collection)
    └── calibration/                 gain.npy, offset.npy, panel_*_spectra.npy
                                     written by notebook 01, read by notebook 02
```

`config.yaml`'s placeholders already follow this shape under
`data/my_collection/`; edit them for your collection name and paths.

`collection_dir` names that per-collection directory (default
`data/my_collection`). Notebook 03's ROI Save/Load dialogs open there, so
training-ROI pickles land beside the collection's imagery. YAML has no variable
substitution, so the other paths spell the directory out in full — change them
alongside `collection_dir`.

## Getting the full dataset

The full imagery is distributed separately (too large for git).

> **TODO (data owner):** add the download link or DOI here. Until this is
> filled in, a fresh clone has no way to obtain the imagery.

After downloading, edit the paths in `config.yaml` to point at wherever you keep
the files.

## The devcontainer mount

`.devcontainer/devcontainer.json` bind-mounts an external data directory onto
`data/` inside the container, so imagery can live outside the repo:

```
source=${localEnv:HOME}/projects/upwins/data  ->  /workspaces/upwins-hsi-preprocessing/data
```

**The host path is hardcoded.** If your data is not at `~/projects/upwins/data`,
edit that `mounts` line before opening the container — Docker silently creates an
empty directory for a source path that does not exist, and the notebooks then
fail with confusing missing-file errors rather than saying the mount was wrong.
