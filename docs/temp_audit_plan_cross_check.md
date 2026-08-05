# Audit plan cross-check against `research_species_mapping`

Companion to the audit plan now consolidated in `docs/audit_plan_alternate.md`
(the original `docs/audit_plan.md` was folded into it). Every finding in that plan
was checked against the repo it came from — `research_species_mapping` at `df69254`
("initial commit") — to answer one question: **was this problem already there, or did
the handoff introduce it?**

Cross-checked 2026-07-28 on branch `claude/audit-plan-cross-check-2qya0i`.

> **Status note — 2026-07-30.** This document answers *attribution* (pre-existing vs.
> handoff-introduced), and those verdicts are historical facts that do not change. But
> the **codebase has since moved on**: on branch `claude/audit-repo-cleanup-f80o10`
> the owner's handoff decisions and then the remaining correctness/dead-code items
> were implemented over two passes — **nothing ships** (`examples/` deleted, including
> `data/calibration/`-derived artifacts and the cal-tarp library), and **A1a, A1b,
> B1, B2, B4, B5, B6, C1, C5, C6, C7a, C8, C9** are now resolved (B7 mitigated, B8
> moot), leaving only **C4** open. So the byte-identity and "still present" statements
> below describe the tree **as of the 2026-07-28 cross-check**, not today. For current
> per-finding status see `docs/audit_plan_alternate.md` (Status at a glance) and
> `AUDIT_HANDOFF.md` (Handoff-decision cleanup). Paths like `data/calibration/*` and
> `atmospheric_compensation.py` line references are historical.

> **Status note — 2026-08-05, branch `claude/client-repo-docs-consistency-fehfiy`.**
> A docs/comment consistency pass across all three client repos. It changed no
> logic and no attribution verdict below. It does change this document's fate:
> the owner decided that **this file, `AUDIT_HANDOFF.md`,
> `docs/audit_plan_alternate.md` and `docs/recording_runbook.md` are all removed
> before delivery**, and every reference to them has been stripped from the
> shipped tree — including the `(B2)` finding IDs left in
> `scripts/batch_convert_reflectance.py` and notebook 02. Two corrections to
> statuses recorded elsewhere: `utils.py` is **142** lines, not the 64 recorded
> for C1 (the ENVI path helpers were added after the trim), and C4's three unused
> viewer modules must not be deleted in lockstep with
> `upwins-microscene-preprocessing`, which vendors the same package but imports a
> different subset. For the full record and the outstanding-decision task list,
> see *Docs/comment consistency pass* in `AUDIT_HANDOFF.md`.

## Bottom line

**No finding in the audit plan was falsely attributed.** Every issue it raises is
real in the current repo. Fifteen of the eighteen were inherited verbatim from
`research_species_mapping`; three (A1, part of C6, part of C7) are documentation
regressions the handoff introduced, and all three are cheap to fix.

