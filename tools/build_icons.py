"""Sinh PNG icon cho app tu nguon SVG (Feather Icons, MIT).

Tkinter/CustomTkinter khong hien thi SVG truc tiep, nen SVG la file
nguon (assets/icons/svg/) va PNG la ban render san de app nap bang
CTkImage. Chay lai script nay khi muon doi mau / kich thuoc icon:

    python tools/build_icons.py

Moi icon duoc render 2 mau:
- <ten>_dark.png  : mau trang  (dung khi app o che do Dark)
- <ten>_light.png : mau xam dam (dung khi app o che do Light)
"""
import pathlib

import cairosvg

HERE = pathlib.Path(__file__).resolve().parent.parent
SVG_DIR = HERE / "assets" / "icons" / "svg"
OUT_DIR = HERE / "assets" / "icons"
SIZE = 96  # render lon gap 4 lan kich thuoc hien thi (24px) cho net tren man HiDPI

VARIANTS = {
    "dark": "#FFFFFF",
    "light": "#2B2B2B",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for svg_path in sorted(SVG_DIR.glob("*.svg")):
        raw = svg_path.read_text(encoding="utf-8")
        for variant, color in VARIANTS.items():
            svg = raw.replace("currentColor", color)
            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                output_width=SIZE,
                output_height=SIZE,
                write_to=str(OUT_DIR / f"{svg_path.stem}_{variant}.png"),
            )
        print("built", svg_path.stem)


if __name__ == "__main__":
    main()
