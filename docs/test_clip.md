# Test clip

The package bundles a short Newtonian test clip, reachable from Python without
unpacking anything:

```python
from caber.data import test_clip_path
clip = test_clip_path()  # .../caber/data/test_clip.mp4
```

## What it is

A 6000 cP viscosity-standard oil (Newtonian) filament thinning to breakup —
131 frames at 100 fps, 310×226 px. It is a downsampled excerpt (2× spatial,
frames 211–341) of the full-resolution recording
`6000cp_viscosity_standard_100fps.mp4` from the original `capillary_breakup`
repository, cropped to the filament region of interest.

## Provenance notes (read before quoting numbers)

- **Frame rate:** the source file's container metadata claims ~60 fps, but the
  camera's own overlay timestamps advance exactly 0.01 s/frame — the true
  acquisition rate is **100 fps**, and the bundled clip is encoded at 100 fps.
- **Calibration:** the source annotation marks a 6 mm calibration target
  spanning 456 px in the *wide-view* regime → 0.01316 mm/px. The bundled clip
  comes from the *zoomed* regime (2× downsampled), whose scale is not
  independently established in the source material — treat `mm_per_px` as a
  user-supplied calibration and the demo's viscosity as illustrative of the
  method.
- **Polarity/axis:** dark filament on bright background, filament horizontal —
  i.e. `polarity="dark", axis="horizontal"`.
