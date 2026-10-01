# Quickstart

See `notebooks/caber_quickstart.ipynb` — the full walkthrough on the bundled
Newtonian test clip:

1. Load the clip with `caber.data.test_clip_path()`.
2. Define the region of interest interactively with `CaberVideo`
   (crop / threshold / polarity / axis sliders, then **Run Full Analysis**).
3. Or go headless: `caber.measure_video(...)` → neck (px) vs time.
4. Newtonian analysis: `caber.thinning_summary(...)` → breakup frame,
   linear thinning fit (slope, $t_c$, $R^2$), viscosity from the
   Papageorgiou similarity solution.

From the shell:

```bash
caber analyze filament.mp4 --polarity dark --axis horizontal --fps 100 \
    --mm-per-px 0.0263 --surface-tension 21 -o neck.csv
```
