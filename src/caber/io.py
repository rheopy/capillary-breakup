"""Video I/O helpers for CaBER analysis.

Thin wrappers around OpenCV's video reader that keep metadata
(frame count, container fps, frame size) next to the capture object.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2


@dataclass
class VideoInfo:
    path: str
    n_frames: int
    fps_container: float
    width: int
    height: int


def open_video(path: str) -> tuple[cv2.VideoCapture, VideoInfo]:
    """Open a video file and return the capture object plus metadata.

    Note: container fps metadata is not always trustworthy (some camera
    software writes the wrong value). Prefer the camera's own timestamps
    or a known acquisition rate and pass it as ``fps`` to
    :func:`caber.measure.measure_video`.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {path}")
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n_frames <= 0:
        raise ValueError(f"Could not read frames from video: {path}")
    info = VideoInfo(
        path=path,
        n_frames=n_frames,
        fps_container=float(cap.get(cv2.CAP_PROP_FPS)),
        width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    )
    return cap, info


def read_frame(cap: cv2.VideoCapture, index: int):
    """Seek to ``index`` and read one frame (BGR numpy array)."""
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = cap.read()
    if not ok:
        raise ValueError(f"Could not read frame {index}")
    return frame
