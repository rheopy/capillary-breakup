# caber

Video analysis for capillary-breakup (CaBER) extensional rheometry — pip-installable and Pyodide-compatible.

```{toctree}
:maxdepth: 2

quickstart
test_clip
api
```

## Install

```bash
pip install caber          # headless: measure + analyze + CLI
pip install caber[widgets] # + the interactive Jupyter viewer
```

In JupyterLite/Pyodide:

```python
%pip install -q opencv-python pillow ipywidgets caber
```

Note the non-headless `opencv-python` — the build with GUI-less video I/O has no
Pyodide wheel; `opencv-python` was verified to install in Pyodide.

## The method

Each frame is cropped to a region of interest, thresholded to a binary mask of
the filament, and the filament's minimum extent is measured — row widths for a
vertical filament, column heights for a horizontal one. A fully empty line inside
the filament span means breakup (neck = 0).

Close to breakup a Newtonian filament thins linearly
($R(t) = 0.0709\,(\sigma/\eta)\,(t_c - t)$, Papageorgiou 1995), so the thinning
slope gives the viscosity once the surface tension is known.
