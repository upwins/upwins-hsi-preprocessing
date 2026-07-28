# Audit Handoff — upwins-hsi-preprocessing

> **Working document, not part of the client deliverable.** Delete this file before
> merging to `main` / shipping.

**Audited:** `upwins-hsi-preprocessing` @ `be9923e` (branch `claude/upwins-hsi-preprocessing-audit-ma57o5`,
identical to `main`) against `research_species_mapping` @ `df69254`.
**Audit was read-only** — no code was changed. Everything below is unimplemented.

**Second pass (this revision):** reviewed against the already-cleaned companion repo
`upwins-veg-classifier` @ `ee8b474`, which ships to the same client and consumes this
repo's outputs. The fixes below have been rewritten to use the patterns that repo already
established, so the two deliverables look and behave the same. Where a recommendation
changed from the first pass, it is marked **[revised]**. Section 3 is the new consistency
baseline; read it before implementing anything.

**Goal being audited against:** consolidate notebook configuration into one config file,
and make the notebooks straightforward to run from a clone of the repo.

**Verdict:** the science is faithful; the packaging is not runnable. The port preserved the
numerical content essentially perfectly, but moving the notebooks into `notebooks/` broke
every relative path, and the docs promise a from-clone run that the repo cannot currently
deliver. The companion repo already solved every one of these problems — this repo should
copy those solutions rather than invent new ones.

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

> **Note for P0-1:** the fix below relocates `utils.py` and `hsiViewer/` into `src/`.
> Do this with `git mv` — the file *contents* stay byte-identical, so the table above
> still holds. Only the import statement in the notebooks changes.

---

## 2. What the companion repo already does — the consistency baseline

`upwins-veg-classifier` (cleaned, same client, consumes this repo's reflectance images
and ROI pickles) has already made a decision on each of these problems. Use its answer.
Files worth reading side-by-side before starting: its `pyproject.toml`, `config.yaml`,
`.gitignore`, `.devcontainer/devcontainer.json`, `docs/data.md`, and the setup cell of
`notebooks/01_train_multitask_cnn.ipynb`.

| Problem | `upwins-veg-classifier`'s answer | This repo today | Item |
|---|---|---|---|
| Notebooks in `notebooks/`, config at root | `REPO_ROOT` walk-up + absolutize every configured path. **No `os.chdir`, no `sys.path` mutation.** | `open('config.yaml')` — breaks | P0-1 |
| Importing repo code from a notebook | `src/` layout + `pyproject.toml` + `pip install -e .` | bare `import utils` / `from hsiViewer import …` — breaks | P0-1 |
| Editable install in the container | `"postCreateCommand": "python -m pip install --no-cache-dir -e ."` | absent | P0-1 / P1-3 |
| Devcontainer data mount | `source=${localEnv:HOME}/projects/upwins/data`, correct workspace name, 5-line comment + README/`docs/data.md` warning | hardcoded `/home/jwvandyke/...`, **wrong** target repo name | P1-3 |
| Data directory | `data/` gitignored **in full**; nothing shipped lives there | `data/calibration/` committed *inside* the future mount point | P0-3 |
| Shipped runnable example | top-level `examples/` — deliberately outside the mount | `data/sample/` — inside the mount | P0-3 |
| Notebook outputs | written under gitignored `data/` | written over tracked files | P1-6 |
| Data documentation | `docs/data.md` | `data/README.md` (invisible once mounted) | P1-10 |
| README structure | Quickstart → notebook table → **Layout** → Data → *If you use the devcontainer* → Acknowledgment | no Layout section, no devcontainer subsection | P1-10 |
| ENVI path convention | explicit pair: `image` + `image_hdr` | mixed: two extension-less, one with `.img` | P1-5 |

**Already consistent — leave alone:** `LICENSE` (MIT, "Copyright (c) 2025 upwins"),
`CITATION.cff` (same shape, same NSF grant), `requirements.txt` (pinned, commented
header explaining *why* pinned), the "markdown cell above every code cell" narration
style, and the `docs/recording_runbook.md` structure (both are "Video 1 / Video 2" of
one series and cross-reference each other correctly).

