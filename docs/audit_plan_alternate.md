# Repo audit (alternate) — status against `main`

This is the **status record of the shelved, fuller audit** of
`upwins-hsi-preprocessing` — the more aggressive pass whose Phase 2/3
correctness findings the owner set aside as out of scope. Every finding it
raised (the A/B/C items below) is restated here with its own evidence, now
carrying a **status column checked against the current `main`**, so this
document stands on its own.

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
- **Re-checked again (2026-07-30):** branch `claude/audit-repo-cleanup-f80o10` @
  `2c218cf`, where the owner's handoff decisions were implemented (see the update box
  below). Several findings this document tracked as Open/Deferred are now closed.

> **Update — 2026-07-30, branch `claude/audit-repo-cleanup-f80o10`** (two passes,
> same day). The owner resolved the outstanding decisions and then asked for the
> remaining correctness/dead-code items. The change that reframes the most findings:
> **the repo now ships no imagery and no calibration, and is not expected to run from
> a clone.** `examples/` was deleted in full — the committed calibration set
> (`CalPanels.pkl`, `gain.npy`, `offset.npy`, `panel_*_spectra.npy`) *and* the
> cal-tarp library (`cal_tarp_spectra.sli/.hdr`).
>
> - **First pass:** **B1 fixed** (`gain*counts + offset`), **B5 fixed** (`loadROIs`
>   keeps the loaded mask), **C6 fixed** (typos), **C9 resolved** (legacy notebook
>   deleted), **A1a/A1b/C7a resolved** (docs honest; nothing ships), **B7 surface
>   reduced**, **B8 removed with the artifacts**.
> - **Second pass:** **B2 fixed** (band-grid guard in nb02 + batch), **B4 fixed**
>   (dead branch removed; high tarp kept for context by choice), **B6 fixed**
>   (smoothing re-applies the mask), **C1 fixed** (`utils.py` trimmed to 64 lines,
>   `psutil`/`scipy` dropped), **C5 fixed** (import blocks trimmed), **C8 fixed**
>   (nb02 kernelspec).
>
> **Only one finding remains open: C4** (three unused viewer modules), plus B3
> (idempotency, comment-only) and B7 (mitigated, no hard guard) still Partial. The
> Status-at-a-glance table and per-finding notes below carry a **(07-30)** marker
> where the status changed; the original analysis is retained as the record.

The calibration binaries were re-hashed *at the earlier re-check*: `CalPanels.pkl`,
`gain.npy`, `offset.npy`, `panel_low_spectra.npy`, `panel_mid_spectra.npy` and
`cal_tarp_spectra.sli` were **byte-identical** between the audited commit and `main`
(they only moved `data/calibration/ → examples/calibration/`). **As of 2026-07-30
those files no longer exist in the repo** — `examples/` was deleted — so the findings
that rested on their bytes (B1's +0.015 bias magnitude, B7's frozen DN, B8's 98.6 %
saturation) describe data that is no longer shipped; see each finding's 2026-07-30 note.

---

## What `main`'s cleanup changed (structure)

So the line references below resolve, note how the tree moved:

| Was (audited) | Now (`main`) |
|---|---|
| `utils.py` (repo root) | `src/upwins_hsi/utils.py` — **byte-identical**, `git mv` only |
| `hsiViewer/*.py` | `src/hsiViewer/*.py` — byte-identical, `+ __init__.py` |
| `data/calibration/` (committed) | `examples/calibration/` (committed seed) → **deleted 2026-07-30** (nothing ships) |
| `data/sample/` | `examples/sample/` (README-only) → **deleted 2026-07-30** |
| `data/README.md` | `docs/data.md` |
| — | `pyproject.toml` (new — `pip install -e .`) |
| notebook 01/02/03 config load | `REPO_ROOT` walk-up added; logic otherwise unchanged |

Notebook 01 writes its outputs to a gitignored per-collection `calibration_dir`
under `data/`, and notebook 02 / the batch script read from there. **On `main` this
had a fallback to the committed `examples/calibration/` seed set; on branch
`claude/audit-repo-cleanup-f80o10` (2026-07-30) `examples/` was deleted and the seed
fallback removed** — nothing ships, so notebook 01 must be run for a collection
before notebook 02 can read its calibration. `config.yaml` now points every input at
user-supplied `data/<collection>/` placeholders.

---

## Status at a glance

Legend — ✅ **Resolved** · 🟡 **Partial** (mitigated — a comment or half the surface
— but a piece remains) · ⛔ **Deferred** (a live owner decision) · 🔲 **Open** (a
defect still standing). The **Status** column is now as of branch
`claude/audit-repo-cleanup-f80o10` @ `2c218cf` (2026-07-30); rows changed in that pass
are marked **(07-30)**.

| # | Finding (short) | Severity | Status (as of 2026-07-30) | Slimmer-audit item |
|---|---|---|---|---|
| A1a | Docs promise a from-clone run | Blocking | ✅ **Resolved (07-30)** — docs honest; nothing ships | P0-2 (§6b-1) |
| A1b | No sample imagery ships | Blocking | ✅ **Resolved (07-30)** — decided: no data ships | §6b-1 |
| A2 | Config example images don't chain | Blocking | ✅ **Resolved** | P1-4 |
| B1 | Offset applied inside the gain | High | ✅ **Fixed (07-30)** — `gain*counts + offset` | P2-8 |
| B2 | No band-grid check when applying calibration | Medium | ✅ **Fixed (07-30)** — guard in nb02 + batch | not covered |
| B3 | Notebook 02 cell 9 not idempotent | Medium | 🟡 **Partial** (comment only) | P2-7 |
| B4 | Dead `use_all_regions`/`thm` branch; unused high tarp | Medium | ✅ **Resolved (07-30)** — dead branch removed, fit commented as two-tarp; high tarp kept for context by choice | not covered |
| B5 | `loadROIs` throws away the masks it loaded | Medium | ✅ **Fixed (07-30)** | not covered |
| B6 | Smoothing bleeds into no-data pixels | Low | ✅ **Fixed (07-30)** — mask re-applied after averaging | not covered |
| B7 | `CalPanels.pkl` freezes DN → silent re-fit | High | 🟡 **Mitigated (07-30)** — no shipped pickle, seed fallback gone, reminder added; no hard guard | not covered |
| B8 | Mid tarp 98.6 % saturated in committed calibration | High | ✅ **Moot (07-30)** — committed calibration removed | not covered (was "faithful") |
| C1 | `utils.py` 850 lines, ~55 used; `psutil`/`scipy` pins | — | ✅ **Fixed (07-30)** — trimmed to 64 lines; `psutil`/`scipy` dropped | not covered |
| C2 | Devcontainer mount dev-specific + wrong workspace | — | ✅ **Resolved** | P1-3 |
| C3 | Devcontainer on multi-GB CUDA/TF image | — | ✅ **Resolved** | P1-3 |
| C4 | Three unused viewer modules | — | 🔲 **Open** — the one remaining item | not covered |
| C5 | Copy-pasted import block none of the notebooks needs | — | ✅ **Fixed (07-30)** — each notebook's imports trimmed | not covered |
| C6 | Leftover pre-config instruction cells + typos | — | ✅ **Resolved (07-30)** — typos fixed | P2-11 |
| C7a | Docs overstate what ships | — | ✅ **Resolved (07-30)** — docs honest | P0-2 / P1-10 |
| C7b | Demo run dirties committed files | — | ✅ **Resolved** | P1-6 |
| C8 | Developer-local kernel name (`.venv`) | — | ✅ **Fixed (07-30)** — nb02 kernelspec set to Python 3 | not covered |
| C9 | Legacy notebook latent errors | — | ✅ **Resolved (07-30)** — notebook deleted | not covered |
| C10 | Batch script's calibration source changed, undocumented | — | ✅ **Resolved** (mostly) | §7 |

