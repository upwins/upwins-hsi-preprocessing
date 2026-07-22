# Data

Large imagery is **not** committed. What ships:

```
data/
├── calibration/       Committed calibration set (small), so notebooks 02-03 reproduce:
│   ├── cal_tarp_spectra.sli / .hdr   ASD cal-tarp reference library
│   ├── CalPanels.pkl                 saved cal-panel ROIs (from the hsiViewer step in nb 01)
│   ├── panel_low_spectra.npy         intermediate panel spectra
│   ├── panel_mid_spectra.npy
│   ├── gain.npy / offset.npy         per-band calibration coefficients
└── sample/            Drop a small raw + reflectance example here for a runnable demo
```

## Full data

Point the `*_image_dir` entries in `config.yaml` at your real collection
directory for recording, or copy a raw cube + its reflectance product into
`data/sample/`. Raw ENVI cubes are large, so keep committed samples small.