---

## 3. P0 — Blocking. The repo does not run from a clone.

### P0-1. Moving notebooks into `notebooks/` broke every path  **[revised]**

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

> **The first pass recommended a `os.chdir` + `sys.path.insert` bootstrap block. Do not
> use it.** `upwins-veg-classifier` splits this into two separate mechanisms, and that
> split is better as well as consistent: `sys.path.insert` accumulates duplicate entries
> on every cell re-run, and `os.chdir` mutates process-global state that later cells and
> the viewer inherit. The packaging approach has neither problem.

**Recommended fix — copy the companion repo's two mechanisms.**

**(a) Imports: `src/` layout + editable install.** Add a `pyproject.toml` modelled on the
companion's, including its two explanatory comments (why `license = {text = "MIT"}` is
kept as a table, and why there is deliberately no `[project.dependencies]` — the pins in
`requirements.txt` are the single source of truth):

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "upwins-hsi-preprocessing"
version = "1.0.0"
description = "Empirical-line calibration of hyperspectral imagery to reflectance, and interactive ROI collection."
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}          # + the companion's "do not modernize" comment

[tool.setuptools.packages.find]
where = ["src"]
```

Then restructure (all moves are `git mv`; contents unchanged):

```
src/upwins_hsi/__init__.py        new — one-line docstring, mirrors src/upwins_veg/__init__.py
src/upwins_hsi/utils.py           was utils.py (byte-identical)
src/hsiViewer/__init__.py         new — REQUIRED: setuptools' packages.find skips
                                  directories without one, and there is none today
src/hsiViewer/hsi_viewer*.py      the 5 files, byte-identical
```

Verified safe: no module inside `hsiViewer/` imports `utils` or any sibling `hsi_viewer_*`
module, and `utils.py` imports nothing local — so the move creates no broken references.

Notebook/script edits: `import utils` → `from upwins_hsi import utils` (notebook 02,
`legacy/`, and `scripts/batch_convert_reflectance.py`). **`from hsiViewer import …` stays
exactly as-is** — that import path must not change, because `CalPanels.pkl` and every ROI
pickle this repo produces record the class as `hsiViewer.hsi_viewer_ROI.ROIs_class`, and
`upwins-veg-classifier` ships a stand-in class at that same path to unpickle them. Renaming
`hsiViewer` here would silently break the companion repo's training notebook.

**(b) Paths: `REPO_ROOT` walk-up, no `chdir`.** Use the companion's block verbatim (its
`notebooks/01_train_multitask_cnn.ipynb` cell 4), adapted to this repo's config sections:

```python
# config.yaml (and the paths inside it) are relative to the repo root, but
# this notebook lives in notebooks/. Locate the repo root and resolve every
# configured path against it so it works from either directory.
REPO_ROOT = Path.cwd()
while not (REPO_ROOT / 'config.yaml').exists() and REPO_ROOT != REPO_ROOT.parent:
    REPO_ROOT = REPO_ROOT.parent

with open(REPO_ROOT / 'config.yaml') as _f:
    CONFIG = yaml.safe_load(_f)
for _section in ('paths', 'batch'):
    for _key, _val in CONFIG.get(_section, {}).items():
        if isinstance(_val, str):
            CONFIG[_section][_key] = str(REPO_ROOT / _val)
