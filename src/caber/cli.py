"""Command line interface: ``caber analyze video.mp4 -o radius.csv``."""

from __future__ import annotations

import argparse

from .analysis import thinning_summary
from .measure import measure_video


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="caber", description="Capillary-breakup (CaBER) video analysis"
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="video -> neck size vs time CSV")
    a.add_argument("video", help="path to the video file")
    a.add_argument("-o", "--output", default="neck.csv", help="output CSV path")
    a.add_argument("--threshold", type=int, default=100)
    a.add_argument("--polarity", choices=["dark", "bright"], default="dark",
                   help="dark: dark filament on bright background")
    a.add_argument("--axis", choices=["vertical", "horizontal"], default="vertical",
                   help="filament orientation in the image")
    a.add_argument("--rotation", type=int, choices=[0, 90, 180, 270], default=0)
    a.add_argument("--trim", type=int, nargs=4, default=[0, 0, 0, 0],
                   metavar=("L", "R", "T", "B"), help="crop pixels per side")
    a.add_argument("--fps", type=float, default=None,
                   help="frames per second (default: container metadata)")
    a.add_argument("--mm-per-px", type=float, default=None,
                   help="pixel calibration; adds radius_mm column")
    a.add_argument("--surface-tension", type=float, default=None,
                   help="surface tension in mN/m; reports Newtonian viscosity")
    a.add_argument("--frames", type=int, nargs=2, default=None,
                   metavar=("FIRST", "LAST"), help="frame range to analyze")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        df = measure_video(
            args.video,
            threshold=args.threshold,
            polarity=args.polarity,
            axis=args.axis,
            rotation=args.rotation,
            trim=tuple(args.trim),
            fps=args.fps,
            frame_range=tuple(args.frames) if args.frames else None,
        )
        if args.mm_per_px:
            summary = thinning_summary(
                df,
                mm_per_px=args.mm_per_px,
                surface_tension_mN_per_m=args.surface_tension,
            )
            df = summary["df"]
            fit = summary["fit"]
            print(f"frames: {len(df)}, breakup at frame {summary['breakup']}")
            print(f"thinning slope: {fit['slope']:.4f} mm/s, R^2 = {fit['r_squared']:.4f}")
            if summary["viscosity_Pa_s"] is not None:
                print(f"Newtonian viscosity: {summary['viscosity_Pa_s']:.3f} Pa.s")
        else:
            print(f"frames: {len(df)}")
        df.to_csv(args.output, index=False)
        print(f"wrote {args.output}")