**Tally as of 2026-07-30** (22 findings, after both passes on branch
`claude/audit-repo-cleanup-f80o10`): ✅ Resolved 19 (A1a, A1b, A2, B1, B2, B4, B5,
B6, B8, C1, C2, C3, C5, C6, C7a, C7b, C8, C9, and C10 mostly — B8 by removal) ·
🟡 Partial/Mitigated 2 (B3 idempotency comment-only, B7 mitigated with no hard
guard) · 🔲 Open 1 (**C4** — three unused viewer modules) · ⛔ Deferred 0. Every
reflectance-affecting or silently-miscalibrating item is now closed: **B1 fixed**,
**B2 guarded**, **B6 fixed**, **B8 moot**, **B7 mitigated**. The lone open item, C4,
is cosmetic dead code left in place.

> **Earlier tally (first pass, same day):** ✅ 13 · 🟡 3 (B3, B7, C8) · 🔲 6 (B2, B4,
> B6, C1, C4, C5). The second pass then fixed B2, B4, B6, C1, C5 and C8.
>
> **Original tally (as of `main`, pre-2026-07-30):** ✅ Resolved 5 (A2, C2, C3, C7b,
> C10) · 🟡 Partial 4 (B3, C6, C7a, C8) · ⛔ Deferred 3 (A1a, A1b, B1) · 🔲 Open 10
> (B2, B4, B5, B6, B7, B8, C1, C4, C5, C9).

> **Original tally (as of `main`, pre-2026-07-30):** ✅ Resolved 5 (A2, C2, C3, C7b,
> C10) · 🟡 Partial 4 (B3, C6, C7a, C8) · ⛔ Deferred 3 (A1a, A1b, B1) · 🔲 Open 10
> (B2, B4, B5, B6, B7, B8, C1, C4, C5, C9).

---

## Findings — detail and evidence on `main`

### A. Blocking

**A1a — docs still promise a from-clone run. Status: ✅ Resolved (2026-07-30).**
The owner decided nothing ships. `README.md`, `docs/data.md`,
`docs/recording_runbook.md`, `.gitignore`, and the devcontainer comment were
rewritten to say plainly that no imagery or calibration ships and the user supplies
it under `data/`; the from-clone claim and the stale `data/calibration/` path are
gone (with `examples/`). Closes P0-2/C7a. The original deferred analysis follows.
`README.md:26-27` used to read: *"A small calibration set ships in
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

**A1b — no sample imagery ships. Status: ✅ Resolved by decision (2026-07-30).**
The deferred sample-data decision (§6b-1) was made: **no data ships.** `examples/`
was deleted entirely and the docs now say the user supplies imagery. This is no
longer a gap to close — it is the intended, documented state.

**A2 — config example images don't chain. Status: ✅ Resolved (P1-4).**
`config.yaml` now uses explicit `*_image` / `*_image_hdr` pairs, and
`reflectance_image` defaults (blank) to `<raw_image>_ref`, so notebook 02's
output feeds notebook 02's viewer cell and notebook 03. The mismatched
`raw_34850_or` vs `raw_4000_or_ref.img` pairing is gone.

### B. Correctness — the heart of what was shelved

**B1 — the offset is applied inside the gain. Status: ✅ Fixed (2026-07-30).**
The owner ruled on the formula. Both consumers now compute `gain·DN + offset`:
- `notebooks/02_convert_to_reflectance.ipynb` cell 9 and
  `scripts/batch_convert_reflectance.py` were changed from
  `(gain[i]*np.squeeze(im.read_band(b) + offset[i])*mask)` to
  `((gain[i]*np.squeeze(im.read_band(b)) + offset[i])*mask)`, i.e. the `*mask`
  stays outside the affine term so no-data pixels remain exactly 0.

This matches notebook 01's `fit_intercept=True` empirical-line fit and closes P2-8.
Because no reflectance products ship in the repo, there is no archived-product
reprocessing burden here. The original analysis follows for the record.

The slimmer audit reached the same finding (its P2-8) and **had classified it
"DEFERRED — do not touch," a science decision for the owner.** With the (now-removed)
committed `gain.npy`/`offset.npy`, the quantified effect of the *old* formula was:
the intercept (~10⁻² reflectance) multiplied by a ~10⁻⁴ gain and annihilated,
biasing every product by **mean 0.0151 / max 0.0215 reflectance**. This was the one
open item that changed output numbers — now corrected.

**B2 — no band-grid check when applying the calibration. Status: ✅ Fixed (2026-07-30).**
Both consumers now guard the coefficient length against the target image's band
count before applying:
- `notebooks/02_convert_to_reflectance.ipynb` cell 9 raises `ValueError` if
  `len(gain) != len(wl)`.
- `scripts/batch_convert_reflectance.py` skips (and reports) any image whose band
  count does not match, so a batch keeps going rather than aborting.

A 343-element `gain`/`offset` applied to a differently-banded cube is now caught up
front with a clear message instead of misaligning silently or `IndexError`-ing deep
in the loop. (`main` had a *seed-vs-collection fallback* here; the first 2026-07-30
pass removed it — nothing ships — so both consumers load `gain`/`offset` straight
from `calibration_dir`.)

**B3 — notebook 02 cell 9 is not idempotent. Status: 🟡 Partial (P2-7).**
Cell 9 still rebinds in place (`gain = gain[indices]`, `offset = offset[indices]`,
`wl = wl[indices]`). `main` added the P2-7 mitigation — an explanatory comment
warning that re-running the cell without re-running the load cell double-subsets
and raises `IndexError`. The hazard itself is unchanged; the batch script was
already safe (`gain = gain_full[indices]`).

**B4 — dead branch + unused high tarp. Status: ✅ Resolved (2026-07-30).**
The dead code is gone: the `use_all_regions = True` flag and its unreachable `else`
branch (which referenced the never-defined `thm`) were removed from
`notebooks/01_calibrate_cal_panels.ipynb`'s fit cell, and a comment now states the
fit explicitly — *"regress the two tarp reflectances (plus a forced origin) on the
measured panel counts."* That closes the two things B4 flagged as defects: the dead
branch and the unstated two-tarp nature of the fit.

The high-reflectance tarp is **intentionally** still loaded, averaged (`asdhm`) and
plotted — the owner asked that the high-tarp code not be touched. So the fit remains
a two-tarp (dark + med) empirical line through a forced origin, with the high tarp
shown for context only, and that is now a deliberate, documented choice rather than
an oversight.

**B5 — `loadROIs` throws away the masks it loaded. Status: ✅ Fixed (2026-07-30).**
`src/hsiViewer/hsi_viewer_ROI.py` line 523 now stores the mask just read —
`np.reshape(mask, self.ROImask_empty.shape).copy()` — instead of
`copy.deepcopy(self.ROImask_empty[:])`. Re-opening an ROI file to extend it and
saving no longer writes empty ROIs over the real ones. This is the one intentional
divergence from the original `hsiViewer` (otherwise byte-identical); the fix is
commented in place. Live-test caveats from Phase 4 (rotation, cross-image spectra
re-extraction) still apply before trusting it on a real ROI file.

**B6 — smoothing bleeds into no-data pixels. Status: ✅ Fixed (2026-07-30).**
`src/upwins_hsi/utils.py`'s `spatial_smoothing` now re-applies the mask after the
neighbor averaging (`arr_out[:,:,i] = arr_out[:,:,i]/mask_sum*mask`), so a no-data
pixel (mask == 0) bordering valid data is held at 0 instead of picking up a
neighbor's spectrum. This stops the valid-data region from growing one pixel per
`smoothing_level` pass and keeps the downstream `band0 > 0` mask convention intact.
Verified with a unit check (a no-data pixel surrounded by valid data stays exactly 0;
a uniform image is unchanged).

