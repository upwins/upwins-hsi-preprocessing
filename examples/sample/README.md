# Sample data placeholder

**Nothing ships here yet.** Whether a small runnable example is committed to
this repo is still an open decision (the data owner's call).

If one is added, drop a small example collection here so the notebooks run end
to end from a clone:

- `raw_0_or` + `.hdr` — a raw cube containing the calibration panels (notebook 01)
- `raw_34850_or` + `.hdr` — a raw cube to convert to reflectance (notebook 02)
- `raw_34850_or_ref.img` + `.hdr` — notebook 02's reflectance output, drawn on in
  notebook 03 (produced by running notebook 02, or committed for a from-clone demo)

`config.yaml` already points the image pairs at `examples/sample/...`; keep the
committed example small (crop the cubes) so cloning stays fast. Or edit
`config.yaml` to point at wherever you keep the full data.

This directory sits outside `data/` on purpose — see `examples/README.md`.
