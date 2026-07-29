# Repo audit (alternate) — status against `main`

This is the **shelved** audit of `upwins-hsi-preprocessing` — the fuller, more
aggressive one in `docs/audit_plan.md`, whose Phase 2/3 correctness findings the
owner set aside as out of scope. It is preserved here, unchanged in substance,
but with a **status column checked against the current `main`**.

`main` was cleaned up under a *different, slimmer* audit — `AUDIT_HANDOFF.md`,
which focused on packaging (making the repo run from a clone) and consistency
with the companion `upwins-veg-classifier` repo. That work is real and landed;
several findings below are genuinely closed by it. But the slimmer audit
**deliberately deferred or never covered** most of the correctness (`B*`) and
dead-code (`C*`) findings this alternate plan raised. This document records
exactly which of those still remain, so the decision to keep them out of scope
is made with the current state in view rather than from memory.

- **Audited (original):** `main` @ `be9923e`.
- **Status re-checked against:** `origin/main` @ `b7abc2d` (the post-cleanup head).
- **This document changes no code.** It is a status overlay, and the findings it
  tracks remain out of scope unless the owner says otherwise.

The calibration binaries were re-hashed: `CalPanels.pkl`, `gain.npy`,
`offset.npy`, `panel_low_spectra.npy`, `panel_mid_spectra.npy` and
`cal_tarp_spectra.sli` are **byte-identical** between the audited commit and
`main` (they only moved `data/calibration/ → examples/calibration/`). So every
finding that rests on those bytes — B1's +0.015 bias magnitude, B7's frozen DN,
B8's 98.6 %-saturated mid tarp — holds on `main` exactly as first written.

---

## What `main`'s cleanup changed (structure)

So the line references below resolve, note how the tree moved:

| Was (audited) | Now (`main`) |
|---|---|
| `utils.py` (repo root) | `src/upwins_hsi/utils.py` — **byte-identical**, `git mv` only |
| `hsiViewer/*.py` | `src/hsiViewer/*.py` — byte-identical, `+ __init__.py` |
| `data/calibration/` (committed) | `examples/calibration/` (committed, read-only seed) |
| `data/sample/` | `examples/sample/` (still README-only) |
| `data/README.md` | `docs/data.md` |
| — | `pyproject.toml` (new — `pip install -e .`) |
| notebook 01/02/03 config load | `REPO_ROOT` walk-up added; logic otherwise unchanged |

Notebook 01 now writes its outputs to a gitignored per-collection
`calibration_dir` under `data/`, and notebook 02 / the batch script read from
there, falling back to the committed `examples/calibration/` seed set (with a
warning) when a collection hasn't been calibrated yet.

---

## Status at a glance

Legend: **Resolved** — fixed on `main`. **Partial** — mitigated (usually a
comment or half the surface) but the defect or a piece of it remains.
**Open** — unchanged on `main`.

| # | Finding (short) | Severity | Status on `main` | Slimmer-audit item |
|---|---|---|---|---|
| A1a | Docs promise a from-clone run | Blocking | **Open** (deferred) | P0-2 (deferred, §6b-1) |
| A1b | No sample imagery ships | Blocking | **Open** (deferred) | §6b-1 (deferred) |
| A2 | Config example images don't chain | Blocking | **Resolved** | P1-4 |
| B1 | Offset applied inside the gain | High | **Open** (deferred) | P2-8 (deferred, "do not touch") |
| B2 | No band-grid check when applying calibration | Medium | **Open** | not covered |
| B3 | Notebook 02 cell 9 not idempotent | Medium | **Partial** (comment only) | P2-7 |
| B4 | Dead `use_all_regions`/`thm` branch; unused high tarp | Medium | **Open** | not covered |
| B5 | `loadROIs` throws away the masks it loaded | Medium | **Open** | not covered |
| B6 | Smoothing bleeds into no-data pixels | Low | **Open** | not covered |
| B7 | `CalPanels.pkl` freezes DN → silent re-fit | High | **Open** | not covered |
| B8 | Mid tarp 98.6 % saturated in committed calibration | High | **Open** | not covered (noted "faithful") |
| C1 | `utils.py` 850 lines, ~55 used; `psutil`/`scipy` pins | — | **Open** | not covered |
| C2 | Devcontainer mount dev-specific + wrong workspace | — | **Resolved** | P1-3 |
| C3 | Devcontainer on multi-GB CUDA/TF image | — | **Resolved** | P1-3 |
| C4 | Three unused viewer modules | — | **Open** | not covered |
| C5 | Copy-pasted import block none of the notebooks needs | — | **Open** | not covered |
| C6 | Leftover pre-config instruction cells + typos | — | **Partial** (cells gone, typos remain) | P2-11 |
| C7a | Docs overstate what ships | — | **Partial** (docs moved; claim stands) | P0-2 / P1-10 |
| C7b | Demo run dirties committed files | — | **Resolved** | P1-6 |
| C8 | Developer-local kernel name (`.venv`) | — | **Partial** (01 fixed, 02 not) | not covered |
| C9 | Legacy notebook latent errors | — | **Open** | not covered |
| C10 | Batch script's calibration source changed, undocumented | — | **Resolved** (mostly) | §7 |