**B7 — `CalPanels.pkl` freezes measured DN. Status: 🟡 Mitigated (2026-07-30).**
The 2026-07-30 pass reduced the surface without adding a hard guard:
- **No shipped pickle to reuse.** `examples/calibration/CalPanels.pkl` was deleted,
  so the most likely silent re-fit — falling back to the shipped example's tarps —
  can no longer happen. The seed fallback in notebook 02 / the batch script was
  removed too.
- **A per-collection reminder was added** at notebook 01 cell 12 and in `config.yaml`:
  cal-panel ROIs store measured DN, not a reusable region, so they must be drawn
  fresh for each collection; reusing another collection's pickle re-fits its tarps.

What remains (why this is Mitigated, not Resolved): no code *guard* was added. A user
who points `cal_panel_rois` at a prior collection's pickle on the same sensor/band
grid still gets a silent wrong-collection fit — the fit still reads spectra straight
from the pickle (`cal_panel_rois.df ... .iloc[:, 4:]`) with no wavelength/identity
check. The whole-collection-aware remediation below is still the proposed real fix,
still out of scope. **See [Proposed remediation for B7](#proposed-remediation-for-b7).**

**B8 — the mid tarp is 98.6 % saturated. Status: ✅ Moot (2026-07-30).**
This finding was a data-quality flag on the *shipped* calibration, and that data no
longer ships: `examples/calibration/CalPanels.pkl`, `panel_mid_spectra.npy` and
`gain.npy` were deleted with `examples/`. The saturated mid tarp is not in the repo
to bias anything. The underlying data problem still exists in the *source*
collection (it was an exposure setting at collection time, not a software bug), so
if that same collect is ever supplied as user data the caveat applies — but there is
nothing in the tree to fix. Note the code still uses `int(0.97 * np.max(panel_mid_spectra))`
as the threshold (Appendix B's open question about a bit-depth-based threshold is a
separate, still-open design point, not part of this pass).

### C. Packaging, hygiene, docs

**C1 — `utils.py` dead code + `psutil`/`scipy` pins. Status: ✅ Fixed (2026-07-30).**
`src/upwins_hsi/utils.py` was trimmed from 850 lines to **64** — only
`spatial_smoothing` (the one function the notebooks and batch script call) plus
`numpy`/`copy` remain. The broken geotiff functions, `lda_predict_proba`, the
display/PDF helpers, and the unused `PdfPages`/`psutil`/`platform`/`sys`/`math`/
`importlib`/`pandas`/`mpatches` imports are gone. `requirements.txt` dropped
`psutil==6.0.0` (only there for the now-removed dead import) and `scipy==1.13.1`
(imported nowhere). Verified: `spatial_smoothing` still imports and runs (it also
carries the B6 fix). This supersedes the slimmer audit's "byte-identical, do not
re-audit" note, which was about fidelity to the original, not the dead code.

**C2 / C3 — devcontainer. Status: ✅ Resolved (P1-3).**
`.devcontainer/devcontainer.json` now uses
`source=${localEnv:HOME}/projects/upwins/data,target=/workspaces/upwins-hsi-preprocessing/data`,
adds `postCreateCommand: python -m pip install ... -e .`, drops
`runArgs: ["--gpus","all"]` (with a comment telling future editors not to re-add
it), and renames to `upwins-hsi-preprocessing`. The `Dockerfile` base is now
`mcr.microsoft.com/devcontainers/python:3.12-bookworm` with `python3-pyqt5` — no
CUDA, no TensorFlow.

**C4 — three unused viewer modules. Status: 🔲 Open — the one remaining finding.**
`src/hsiViewer/hsi_viewer.py`, `hsi_viewer_2.py` and `hsi_viewer_array.py` are
all still present and still unimported by any notebook or script here. Left in place
deliberately for now — the notebooks import only `hsi_viewer_layers` and
`hsi_viewer_ROI`, so these three are dead weight but harmless. This is the last
unaddressed item in this document.

**C5 — copy-pasted import block. Status: ✅ Fixed (2026-07-30).**
Each notebook's first cell was trimmed to the names it actually uses, verified
against a per-notebook usage scan:
- **nb01:** `linear_model`, `numpy`, `os`, `pickle`, `spectral`, `plt`, `mpl`, `hvr`.
- **nb02:** `numpy`, `os`, `spectral`, `utils`, `hlv`.
- **nb03:** `numpy`, `spectral`, `hvr`.

The `PCA`/`GaussianMixture`/`mean_squared_error`/`r2_score`/`colors`/`csv`/`time`/
`copy`/`importlib` imports, the duplicate `import numpy as np`, the commented-out
block in nb03, and the wrong-viewer alias (`hlv` in nb01, `hvr` in nb02) were all
removed. A check confirmed no removed name is referenced anywhere in its notebook.

**C6 — leftover instruction cells + typos. Status: ✅ Resolved (2026-07-30).**
The contradictory red-HTML "*Change the dir and fname…*" cells were already gone on
`main` (P2-11); the 2026-07-30 pass fixed the typos flagged alongside them in cell 14
— `saturation_trheshold → saturation_threshold` and "*poixels*" → "pixels" (×2). (The
separate, non-contradictory "*Run the cell with hrv.viewer…*" red-HTML cell was never
part of this finding and is untouched.)

**C7a — docs overstate what ships. Status: ✅ Resolved (2026-07-30).**
Same sentence as A1a. The README's from-clone/"ships a calibration set"
overstatement was rewritten: the repo now states plainly that nothing ships. Closed
together with A1a/P0-2.

**C7b — demo run dirties committed files. Status: ✅ Resolved (P1-6).**
Notebook 01 writes `gain`/`offset`/`panel_*` into a **gitignored** per-collection
`calibration_dir` under `data/`. (On `main` a read-only reference set also lived in
`examples/calibration/`; as of 2026-07-30 that is deleted — nothing ships — so there
are no tracked calibration artifacts left for a demo run to clobber at all.)

**C8 — developer-local kernel name. Status: ✅ Fixed (2026-07-30).**
`02_convert_to_reflectance.ipynb`'s kernelspec `display_name` was changed from
`.venv` to `Python 3` (`name`/`language_info` left alone, so the diff is the one
meaningful line). Notebooks 01 and 03 were already `Python 3`, so all three are now
consistent and free of the developer-local kernel name.

**C9 — legacy notebook latent errors. Status: ✅ Resolved (2026-07-30).**
`notebooks/legacy/train_apply_lda_model.ipynb` was **deleted** (owner decision), and
its row was removed from the README notebook table. The `legacy/` directory is gone.
The latent errors it carried (cell 15's same-quote nested f-string, cell 20's
never-assigned `LDA_result_probs`, cell 5's `D:/SpectralLibrary` Windows path) are no
longer in the repo. The notebook was already labelled superseded by
`upwins-veg-classifier`; deleting it is cleaner than fixing code nobody runs.

**C10 — batch script's calibration source changed, undocumented. Status: ✅
Resolved (mostly).**
The divergent hardcoded copy (`atmospheric_compensation.py`, with a different
collect's coefficients inline) was dropped — its supersession is reasoned out in
`AUDIT_HANDOFF.md` §7. `batch_convert_reflectance.py` loads coefficients from
`config.yaml`'s `calibration_dir` with explanatory comments (the
`calibration_seed_dir` fallback was removed on 2026-07-30 — nothing ships), and
`docs/recording_runbook.md` documents that flow. Residual: the explicit "these
coefficients differ from the pre-handoff inline ones" note lives only in
`AUDIT_HANDOFF.md` (marked for deletion before shipping); once that file is removed,
nothing in the shipped tree records the historical change. Minor.

---

## Proposed remediation for B7

> **Still out of scope — a proposal, not implemented.** This section records the
> design so the decision to defer B7 is made with a concrete remedy in view. It
> supersedes the terse "wavelength guard" that the original shelved audit
> proposed under its Phase 3; the reasoning for the change is kept below so the
> discarded option is not re-proposed.
>
> **2026-07-30 note:** the 2026-07-30 pass already did part of step 3 for a different
> reason — the gain/offset **seed fallback was removed** and the shipped
> `examples/calibration/CalPanels.pkl` **deleted**, so the "silent fallback to the
> shipped example" trap this proposal warns about no longer exists. Steps 1, 2, 4 and
> 5 (self-contained per-collection bundle, pickle-driven band axis, apply-time
> band-grid guard, explicit collection tag) are **still unimplemented** and are what a
> full B7 fix would add. B7's residual same-sensor cross-collection case (§ status:
> Mitigated) is exactly what step 5 addresses.

### The fact that reframes B7: the collection is the unit, not the image

The cal-panel ROIs are not tied to a single image — they are a **whole-collection
artifact**. The tarps are imaged once per collection; `CalPanels.pkl` is that
collection's cal *measurement*; and the fitted `gain`/`offset` are then applied
to **every other image collected in the same session** (same illumination,
exposure and sensor config), most of which contain no tarps at all. That reuse is
the entire point of the empirical-line method and is **correct** — nothing should
guard against it.

Two consequences follow, and they redirect the fix:

1. **The reuse happens on the apply side.** Notebook 02 and the batch script
   consume `gain.npy`/`offset.npy`; they never touch `CalPanels.pkl`. So any
   guard that protects the *many-images* workflow has to live there, not in the
   fit.
2. **The pickle is self-contained.** Its DataFrame carries both the tarp DN
   (`df.iloc[:, 4:]`) **and** the band axis (`df.columns[4:]` — the 343
   wavelength columns, 399.10–1000.35 nm). In the *reuse* path, notebook 01 opens
   the cal image only to read `im.wl`, which the pickle already contains; the
   image's pixels never enter the fit.

### The hard limit: same-sensor cross-collection reuse is invisible in the bytes

When two collections use the same sensor and the same band grid — the common
"next deployment" case — there is **no data-derived signal** that distinguishes
collection A's calibration from collection B's. Not in the fit (the reuse path's
only image input, `im.wl`, is identical), and emphatically not at apply time (the
images being converted have no tarps to check against). This is the load-bearing
fact: **B7's silent case cannot be closed by any self-consistency check — only by
explicit provenance.** Everything below is arranged around that.

### Why the obvious fit-time check is *not* the answer (recorded so it isn't re-proposed)

An earlier revision of this analysis proposed a fit-time self-consistency check:
re-read the tarp pixels from the cal image and refuse if they don't reproduce the
pickle's stored DN. **Reject this as the centrepiece.** It only has value if the
cal image is a source of truth to validate the pickle against — but in the reuse
path the cal image contributes nothing the pickle doesn't already carry (just
`im.wl`), so the check validates the pickle against a redundant input. It also
cannot catch the same-sensor cross-collection case (identical band axis passes),
which is precisely the silent one. It is ceremony, not safety. The single-line
*wavelength* guard from the original Phase 3 is weaker still — it catches only a
different sensor/band-count, i.e. the loud case that already tends to `IndexError`
on its own.

