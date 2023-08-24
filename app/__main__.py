import argparse

from app.fg_app import FGApp


parser = argparse.ArgumentParser()
parser.add_argument("--window-width", help=f"Window width", type=int, default=1280)
parser.add_argument("--window-height", help=f"Window height", type=int, default=720)
parser.add_argument("--fullscreen", help="Fullscreen window", action="store_true", default=False)
args = parser.parse_args()


app = FGApp(
    window_width=args.window_width,
    window_height=args.window_height,
    fullscreen=args.fullscreen)

app.run()
