# Examples

Everything the repo ships for a run lives here, outside `data/`. Two things:

- **`calibration/`** — the committed calibration reference set (cal-tarp
  library, cal-panel ROIs, and the per-band `gain`/`offset` coefficients).
  Notebook 02 and the batch script read `gain`/`offset` from here by default.
- **`sample/`** — a placeholder for a small raw + reflectance example so the
  notebooks run end to end from a clone. See `examples/sample/README.md`.

## Why this is not under `data/`

The devcontainer bind-mounts an external directory onto `data/`, which replaces
the whole directory inside the container — anything committed under `data/`
would be invisible there. `examples/` sits outside the mount, so committed
content works both in a plain clone and in the container. See `docs/data.md`.