### The remediation — four steps plus the provenance follow-on

Ordered simplest-first. Steps 1–4 are the cleanest-simple fix; step 5 is what it
takes to close the same-sensor case and is the one format change.

1. **Make each collection a self-contained bundle.** Keep the ROI pickle *and*
   `gain.npy` *and* `offset.npy` together in that collection's `calibration_dir`.
   `main` already put gain/offset there (per collection, gitignored, with a
   committed seed); extend the same pattern to the pickle. A `calibration_dir`
   then represents a *collection*, and everything the fit produced for it travels
   together.

2. **Drive the fit's band axis from the pickle; drop the load-bearing cal-image
   dependency in the reuse path.** Source `wl` for the fit and the library
   resample from `cal_panel_rois.df.columns[4:]` instead of from a separately
   opened cal cube. This removes B7's "wrong image" surface *outright* rather than
   guarding it, and it has two useful side effects:
   - Notebook 01's fit becomes runnable **from a clone** using only the committed
     calibration set — it no longer needs the raw cal cube, which does not ship
     (this is also finding A1b's blocker for notebook 01).
   - Re-fitting a collection reproduces *that collection's* bundle deterministically,
     instead of depending on which image an operator happened to open.

   The cal image is still needed for the one step that genuinely requires it —
   drawing **new** ROIs in the viewer (`hvr.viewer(im, …)`, cell 10). In that step
   the image and the pickle match by construction, so B7 cannot arise there.

3. **A missing per-collection ROI pickle is a loud error, not a silent seed
   fallback.** The gain/offset seed fallback that `main` added is a reasonable
   convenience for *applying* the shipped example; it is the wrong behaviour for
   *fitting* a real collection, because falling back to the committed
   `examples/calibration/CalPanels.pkl` is exactly the B7 trap. Notebook 01 should
   stop and say "draw the cal-panel ROIs for this collection" when the
   collection's own pickle is absent. You draw ROIs once **per collection**, never
   per image.

   ```python
   # notebook 01 — fit input is the collection's own ROI pickle; no silent
   # fallback to the shipped example (that would re-fit the example's tarps, B7).
   roi_path = os.path.join(CONFIG['paths']['calibration_dir'], 'CalPanels.pkl')
   if not os.path.exists(roi_path):
       raise FileNotFoundError(
           f"No CalPanels.pkl in {CONFIG['paths']['calibration_dir']}. Draw the "
           "cal-panel ROIs on THIS collection's cal image (viewer cell) and save "
           "them here before fitting — do not reuse another collection's ROIs.")
   ```

4. **Put the one guard that rides with the whole-collection workflow at APPLY
   time.** For every tarp-free image the collection converts, check the band grid
   before applying — this is finding **B2**, and it is the check that scales to
   "the other images collected in the same context." It catches a sensor/band
   mismatch (the only thing checkable without tarps) and protects the many-images
   reuse directly.

   ```python
   # notebook 02 / batch — the collection's gain/offset only fit one band grid.
   if len(gain_full) != len(wl):
       raise ValueError(
           f"Calibration has {len(gain_full)} bands but {fname} has {len(wl)}. "
           "gain.npy/offset.npy are valid only for the sensor/band configuration "
           "they were fitted on — re-run notebook 01 for this collection.")
   ```

5. **The only thing that closes the same-sensor cross-collection case: an explicit
   collection tag.** Since no data-derived check can catch it (see the hard limit
   above), stamp the collection identity — the cal-image or session name — into
   the saved bundle, and echo it into the reflectance ENVI header on conversion.
   Then `raw_59000_or_ref` visibly records that it was made with, say,
   `Morven_20250708`'s calibration, and a human (or a one-line check) can verify
   provenance instead of trusting a directory name. This is a small **metadata
   addition**, not a one-liner, so it is not the *simplest* step — but given
   whole-collection reuse it is the piece that turns "trust the directory" into
   "verify the provenance." It is the same item the plan's Future-work list
   defers as "platform / source as ROI metadata," now with a concrete motivation.

### Net

The cleanest-simple fix is steps 1–4: **treat the collection as the self-contained
unit (pickle + gain + offset in one per-collection `calibration_dir`), drive the
fit's band axis from the pickle so the stale-cal-image coupling disappears, make a
missing per-collection pickle a loud error, and guard the apply side with a
band-grid check.** Step 5 (an explicit collection tag in the bundle and the
reflectance header) is the follow-on that also covers the same-sensor
cross-collection case, at the cost of one metadata-format change.

**Progress (2026-07-30):** step 4 (the apply-side band-grid check) is now
implemented — this is finding **B2**, done in nb02 + the batch script. Steps 1–3 and
5 remain unimplemented, so B7's full remediation is still **out of scope**; its
surface was reduced on 2026-07-30 (see the B7 status above).

## Bottom line

> **Updated 2026-07-30 (after both passes).** The two 2026-07-30 passes on branch
> `claude/audit-repo-cleanup-f80o10` closed nearly everything. First pass: **B1
> fixed**, **B5 fixed**, **B8 moot** (saturated calibration removed with `examples/`),
> **B7 mitigated**, plus the packaging/docs work (A1a/A1b/C6/C7a/C9). Second pass:
> **B2 fixed** (band-grid guard), **B4 fixed** (dead branch removed), **B6 fixed**
> (smoothing mask), **C1 fixed** (`utils.py` trimmed; `psutil`/`scipy` dropped),
> **C5 fixed** (import blocks), **C8 fixed** (kernelspec). **What remains:** only
> **C4** (three unused viewer modules, left in place as harmless dead weight), with
> **B3** (idempotency, comment-only) and **B7** (mitigated, no hard guard) still
> Partial. The original bottom line (as of `main`) follows.

The packaging half of this alternate plan was largely done on `main` — it runs from a
clone, the devcontainer is client-safe, the demo no longer dirties tracked
files, and the config chains. **What remained out of scope was the correctness
core:** the reflectance formula (B1), the missing band-grid guard (B2), the
two-tarp/dead-branch calibration structure (B4), the silent DN re-fit (B7), and
the saturated mid tarp (B8) — plus the viewer data-loss bug (B5), the smoothing
edge-bleed (B6), and the dead-code cleanup (C1, C4, C5). None of these was
addressed by the slimmer audit that guided `main`; B1 and B8 were seen there and
consciously left alone. That was a defensible call — and the 2026-07-30 pass above
then acted on B1/B5/B8/B7 once the owner decided.

---

## Appendix — Preserved remediation plan from the shelved audit

> **Why this is here.** The full remediation **Plan (Phases 0–6)** and
> **Appendices A/B** below are lifted verbatim from the original shelved audit
> (`audit_plan.md` as it stood at `be9923e`), consolidated into this document so
> the guidance survives deletion of the audit branches. Nothing in it has been
> re-written for the current tree.
>
> **Read it with two adjustments in mind:**
> 1. **Status is as-originally-written** — every phase says "Proposed" and the
>    verdict says "nothing implemented." That was true at `be9923e`. For what has
>    actually landed on `main` since, use the **Status at a glance** table at the
>    top of this document — several of these phases are now Done, Partial, or
>    deliberately Deferred.
> 2. **Paths and cell numbers are pre-cleanup.** The cleanup relocated
>    `utils.py → src/upwins_hsi/utils.py`, `hsiViewer/ → src/hsiViewer/`, and
>    `data/calibration/ → examples/calibration/`, and lightly shifted notebook
>    cell indices. Translate references accordingly.
>
> Two sections of the original — "What was verified" and "What I need from you"
> — were **not** carried over (a verification log and a decisions letter, both
> superseded by the status table above). Ask if you want them preserved too.

### Plan

Each phase is one commit; phases are independent, so you can approve any subset.

#### Phase 0 — Undo the handoff regressions (A1a, A2, C6, C7a) — do this first

Everything here is a **handoff** finding: the original repo did not have these
problems, and fixing them restores accuracy rather than changing behavior. No
numbers move, no decision is needed from you, and nothing is blocked on the B8
question. This is the natural first commit — it makes the repo honest before
anything touches the calibration.

- **A1a / C7a — stop claiming a from-clone run.** Three files:
  `README.md:23-24`, `data/README.md:7`, and `config.yaml:5-6` (a header comment,
  easy to miss). Say plainly that imagery is distributed separately and point at
  `data/sample/README.md`, which already says the right thing. While in
  `data/README.md`, drop "small" for the calibration set or state that it is
  ~14 MB and that `CalPanels.pkl` is the bulk of it.
- **A2 — make the example images chain.** One line: set `reflectance_image` to
  what notebook 02 actually writes (`raw_34850_or_ref.img`), or change
  `raw_image` to `raw_4000_or`. Either is fine while no data ships; pick to match
  whatever Phase 1 eventually supplies.
- **C6 — delete nb 01 cells 3 and 9** (the red-HTML notes that the cells beneath
  them contradict) and fix the three typos in cell 15 (`saturation_trheshold`,
  "poixels" ×2, "so choose").

Do C6 even if you skip everything else in this phase. Those two cells are the only
place in the repo that tells a reader to do something the next cell tells them not
to.

#### Phase 1 — Ship a runnable sample (A1b) — needs you, and optional

Distinct from Phase 0 and lower priority than the original draft of this audit
implied. `research_species_mapping` never ran from a clone and never claimed to,
so shipping a sample cube gives the client something that has never existed — an
enhancement, not a repair. Phase 0 already closes the honesty gap.

If you want it: supply a cropped raw cube containing the tarps, plus one small raw
cube to convert. I commit them, verify `git check-ignore` passes them, and
reconcile `config.yaml` so nb 01 → 02 → 03 chains on the same image. A cropped cube
of a few hundred rows is enough — the point is that the notebooks execute, not
that the scene is complete.

If you don't, nothing further is needed: Phase 0's reword already leaves the docs
accurate.

#### Phase 2 — Fix the reflectance conversion (B1, B2, B3) — recommended first

**The change.** In notebook 02 cell 9 and `batch_convert_reflectance.py:67`:

```python
# before
imRef[:, :, i] = (gain[i] * np.squeeze(im.read_band(b) + offset[i]) * mask).astype(np.float32)
# after
imRef[:, :, i] = ((gain[i] * np.squeeze(im.read_band(b)) + offset[i]) * mask).astype(np.float32)
```

The `* mask` stays outside so no-data pixels still come out as exactly 0 —
without that, the offset would write a non-zero value into every masked pixel
and break the `band0 > 0` mask convention that notebooks 02/03 and the
classifier all rely on.

Alongside it, two small guards:

```python
# B2 — the coefficients are position-indexed; they only fit one band grid.
if len(gain_full) != len(wl):
    raise ValueError(
        f"Calibration has {len(gain_full)} bands but {fname} has {len(wl)}. "
        "gain.npy/offset.npy are only valid for the sensor configuration they "
        "were fitted on — re-run notebook 01 for this collection."
    )

# B3 — keep the full arrays, subset into new names (the batch script's pattern).
gain = gain_full[indices]
offset = offset_full[indices]
```

Notebook 02 cell 3 becomes `gain_full = np.load(...)` / `offset_full = np.load(...)`,
so cell 9 can be re-run freely.

**What this costs you.** Every existing `*_ref` product is biased, and so is any
model trained on ROIs drawn from one. After this lands you have three options,
and this is a decision I need from you:

1. **Reprocess and retrain.** Correct, and the classifier repo is already going
   to be retrained (its Phase 4b changed the split), so the marginal cost is
   re-running the batch script over your archive.
2. **Reprocess going forward only.** Cheapest, but then old and new reflectance
   products differ and must never be mixed in one training set. If you take
   this, the version has to be recorded somewhere the classifier can see —
   otherwise it is exactly the silent-drift problem the classifier's Phase 2
   just fixed on the normalization side. **The archive is not one uniform
   thing**, which strengthens the warning: per C10, anything produced by the
   original `atmospheric_compensation.py` was biased by `gain·offset` on the
   *Greenhead* coefficients, not the committed Morven ones — a different
   magnitude, and a different sign across the blue end. "Old products are all
   ~0.015 high" is true of this repo's products, not of everything you have.
3. **Decide the current behavior is what you want** — i.e. treat the calibration
   as gain-only through the origin. Defensible for a two-point fit with a forced
   origin, but then notebook 01 should stop fitting an intercept it discards
   (`fit_intercept=False`), rather than computing one and quietly dropping it.

I recommend (1), with (3) as the honest fallback if reprocessing is impractical.
What is not acceptable is leaving fit and application disagreeing.

**Risk:** the numbers move. Reflectance drops by ~0.015 in most bands. Spectra
plotted from new products will not overlay old ones.

#### Phase 3 — Say what the calibration actually does (B4, B7, B8)

Documentation, dead-branch removal, and three guards. No numbers change — but
the B7 guard will start refusing runs that used to "succeed", which is the point.

(C6 was originally grouped here. It has nothing to do with the calibration and is
not blocked on the B8 question, so it moved to Phase 0.)

- Delete the `use_all_regions` / `thm` branch in nb 01 cell 32. It cannot run.
- State in cell 31's markdown that the fit uses **two tarps plus a forced
  origin** — dark and med — and that the high tarp is shown for context only.
  Either that, or add it to the fit (a real change; see Future work). Right now
  a reader reasonably assumes all three are used.
- Add a short **"What this calibration is tied to"** block to
  `docs/recording_runbook.md` and link it from the README. Content is in
  Appendix A below; the hard dependencies (tarp library naming, ROI names, band
  grid, illumination, two-tarp range, and the reuse scope in Appendix B) are all
  invisible in the code today and each fails silently.
- Note in cell 15's markdown how many pixels the saturation filter dropped, and
  print it — see the B8 guard below.

Three of those failures are worth a guard rather than only a sentence:

```python
# nb 01 cell 24 — a library whose names don't contain 'dark'/'med' yields
# empty lists, and np.mean of an empty array gives NaN gains with no error.
for label, idx in (('dark', idx_l), ('med', idx_m), ('high', idx_h)):
    if not idx:
        raise ValueError(f"No spectra matching '{label}' in {fname_sli}.")

# nb 01 cell 13 — the ROI names are literal strings.
for roi_name in ('Cal Panel Low', 'Cal Panel Mid'):
    if roi_name not in names:
        raise ValueError(f"ROI '{roi_name}' not in {CONFIG['paths']['cal_panel_rois']}: {names}")

# nb 01 cell 13 — B7. The pickle stores DN, not a region. Its column names are
# the wavelengths of the image the ROIs were drawn on; if they don't match the
# image opened in cell 5, the fit is about to use another collect's tarps.
wl_roi = np.asarray(cal_panel_rois.df.columns[4:], dtype=float)
if len(wl_roi) != len(im.wl) or not np.allclose(wl_roi, im.wl):
    raise ValueError(
        f"{CONFIG['paths']['cal_panel_rois']} holds spectra on a different band "
        f"axis ({len(wl_roi)} bands, {wl_roi[0]:.1f}-{wl_roi[-1]:.1f} nm) than "
        f"{fname} ({len(im.wl)} bands, {im.wl[0]:.1f}-{im.wl[-1]:.1f} nm). "
        "Re-draw the cal-panel ROIs on this image."
    )

# nb 01 cell 15 — B8. Saturation is an exposure problem, not a software one;
# the least this can do is refuse to fit a tarp that is mostly clipped.
for label, before, after in (('low', panel_low_spectra_all, panel_low_spectra),
                             ('mid', panel_mid_spectra_all, panel_mid_spectra)):
    kept = len(after) / len(before)
    print(f'{label} panel: {len(before)} -> {len(after)} pixels ({kept:.1%} unsaturated)')
    if kept < 0.5:
        raise ValueError(
            f"{label} panel is {1 - kept:.1%} saturated. The fit would rest on the "
            f"dimmest {kept:.1%} of the tarp, biasing gain high. Re-collect the cal "
            "image at a lower exposure."
        )
```

The B7 guard catches the loud case outright and, in practice, most of the silent
one — two collects from the same sensor with identical band centers will slip
through, so the runbook line matters too: **re-draw the cal-panel ROIs for every
collect.** The B8 threshold of 50 % is a starting point, not a derived number;
set it to whatever your good collects actually achieve.

#### Phase 4 — ROI load loses its masks (B5)

One line in `hsiViewer/hsi_viewer_ROI.py:523`: store the mask that was just read
instead of an empty one.

```python
# before
self.ROI_dict["ROI_num_"+str(self.ROI_Id_num_count)] = copy.deepcopy(self.ROImask_empty[:])
# after
self.ROI_dict["ROI_num_"+str(self.ROI_Id_num_count)] = np.reshape(mask, self.ROImask_empty.shape).copy()
```

**This needs a live test before it is trusted, and I cannot run one.** Two
reasons: `saveROIs` applies a rotation to the mask when `rotate=True`
(line 569), so a mask loaded back into a viewer opened with a different `rotate`
setting may need the inverse transform; and `saveROIs` reads pixel spectra from
`self.imList` for the *current* image, so loading ROIs drawn on a different
image will silently re-extract spectra from the new one. Both want a check in
front of the viewer with a real ROI file.

While in the file, two adjacent nits worth folding in: both `loadROIs` and
`saveROIs` use `QFileDialog.getSaveFileName` — so *loading* prompts with a save
dialog and an overwrite warning — and both have a `try` whose body references a
bare `im` that does not exist in method scope, so the `except` always fires and
falls back to a hardcoded `C:\Spectra_data\Spectral_images`.

If you would rather not touch the viewer at all, the alternative is a one-line
warning in the docs: *do not load an existing ROI file to extend it; make a new
one per session.* That is the lower-risk option and I would not argue against it.

#### Phase 5 — Delete dead code (C1, C4, C5)

No behavior change, ~1,100 lines removed.

- **`utils.py` → `spatial_smoothing` only** (~55 lines with the docstring), plus
  `numpy` and `copy`. Everything else is unreferenced; the geotiff functions are
  additionally broken (C1).
- **Drop `psutil==6.0.0` and `scipy==1.13.1` from `requirements.txt`.** Both were
  added during the handoff, not inherited: `psutil` only to satisfy `utils.py`'s
  dead import, `scipy` for nothing at all — it is imported nowhere in the repo.
  Removing them reverts handoff additions rather than cleaning up legacy.

  > **Ordering — do not remove `psutil` first.** `utils.py:7` is a *module-level*
  > `import psutil`, so dropping the pin before the file is trimmed breaks
  > `import utils` in notebook 02 and the batch script. Trim `utils.py` in the
  > same commit, or before. `scipy` is safe to remove at any point.
- **Delete `hsi_viewer.py`, `hsi_viewer_2.py`, `hsi_viewer_array.py`.** Keep a
  one-line note in the README that the fuller viewer set lives in
  `research_UPWINS_Microscene`, so nobody thinks they were lost.
- **Trim each notebook's cell 1** to what that notebook uses. Notebook 03 drops
  to `numpy`, `spectral`, `os`, `yaml`, `matplotlib` and `hvr` — the five
  commented-out imports go with them, and so does `hlv`, which it never calls.

Verify with `python -m pyflakes utils.py scripts/*.py hsiViewer/*.py` — it should
come back clean, which makes it a usable signal from then on.

#### Phase 6 — Devcontainer, docs, hygiene (C2, C3, C7b, C8, C9, C10)

- **C2 — devcontainer mount.** Match what `upwins-veg-classifier` already does:
  `source=${localEnv:HOME}/projects/upwins/data,target=/workspaces/upwins-hsi-preprocessing/data`.
  Document in the README that the host path is a default and must be edited if
  yours differs, and note the same gotcha the classifier's README now carries:
  **the mount replaces the repo's `data/`, so committed `data/calibration/` and
  `data/sample/` become invisible inside the container** unless the external
  directory has its own copies. Also drop the commented-out `/home/gta/...`
  line.
- **C3 — devcontainer base image.** Recommend `python:3.11-slim` (or `3.12`) with
  `python3-pyqt5` from apt, and drop `runArgs: ["--gpus","all"]`. That removes a
  multi-GB pull and the requirement for an NVIDIA GPU on the host, for a repo
  with no TensorFlow. If you would rather keep one image across both repos, say
  so and I will leave it and add a comment explaining why it is heavier than it
  looks. **Needs a real Docker build to verify** — PyQt5 in a slim image
  sometimes needs extra X libraries (`libgl1`, `libxkbcommon-x11-0`).
- **C7b — the demo overwrites tracked artifacts.** Add one line to the runbook's
  pre-flight checklist: *running notebook 01 overwrites the committed
  `gain.npy` / `offset.npy` — `git checkout data/calibration/` to restore them.*
  (C7a, the docs overstatement, moved to Phase 0. If Phase 1 later ships a
  sample, re-check that the README matches what actually ships.)
- **C8 — kernelspec.** Set `display_name` to `Python 3` in
  `01_calibrate_cal_panels.ipynb` and `02_convert_to_reflectance.ipynb`
  — **those two only**. Notebook 03 and the legacy notebook already have it.
  Leave their `language_info` alone: they record Python 3.12.3 against 01/02's
  3.13.5, and normalizing that would produce a diff with no meaning.
- **C10 — record the batch script's calibration source.** Two sentences, no code
  change: note in `batch_convert_reflectance.py`'s docstring that the
  coefficients come from `config.yaml` → `data/calibration/gain.npy` (i.e. from
  notebook 01, per collect), and add a runbook line that this is a change from
  the pre-handoff script, which carried a different collect's coefficients
  inline. Anyone comparing new batch output against archived Greenhead products
  needs to know this before they conclude something regressed.
- **C9 — legacy notebook.** Three options, your call: leave it and add one line
  to its banner noting it needs Python ≥ 3.12 to open and has an unfinished
  final cell; fix the two lines so it at least parses everywhere; or delete it.
  I lean toward the first — it is explicitly labelled superseded, and fixing code
  nobody runs is its own kind of over-engineering.

---

### Appendix A — How the calibration works, and what it is tied to

Written in response to your question, and the source for the doc block proposed
in Phase 3. Contrasted with `research_UPWINS_Microscene`, which you know better.

#### `research_UPWINS_Microscene` — white reference, per image

From `1 UPWINS Mircoscene preprocesing.ipynb`, cells 14 and 20:

1. A **dark cube** (lens cap on, collected alongside the scene) is averaged over
   all pixels to a per-band dark spectrum, `image_dark_mean[b]`.
2. The scene is cropped so a **white reference panel spans the full width** of
   the image at the top; averaging over those rows gives `im_FPA[c, b]` — a
   *(column, band)* array.
3. Reflectance is then, per pixel:

   ```
   ref[r,c,b] = (DN[r,c,b] − dark[b]) / (FPA[c,b] − dark[b])
   ```

What that buys and costs:

- **Per column.** The divisor varies with `c`, so cross-track illumination and
  focal-plane non-uniformity — the characteristic pushbroom artifact — are
  corrected.
- **Relative, not absolute.** No known reflectance spectrum is ever used. The
  panel is implicitly treated as 100 % reflective, so the output is reflectance
  *relative to the panel* and any spectral structure in the panel is baked in.
- **Self-contained per image.** Nothing is carried between images. Every scene
  carries its own reference, so calibration cannot go stale.
- **Requires the panel in every frame**, spanning the full width, plus a
  matching dark collect. Manual per-image inputs: `crop_rows`, `crop_cols`,
  `white_ref_rows`, and the dark directory.

#### `upwins-hsi-preprocessing` — empirical line, fitted once and reused

Notebook 01 fits, notebook 02 (or the batch script) applies:

1. **Reference.** `data/calibration/cal_tarp_spectra.sli` — 19 ASD spectra,
   350–2500 nm at 1 nm — resampled onto the image's band centers with
   `spectral.BandResampler` (cell 7).
2. **Measurement.** ROIs drawn on the low and mid tarps in one raw image that
   contains them, saved as `CalPanels.pkl`. Spectra above `0.97 × max(mid panel)`
   are dropped as saturated (cell 15), and each set is averaged (cell 17).
3. **Fit.** Per band, `LinearRegression(fit_intercept=True)` over **three
   points** — `(0, 0)`, `(low DN, dark tarp reflectance)`, `(mid DN, med tarp
   reflectance)` — giving `gain[b]` and `offset[b]`, saved as 343-element arrays
   (cells 32, 34).
4. **Apply.** Drop the configured bad-band ranges, compute
   `reflectance = gain·DN + offset` — *currently mis-parenthesized, finding B1* —
   mask, smooth twice, write `<name>_ref`.

What that buys and costs:

- **Absolute reflectance**, because the tarps' true reflectance is known. This is
  the main difference from Microscene.
- **One coefficient pair per band for the whole frame.** No per-column term, so
  cross-track non-uniformity is *not* corrected.
- **No separate dark frame.** The regression's intercept absorbs the dark level
  and path radiance together — which is exactly why B1 matters: dropping the
  intercept drops the dark-current correction.
- **Reused across images.** One fit serves a whole collect, which is what makes
  the batch script possible — and what makes the calibration go stale if
  conditions change.

#### Side by side

| | Microscene | upwins-hsi-preprocessing |
|---|---|---|
| Reference | White panel in every scene | ASD-measured tarps, in one scene |
| Known reflectance? | No — panel assumed 1.0 | Yes — from the `.sli` library |
| Output | Relative reflectance | Absolute reflectance |
| Dark handling | Explicit dark cube, subtracted | Folded into the fitted intercept |
| Cross-track correction | Yes, per column | No, one gain/offset per band |
| Scope of a calibration | One image | One collect (many images) |
| Reusable artifact | None | `gain.npy` / `offset.npy` |
| Manual inputs | Crop rows/cols, white-ref rows, dark dir | Two tarp ROIs, drawn once |

#### Yes — it is tied to a specific panel set and configuration

Five ways, and **four of them fail silently**:

1. **The tarp library.** `cal_tarp_spectra.sli` is one specific set — spectra are
   named `tarp_near_7321-003-29_{dark,high,med}`. Cell 24 selects by substring
   `'high'` / `'med'` / `'dark'` in the name. A library using different names
   produces empty index lists, `np.mean` of an empty array, and **NaN gains with
   no error**.
2. **Two tarps, not three.** Only dark and med enter the fit. The high tarp is
   loaded, averaged and plotted, then unused (B4). The fit's dynamic range
   therefore tops out at the mid tarp's brightness, and anything brighter — dry
   sand, specular vegetation — is extrapolated.
3. **The ROI names.** Cell 13 filters `df['Name'] == 'Cal Panel Mid'` and
   `'Cal Panel Low'`, literal strings. A differently-named ROI yields an empty
   array and, again, no error.
4. **The band grid.** `gain.npy` / `offset.npy` are 343-element and
   *position*-indexed. They are valid only for images with that exact band count
   and ordering. Both consumers index them using indices derived from the
   *target* image's wavelengths, so a different sensor configuration misaligns
   silently (B2).
5. **The illumination.** The empirical line absorbs illumination geometry and
   exposure into the coefficients. Reuse is valid only within one collect under
   stable lighting — which is why the artifact is per-collect, not per-project.

Points 1, 3 and 4 are the two-line guards in Phase 3; point 2 is a sentence in
the notebook; point 5 is a line in the runbook.

#### What this repo needs to work properly

**Software.** Python (the notebook metadata says 3.13; the devcontainer base
ships its own) and the pins in `requirements.txt`: `numpy`, `scipy`,
`scikit-learn`, `pandas`, `spectral`, `matplotlib`, `PyYAML`, plus `PyQt5` /
`PyQt5-sip` / `pyqtgraph` for the viewer. `psutil` is only there for a dead
import in `utils.py` (C1). Notebooks 01 and 03 need a **real display session** —
they open a Qt window. Everything must be launched **from the repo root**:
`import utils`, `from hsiViewer import ...` and `open('config.yaml')` are all
root-relative.

**Data, none of which ships.** ENVI cubes (`.img` + `.hdr`) whose headers carry
band centers; one raw cube containing the tarps; one or more raw cubes to
convert. What *does* ship is the calibration set: the tarp `.sli`/`.hdr`, the
tarp ROI pickle, and fitted `gain`/`offset`.

**Implicit data conventions** that everything downstream assumes: reflectance is
written as unscaled float32 in 0–1 (no `reflectance scale factor` in the
header); no-data is 0; and the valid-data mask is `band 0 > 0`.

**The contract with `upwins-veg-classifier`.** The handoff is the ROI `.pkl`
file, which is a pickled `hsiViewer.hsi_viewer_ROI.ROIs_class` whose `.df` has
columns `Name`, `Color`, `Pixel_x`, `Pixel_y`, then **one column per wavelength**.
The classifier reads `df.iloc[:, 4:]` for spectra and takes the wavelength axis
from `df.columns[4:]`, so the band grid travels with the ROI file — which means
this repo's `reflectance.bbl_wl_ranges` setting is part of the contract. (The
classifier resamples each ROI file onto a reference axis, so mixing files made
with different bad-band settings degrades rather than breaks. Worth recording in
the runbook either way.) Two further requirements:

