# Recording Runbook — Preprocessing Tutorial (Video 1)

A high-level guide to follow **while recording** the first video: raw
hyperspectral imagery → reflectance → labeled training ROIs. The detailed
narration is already in the notebooks (the markdown cell above each code cell is
your script); this runbook gives the running order, the beats to emphasize, and
the gotchas.

> **Scope.** This is **Video 1** of the pipeline. It ends by handing labeled ROIs
> and reflectance imagery to the **`upwins-veg-classifier`** repo, which is
> **Video 2** (training + prediction).

> **Interactive steps.** Notebooks 01 and 03 use the **hsiViewer** (a PyQt
> window) to draw ROIs — those are live, on-camera demonstrations, not
> run-all-cells steps. Have your mouse ready to draw.

---

## 0. Before you hit record

- [ ] `pip install -r requirements.txt && pip install -e .` in a clean env (or open the devcontainer). PyQt5 + pyqtgraph must work — you need a desktop/display session for the viewer.
- [ ] Set `config.yaml` for your **real** collection (see *config.yaml in brief* below): the `cal_image` and `raw_image` pairs, and `calibration_dir`.
- [ ] Confirm the data is reachable: the raw cal-panel image and a raw image to convert. (nb 03 opens the reflectance image nb 02 produces.)
- [ ] `jupyter lab` — with the editable install above, imports (`from upwins_hsi import utils` / `from hsiViewer import …`) resolve whether you launch from the repo root or from `notebooks/`. Restart kernels so cell numbers are clean.

### config.yaml in brief (worth narrating)

All paths and parameters live in `config.yaml` — you edit this, never the
notebook code. On camera, point out:

- **Image pairs.** Each ENVI cube is a `*_image` + `*_image_hdr` pair naming the
  same file (raw cubes have no extension; `_ref` products end in `.img`). Set
  `cal_image` for nb 01 and `raw_image` for nb 02.
- **`calibration_dir`.** Where nb 01 writes this collection's `gain`/`offset` and
  where nb 02 reads them back — one folder per collection, so runs never collide.
  Nothing ships, so nb 02 needs nb 01 to have run for this collection first.
- **`reflectance_image` left blank** = nb 02's own `<raw_image>_ref` output, used
  automatically by nb 02's viewer and nb 03. Only set it to draw ROIs on a
  reflectance image you didn't just produce.
- Paths are relative to the repo root and resolve whether you launch Jupyter from
  the repo root or `notebooks/`.

---

## 1. Part 1 — Calibrate  →  `notebooks/01_calibrate_cal_panels.ipynb`

Empirical-line calibration from in-scene tarps. Beats to hit:

| Section | Say / show |
|---|---|
| Open cal-panel image + tarp library | We calibrate using tarps of known reflectance visible in the scene. |
| **Draw ROIs on the tarps** *(interactive)* | Demo drawing ROIs on the low and mid tarps in the hsiViewer, then save. |
| Remove saturated pixels, average | Clean the panel spectra before fitting. |
| Plot panel + ASD reference spectra | Compare measured counts to known reflectance. |
| **Fit gain/offset for every band** | This is the empirical line: reference reflectance vs. measured counts, per band. Show the gain/offset curves. |
| Save calibration | `gain.npy` / `offset.npy` written into `calibration_dir` — the hand-off to Part 2. |

**Expected result:** `gain.npy` and `offset.npy` (plus the panel-spectra intermediates) written into `calibration_dir` — e.g. `data/<collection>/calibration/`.

---

## 2. Part 2 — Convert to reflectance  →  `notebooks/02_convert_to_reflectance.ipynb`

| Section | Say / show |
|---|---|
| Load calibration | Reuse the gain/offset from Part 1 (read from `calibration_dir`). Run nb 01 for this collection first — nothing ships, so there is no fallback. |
| Open a raw image | Point out the smoothing level and bad-band ranges come from the config. |
| **Convert to reflectance** | Bad-band removal → per-band gain/offset → mask → spatial smoothing → save. This is the core transform. |
| *(optional)* open reflectance in the viewer | Inspect a few pixel spectra to confirm they look like reflectance. |

**Expected result:** a `<name>_ref` reflectance image written next to the raw one.
*Mention* `scripts/batch_convert_reflectance.py` for converting a whole folder at once.

---

## 3. Part 3 — Create training ROIs  →  `notebooks/03_create_training_rois.ipynb`

| Section | Say / show |
|---|---|
| Open the reflectance image | The image we just produced. |
| **Draw labeled ROIs** *(interactive)* | Demo drawing ROIs on vegetation, **naming them with the library convention** (e.g. `Ammo_bre_...`). Save them. |

**Expected result:** labeled ROI `.pkl` files — the input to Video 2.

---

## 4. The hand-off (bridge to Video 2)

Close by showing that the reflectance image **and** the labeled ROIs now feed the
`upwins-veg-classifier` repo: its training notebook loads these ROIs (via the
bundled `hsiViewer` shim) alongside the spectral library to train the model.
That's where Video 2 picks up.

---

## 5. Talking points worth landing

- **Why calibrate with in-scene tarps:** it corrects each collection's illumination/sensor response empirically — no atmospheric model needed.
- **Why smoothing + bad-band removal:** cleaner spectra, fewer noise-dominated bands.
- **Why the naming convention matters:** ROI names carry the labels the classifier trains on; mismatched names = mislabeled training data.

---

## 6. After recording

- Tag the state you filmed:
  ```bash
  git tag -a v1.0.0-tutorial -m "State used in the tutorial videos"
  git push origin v1.0.0-tutorial
  ```
- Pinned clone command for viewers:
  ```bash
  git clone --branch v1.0.0-tutorial https://github.com/upwins/upwins-hsi-preprocessing
  ```
- Export the notebooks you filmed (`jupyter nbconvert --to html notebooks/*.ipynb`)
  if you want a static companion to the video. Do not pass `--execute` here — the
  hsiViewer cells need a live desktop session — and regenerate the exports rather
  than committing them, so they cannot drift out of step with the notebooks.
