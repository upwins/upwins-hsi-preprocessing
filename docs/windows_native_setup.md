# Windows-Native Setup (fallback to the devcontainer)

A plain Windows Python environment for this repo, driven from VS Code — no
Docker, no WSL, no X/display server. Use it as the **backup path for recording**
if the hsiViewer feels sluggish in the devcontainer: the viewer's PyQt window
becomes an ordinary Windows window drawn by Windows itself, with no display
server between it and the screen, so panning and clicking redraw at native
speed.

Nothing in the repo changes. The notebooks, `config.yaml`, and the code are the
same either way — only where Python lives differs.

> **The devcontainer stays the primary install path** and is what `README.md`
> assumes. This document is the fallback.

---

## 0. Install once

| | What | Notes |
|---|---|---|
| 1 | **Python 3.12.x, 64-bit**, from [python.org](https://www.python.org/downloads/windows/) | **3.12 specifically.** Tick *"Add python.exe to PATH"* and leave the *py launcher* checked. Do **not** use the Microsoft Store build. |
| 2 | **VS Code** for Windows | Not the WSL/container instance — the ordinary Windows app. |
| 3 | VS Code extensions **Python** (`ms-python.python`) and **Jupyter** (`ms-toolsai.jupyter`) | Install them in the **local** window. Extensions installed inside a devcontainer do not carry over. |
| 4 | **Git for Windows** | Only if you are cloning rather than reusing a clone you already have. |

**Why 3.12 and not newer:** `requirements.txt` pins `numpy==1.26.4`,
`scikit-learn==1.5.1` and `pandas==2.2.2`, whose newest Windows wheels are built
for CPython 3.12. On 3.13+ pip finds no wheel and tries to compile them from
source, which fails without a C toolchain. 3.12 also matches the devcontainer.

**Where to put the repo:** somewhere short and local, e.g. `C:\upwins\`. Avoid
OneDrive-synced folders (`Documents`, `Desktop`) — sync locks files mid-write
and collection folder names are long enough to run into the 260-character path
limit.

---

## 1. Create the environment

Open the repo folder in VS Code, then a **PowerShell** terminal (`` Ctrl+` ``),
and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
pip install ipykernel
```

That is the same two-step install the README and the devcontainer do
(`requirements.txt`, then the editable install that puts `upwins_hsi` and
`hsiViewer` on the import path), plus `ipykernel` so VS Code can use the
environment as a notebook kernel. The devcontainer's `Dockerfile` installs
`ipykernel` for the same reason.

Add `pip install jupyterlab` only if you also want the browser Jupyter UI; VS Code
does not need it.

**If activation is blocked** — `Activate.ps1 cannot be loaded because running
scripts is disabled on this system` — allow scripts for this terminal only and
re-run the activate line:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

(Or use a **Command Prompt** terminal instead and activate with
`.venv\Scripts\activate.bat`.)

Your prompt should now start with `(.venv)`. It stays that way for the rest of
this document.

**One venv per repo.** This repo and `upwins-microscene-preprocessing` both
install a package importable as `hsiViewer`; two editable installs in one shared
environment make it ambiguous which copy wins. Give each repo its own `.venv`.

---

## 2. Point VS Code at it

1. Make sure the window is **local**. Look at the bottom-left corner: if it says
   `WSL: …` or `Dev Container: …`, click it and choose *Close Remote Connection*,
   then `File → Open Folder…` on the Windows copy of the repo.
2. `Ctrl+Shift+P` → **Python: Select Interpreter** → `.\.venv\Scripts\python.exe`
   (usually listed as *Recommended*).
3. Open a notebook → click **Select Kernel** (top right) → **Python
   Environments…** → the `.venv` entry.

Do step 3 once per notebook. The kernel picker, not the interpreter picker, is
what notebooks actually use.

`scripts/batch_convert_reflectance.py` runs from the same activated terminal —
`python scripts/batch_convert_reflectance.py`.

---

## 3. Point `config.yaml` at your data

The devcontainer bind-mounts an external data directory over `data/`. There is no
mount natively, so pick one of these — all three leave the notebooks untouched:

**a. Put the data under `data\`** in the repo. `config.yaml`'s placeholder paths
then work as written. `data/` is gitignored in full, so nothing is committed.

**b. Reproduce the mount with a directory junction** (closest to the container
behavior, and no admin rights needed). From a **Command Prompt** in the repo root:

```
mklink /J data C:\upwins\data
```

The junction is inside the gitignored `data/`, so it is never committed. Delete
it with `rmdir data` (this removes the link, not the target).

**c. Use absolute paths in `config.yaml`.** The notebooks resolve configured
paths against the repo root, and an absolute Windows path wins that join, so this
works — but **write them with forward slashes**, which YAML treats literally:

```yaml
collection_dir:  C:/upwins/data/my_collection
cal_image:       C:/upwins/data/my_collection/raw_0_or
cal_image_hdr:   C:/upwins/data/my_collection/raw_0_or.hdr
calibration_dir: C:/upwins/data/my_collection/calibration
```

Backslashes in a YAML scalar are escape characters and will bite you. YAML has no
variable substitution here, so if you change `collection_dir` change the paths
under it too. See `docs/data.md` for what each key means and the expected
collection layout.

---

## 4. Smoke test before you record

With `(.venv)` active:

```powershell
python -c "import numpy, spectral, pandas, sklearn, matplotlib, yaml, PyQt5, pyqtgraph; print('imports ok')"
python -c "from upwins_hsi import utils; from hsiViewer import hsi_viewer_ROI; print('repo ok')"
```

Then confirm the GUI stack actually paints a window — this is the part the
devcontainer does through a display server:

```powershell
python -c "import numpy as np, pyqtgraph as pg; pg.image(np.random.rand(256,256)); pg.exec()"
```

A window should open and pan/zoom smoothly under the mouse. **Close it** to
return the prompt — `pg.exec()` blocks until the window closes, exactly as the
notebook viewer cells do.

Finally, on real data, open `notebooks/01_calibrate_cal_panels.ipynb` and run its
imports cell and the `hvr.viewer(...)` cell that draws the cal-panel ROIs. Draw
one ROI and save it, so you have confirmed the Save dialog too. That is the first
interactive step you record, and `notebooks/03_create_training_rois.ipynb` uses
the same viewer.

---

## 5. What is different on camera

- **The viewer is a normal Windows window.** It can open *behind* VS Code —
  check the taskbar, or alt-tab. Worth knowing before you are recording.
- **Keep VS Code windowed, not fullscreen**, so the viewer window has somewhere
  to land and both stay in frame.
- **A viewer cell shows as still running** the whole time the window is open.
  That is `pg.exec()`, and it is the same in the devcontainer — the cell finishes
  when you close the window.
- **Everything else is identical**: same notebooks, same `config.yaml`, same
  outputs, same running order — the notebooks go top to bottom exactly as they
  do in the container.

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Activate.ps1 cannot be loaded…` | PowerShell execution policy. `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`, then activate again. |
| pip prints *"Building wheel for numpy"* / *"Getting requirements to build wheel"* and fails | Wrong Python. Check with `python -c "import sys; print(sys.version)"` — it must say 3.12 and 64-bit. Delete `.venv` and recreate it with `py -3.12`. |
| `'py' is not recognized` | The py launcher was not installed. Recreate the venv with the full path, e.g. `"C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv`. |
| `ModuleNotFoundError: No module named 'upwins_hsi'` or `'hsiViewer'` | `pip install -e .` was not run in this venv, or the notebook kernel is not the venv. Re-check step 1, then the kernel picker in step 2. |
| `ImportError: DLL load failed while importing QtWidgets` or `Could not find the Qt platform plugin "windows"` | Another Qt on `PATH` (Anaconda, PyQt6, PySide, `opencv-python`) is shadowing PyQt5. Confirm `(.venv)` is active, and keep this venv free of other Qt bindings — `pip list` should show only `PyQt5`, `PyQt5-sip`, `PyQt5-Qt5`, `pyqtgraph`. |
| The viewer window never appears | It is behind another window. Check the taskbar. |
| `FileNotFoundError` on a configured path | The devcontainer mount is not there natively — see step 3. Print the resolved path from the imports cell's `CONFIG['paths']` to see exactly where it looked. |
| Notebook kernel says *ipykernel is required* | `pip install ipykernel` inside the activated venv, then re-pick the kernel. |
| Long-path errors deep in a collection folder | Move the repo and data somewhere short (`C:\upwins\`), or enable Win32 long paths in Windows. |

---

## 7. Going back to the devcontainer

Nothing to undo. `.venv/` is untracked and ignored, and the container has its own
Python — reopen the folder in the container and it behaves as before. If you used
a junction for `data`, remove it first (`rmdir data`) so the container's bind
mount has a clean mount point.