- **ROI names must follow the ASD library convention** (`Ammo_bre_...`) — that
  is how the classifier parses labels, via `upwins_veg.roi_labels`. Notebook 03's
  markdown already says this; the runbook repeats it.
- **Filenames carry processing semantics.** The classifier's
  `is_piloted_source()` decides pixel-wise normalization by matching
  `"crisfield"` / `"piloted"` anywhere in the ROI filename. Renaming a file
  changes how it is preprocessed. The classifier's audit lists moving that into
  ROI metadata as future work, and **this repo is where that metadata would have
  to originate** — `ROIs_class` has no field for it today. Not proposed here; it
  is a two-repo change and neither is ready for it.

---

### Appendix B — What to redo per collect, and what to keep

The three calibration inputs have three different lifetimes. Conflating them is
how B7 happens. This table is the intended source for the runbook block proposed
in Phase 3.

| Artifact | Redo when | Why |
|---|---|---|
| `cal_tarp_spectra.sli` — ASD tarp library | **Rarely.** Only when the physical tarps change. | It holds *reflectance*, an intrinsic material property. Independent of illumination, sensor and geometry, and resampled onto the image band centers at runtime (cell 7) — so it is portable across collections *and* across sensors. The most reusable artifact in the repo. |
| `CalPanels.pkl` — cal-panel ROIs | **Every collect.** | It is not a region definition; it stores measured **DN** (finding B7). Reusing it re-fits the previous collect's tarps and, on a matching band grid, does so silently. |
| `gain.npy` / `offset.npy` | **Every collect.** | They absorb illumination, exposure and dark level — see the five dependencies in Appendix A. Valid for one session under stable lighting; that is the scope the batch script is built for. |

