# Audit Handoff — upwins-hsi-preprocessing

> **Working document, not part of the client deliverable.** Delete this file before
> merging to `main` / shipping.

**Audited:** `upwins-hsi-preprocessing` @ `be9923e` (branch `claude/upwins-hsi-preprocessing-audit-ma57o5`,
identical to `main`) against `research_species_mapping` @ `df69254`.
**Audit was read-only** — no code was changed. Everything below is unimplemented.

**Goal being audited against:** consolidate notebook configuration into one config file,
and make the notebooks straightforward to run from a clone of the repo.

**Verdict:** the science is faithful; the packaging is not runnable. The port preserved the
numerical content essentially perfectly, but moving the notebooks into `notebooks/` broke
every relative path, and the docs promise a from-clone run that the repo cannot currently
deliver.

---

## 1. Verified faithful — do not re-audit, do not "fix"

Confirmed by direct comparison. Treat as settled.

| Item | Result |
|---|---|
| `utils.py` | byte-identical to original |
| `hsiViewer/` (all 5 files) | byte-identical |
| `.devcontainer/` | byte-identical (see P1-3 — this is a *problem*, not a pass) |
| Notebooks 01/02/03 code | logic identical; only edit is hardcoded paths → `CONFIG[...]` lookups |
| `legacy/train_apply_lda_model.ipynb` | all 17 code cells byte-identical to `4. Traing and Apply Model.ipynb` |
| `CalPanels.pkl`, `gain.npy`, `offset.npy`, `panel_*.npy`, `cal_tarp_spectra.sli` | byte-identical to originals |
| `requirements.txt` pins | resolve and install cleanly |

Every numeric constant survived: `0.97` saturation threshold, band `idx = 150`,
`use_all_regions = True`, `smoothing_level = 2`, `bbl_wl_ranges = [[0,425],[750,770],[900,2500]]`.

**The committed calibration set is internally reproducible.** Re-running notebook 01's
arithmetic from the committed inputs regenerates the committed outputs exactly:

```
CalPanels.pkl --(0.97 saturation filter)--> panel_low (2743,343), panel_mid (43,343)   identical=True
panel spectra + tarp library --(per-band 3-point fit)--> gain, offset      max|diff| = 0.000e+00
```

Sensor axis is 343 bands, 399.10–1000.35 nm (VNIR).

---

## 2. P0 — Blocking. The repo does not run from a clone.

### P0-1. Moving notebooks into `notebooks/` broke every path

Jupyter sets the kernel's working directory to the **notebook's own directory**, not the
directory the server was launched from. Confirmed in `jupyter_server`'s
`MappingKernelManager.cwd_for_path`, which resolves the notebook's API path to its
containing folder and passes it as `cwd` to `start_kernel`.

With cwd = `notebooks/`, all three notebooks fail at cell 1:

```
open('config.yaml')          -> FileNotFoundError
import utils                 -> ModuleNotFoundError
from hsiViewer import ...    -> ModuleNotFoundError
```

...and every `data/...` path in `config.yaml` resolves wrong. `CalPanels.pkl` additionally
**cannot unpickle** without `hsiViewer` importable — it deserializes to
`hsiViewer.hsi_viewer_ROI.ROIs_class`, so notebook 01 cell 13 fails for a second reason.

`docs/recording_runbook.md` documents the wrong workaround and must be corrected too:

> `jupyter lab` launched **from the repo root** (so `import utils` / `from hsiViewer import …` resolve)

Launching from the repo root does not have that effect.

**Recommended fix.** Add a bootstrap block to the existing setup cell of each of
`01`, `02`, `03` (and `legacy/`, which is one level deeper). Root-anchored, so it works
whether the kernel starts in `notebooks/` or the repo root:

```python
# --- Resolve the repo root so paths/imports work regardless of kernel cwd ---
import os, sys
from pathlib import Path
_root = Path.cwd()
while not (_root / 'config.yaml').exists() and _root != _root.parent:
    _root = _root.parent
os.chdir(_root)
sys.path.insert(0, str(_root))
```

Place it **above** `import utils` / `from hsiViewer import ...` — those imports fail without it.
Then update the runbook's checklist line.

Alternatives considered: moving the notebooks back to the repo root (simplest, works, but
loses the tidy layout and reverts a deliberate choice); packaging the project properly
(overkill for a handoff repo).

**Acceptance:** from a fresh clone, launch `jupyter lab` from the repo root, open
`notebooks/02_convert_to_reflectance.ipynb`, run the first three cells — config loads,
`utils`/`hsiViewer` import, `gain`/`offset` load with shape `(343,)`.

### P0-2. Docs promise a from-clone run that is not possible

