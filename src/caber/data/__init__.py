"""Bundled test data: a Newtonian CaBER clip.

The bundled clip is a downsampled excerpt of a capillary-breakup
recording of a 6000 cP viscosity-standard oil (Newtonian) at 100 fps,
zoomed view of the filament thinning to breakup. The full-resolution
recording lives in the repository's ``data/`` folder.
"""

from __future__ import annotations

from importlib.resources import files


def test_clip_path() -> str:
    """Filesystem path of the bundled Newtonian test clip (mp4)."""
    return str(files("caber.data") / "test_clip.mp4")


TEST_CLIP_FPS = 100.0
"""Acquisition rate of the test clip, from the camera overlay timestamps."""

TEST_CLIP_MM_PER_PX = 0.01316
"""Pixel calibration (mm/px) in the wide-view regime, from the 6 mm
calibration target visible in the full recording. The bundled clip is a
spatial downsample — multiply by the downsample factor (see
:func:`test_clip_downsample`)."""

TEST_CLIP_DOWNSAMPLE = 2
"""The bundled clip is downsampled 2x vs the full recording, so its
effective calibration is ``TEST_CLIP_MM_PER_PX * TEST_CLIP_DOWNSAMPLE``."""
