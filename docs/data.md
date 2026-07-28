# Data

Large imagery is **not** committed. Everything under `data/` is external —
downloaded, bind-mounted, or written by a run — and the whole directory is
gitignored. A fresh clone has no `data/` at all; it is created by the
devcontainer mount, or by the notebooks when they write their outputs.

What the repo *does* ship for a run lives outside `data/`, under `examples/`
(see `examples/README.md`), so the devcontainer mount can never hide it.

## Expected layout

```
examples/
├── calibration/                Shipped SEED calibration (committed, read-only):
│   ├── cal_tarp_spectra.sli / .hdr   ASD cal-tarp reference library (fit input)
│   ├── CalPanels.pkl                 saved cal-panel ROIs (fit input)
│   ├── gain.npy / offset.npy         seed coefficients -- notebook 02's fallback
│   └── panel_low/mid_spectra.npy     intermediate panel spectra (record)
└── sample/                     Placeholder for a small raw + reflectance example
                                (see examples/sample/README.md)

data/                           External, gitignored. Full imagery you supply,
└── calibration/<collection>/   plus each collection's calibration bundle,
                                written by notebook 01 (gain.npy, offset.npy,
                                panel_*_spectra.npy) and read by notebook 02.
```

Each collection keeps its own calibration bundle. Notebook 01 writes gain/offset
(and the panel-spectra intermediates) into `calibration_dir`
(`data/calibration/<collection>/`, gitignored), and notebook 02 and the batch
script read gain/offset from there — so re-calibrating one collection never
clobbers another's. Until a collection has been calibrated, they fall back to
the shipped seed set in `examples/calibration/` and say so, so the repo still
runs from a fresh clone. The seed set is exactly reproducible: re-running
notebook 01 on its inputs regenerates `gain`/`offset` bit-for-bit.

## Where the data comes from

Raw ENVI cubes come off the hyperspectral sensor (no extension on the image
file, e.g. `raw_0_or` + `raw_0_or.hdr`). Reflectance products are written by
notebook 02 / the batch script with a `.img` extension
(`raw_34850_or_ref.img` + `.hdr`). The reflectance images and ROI pickles this
repo produces feed the companion **`upwins-veg-classifier`** training notebook.

## Getting the full dataset

The full imagery is distributed separately (too large for git).

> **TODO (data owner):** add the download link or DOI here. Until this is
> filled in, a fresh clone has no way to obtain the full imagery.

After downloading, drop the files under `examples/sample/` for a runnable demo,
or edit the paths in `config.yaml` to point at wherever you keep them.

## The devcontainer mount

`.devcontainer/devcontainer.json` bind-mounts an external data directory onto
`data/` inside the container, so full imagery can live outside the repo:

```
source=${localEnv:HOME}/projects/upwins/data  ->  /workspaces/upwins-hsi-preprocessing/data
```

**The host path is hardcoded.** If your data is not at `~/projects/upwins/data`,
edit that `mounts` line before opening the container — Docker silently creates
an empty directory for a source path that does not exist, and the notebooks then
fail with confusing missing-file errors rather than saying the mount was wrong.

Because nothing the repo ships lives under `data/`, the mount hides nothing:
the shipped calibration set and examples stay in `examples/`, outside the mount.
