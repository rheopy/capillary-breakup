"""Filament neck measurement: video frames -> neck size vs frame.

The core image-processing pipeline, kept free of any widget code so it
runs headless (scripts, CI) as well as inside the interactive viewer.

Pipeline per frame:

1. optional rotation (0/90/180/270 deg)
2. crop to region of interest (trim in pixels)
3. grayscale + global threshold -> binary mask of the filament
4. per-line extent of the mask:

   - ``axis="vertical"`` (filament runs top-to-bottom): width of every
     image row, neck = minimum row width
   - ``axis="horizontal"`` (filament runs left-to-right): height of every
     image column, neck = minimum column height
5. connectivity check: if any empty line sits between the first and last
   filament line the filament is broken/disconnected -> neck = 0

``polarity="dark"`` means a dark filament on a bright background (the
usual backlit CaBER view); ``polarity="bright"`` is the reverse.
"""

from __future__ import annotations

import cv2
import numpy as np
import pandas as pd

from .io import open_video

_VALID_POLARITIES = ("dark", "bright")
_VALID_AXES = ("vertical", "horizontal")


def rotate_frame(frame: np.ndarray, rotation: int) -> np.ndarray:
    """Rotate a frame by 0, 90, 180 or 270 degrees clockwise."""
    if rotation == 0:
        return frame
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError(f"rotation must be one of 0/90/180/270, got {rotation}")


def crop_frame(
    frame: np.ndarray,
    trim_left: int = 0,
    trim_right: int = 0,
    trim_top: int = 0,
    trim_bottom: int = 0,
) -> np.ndarray:
    """Crop ``trim_*`` pixels off each side of a frame."""
    h, w = frame.shape[:2]
    left = min(max(0, trim_left), w - 2)
    right = min(max(0, trim_right), max(0, w - 1 - left))
    top = min(max(0, trim_top), h - 2)
    bottom = min(max(0, trim_bottom), max(0, h - 1 - top))
    end_x = w - right if right > 0 else w
    end_y = h - bottom if bottom > 0 else h
    return frame[top:end_y, left:end_x]


def threshold_frame(frame: np.ndarray, threshold: int, polarity: str) -> np.ndarray:
    """Grayscale + global threshold -> binary mask with filament white."""
    if polarity not in _VALID_POLARITIES:
        raise ValueError(f"polarity must be one of {_VALID_POLARITIES}")
    gray = (
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if frame.ndim == 3
        else frame.copy()
    )
    flag = cv2.THRESH_BINARY_INV if polarity == "dark" else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, int(threshold), 255, flag)
    return binary


def neck_size_px(binary: np.ndarray, axis: str) -> tuple[int, tuple[int, int] | None]:
    """Minimum filament extent in pixels from a binary mask.

    Returns ``(size_px, (pos, center))`` where ``pos`` is the row/column
    index of the neck and ``center`` its midpoint along that line, or
    ``(0, None)`` when the filament is disconnected/absent.
    """
    if axis not in _VALID_AXES:
        raise ValueError(f"axis must be one of {_VALID_AXES}")
    # per-line extent of the white (filament) pixels
    extents = (
        np.count_nonzero(binary, axis=1)
        if axis == "vertical"
        else np.count_nonzero(binary, axis=0)
    )
    nz = np.nonzero(extents)[0]
    if len(nz) == 0:
        return 0, None
    # a fully empty line inside the filament span means breakup
    if np.any(extents[nz.min() : nz.max() + 1] == 0):
        return 0, None
    span = extents[nz.min() : nz.max() + 1]
    neck_idx = int(nz.min() + np.argmin(span))
    line = binary[neck_idx, :] if axis == "vertical" else binary[:, neck_idx]
    cols = np.nonzero(line)[0]
    center = int((cols[0] + cols[-1]) / 2) if len(cols) else 0
    return int(extents[neck_idx]), (neck_idx, center)


def process_frame(
    frame: np.ndarray,
    *,
    threshold: int = 100,
    polarity: str = "dark",
    axis: str = "vertical",
    rotation: int = 0,
    trim: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> tuple[np.ndarray, int]:
    """Full per-frame pipeline. Returns ``(cropped_frame, neck_px)``."""
    frame = rotate_frame(frame, rotation)
    frame = crop_frame(frame, *trim)
    binary = threshold_frame(frame, threshold, polarity)
    size_px, _ = neck_size_px(binary, axis)
    return frame, size_px


def measure_video(
    path: str,
    *,
    threshold: int = 100,
    polarity: str = "dark",
    axis: str = "vertical",
    rotation: int = 0,
    trim: tuple[int, int, int, int] = (0, 0, 0, 0),
    fps: float | None = None,
    frame_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Measure the filament neck on every frame of a video.

    Returns a DataFrame with ``frame``, ``time_s`` and ``neck_px``.
    ``neck_px`` is 0 for frames where the filament is disconnected.

    Parameters
    ----------
    fps:
        Frames per second used for ``time_s``. Defaults to the container
        metadata, but camera-written fps is not always right — pass the
        acquisition rate when you know it.
    frame_range:
        Optional ``(first, last)`` frame indices (inclusive) to analyze.
    """
    cap, info = open_video(path)
    try:
        first, last = 0, info.n_frames - 1
        if frame_range is not None:
            first, last = frame_range
            first = max(0, first)
            last = min(info.n_frames - 1, last)
        fps = info.fps_container if fps is None else fps
        cap.set(cv2.CAP_PROP_POS_FRAMES, first)
        rows = []
        for idx in range(first, last + 1):
            ok, frame = cap.read()
            if not ok:
                break
            _, size_px = process_frame(
                frame,
                threshold=threshold,
                polarity=polarity,
                axis=axis,
                rotation=rotation,
                trim=trim,
            )
            rows.append((idx, idx / fps, size_px))
    finally:
        cap.release()
    return pd.DataFrame(rows, columns=["frame", "time_s", "neck_px"])
