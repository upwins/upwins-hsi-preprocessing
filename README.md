# UPWINS Hyperspectral Preprocessing

Turn raw hyperspectral imagery into labeled training data for the
`upwins-veg-classifier`. Three steps:

1. **Calibrate** — empirical-line calibration from in-scene tarps → per-band gain/offset.
2. **Convert to reflectance** — apply the calibration, drop bad bands, smooth, and save.
3. **Create training ROIs** — draw labeled regions on the reflectance image; these `.pkl`
   ROIs feed the classifier's training notebook.

This is the **first half** of the UPWINS pipeline; training and prediction live in the
companion `upwins-veg-classifier` repo.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate     # or use the devcontainer
pip install -r requirements.txt
pip install -e .                                      # makes `upwins_hsi` importable
jupyter lab                                            # launch from the repo root or notebooks/
```

> The devcontainer does the two install steps for you.

> Notebooks 01 and 03 use the interactive **hsiViewer** (PyQt) to draw ROIs, and
> notebook 02 ends with an optional viewer cell, so all three need a
> desktop/display session. **No imagery or calibration ships in this repo** —
> you supply your own (see [Data](#data)), so the notebooks do not run from a bare
> clone.

| Notebook | What it does |
|----------|--------------|
| `notebooks/01_calibrate_cal_panels.ipynb` | Draw ROIs on the cal tarps and fit per-band gain/offset. |
| `notebooks/02_convert_to_reflectance.ipynb` | Apply the calibration to a raw image → reflectance. |
| `notebooks/03_create_training_rois.ipynb` | Draw labeled training ROIs on a reflectance image. |
| `scripts/batch_convert_reflectance.py` | Convert a whole directory of images to reflectance in one run. |

Each code cell has a short markdown cell above it explaining what it does, so
the notebooks double as a written walkthrough. If you're recording or following
the tutorial videos, `docs/recording_runbook.md` is the high-level guide.

## Layout

```
config.yaml              All paths and parameters live here.
notebooks/               The three deliverable notebooks (run in order).
src/upwins_hsi/          Importable support code (installed via `pip install -e .`).
src/hsiViewer/           Interactive PyQt viewer + ROI tools. Import path kept as `hsiViewer`
                         so ROI/cal-panel pickles (recorded as hsiViewer.hsi_viewer_ROI) load.
scripts/                 Batch reflectance conversion.
data/                    Not committed -- your imagery, calibration inputs, and run
                         outputs go here; see docs/data.md.
docs/                    Data guide and recording runbook.
```

## Data

**Nothing ships in this repo** — no imagery, no calibration. You supply your own
raw cubes, the ASD cal-tarp library, and the cal-panel ROIs, and notebook 01
fits the per-band `gain`/`offset` for each collection. All paths and parameters
are in `config.yaml`; point the image pairs and calibration inputs at your data
(the placeholders sit under `data/`, which is gitignored). See `docs/data.md`
for the expected layout and `docs/recording_runbook.md` for the recording guide.

### If you use the devcontainer

`.devcontainer/` bind-mounts an external data directory over the repo's `data/`:

```
source=${localEnv:HOME}/projects/upwins/data  ->  /workspaces/upwins-hsi-preprocessing/data
```

**The host path is hardcoded.** Edit that `mounts` line in
`.devcontainer/devcontainer.json` if your data is not at `~/projects/upwins/data`,
or Docker silently creates an empty directory and the notebooks fail with
missing-file errors. See `docs/data.md`.

## Acknowledgment

This material is based upon work supported by the National Science Foundation
under Grant No. 2319470.