```

Two adaptations this repo needs that the companion did not:

- The section list is `('paths', 'batch')`, not `('paths', 'prediction')`.
- **`paths.cal_image`, `paths.raw_image` and `paths.reflectance_image` are bare ENVI file
  *names*, not paths** — absolutizing them would produce `<root>/raw_0_or`. Either exclude
  those three keys from the loop, or fold them into their `*_image_dir` first. Resolving
  P1-5 by collapsing each dir+name pair into a single path key removes this wrinkle
  entirely and is the cleaner order of operations — do P1-5 first.

Also apply the same walk-up in `scripts/batch_convert_reflectance.py`, which currently does
`open("config.yaml")` and only works from the repo root; its docstring says so, and that
constraint can just go away.

Then update the runbook's checklist line to
`pip install -r requirements.txt && pip install -e .` — matching the companion runbook's
"Before you hit record" item word for word — and drop the false "launch from the repo root
so imports resolve" claim.

Alternatives considered and rejected: moving the notebooks back to the repo root (works,
but reverts a deliberate choice *and* diverges from the companion); a `sys.path` bootstrap
(diverges, and re-run-hostile).

**Acceptance:** from a fresh clone — `pip install -r requirements.txt && pip install -e .`,
launch `jupyter lab` from the repo root, open `notebooks/02_convert_to_reflectance.ipynb`,
run the first three cells: config loads, `upwins_hsi.utils`/`hsiViewer` import, `gain`/`offset`
load with shape `(343,)`. Repeat with `jupyter lab` launched from inside `notebooks/` — the
companion repo passes both, and so must this one.

### P0-2. Docs promise a from-clone run that is not possible

`data/sample/` contains only a `README.md`, but `config.yaml` defaults point into it
(`raw_0_or`, `raw_34850_or`, `raw_4000_or_ref.img`). Two claims are therefore false today:

- `README.md`: "A small calibration set ships in `data/calibration/` so notebook 02
  (and the non-interactive cells of 01) run from a fresh clone."
- `data/README.md`: "Committed calibration set (small), so notebooks 02-03 reproduce"

Shipping calibration alone does **not** make 02 runnable — 02 needs a raw cube to convert.
This is gated on the open decision in §6; fix the claims to match whichever way it goes.

**Consistency note.** The companion repo has the *same* unresolved gap and handles it
honestly rather than by claiming otherwise: its `README.md` says plainly "No data ships in
the repo", `examples/README.md` says "Placeholder — **nothing ships here yet**", and
`docs/data.md` carries an explicit `> **TODO (data owner):** add the download link or DOI
here.` Whatever §6 decides, both repos should end up telling the client the same story.
If the answer is "no sample data ships", copy the companion's wording; do not leave this
repo asserting a from-clone run that the companion correctly disclaims.

### P0-3. The devcontainer mount will hide the shipped calibration set  **[new]**

This is an interaction between P1-3 and the committed data, and it is why P1-3 cannot be
fixed naively.

`data/calibration/` is committed and *not* gitignored (verified — `git check-ignore`
matches nothing under it). The devcontainer's `mounts` entry bind-mounts a host directory
onto `data/` inside the container. A bind mount **replaces the entire directory view**:
everything committed under `data/` becomes invisible inside the container.

Today this is masked by a bug — the mount target is `/workspaces/species_mapping/data`
(the *old* repo name), so it lands outside the workspace and `data/` survives untouched.
**Fixing the target path, as P1-3 requires, activates the collision:** the shipped
calibration set, `data/README.md`, and `data/sample/README.md` all disappear in the
container, and the notebooks fail with confusing missing-file errors.

The companion repo hit this and designed around it. Its `.gitignore` ignores `data/` in
full with the comment "Anything the repo does ship for a run lives outside `data/`", and
its `examples/README.md` has a section titled *"Why this is not under `data/`"* stating
the rule explicitly.

**Fix — adopt the same rule.** Move everything the repo ships for a run out of `data/`:

```
examples/calibration/    was data/calibration/ — the committed reference set
examples/README.md       was data/sample/README.md, rewritten in the companion's shape,
                         including its "Why this is not under data/" section