**Tally:** Resolved 6 (A2, C2, C3, C7b, C10, and B3/C6 in part) · Partial 4
(B3, C6, C7a, C8) · **Open 13**, of which the ones that change reflectance
numbers or silently mis-calibrate — **B1, B2, B4, B7, B8** — are all still
live.

---

## Findings — detail and evidence on `main`

### A. Blocking

**A1a — docs still promise a from-clone run. Status: Open (deferred).**
`README.md:26-27` still reads: *"A small calibration set ships in
`data/calibration/` so notebook 02 (and the non-interactive cells of 01) run
from a fresh clone."* The slimmer audit deferred this deliberately (P0-2, holding
pattern §6b-1: "leave P0-2's wording exactly as it is today, false claims and
all"). Two notes for whenever it is picked up:
- The path in the claim is now **also stale** — the calibration set moved to
  `examples/calibration/`, so the sentence points at a directory that no longer
  holds it.
- `main` did add a real improvement in this area: the seed-calibration fallback
  means notebook 02's *calibration load* genuinely works from a clone now. But
  "convert to reflectance" still needs a raw cube, which does not ship (A1b), so
  the end-to-end from-clone claim remains false.

**A1b — no sample imagery ships. Status: Open (deferred).**
`examples/sample/` still contains only `README.md`. This is the explicitly
deferred sample-data decision (§6b-1). Unchanged.

**A2 — config example images don't chain. Status: Resolved (P1-4).**
`config.yaml` now uses explicit `*_image` / `*_image_hdr` pairs, and
`reflectance_image` defaults (blank) to `<raw_image>_ref`, so notebook 02's
output feeds notebook 02's viewer cell and notebook 03. The mismatched
`raw_34850_or` vs `raw_4000_or_ref.img` pairing is gone.

### B. Correctness — the heart of what was shelved

**B1 — the offset is applied inside the gain. Status: Open (deferred, P2-8).**
Both consumers still compute `gain·(DN + offset)`:
- `notebooks/02_convert_to_reflectance.ipynb` cell 9:
  `imRef[:, :, i] = (gain[i]*np.squeeze(im.read_band(b) + offset[i])*mask)...`
- `scripts/batch_convert_reflectance.py:98`: identical expression.

The slimmer audit reached the same finding (its P2-8) and **classified it
"DEFERRED — do not touch," a science decision for the owner.** Because
`gain.npy`/`offset.npy` are byte-identical to the audited set, the quantified
effect is unchanged: the intercept (~10⁻² reflectance) is multiplied by a
~10⁻⁴ gain and annihilated, biasing every product by **mean 0.0151 / max 0.0215
reflectance**. This is the one open item that changes output numbers.

**B2 — no band-grid check when applying the calibration. Status: Open.**
Neither consumer guards the coefficient length against the target image's band
count. `main` added a *seed-vs-collection fallback* (notebook 02 cell 3;
`batch_convert_reflectance.py:48-65`) that reports which calibration was used —
useful, but it is not the band-grid guard. A 343-element `gain`/`offset` applied
to a differently-banded cube still misaligns silently or `IndexError`s deep in
the loop. Not covered by the slimmer audit.