The audit needs four small corrections before you implement against it — two
scope errors, one attribution, one missing piece of evidence. They are in
[Corrections](#corrections-to-apply-to-the-audit-plan) and none of them changes a
phase's shape.

The cross-check also turned up **one behavior change the audit does not mention
at all**: the batch script's calibration coefficients were silently swapped for a
different collect's during the handoff. See [Not in the
audit](#not-in-the-audit-the-batch-script-changed-calibrations).

## Method

Files common to both repos were compared byte-for-byte; notebooks were compared
cell-by-cell on `source` after stripping the handoff's config substitutions.

| Compared | Result |
|---|---|
| `utils.py` | **byte-identical** |
| `hsiViewer/*.py` (all 5) | **byte-identical** |
| `data/calibration/*` — `CalPanels.pkl`, `gain.npy`, `offset.npy`, `panel_{low,mid}_spectra.npy`, `cal_tarp_spectra.{sli,hdr}` | **byte-identical** (md5 match on all 7) |
| `.devcontainer/devcontainer.json`, `.devcontainer/Dockerfile` | **byte-identical** |
| Notebooks 01 / 02 / 03 code cells | identical except hardcoded paths → `CONFIG[...]` lookups |
| Legacy notebook code cells | identical; one markdown banner added |
| `requirements.txt` | rewritten — pinned, `psutil` + `scipy` added, `importlib` removed |
| `.gitignore` | rewritten — blanket `data/` → negation rules for `data/calibration/` and `data/sample/` |
| `README.md`, `data/README.md`, `data/sample/README.md`, `docs/`, `config.yaml`, `LICENSE`, `CITATION.cff` | new in the handoff, no counterpart |
| `atmospheric_compensation.py` → `scripts/batch_convert_reflectance.py` | rewritten (see below) |

Original files with no counterpart here — `analysis_2025_Greenhead_HWref_to_2PNLref.ipynb`,
`old analysis_2025_Greenhead _v2.ipynb` — were dropped by the handoff and are out
of scope for the audit.

## Verdict on every finding

**Pre-existing** — present in `research_species_mapping`, inherited unchanged.
**Introduced** — created by the handoff.
**Amplified** — the underlying flaw pre-existed, but the handoff made it worse or
made it matter more.

| # | Finding | Verdict | Evidence |
|---|---|---|---|
| A1 | No sample imagery, README says otherwise | **Introduced** (the claim; the data gap is pre-existing) | The original committed no cubes either — `.gitignore` was a blanket `data/`, and nb 03 read `data/morven_4000/`, which was ignored. But the original had **no README and made no claim**. Every "runs from a fresh clone" promise is new: `README.md:23-24`, `data/README.md:7`, and — not cited in the audit — `config.yaml:5-6`. |
| A2 | Config's example images don't chain | **Amplified** | The original also converted one image (`D:/Site Collections/Morven_20250708/raw_34850_or`) and inspected another (`data/morven_4000/raw_4000_or_ref.img`) — but they were different hardcoded drives, obviously two unrelated sessions. The handoff put both under `data/sample` in one config, which implies a chain that doesn't exist. |
| B1 | Offset applied inside the gain | **Pre-existing** | Character-for-character identical: orig nb 02 cell 5 = new nb 02 cell 9; `atmospheric_compensation.py:80` = `batch_convert_reflectance.py:67`. |
| B2 | No band-grid check | **Pre-existing** | Same indexing in both, both consumers. |
| B3 | Notebook 02 cell 9 not idempotent | **Pre-existing** in nb 02 — **and the handoff *fixed* the worse half** | Orig nb 02 rebinds `gain = gain[indices]`, same as now. But `atmospheric_compensation.py:67-68` did the same rebinding **inside the per-image loop**, so the original batch script raised `IndexError` on its *second* image, every time. The handoff's `gain_full`/`offset_full` split repaired that. The audit's "the batch script already does this correctly" is true only because of the handoff. |
| B4 | Dead `use_all_regions` branch; unused high tarp | **Pre-existing** | Orig nb 01 cell 18 is identical, `thm` included. |
| B5 | `loadROIs` throws away masks | **Pre-existing** | `hsi_viewer_ROI.py` byte-identical. |
| B6 | Smoothing bleeds into no-data pixels | **Pre-existing** | `utils.py` byte-identical. |
| B7 | `CalPanels.pkl` freezes measured DN | **Pre-existing** | Orig nb 01 cell 8 is identical apart from the literal `'CalPanels.pkl'` becoming a config lookup. |
| B8 | Mid tarp 98.6 % saturated | **Pre-existing** | `CalPanels.pkl` is byte-identical (md5 `f8148ac3…`), as are the derived `panel_mid_spectra.npy` and `gain.npy`. This is a property of the original collect, carried across untouched. |
| C1 | `utils.py` 850 lines, ~51 used | **Pre-existing** — except the `psutil` pin, which is **introduced** | `utils.py` byte-identical. But `psutil` is **not** in the original `requirements.txt`; the handoff added `psutil==6.0.0` to satisfy a dead import. See correction 3. |
| C2 | Devcontainer mount developer-specific + wrong workspace | **Pre-existing** | `devcontainer.json` byte-identical. Note the target `/workspaces/species_mapping/data` matched **neither** repo name — the original directory is `research_species_mapping` — so the rename did not break this; it was already wrong. |
| C3 | CUDA/TensorFlow base image | **Pre-existing** | `Dockerfile` and `runArgs` byte-identical. |
| C4 | Three unused viewer modules | **Pre-existing** | All 5 viewer files byte-identical; the original's notebooks import the same two. |
| C5 | Copy-pasted import block | **Pre-existing** | Cell 1 of each notebook is identical to the original's cell 0, including the `hlv`/`hvr` swap and nb 03's commented-out block. See correction 2 for the count. |
| C6 | Leftover pre-config instruction cells | **Introduced** (staleness) / pre-existing (text) | The two red-HTML cells exist verbatim in the original — where they were **correct**: orig nb 01 cell 3 really did hardcode `dir = 'D:/Site Collections/Morven_20250708'`. The handoff moved paths into `config.yaml` and inserted a contradicting markdown cell directly beneath each, which is what makes them wrong now. The typos (`saturation_trheshold`, "poixels", "so choose") are pre-existing. |
| C7 | Docs overstate what ships; demo run dirties committed files | **Split** | Docs overstatement: **introduced** (there were no docs). Notebook 01 overwriting tracked artifacts: **pre-existing** — orig cell 19 is `np.save('gain.npy', gain)` and `gain.npy` was committed at the repo root, so the same footgun existed, just at a different path. |
| C8 | Developer-local kernel name | **Pre-existing** — but scope is wrong. See correction 1. | Original 01/02 carry `.venv`; original 03/04 already carry `Python 3`. Handoff copied metadata unchanged. |
| C9 | Legacy notebook latent errors | **Pre-existing** | All code cells identical; only a markdown banner was added. |

## Corrections to apply to the audit plan

Four factual fixes. None changes a phase's scope or order.

1. **C8 — only two notebooks, not four.** `03_create_training_rois.ipynb` and
   `notebooks/legacy/train_apply_lda_model.ipynb` already have
   `display_name: "Python 3"`. Only `01_calibrate_cal_panels.ipynb` and
   `02_convert_to_reflectance.ipynb` carry `.venv`. Phase 6 says "in all four
   notebooks" — editing the other two would produce a no-op diff, or a spurious
   one if their `language_info` (Python 3.12.3, vs 3.13.5 for 01/02) is touched
   at the same time. Leave 03 and legacy alone.

2. **C5 — notebook 03 has six commented-out imports, not five.** `#import copy`,
   `#import time`, `#import csv`, `#import importlib`, `#import pickle`,
   `#import utils`.

3. **C1 — reword the `psutil` note.** The plan says trimming `utils.py` "lets
   `psutil` come out of `requirements.txt`, which is only there for `utils.py`'s
   unused import." Accurate about *why* it is there, but it reads as though the
   pin were inherited; it was added during the handoff, to satisfy an import that
   was already dead. Removing it reverts a handoff change rather than cleaning up
   legacy. **While you are in that file: `scipy==1.13.1` was also added by the
   handoff and is imported nowhere** — not in `utils.py`, the scripts, or any
   notebook. The audit does not mention it. Drop it in Phase 5 alongside
   `psutil`, or keep it deliberately if you want `spectral`'s optional
   scipy-backed paths available.

4. **A1 — add `config.yaml:5-6` to the evidence.** The header comment says "a
   small calibration set ships under `data/calibration/` so notebooks 02-03
   reproduce from a clone." That is the same false claim as `README.md:23-24` and
   `data/README.md:7`, and Phase 1's reword has to catch it too — it is easy to
   miss because it is a comment rather than prose. Worth noting that
   `data/sample/README.md` and `docs/recording_runbook.md` are already honest
   ("Drop a small example collection here", "Confirm the data is reachable"), so
   only three places need changing and two documents already contradict the other
   three.

## Not in the audit: the batch script changed calibrations

`atmospheric_compensation.py` carried its gain and offset arrays **hardcoded
inline** — 343 values each, pasted into the source, from the
`Greenhead_May2025` collection it pointed at. `batch_convert_reflectance.py`
replaced them with `np.load(CONFIG["paths"]["gain"])`, i.e. the committed
`gain.npy` from the Morven collect.

These are not the same numbers:

| | hardcoded (original) | committed `gain.npy` / `offset.npy` |
|---|---|---|
| gain range | 9.60e-05 … 3.87e-03 | 9.16e-05 … 4.43e-03 |
| offset range | −0.02167 … **+0.01613** | −0.02153 … +0.00551 |
| max abs difference | gain **1.06e-03**, offset **1.62e-02** | — |

Both are 343-band, so the same sensor configuration — but a gain difference of
1.06e-03 is larger than the mean gain itself (7.82e-04), and the offsets differ
by up to 0.0162 in reflectance units.

**This is almost certainly the right change** — config-driven coefficients are
the whole point of the restructure, and a batch script that ships someone's
pasted numbers is worse. Three things follow from it anyway:

- **It is undocumented.** Nothing in the README, the runbook, or the script's
  docstring says the batch script used to apply a different collect's
  calibration. Anyone re-running it over the Greenhead archive expecting the old
  output will get different numbers, for a reason they cannot see.
- **It sharpens B2.** The original's inline arrays made the band-grid dependency
  visible — 343 numbers in the file. Loading `gain.npy` hides it, so the Phase 3
  guard matters more now than the audit's framing suggests.
- **It narrows B1's blast radius, slightly.** The audit says the ~+0.015 bias
  affects "every reflectance product this repo has ever written." True of the
  formula, but the *magnitude* was computed from the committed coefficients
  only. Products made by the original batch script were biased by
  `gain·offset` on the Greenhead numbers instead — same defect, different size,
  and their offsets are positive across the blue end where the committed ones
  are not. If you take Phase 2 option (1) and reprocess, this is moot. If you
  take option (2), forward-only, the archive is not uniformly biased the way the
  plan assumes, and that is worth knowing before mixing anything into one
  training set.

## What the handoff fixed

Recorded so it is not undone by accident:

- **The batch script's multi-image `IndexError`** (B3's other half) — the
  original crashed on the second image of every run. `gain_full`/`offset_full`
  fixed it.
