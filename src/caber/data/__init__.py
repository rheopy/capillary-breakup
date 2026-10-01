"""Test data for caber: a Newtonian CaBER clip, downloaded on first use.

The clip is deliberately *not* shipped inside the wheel — it lives in the
repository's ``data/`` folder and is fetched from its public URL the first
time :func:`test_clip_path` is called, then cached locally.
"""

from __future__ import annotations

import os
import sys
import urllib.request

TEST_CLIP_URL = (
    "https://raw.githubusercontent.com/rheopy/capillary-breakup"
    "/main/data/test_clip.mp4"
)
"""Public download URL of the Newtonian test clip."""

TEST_CLIP_SIZE = 18323
"""Expected size of the clip in bytes (integrity check after download)."""

FULL_VIDEO_URL = (
    "https://raw.githubusercontent.com/marcocaggioni/capillary_breakup"
    "/main/6000cp_viscosity_standard_100fps.mp4"
)
"""Public download URL of the full-resolution source recording (~38.8 MB)."""

TEST_CLIP_FPS = 100.0
"""Acquisition rate of the test clip, from the camera overlay timestamps."""

TEST_CLIP_MM_PER_PX = 0.01316
"""Pixel calibration (mm/px) in the wide-view regime, from the 6 mm
calibration target visible in the full recording. The test clip is a
spatial downsample — multiply by the downsample factor (see
``TEST_CLIP_DOWNSAMPLE``)."""

TEST_CLIP_DOWNSAMPLE = 2
"""The test clip is downsampled 2x vs the full recording, so its effective
calibration is ``TEST_CLIP_MM_PER_PX * TEST_CLIP_DOWNSAMPLE``."""


def _cache_dir() -> str:
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches")
    elif os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    return os.path.join(base, "caber")


def test_clip_path() -> str:
    """Local path of the Newtonian test clip (mp4).

    Downloads the clip from :data:`TEST_CLIP_URL` on first use and caches
    it under the platform cache directory (``~/.cache/caber`` on Linux).
    """
    dest = os.path.join(_cache_dir(), "test_clip.mp4")
    if not (
        os.path.exists(dest) and os.path.getsize(dest) == TEST_CLIP_SIZE
    ):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        tmp = dest + ".part"
        urllib.request.urlretrieve(TEST_CLIP_URL, tmp)
        got = os.path.getsize(tmp)
        if got != TEST_CLIP_SIZE:
            os.remove(tmp)
            raise IOError(
                f"downloaded clip has unexpected size "
                f"({got} bytes); refusing to use it"
            )
        os.replace(tmp, dest)
    return dest