**B3 — notebook 02 cell 9 is not idempotent. Status: Partial (P2-7).**
Cell 9 still rebinds in place (`gain = gain[indices]`, `offset = offset[indices]`,
`wl = wl[indices]`). `main` added the P2-7 mitigation — an explanatory comment
warning that re-running the cell without re-running the load cell double-subsets
and raises `IndexError`. The hazard itself is unchanged; the batch script was
already safe (`gain = gain_full[indices]`).

**B4 — dead branch + unused high tarp. Status: Open.**
`notebooks/01_calibrate_cal_panels.ipynb` cell 31 still carries
`use_all_regions = True` with an `else` branch referencing `thm`, which is never
defined (flipping the flag → `NameError`). The high-reflectance tarp is still
loaded and averaged (`asdhm`, cell 23) and plotted (cell 25) but **never enters
the fit** — cell 31 fits only `asdlm` (dark) and `asdmm` (med). The calibration
remains a two-tarp fit through a forced origin that the notebook never states.
Not covered by the slimmer audit.

**B5 — `loadROIs` throws away the masks it loaded. Status: Open.**
`src/hsiViewer/hsi_viewer_ROI.py:523` still assigns
`copy.deepcopy(self.ROImask_empty[:])`, discarding the mask just read (the file
is byte-identical to the original apart from the `git mv`). Re-opening an ROI
file to extend it and saving still writes empty ROIs over the real ones. Not
covered by the slimmer audit.

**B6 — smoothing bleeds into no-data pixels. Status: Open.**
`src/upwins_hsi/utils.py`'s `spatial_smoothing` still divides by `mask_sum`
without re-applying the mask afterward (utils.py byte-identical). The
`smoothing_level: 2` edge-growth and the downstream `im.mask = Arr[:,:,0] != 0`
interaction stand. Not covered by the slimmer audit.