- **`.gitignore`** — the blanket `data/` became negation rules, which is what
  lets the calibration set be committed at all. The audit's note that A1 is not
  a `.gitignore` problem is correct and worth keeping: these rules work.
- **Dead `min_wl`/`max_wl` locals** in `atmospheric_compensation.py:49-50`,
  dropped in the rewrite.
- **`importlib`** removed from `requirements.txt` — it is stdlib and the pip
  package of that name is an unrelated backport.

## What this changes about the plan

Very little, which is the useful result. Specifically:

- **Phase 2 stays the highest-value phase.** B1, B2 and B3 are all pre-existing
  and all still real.
- **Phase 3 stays where it is.** B7 and B8 rest on a `CalPanels.pkl` that is
  byte-identical to the original's, so the audit's analysis of it transfers
  intact — including the 3048 → 43 saturation result.
- **Phase 1 is cheaper than it looks.** A1's fallback ("I correct the
  documentation instead") does not degrade the repo relative to where it started
  — the original never claimed a from-clone run. Rewording three places restores
  accuracy rather than conceding something.
- **C6 is worth doing even if you skip the rest of Phase 3.** Those two cells
  are the one place the handoff left instructions that are now actively wrong,
  and they sit directly above the correct instruction.
- **Nothing found here justifies reverting a handoff decision.** The restructure
  did not introduce a correctness bug; the calibration-source swap in the batch
  script is a behavior change to document, not to undo.