**What eventually invalidates the library**, despite "rarely": dust, dirt, UV
fading, wear, and wetness (which changes NIR/SWIR reflectance sharply). Re-measure
periodically with the ASD. Note the committed library records **no acquisition
date** — the spectra are named `tarp_near_7321-003-29_{dark,med,high}`, a serial
with no date — so there is currently no way to tell how old the reference
measurements are. A date in the filename or the `.hdr` description would fix that
for the cost of one edit, and is worth doing at the next re-measurement.

**One caveat that applies even to a valid library.** The ASD measures the tarps
at one geometry; the airborne sensor views them at another, under a different
solar angle. Tarps are not perfectly Lambertian, so the effective reflectance at
the sensor differs slightly from the library value, and that difference *is*
collection-dependent. Second-order for this project's purposes, but it is the
reason the same library can be genuinely reusable and still contribute a small
per-collect bias. Not worth acting on; worth knowing before chasing a few
percent of disagreement.

---

### Open questions (unresolved; not blocking any phase)

- **Is the high-reflectance tarp deliberately excluded from the fit, or was it
  dropped along the way?** It is read, averaged and plotted, which suggests it
  was once intended to be used. Including it would extend the fit's range to
  bright targets; excluding it may have been a deliberate response to saturation
  on the high tarp — which B8 makes considerably more plausible, since the *mid*
  tarp is already 98.6 % clipped and the high tarp would be worse. If that is the
  reason, then the exposure was set for the dark tarp and the calibration has
  effectively been a one-tarp fit through a forced origin for some time. You will
  know. The answer decides whether B4 is a documentation fix or a real change.
