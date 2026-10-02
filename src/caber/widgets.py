"""Interactive CaBER video viewer/analyzer (Jupyter widget).

:class:`CaberVideo` is the interactive interface for region-of-interest
definition and filament tracking: flip through frames with a slider,
tune the crop/threshold/rotation live, then run the full analysis to get
neck size vs frame. The per-frame image processing is shared with
:mod:`caber.measure`, so widget and headless results agree.

Requires the ``widgets`` extra (``pip install rheopy-caber[widgets]``).
Pyodide-compatible: install with ``%pip install -q opencv-python pillow
ipywidgets`` as in the quickstart notebook.
"""

from __future__ import annotations

import io

try:
    import ipywidgets as widgets
    from IPython.display import display
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "caber.widgets needs ipywidgets: pip install rheopy-caber[widgets]"
    ) from exc

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from .io import open_video
from .measure import neck_size_px, threshold_frame, crop_frame, rotate_frame


class CaberVideo(widgets.VBox):
    """Interactive viewer + analyzer for a CaBER video.

    :param video_path: Path to the video file.
    :param fps: Frames per second for the time axis. Defaults to the container
        metadata (see :mod:`caber.io` for the caveat).

    After :meth:`run_full_analysis` (or the "Run Full Analysis" button),
    ``self.result`` is a DataFrame with ``frame``, ``time_s`` and
    ``neck_px``.
    """

    def __init__(self, video_path: str, fps: float | None = None):
        super().__init__()
        self.video_path = video_path
        self.cap, self.info = open_video(video_path)
        self.fps = self.info.fps_container if fps is None else fps

        self.result: pd.DataFrame | None = None
        self._is_analyzing = False

        # --- controls -------------------------------------------------
        self.slider = widgets.IntSlider(
            value=0, min=0, max=self.info.n_frames - 1, step=1,
            description="Frame:", continuous_update=False,
        )
        self.trim_left = widgets.IntSlider(value=0, min=0, max=100, description="Trim L:")
        self.trim_right = widgets.IntSlider(value=0, min=0, max=100, description="Trim R:")
        self.trim_top = widgets.IntSlider(value=0, min=0, max=100, description="Trim T:")
        self.trim_bottom = widgets.IntSlider(value=0, min=0, max=100, description="Trim B:")
        self.thresh_slider = widgets.IntSlider(
            value=100, min=0, max=255, step=1,
            description="Threshold:", continuous_update=False,
        )
        self.polarity = widgets.Dropdown(
            options=[("dark filament", "dark"), ("bright filament", "bright")],
            value="dark", description="Filament:",
        )
        self.axis = widgets.Dropdown(
            options=[("vertical", "vertical"), ("horizontal", "horizontal")],
            value="vertical", description="Axis:",
        )
        self.rotate_btn = widgets.Button(
            description="Rotate 90° CW", button_style="info", icon="rotate-right"
        )
        self.detect_toggle = widgets.Checkbox(
            value=True, description="Detect Neck & Measure", indent=False
        )
        self.track_btn = widgets.Button(
            description="Run Full Analysis", button_style="success", icon="play"
        )
        self.img_widget = widgets.Image(format="jpeg", width=480)
        self.status_label = widgets.Label(value="Ready")
        self.output_area = widgets.Output()
        self._rotation = 0

        for w in (self.slider, self.trim_left, self.trim_right, self.trim_top,
                  self.trim_bottom, self.thresh_slider, self.polarity,
                  self.axis, self.detect_toggle):
            w.observe(self._on_change, names="value")
        self.rotate_btn.on_click(self._on_rotate)
        self.track_btn.on_click(self.run_full_analysis)

        self.children = [
            self.slider,
            widgets.HBox([self.trim_left, self.trim_right]),
            widgets.HBox([self.trim_top, self.trim_bottom]),
            widgets.HBox([self.thresh_slider, self.polarity, self.axis]),
            widgets.HBox([self.rotate_btn, self.detect_toggle, self.track_btn]),
            self.status_label,
            self.img_widget,
            self.output_area,
        ]
        self._update_frame_view()

    # --- internals ----------------------------------------------------
    def _params(self):
        return dict(
            threshold=self.thresh_slider.value,
            polarity=self.polarity.value,
            axis=self.axis.value,
            rotation=self._rotation,
            trim=(self.trim_left.value, self.trim_right.value,
                  self.trim_top.value, self.trim_bottom.value),
        )

    def _process(self, frame: np.ndarray):
        """Apply ROI + threshold + neck detection; returns display frame + neck px."""
        p = self._params()
        frame = rotate_frame(frame, p["rotation"])
        frame = crop_frame(frame, *p["trim"])
        display_frame = frame.copy()
        if display_frame.ndim == 2:
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_GRAY2BGR)
        neck_px, loc = 0, None
        if self.detect_toggle.value:
            binary = threshold_frame(frame, p["threshold"], p["polarity"])
            neck_px, loc = neck_size_px(binary, p["axis"])
            overlay = display_frame.copy()
            overlay[binary > 0] = [0, 0, 255]
            alpha = 0.3 if neck_px else 0.2
            display_frame = cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0)
            if loc is not None:
                pos, center = loc
                if p["axis"] == "vertical":
                    cv2.line(display_frame, (center, pos - 3), (center, pos + 3), (0, 255, 0), 2)
                else:
                    cv2.line(display_frame, (pos - 3, center), (pos + 3, center), (0, 255, 0), 2)
                cv2.circle(display_frame, (center, pos) if p["axis"] == "vertical"
                           else (pos, center), 4, (255, 0, 0), -1)
        return display_frame, neck_px

    def _show(self, display_frame: np.ndarray):
        im = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
        im.thumbnail((640, 480))
        buf = io.BytesIO()
        im.save(buf, format="JPEG")
        self.img_widget.value = buf.getvalue()

    def _on_change(self, change):
        if not self._is_analyzing:
            self._update_frame_view()

    def _on_rotate(self, b):
        self._rotation = (self._rotation + 90) % 360
        self._update_frame_view()

    def _update_frame_view(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.slider.value)
        ok, frame = self.cap.read()
        if not ok:
            return
        display_frame, neck_px = self._process(frame)
        text = f"Frame {self.slider.value}/{self.info.n_frames - 1} | Neck: {neck_px} px"
        if neck_px == 0 and self.detect_toggle.value:
            text += " (disconnected)"
        self.status_label.value = text
        self._show(display_frame)

    # --- full analysis --------------------------------------------------
    def run_full_analysis(self, b=None):
        """Measure the neck on every frame; stores ``self.result`` and plots."""
        self._is_analyzing = True
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        rows = []
        for idx in range(self.info.n_frames):
            ok, frame = self.cap.read()
            if not ok:
                break
            display_frame, neck_px = self._process(frame)
            rows.append((idx, idx / self.fps, neck_px))
            self.slider.value = idx
            self.status_label.value = (
                f"[Analyzing {idx + 1}/{self.info.n_frames}] Neck: {neck_px} px"
            )
            self._show(display_frame)
        self.result = pd.DataFrame(rows, columns=["frame", "time_s", "neck_px"])
        self._is_analyzing = False
        self.status_label.value = f"Analysis complete: {len(rows)} frames."
        with self.output_area:
            self.output_area.clear_output()
            plt.figure(figsize=(7, 3.5))
            plt.plot(self.result["frame"], self.result["neck_px"], marker="o", markersize=3)
            plt.title("CaBER filament neck size vs frame")
            plt.xlabel("Frame")
            plt.ylabel("Neck (px)")
            plt.grid(True)
            plt.tight_layout()
            plt.show()

    def __del__(self):
        try:
            if hasattr(self, "cap") and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