docs/data.md             was data/README.md (see P1-10)
data/                    gitignored in full; external imagery + run outputs only
```

Then update `paths.cal_library_sli`, `cal_library_hdr`, `cal_panel_rois`, `gain` and
`offset` in `config.yaml` to point at `examples/calibration/...`, and rewrite `.gitignore`
as a full `data/` ignore with the companion's explanatory comments. This is a strict
improvement even setting the container aside: it is what makes P1-6 disappear.

---

## 4. P1 — Fix before client handoff

### P1-3. `.devcontainer/` was copied verbatim and is client-hostile  **[revised]**

`README.md` offers it as an install path ("or use the devcontainer"), but:

- `devcontainer.json` bind-mounts a personal path:
  `source=/home/jwvandyke/projects/upwins/data,target=/workspaces/species_mapping/data`.
  The target uses the **old repo name**, so in this repo the data lands outside the
  workspace and `data/` stays empty. It also leaks the maintainer's local filesystem layout.
- `"runArgs": ["--gpus","all"]` hard-requires an NVIDIA GPU; a client without one cannot open it.
- Base image `nvcr.io/nvidia/tensorflow:24.12-tf2-py3` is ~20 GB, for a project that uses no TensorFlow.
- `"name": "tf2-py3"` describes a stack this repo does not use.
- No `postCreateCommand`, so the editable install from P0-1 would not happen in the container.

**Fix — match the companion's *structure and comments*, not its base image.**

Copy verbatim from `upwins-veg-classifier/.devcontainer/devcontainer.json`:

- The `mounts` line's form: `source=${localEnv:HOME}/projects/upwins/data,target=/workspaces/upwins-hsi-preprocessing/data,type=bind,consistency=cached`
  — `${localEnv:HOME}` instead of a hardcoded home, and the **correct** repo name in the target.
- The comment block above it, adapted: what it does, that the host path is hardcoded, that
  Docker silently creates an empty directory if the source does not exist, and a pointer to
  the Data section of `README.md`.
- `"postCreateCommand": "python -m pip install --no-cache-dir -e ."`, with the companion's
  comment ("Runs after the workspace is mounted, so the editable install points at the live
  source tree rather than a build-time copy").

**Deliberately diverge on the image, and say so in a comment** so nobody later "makes them
consistent" and puts the 20 GB image back:

- Drop `"runArgs": ["--gpus","all"]`. The companion keeps it because it trains a TensorFlow
  CNN and genuinely wants the GPU; **this repo runs no TensorFlow and no CUDA code at all**
  (`requirements.txt` has no TF), so requiring an NVIDIA GPU only locks clients out.
- Base image `python:3.11-slim` with `python3-pyqt5` installed via apt (the existing
  Dockerfile already installs `python3-pyqt5` — keep that line, change only the `FROM`).
- Rename `"name"` from `tf2-py3` to something accurate, e.g. `upwins-hsi-preprocessing`.

### P1-4. Default config doesn't chain across notebooks

Notebook 02 converts `raw_image` (`raw_34850_or`) and writes `raw_34850_or_ref`, but
`reflectance_image` defaults to `raw_4000_or_ref.img`. So 02's own viewer cell and all of
notebook 03 read something 02 did not produce. Inherited from the originals (which pointed at
two different collections), but it defeats "straightforward to run from a clone."

**Fix:** make the defaults chain — `reflectance_image` should default to the `_ref` product of
`raw_image`, either by convention in the config or derived in the notebook.

Precedent for deriving-in-the-notebook: the companion's `03_display_classification.ipynb`
rebuilds its input path from the config rather than storing a second, driftable copy —
`base = os.path.splitext(os.path.basename(CONFIG['prediction']['input_hdr']))[0]`, then
`f"{base}_{TASK}_classification.hdr"`, with a comment explaining the naming rule. Do the
same here: derive `<raw_image>_ref` in notebook 02/03 and comment it, rather than asking the
user to keep two config keys in sync by hand.

### P1-5. `config.yaml` extension convention is inconsistent  **[revised]**

`cal_image` and `raw_image` are extension-less ENVI base names; `reflectance_image` includes
`.img`. Nothing flags the difference. Notebook 02/03 paper over it with
`.rsplit('.', 1)[0] + '.hdr'`, which tolerates both for the header but not for the image file —
a user who follows the other two entries' convention gets a failure inside `spectral.envi.open`.

The companion's convention is an **explicit pair** with a comment:

```yaml
  # Reference reflectance image used to read the sensor's band centers
  # (ENVI cube: give the file with and without the .hdr extension).
  image:     data/sample/raw_0_ref
  image_hdr: data/sample/raw_0_ref.hdr