- **Was `0.97 × max(mid panel)` chosen as a saturation threshold, or inherited?**
  On the committed data `max(mid panel)` is 4094, one count below 12-bit
  saturation, so the threshold lands at 3971 — it happens to work here *because*
  the panel is clipped. On a properly exposed cal image the same expression would
  scale to 97 % of whatever the tarp's brightest pixel happened to be and discard
  a slice of perfectly good data. A fixed threshold from the sensor's bit depth
  (e.g. `0.97 × 4095`) would be stable in both cases and is a one-line change;
  worth folding into Phase 3 if you agree.

### Future work (deliberately deferred, not oversights)

- **Platform / source as ROI metadata.** `ROIs_class` carries no provenance, so
  the classifier infers it from filenames. Adding a field here is the upstream
  half of an item already on the classifier's future-work list. Deferred: it is a
  coordinated two-repo change and would invalidate every existing ROI pickle.
- **Record the calibration in the reflectance header.** Writing the gain/offset
  source (and, after Phase 2, the formula version) into the output ENVI metadata
  would let anyone tell a corrected product from an uncorrected one. Deferred
  for the same reason the classifier deferred recording preprocessing in the
  model bundle: it changes an artifact format to guard a case that has happened
  exactly once.
- **Re-apply the mask after smoothing (B6).** A one-line fix, but it changes
  every reflectance product's edge pixels, so it belongs with a reprocessing
  decision rather than ahead of one. If Phase 2 option (1) is chosen, fold it in
  there.
- **Per-column calibration.** The Microscene approach corrects cross-track
  non-uniformity; the empirical line does not. Whether that matters for this
  sensor is an empirical question, and answering it needs a flat-field collect.

### Out of scope unless you ask

Tests and CI (the classifier repo declined these on 2026-07-27; keeping both
repos consistent). Restructuring the notebooks. Packaging the repo — `utils.py`
at the root and `hsiViewer/` as a namespace package both work, and the
run-from-root requirement is documented. Rewriting `spatial_smoothing`, which is
correct for what it does. Anything about the tarps themselves or the collection
protocol.
