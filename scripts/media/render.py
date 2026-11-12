"""Render the docs images for a brand: og.png, the three SVG diagrams, install.gif and the demo GIF.

    py -3 scripts/media/render.py --own-run                        # the upstream's own images, in place
    py -3 scripts/media/render.py --brand <file> --root <copy>     # a branded copy (whitelabel.py runs this)

Needs Pillow, agg (install.gif) and gifski (the demo GIF) on PATH. `--own-run` keeps the upstream's capture
of its real PR thread (pr-19-thread.gif) and skips the illustrated how-it-works.gif.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brandlib  # noqa: E402
import demo_gif  # noqa: E402
import install_gif  # noqa: E402
import og  # noqa: E402
import svgs  # noqa: E402

ROOT = HERE.parent.parent


def render(brand: dict, root: Path, own_run: bool = False) -> list:
    images = root / "docs/images"
    written = svgs.render(brand, images)
    written.append(og.render(brand, images / "og.png", own_run))
    if (images / "install.cast").is_file():
        written.append(install_gif.render(brand, images / "install.cast", images / "install.gif"))
    if not own_run:
        written.append(demo_gif.render(brand, images / "how-it-works.gif"))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--brand", default=str(ROOT / "brand/brand.json"))
    parser.add_argument("--root", default=str(ROOT), help="repo copy whose docs/images to write")
    parser.add_argument("--own-run", action="store_true", help="the upstream's images: keep its real-run capture")
    args = parser.parse_args()
    try:
        written = render(brandlib.load(args.brand), Path(args.root), args.own_run)
    except brandlib.BrandError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
