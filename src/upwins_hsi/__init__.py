"""Support code for the UPWINS hyperspectral preprocessing notebooks.

Installed onto the import path by `pip install -e .`, so the notebooks in
`notebooks/` and the script in `scripts/` can import it without any `sys.path`
mutation or `os.chdir`.

Modules:

- `utils`  -- spatial smoothing, and the ENVI path helpers that define the
              `_ref` product name shared by the notebooks and the batch script.
"""