`data/sample/` contains only a `README.md`, but `config.yaml` defaults point into it
(`raw_0_or`, `raw_34850_or`, `raw_4000_or_ref.img`). Two claims are therefore false today:

- `README.md`: "A small calibration set ships in `data/calibration/` so notebook 02
  (and the non-interactive cells of 01) run from a fresh clone."
- `data/README.md`: "Committed calibration set (small), so notebooks 02-03 reproduce"

Shipping calibration alone does **not** make 02 runnable — 02 needs a raw cube to convert.
This is gated on the open decision in §5; fix the claims to match whichever way it goes.

---

## 3. P1 — Fix before client handoff

### P1-3. `.devcontainer/` was copied verbatim and is client-hostile

`README.md` offers it as an install path ("or use the devcontainer"), but:

- `devcontainer.json` bind-mounts a personal path:
  `source=/home/jwvandyke/projects/upwins/data,target=/workspaces/species_mapping/data`.
  The target uses the **old repo name**, so in this repo the data lands outside the
  workspace and `data/` stays empty. It also leaks the maintainer's local filesystem layout.
- `"runArgs": ["--gpus","all"]` hard-requires an NVIDIA GPU; a client without one cannot open it.
- Base image `nvcr.io/nvidia/tensorflow:24.12-tf2-py3` is ~20 GB, for a project that uses no TensorFlow.

**Fix:** drop the bind mount (or make it a documented, commented-out example), drop `--gpus all`,
and move to a plain `python:3.11-slim` base with `python3-pyqt5` installed. Nothing in this
repo needs CUDA or TF.

### P1-4. Default config doesn't chain across notebooks

Notebook 02 converts `raw_image` (`raw_34850_or`) and writes `raw_34850_or_ref`, but
`reflectance_image` defaults to `raw_4000_or_ref.img`. So 02's own viewer cell and all of
notebook 03 read something 02 did not produce. Inherited from the originals (which pointed at
two different collections), but it defeats "straightforward to run from a clone."

**Fix:** make the defaults chain — `reflectance_image` should default to the `_ref` product of
`raw_image`, either by convention in the config or derived in the notebook.

### P1-5. `config.yaml` extension convention is inconsistent

`cal_image` and `raw_image` are extension-less ENVI base names; `reflectance_image` includes
`.img`. Nothing flags the difference. Notebook 02/03 paper over it with
`.rsplit('.', 1)[0] + '.hdr'`, which tolerates both for the header but not for the image file —
a user who follows the other two entries' convention gets a failure inside `spectral.envi.open`.

**Fix:** make all three extension-less and derive `.hdr`/`.img` in code, or document the
difference explicitly in the config comments.

### P1-6. Notebook 01 overwrites tracked, shipped files

Cells 21 and 34 write `panel_low_spectra.npy`, `panel_mid_spectra.npy`, `gain.npy`, `offset.npy`
into `data/calibration/`, which is committed and **not** gitignored (verified with
`git check-ignore`). Running 01 dirties the working tree and clobbers the reference calibration
the repo ships.

**Fix:** write notebook 01 outputs to a separate, gitignored location (e.g.
`data/calibration/generated/` or an `outputs:` block in the config), keeping the shipped
reference set read-only. Note the shipped set is exactly reproducible (§1), so it can always
be regenerated.

---

## 4. P2 — Worth a comment, not a rewrite

### P2-7. `gain = gain[indices]` re-run hazard in notebook 02

Cell 9 rebinds `gain`/`offset`, which cell 3 loaded. Re-running cell 9 without re-running
cell 3 double-subsets and raises `IndexError`. Faithful to the original; add a one-line comment
or reload inside the cell.

This is the same bug that made the original `atmospheric_compensation.py` unusable — see §6.

### P2-8. Inherited math discrepancy in the reflectance formula

Notebook 02 and the batch script apply:

```python
imRef[:, :, i] = (gain[i] * np.squeeze(im.read_band(b) + offset[i]) * mask)   # gain*(counts + offset)
```

Notebook 01 **fits** the coefficients as `reflectance = m·counts + b`, and the original
`old analysis_2025_Greenhead _v2.ipynb` applies `gain[i]*counts + offset[i]` — the form matching
the fit. The source repo disagrees with itself; the port faithfully copied notebook 2's version.

**Not a porting error, and not for a new session to silently "fix."** Flag it to Joe for a
science decision; a client will run this code.

### P2-9. Unverified metadata assertions

These appear only in the new repo — the original has no README or license:

- NSF Grant No. 2319470 (`README.md`, `CITATION.cff`)
- MIT License, "Copyright (c) 2025 upwins"
- the companion repo name `upwins-veg-classifier`