**B7 — `CalPanels.pkl` freezes measured DN. Status: Open.**
Notebook 01 cell 12 still reads panel spectra straight from the pickle
(`cal_panel_rois.df ... .iloc[:, 4:]`); the image opened earlier contributes only
`im.wl`/`nb`. No guard comparing the pickle's wavelength columns to the image's
band axis was added (the alternate plan's Phase 3 proposed exactly that). Re-run
notebook 01 on a new collect of the same sensor without re-drawing the ROIs and
you silently recompute the *previous* collect's calibration. `CalPanels.pkl` is
byte-identical, so this is unchanged. Not covered by the slimmer audit.

**B8 — the mid tarp is 98.6 % saturated. Status: Open.**
Notebook 01 cell 14 still uses `int(0.97 * np.max(panel_mid_spectra))` as the
saturation threshold, and `CalPanels.pkl` / `panel_mid_spectra.npy` are
byte-identical, so the mid panel still collapses from 3048 pixels to **43** (the
dimmest 1.4 %). The committed `gain.npy` still rests on that. The slimmer audit
listed the `0.97` threshold under "verified faithful — do not fix," i.e. it
confirmed the number carried over correctly but did not treat the saturation as a
defect. Not fixable in software regardless (an exposure setting at collection
time); it remains a data-quality flag on the shipped calibration.

### C. Packaging, hygiene, docs

**C1 — `utils.py` dead code + `psutil`/`scipy` pins. Status: Open.**
`src/upwins_hsi/utils.py` is still 850 lines and byte-identical: the broken
geotiff functions, `lda_predict_proba`, and the unused `PdfPages`/`psutil`/
`platform`/`sys`/`math`/`importlib`/`pandas`/`mpatches` imports are all present.
`requirements.txt` still pins `psutil==6.0.0` (for the dead import) and
`scipy==1.13.1` (imported nowhere). The `src/` move did not trim anything. Not
covered by the slimmer audit — note it re-affirmed `utils.py` as "byte-identical,
do not re-audit," which is about *fidelity to the original*, not about the dead
code.

**C2 / C3 — devcontainer. Status: Resolved (P1-3).**
`.devcontainer/devcontainer.json` now uses
`source=${localEnv:HOME}/projects/upwins/data,target=/workspaces/upwins-hsi-preprocessing/data`,
adds `postCreateCommand: python -m pip install ... -e .`, drops
`runArgs: ["--gpus","all"]` (with a comment telling future editors not to re-add
it), and renames to `upwins-hsi-preprocessing`. The `Dockerfile` base is now
`mcr.microsoft.com/devcontainers/python:3.12-bookworm` with `python3-pyqt5` — no
CUDA, no TensorFlow.

**C4 — three unused viewer modules. Status: Open.**
`src/hsiViewer/hsi_viewer.py`, `hsi_viewer_2.py` and `hsi_viewer_array.py` are
all still present and still unimported by any notebook or script here. Not
covered by the slimmer audit.

**C5 — copy-pasted import block. Status: Open.**
Notebook 01 cell 1 still imports `PCA`, `GaussianMixture`,
`mean_squared_error`/`r2_score`, `colors`, `csv`, `time`, `copy`, `importlib`, a
duplicate `import numpy as np`, and `hsi_viewer_layers as hlv` (which it never
calls). Notebooks 02/03 carry their analogous unused blocks. Not covered by the
slimmer audit.

**C6 — leftover instruction cells + typos. Status: Partial (P2-11).**
The contradictory red-HTML "*Change the dir and fname…*" cells (audited notebook
01 cells 3 and 9) are **gone** — this is the slimmer audit's P2-11. But the
typos flagged alongside them remain in cell 14: `saturation_trheshold` and
"*poixels*" (×2). (A different, non-contradictory red-HTML cell — "*Run the cell
with hrv.viewer…*" — still exists; it was not part of this finding.)

**C7a — docs overstate what ships. Status: Partial.**
The data doc moved (`data/README.md → docs/data.md`, P1-10) and is no longer
hidden under the container mount. But the README's from-clone overstatement is
the same sentence as A1a and is still deferred (P0-2).

**C7b — demo run dirties committed files. Status: Resolved (P1-6).**
Notebook 01 now writes `gain`/`offset`/`panel_*` into a **gitignored**
per-collection `calibration_dir` under `data/`; the shipped reference set lives
read-only in `examples/calibration/`. Running the calibration demo no longer
clobbers tracked artifacts.

**C8 — developer-local kernel name. Status: Partial.**
`01_calibrate_cal_panels.ipynb` is now `Python 3`, but
`02_convert_to_reflectance.ipynb` still carries
`"kernelspec": {"display_name": ".venv"}`. (Notebook 03 was already clean.) So
half of the original two-notebook finding remains. Not covered by the slimmer
audit.

**C9 — legacy notebook latent errors. Status: Open.**
`notebooks/legacy/train_apply_lda_model.ipynb` is unchanged: cell 15's
same-quote nested f-string (`print(f'{0}: {['No Data']}')`, Python ≥ 3.12 only),
cell 20's reference to the never-assigned `LDA_result_probs`, and cell 5's
`sli_dir = 'D:/SpectralLibrary'` Windows path all remain. Not covered by the
slimmer audit.

**C10 — batch script's calibration source changed, undocumented. Status:
Resolved (mostly).**
The divergent hardcoded copy (`atmospheric_compensation.py`, with a different
collect's coefficients inline) was dropped — its supersession is reasoned out in
`AUDIT_HANDOFF.md` §7. `batch_convert_reflectance.py` now loads coefficients from
`config.yaml`'s `calibration_dir`/`calibration_seed_dir` with explanatory
comments, and `docs/recording_runbook.md` documents that flow. Residual: the
explicit "these coefficients differ from the pre-handoff inline ones" note lives
only in `AUDIT_HANDOFF.md` (which is marked for deletion before shipping); once
that file is removed, nothing in the shipped tree records the historical change.
Minor.

---

## Bottom line

The packaging half of this alternate plan is largely done — `main` runs from a
clone, the devcontainer is client-safe, the demo no longer dirties tracked
files, and the config chains. **What remains out of scope is the correctness
core:** the reflectance formula (B1), the missing band-grid guard (B2), the
two-tarp/dead-branch calibration structure (B4), the silent DN re-fit (B7), and
the saturated mid tarp (B8) — plus the viewer data-loss bug (B5), the smoothing
edge-bleed (B6), and the dead-code cleanup (C1, C4, C5). None of these was
addressed by the slimmer audit that guided `main`; B1 and B8 were seen there and
consciously left alone. Keeping them shelved is a defensible call — but it is now
a call made against the *current* tree, which is what this document exists to
make possible.