```

**Recommendation:** go extension-less for all three and derive `.hdr`/`.img` in code — and
collapse each `*_image_dir` + `*_image` pair into a single path key while you are in there
(`cal_image: data/sample/raw_0_or`), which is what P0-1(b)'s absolutize loop wants. A user
cannot create a mismatch with one key; with the companion's pair they can point `image` and
`image_hdr` at different cubes. Comment the convention in `config.yaml` the way the
companion comments its own.

**If exact key-shape parity across the two repos matters more**, the alternative is to adopt
the companion's explicit pair here instead (`reflectance_image` + `reflectance_image_hdr`).
That is a legitimate choice — it needs no change in the companion — but it keeps the
mismatch hazard. Either way, pick one and comment it; do not ship three keys with two
conventions. The owner's call; the first option is the recommendation.

### P1-6. Notebook 01 overwrites tracked, shipped files  **[revised]**

Cells 21 and 34 write `panel_low_spectra.npy`, `panel_mid_spectra.npy`, `gain.npy`, `offset.npy`
into `data/calibration/`, which is committed and **not** gitignored (verified with
`git check-ignore`). Running 01 dirties the working tree and clobbers the reference calibration
the repo ships.

**Fix: this is resolved for free by P0-3** — no separate mechanism needed. Once the shipped
reference set lives in `examples/calibration/` (read-only, committed) and `data/` is
gitignored in full, point notebook 01's *output* keys at `data/calibration/`. Writes then land
in ignored space, the working tree stays clean, and the shipped reference is untouched. This
is exactly the companion's arrangement: every notebook output there (`paths.metrics_dir`,
`prediction.output_dir`, `paths.model_dir`) goes to gitignored space, with the one small
committed bundle kept out of the way.

Separate the config keys accordingly — inputs read from `examples/`, outputs write to
`data/` — and comment which is which. Note the shipped set is exactly reproducible (§1), so
it can always be regenerated.

### P1-10. Docs layout parity  **[new]**

Small, mechanical, and worth doing because the client will open both repos side by side.

- **`data/README.md` → `docs/data.md`.** Same content, same filename as the companion's, and
  it stops being invisible under the container mount (P0-3). Mirror the companion's section
  order: *Expected layout* → *Where the data comes from* → *Getting the full dataset* (with
  the same `> **TODO (data owner):**` marker if there is no link yet) → *The devcontainer
  mount*.
- **`data/sample/README.md` → `examples/README.md`**, rewritten in the companion's shape,
  including its *"Why this is not under `data/`"* closing section.
- **Add a `## Layout` section to `README.md`**, matching the companion's — a fenced block
  with one line per top-level entry. This repo has no such section today.
- **Add an `### If you use the devcontainer` subsection under Data in `README.md`**, with the
  companion's `source=… -> …` arrow diagram and its bolded *"The host path is hardcoded"*
  warning.
- **Update the Quickstart** to include `pip install -e .` with the companion's inline comment
  (`# makes upwins_hsi importable`) and its "The devcontainer does both of these steps for
  you" note.
- **No `.env.example`.** The companion has one only because it can refresh its spectral
  library from MongoDB. This repo reads no credentials, so do not add an empty one for
  symmetry's sake. `.env` should stay in `.gitignore` either way.

---

## 5. P2 — Worth a comment, not a rewrite

### P2-7. `gain = gain[indices]` re-run hazard in notebook 02

Cell 9 rebinds `gain`/`offset`, which cell 3 loaded. Re-running cell 9 without re-running
cell 3 double-subsets and raises `IndexError`. Faithful to the original; add a one-line comment
or reload inside the cell.

This is the same bug that made the original `atmospheric_compensation.py` unusable — see §7.

### P2-8. Inherited math discrepancy in the reflectance formula

Notebook 02 and the batch script apply:

```python
imRef[:, :, i] = (gain[i] * np.squeeze(im.read_band(b) + offset[i]) * mask)   # gain*(counts + offset)
```

Notebook 01 **fits** the coefficients as `reflectance = m·counts + b`, and the original
`old analysis_2025_Greenhead _v2.ipynb` applies `gain[i]*counts + offset[i]` — the form matching
the fit. The source repo disagrees with itself; the port faithfully copied notebook 2's version.

