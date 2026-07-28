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
├── calibration/                Committed calibration reference set (small):
│   ├── cal_tarp_spectra.sli / .hdr   ASD cal-tarp reference library
│   ├── CalPanels.pkl                 saved cal-panel ROIs (hsiViewer step in nb 01)
│   ├── panel_low_spectra.npy         intermediate panel spectra
│   ├── panel_mid_spectra.npy
│   └── gain.npy / offset.npy         per-band calibration coefficients (read by nb 02)
└── sample/                     Placeholder for a small raw + reflectance example
                                (see examples/sample/README.md)

data/                           External, gitignored. Full imagery you supply,
                                plus notebook 01's regenerated outputs
                                (data/calibration/*.npy).
```

The committed calibration set is exactly reproducible: re-running notebook 01
from these inputs regenerates `gain`/`offset` bit-for-bit. Notebook 01 writes
its regenerated outputs to `data/calibration/` (gitignored) so a re-run never
clobbers the shipped reference set.

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