Confirm with Joe before handoff. Do not invent replacements.

---

## 5. Decisions needed from Joe — do not guess

1. **Sample data (his open question).** Either (a) commit a small raw cube + a reflectance
   cube to `data/sample/` so notebooks 02/03 genuinely run from a clone — then the README
   claims become true; or (b) ship no sample data — then P0-2's claims must be rewritten to
   say the user must supply their own imagery and edit `config.yaml` first. Do not leave the
   current mismatch.
2. **P2-8**, the reflectance formula discrepancy.
3. **P2-9**, grant number / license / companion repo name.

---

## 6. Context: `atmospheric_compensation.py` was dropped — this was correct

Recorded because the reasoning is non-obvious and shouldn't be re-litigated.

`scripts/batch_convert_reflectance.py` is a **near-verbatim port of
`atmospheric_compensation.py`**, not new code. Character-identical apart from whitespace: the
bad-band index loop, `nr`/`nc`/`nb` setup, gain/offset subsetting, `imRef` allocation,
`mask = (im.read_band(0) > 0)`, the conversion line, the smoothing loop, the save block with
`md['wavelength']`, and the `gc.collect()`/`time`/`enumerate` batch structure.

The port made two changes, both good:

1. 343 hardcoded gain floats + 343 offset floats and a hardcoded Windows `data_dir` →
   loaded from `config.yaml`. This is exactly the requested consolidation.
2. **It fixed a real bug.** The original rebinds the module-level array inside the per-image
   loop (`gain = gain[indices]`), so on image 2 the already-subset array is indexed with
   full-band indices:

   ```
   image 1: gain now has 281 elements
   image 2: FAIL -> IndexError: index 281 is out of bounds for axis 0 with size 281
   ```

   The original batch script could never process more than one image — in the only mode it
   existed for. The port keeps `gain_full`/`offset_full` intact and derives
   `gain = gain_full[indices]` per image, which is correct. **Keep the fix.**

**Why dropping the file is right:** it is fully superseded; keeping it would ship a second,
divergent copy of the conversion math with a *different* calibration hardcoded into the source,
with nothing telling a client which is authoritative — the exact scattered-config problem the
cleanup targets. Its name is also misleading: it performs empirical-line calibration from
in-scene tarps, not atmospheric compensation.

**One genuine loss to be aware of.** The embedded coefficients are numerically different from
the committed ones (`identical=False` for both gain and offset, both 343 bands). They are a
separate calibration. If that calibration matters, preserve it as a second `.npy` pair under
`data/calibration/` with a provenance note — do not keep the script. It remains recoverable
from `research_species_mapping` history either way.

**Provenance, stated at its true confidence:** `.npy` files store only dtype and shape, and
`CalPanels.pkl` records no source-image field, so neither set is self-identifying.
The committed set is *well-supported* as Morven_20250708: notebook 1's execution counts show
one contiguous run — cell 3 (`dir = 'D:/Site Collections/Morven_20250708'`) at count 65 through
`np.save('gain.npy', gain)` at count 76. Caveat: execution counts reflect the last *save*, so
this assumes the path wasn't edited after running. The embedded set is a *weaker guess* at
Greenhead_May2025, resting only on that file's `data_dir`, which says where the script pointed,
not where its coefficients were fitted. Treat the site names as labels, not facts; the load-bearing
fact is that the two sets differ numerically.

Also dropped and **correctly so**: `analysis_2025_Greenhead_HWref_to_2PNLref.ipynb` and
`old analysis_2025_Greenhead _v2.ipynb` — exploratory research, not pipeline.

---

## 7. Verification recipe

To re-verify after fixes (a throwaway venv is enough; the pinned requirements install clean):

```bash
python3 -m venv /tmp/v && /tmp/v/bin/pip install -r requirements.txt
# P0-1: must now succeed from the notebooks/ directory
cd notebooks && /tmp/v/bin/python -c "
import os,sys; from pathlib import Path
r=Path.cwd()
while not (r/'config.yaml').exists() and r!=r.parent: r=r.parent
os.chdir(r); sys.path.insert(0,str(r))
import yaml, pickle, numpy as np
C=yaml.safe_load(open('config.yaml'))
print('gain', np.load(C['paths']['gain']).shape)
print('rois', pickle.load(open(C['paths']['cal_panel_rois'],'rb')).names)
"
```

PyQt5 imports fine headless with `QT_QPA_PLATFORM=offscreen`; only the interactive viewer
windows in notebooks 01/03 need a real display.

**Suggested order:** P0-1 first (nothing else is testable until notebooks run), then the §5
decisions, then P0-2 to match whatever was decided, then P1.