**Not a porting error, and not for a new session to silently "fix."** Flag it to the owner
for a science decision; a client will run this code.

### P2-9. Unverified metadata assertions

These appear only in the new repo — the original has no README or license:

- NSF Grant No. 2319470 (`README.md`, `CITATION.cff`)
- MIT License, "Copyright (c) 2025 upwins"
- the companion repo name `upwins-veg-classifier`

Confirm with the owner before handoff. Do not invent replacements.

**Update from the consistency pass:** all three assertions are *identical* in
`upwins-veg-classifier`, which the owner has already reviewed and cleaned — same grant number in
its `README.md` and `CITATION.cff`, same `MIT License / Copyright (c) 2025 upwins`, and its
docs name this repo as the companion. That raises confidence but is not confirmation: if
one is wrong it is wrong in both places, and both would need the same correction. Still
worth one explicit yes from the owner.

### P2-11. Leftover research-style instruction in notebook 01  **[new]**

Cell 3 of `01_calibrate_cal_panels.ipynb` is a raw HTML markdown cell:

```html
<p style="color:red">Change the dir and fname so choose the image for your collection with the cal panel.</p>
```

It has a typo, it uses inline red HTML that nothing else in either repo uses, and it tells
the user to edit the notebook — contradicting `config.yaml`'s own header ("Edit paths/
parameters here rather than in the notebooks"). The following cell already says the right
thing ("Set this image in `config.yaml`"). Delete it, or fold it into that cell as plain
markdown.

---

## 6. Decisions needed from the owner — do not guess

> **On names.** This document refers only to "the owner." An earlier revision named a
> person; that name was never stated anywhere in these three repos and had been inferred
> from the `/home/jwvandyke/` path in `devcontainer.json`. Do not reintroduce a name, and
> do not infer pronouns, without being told one.

### 6a. Blocking — answer these before an implementing session starts

Proceeding on a guess here produces work that has to be redone.

1. **Sample data — now a two-repo decision.** Either (a) commit a small raw cube + a
   reflectance cube so notebooks 02/03 genuinely run from a clone — then the README claims
   become true; or (b) ship no sample data — then P0-2's claims must be rewritten to say the
   user must supply their own imagery and edit `config.yaml` first. Do not leave the current
   mismatch.

   `upwins-veg-classifier` has the *same* decision open (its `examples/README.md` is an
   explicit placeholder and its trained model bundle is not committed either, so it cannot
   run from a clone today). Answer it once for both repos and apply the same answer to both
   — a client who can run one from a clone but not the other will assume something is broken.
   If the answer is (a), note that per P0-3 the committed example must live in `examples/`,
   not `data/`, in both repos.

   *This decision drives:* P0-2, P0-3's directory layout, the config defaults, and the
   README / `docs/data.md` / `examples/README.md` wording in **both** repos. It is the one
   answer the most other work hangs off.

2. **Scope: is the implementing session allowed to change `upwins-veg-classifier` too?**
   This document is titled for `upwins-hsi-preprocessing`, but three of its items are
   inherently cross-repo: decision 1 above, the §8 parity defects, and P1-5 if the explicit-pair
   convention is chosen. Say either "preprocessing only, file the rest" or "both repos, one
   branch each." Without an answer a session will either overstep or silently drop §8.

3. **P2-8, the reflectance formula discrepancy.** `gain*(counts + offset)` as shipped, versus
   `gain*counts + offset` as notebook 01 fits and as the original Greenhead notebook applies.
   A science decision, not a code decision — a client will run whichever ships. No default
   is offered on purpose.

### 6b. Has a stated default — a session can proceed, but confirm if you disagree

4. **P1-5**, which ENVI path convention both repos should use. *Default:* extension-less
   everywhere, `.hdr`/`.img` derived in code, `*_image_dir` + `*_image` collapsed into one
   key per image. Alternative is the companion's explicit `image` + `image_hdr` pair.
5. **P2-9**, grant number / license / companion repo name. *Default:* leave as-is — all three
   already match the reviewed companion repo. Confirming costs one sentence; if one is wrong
   it is wrong in both repos.
