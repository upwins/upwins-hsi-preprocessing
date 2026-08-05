"""Interactive hyperspectral viewer and ROI tools (PyQt5).

This copy is the source of truth for the package. Companion UPWINS repos carry
verbatim synced copies of it, so fix bugs here and re-sync rather than patching
a copy, or the two diverge.

The import name `hsiViewer` is load-bearing: every ROI pickle on disk records
its class as `hsiViewer.hsi_viewer_ROI.ROIs_class`, so renaming this package
silently breaks unpickling of existing ROI files, here and anywhere else those
pickles are read.
"""
