"""Tests for the caber measurement core and analysis (headless)."""

import numpy as np
import pandas as pd
import pytest

import caber
from caber import analysis as A
from caber import measure as M
from caber.data import test_clip_path, TEST_CLIP_FPS
from caber.io import open_video


def synthetic_frame(height=200, width=300, bar_width=40, horizontal=False):
    """White background with a dark bar (the filament)."""
    img = np.full((height, width, 3), 255, dtype=np.uint8)
    if horizontal:
        y0 = (height - bar_width) // 2
        img[y0 : y0 + bar_width, 20 : width - 20] = 0
    else:
        x0 = (width - bar_width) // 2
        img[20 : height - 20, x0 : x0 + bar_width] = 0
    return img


def test_open_video_metadata():
    cap, info = open_video(test_clip_path())
    cap.release()
    assert info.n_frames == 131
    assert (info.width, info.height) == (310, 226)


def test_neck_vertical_dark():
    frame = synthetic_frame(bar_width=40)
    _, size = M.process_frame(frame, threshold=100, polarity="dark", axis="vertical")
    assert size == 40


def test_neck_horizontal_dark():
    frame = synthetic_frame(bar_width=24, horizontal=True)
    _, size = M.process_frame(frame, threshold=100, polarity="dark", axis="horizontal")
    assert size == 24


def test_neck_bright_polarity():
    frame = 255 - synthetic_frame(bar_width=30)  # bright bar on dark
    _, size = M.process_frame(frame, threshold=100, polarity="bright", axis="vertical")
    assert size == 30


def test_disconnected_gives_zero():
    frame = synthetic_frame(bar_width=40)
    frame[90:110, :] = 255  # cut the filament in two
    _, size = M.process_frame(frame, threshold=100, polarity="dark", axis="vertical")
    assert size == 0


def test_trim_and_rotation():
    frame = synthetic_frame(bar_width=40)
    _, s1 = M.process_frame(frame, trim=(100, 100, 0, 0))
    assert s1 == 40  # trim off the sides doesn't touch the bar
    rot = M.rotate_frame(frame, 90)
    assert rot.shape[:2] == (frame.shape[1], frame.shape[0])


def test_measure_video_on_clip():
    df = caber.measure_video(
        test_clip_path(), threshold=100, polarity="dark",
        axis="horizontal", fps=TEST_CLIP_FPS,
    )
    assert list(df.columns) == ["frame", "time_s", "neck_px"]
    assert len(df) == 131
    assert df["time_s"].iloc[-1] == pytest.approx(130 / 100)
    # thinning: neck shrinks, then breaks
    assert df["neck_px"].iloc[0] > df["neck_px"].iloc[80] > 0
    assert caber.find_breakup(df) == 98
    assert (df.loc[99:, "neck_px"] == 0).all()


def test_analysis_on_synthetic_linear():
    # R(t) = 1.0 - 0.5*t  (mm, s): slope -0.5, tc = 2.0
    t = np.arange(0, 1.0, 0.02)
    df = pd.DataFrame({
        "frame": np.arange(len(t)),
        "time_s": t,
        "neck_px": ((1.0 - 0.5 * t) * 2 / 0.01).astype(int),
    })
    rdf = A.to_radius(df, mm_per_px=0.01)
    assert rdf["radius_mm"].iloc[0] == pytest.approx(1.0, abs=0.01)
    fit = A.fit_linear_thinning(rdf, n_points=30, end_offset=0)
    assert fit["slope"] == pytest.approx(-0.5, abs=0.02)
    assert fit["t_c"] == pytest.approx(2.0, abs=0.05)
    assert fit["r_squared"] > 0.99


def test_newtonian_viscosity_formula():
    # eta = 0.0709 * sigma / |slope| ; sigma=21 mN/m, slope=-0.1662 mm/s
    eta = A.newtonian_viscosity(-0.1662, 21.0)
    assert eta == pytest.approx(0.0709 * 0.021 / (0.1662 / 1000), rel=1e-9)
    assert eta > 0


def test_thinning_summary_on_clip():
    df = caber.measure_video(
        test_clip_path(), threshold=100, polarity="dark",
        axis="horizontal", fps=TEST_CLIP_FPS,
    )
    s = caber.thinning_summary(df, mm_per_px=0.02632, surface_tension_mN_per_m=21.0)
    assert s["breakup"] == 98
    assert s["fit"]["slope"] < 0
    assert s["fit"]["r_squared"] > 0.5
    assert s["viscosity_Pa_s"] > 0


def test_cli_analyze(tmp_path):
    from caber.cli import main

    out = tmp_path / "neck.csv"
    main(["analyze", test_clip_path(), "-o", str(out), "--polarity", "dark",
          "--axis", "horizontal", "--fps", "100", "--mm-per-px", "0.02632"])
    df = pd.read_csv(out)
    assert len(df) == 131
    assert "radius_mm" in df.columns