6. **The second calibration set** (§7). The coefficients embedded in the dropped
   `atmospheric_compensation.py` are numerically different from the committed ones and are a
   separate calibration. *Default:* do not preserve them — they remain in
   `research_species_mapping` history. Say so if that calibration matters and it should ship
   as a second `.npy` pair with a provenance note.
7. **The dataset download link or DOI** for `docs/data.md`. *Default:* carry the companion's
   `> **TODO (data owner):**` marker across unchanged. Supply a link or DOI if one exists.
8. **The package name** for the `src/` layout. *Default:* `upwins_hsi`, mirroring
   `upwins_veg`. Cosmetic; say if you want something else, because renaming after the fact
   touches every notebook.

---

## 7. Context: `atmospheric_compensation.py` was dropped — this was correct

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
the shipped calibration directory with a provenance note — do not keep the script. It remains
recoverable from `research_species_mapping` history either way.

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

## 8. Small defects found *in* `upwins-veg-classifier` — for parity  **[new]**

Found while reviewing it as the consistency baseline. Not this repo's bugs, and none are
blocking, but they should be fixed there so the pair ships clean. Listed here because this is
the live handoff document; move them to that repo's tracker if you prefer.

1. **`README.md` says "run the two notebooks in order"** (twice — in the Quickstart and in
   the Layout block's `notebooks/` line) but the table below it lists **three**. The third,
   `03_display_classification.ipynb`, was evidently added later. Say "three".
2. **The Layout block claims `docs/` holds "executed HTML exports of the notebooks."**
   `docs/` contains only `data.md`, `model_card.md` and `recording_runbook.md` — no HTML.
   The exports are an *action item* in that repo's runbook §4 ("Export executed copies to
   `docs/`"), not a shipped artifact. Either produce them or drop the claim; as written it
   is the same class of false promise as P0-2 here.
3. **The Layout block describes `models/example_model_v1/` as "The trained model bundle
   (model + scaler + label maps + wavelengths)".** That directory contains only a `README.md`
   and a `model_card.md` pointer — the four bundle files are not committed, and the directory's
   own README says "Running `notebooks/01…` writes the trained bundle here." So notebook 02
   cannot run from a fresh clone. This is that repo's half of decision §6.1 and should be
   answered with it.

---

## 9. Verification recipe

To re-verify after fixes (a throwaway venv is enough; the pinned requirements install clean):

```bash
python3 -m venv /tmp/v
/tmp/v/bin/pip install -r requirements.txt
/tmp/v/bin/pip install -e .            # P0-1(a): puts upwins_hsi + hsiViewer on the path

# P0-1(b): must now succeed from the notebooks/ directory
cd notebooks && /tmp/v/bin/python -c "
import sys; from pathlib import Path
import yaml, pickle, numpy as np
r=Path.cwd()
while not (r/'config.yaml').exists() and r!=r.parent: r=r.parent
C=yaml.safe_load(open(r/'config.yaml'))
import hsiViewer.hsi_viewer_ROI          # required to unpickle CalPanels.pkl
from upwins_hsi import utils
print('gain', np.load(r/C['paths']['gain']).shape)
print('rois', pickle.load(open(r/C['paths']['cal_panel_rois'],'rb')).names)
"
```

Note the test does **not** `chdir` and does **not** touch `sys.path` — if it passes without
them, P0-1 is genuinely fixed rather than papered over.

PyQt5 imports fine headless with `QT_QPA_PLATFORM=offscreen`; only the interactive viewer
windows in notebooks 01/03 need a real display.

Also verify the container half of P0-3 before shipping: build the devcontainer with the
corrected mount target and confirm the shipped calibration set is still visible inside it
(`ls examples/calibration/`). If anything the notebooks need is still under `data/`, it will
be gone.

**Suggested order:** P0-1(a) packaging → P1-5 (config key shape, since P0-1(b) depends on it)
→ P0-1(b) path resolution → P0-3 (the `examples/` move, which also closes P1-6) → the §6
decisions → P0-2 and P1-10 docs to match whatever was decided → P1-3, P1-4 → P2.
