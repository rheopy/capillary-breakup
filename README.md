# caber — capillary-breakup video analysis

[![CI](https://github.com/rheopy/capillary-breakup/actions/workflows/ci.yml/badge.svg)](https://github.com/rheopy/capillary-breakup/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/capillary-breakup/badge/?version=latest)](https://capillary-breakup.readthedocs.io/en/latest/)

A pip-installable, Pyodide-compatible library for analyzing capillary-breakup
(CaBER) extensional rheometry videos: video in → filament neck radius vs time
→ thinning analysis.

```python
import caber

# headless: video -> neck size vs time
df = caber.measure_video("filament.mp4", polarity="dark", axis="horizontal", fps=100)

# Newtonian thinning analysis (Papageorgiou similarity solution)
summary = caber.thinning_summary(df, mm_per_px=0.0263,
                                 surface_tension_mN_per_m=30.0)
print(summary["fit"])            # slope, t_c, R^2 ...
print(summary["viscosity_Pa_s"]) # from the thinning slope
```

Interactive ROI definition in a notebook (works in JupyterLite/Pyodide):

```python
%pip install -q opencv-python pillow ipywidgets
from caber.widgets import CaberVideo
viewer = CaberVideo("filament.mp4")  # tune ROI, then "Run Full Analysis"
viewer.result  # DataFrame: frame, time_s, neck_px
```

Or from the shell:

```bash
caber analyze filament.mp4 --polarity dark --axis horizontal --fps 100 \
    --mm-per-px 0.0263 --surface-tension 30 -o neck.csv
```

## The method

Each frame is cropped to a region of interest, thresholded to a binary mask
of the filament, and the filament's minimum extent is measured —
row widths for a vertical filament, column heights for a horizontal one.
A fully empty line inside the filament span means breakup (neck = 0).

Close to breakup a Newtonian filament thins linearly
(R(t) = 0.0709·(σ/η)·(t_c − t), Papageorgiou 1995), so the thinning slope
gives the viscosity once the surface tension is known.

## Test clip

A short Newtonian test clip is available via `caber.data.test_clip_path()`
(downloaded once from the repo's public URL, then cached — not shipped in the
wheel): a 6000 cP viscosity-standard oil filament thinning to breakup, 100 fps
(rate taken from the camera overlay timestamps — the container metadata is
wrong on the source file).

## License

MIT
