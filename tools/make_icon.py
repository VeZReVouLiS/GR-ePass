"""Generate the brand icon for the GR e-PASS integration.

A toll booth with a raised barrier, written straight into the integration.
Since Home Assistant 2026.3 a custom integration serves its own brand images
from custom_components/<domain>/brand/, and those take priority over the brands
CDN -- no manifest key and no PR to home-assistant/brands, which in fact stopped
accepting icons for custom integrations altogether.

The artwork is deliberately not the operator's logo: that is a registered mark
and this integration is unofficial. Colours are taken from the portal's CSS,
which is not itself trademark use.

Everything is drawn at 1024x1024 and downscaled with LANCZOS: PIL does not
anti-alias shape edges, so drawing large and shrinking is what produces clean
curves and diagonals.

    python tools/make_icon.py
"""

from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw

# Palette anchored on the portal's own colours, with two lighter tints mixed in
# so the booth reads as a booth at 48px instead of a blue blob.
NAVY = (2, 78, 126, 255)  # #024e7e -- their nav bar; roof and dark details
BLUE = (58, 122, 186, 255)  # booth body
GLASS = (176, 212, 243, 255)  # window
YELLOW = (252, 189, 2, 255)  # #fcbd02 -- barrier
GREY = (191, 200, 206, 255)  # ground line, panel bars
POST = (126, 139, 146, 255)  # barrier post

CANVAS = 1024
ARM_ANGLE = 38  # degrees above horizontal
PIVOT = (556, 566)

OUT_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components"
    / "gr_epass"
    / "brand"
)


def _barrier_layer() -> Image.Image:
    """The striped arm, drawn horizontally from the pivot then rotated about it.

    Rotating a full-canvas layer around the pivot keeps the arm attached to the
    post; rotating a small sprite and pasting it means recomputing the offset
    for every angle change.
    """
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    length, thickness = 470, 86
    x0, y0 = PIVOT[0], PIVOT[1] - thickness // 2
    draw.rounded_rectangle(
        [x0, y0, x0 + length, y0 + thickness], radius=thickness // 2, fill=YELLOW
    )

    # Diagonal navy stripes, clipped to the arm so they cannot overhang the ends.
    stripes = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    step = 116
    for x in range(x0 - thickness, x0 + length + thickness, step):
        sd.polygon(
            [
                (x, y0 + thickness),
                (x + step // 2, y0 + thickness),
                (x + step // 2 + thickness, y0),
                (x + thickness, y0),
            ],
            fill=NAVY,
        )
    shape = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(shape).rounded_rectangle(
        [x0, y0, x0 + length, y0 + thickness], radius=thickness // 2, fill=255
    )
    layer.paste(
        stripes,
        (0, 0),
        Image.composite(shape, Image.new("L", shape.size, 0), stripes.split()[3]),
    )

    return layer.rotate(ARM_ANGLE, center=PIVOT, resample=Image.BICUBIC)


def build() -> Image.Image:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    ground_y = 902

    # --- barrier post, behind the arm ---------------------------------------
    d.rounded_rectangle([508, 566, 604, ground_y], radius=30, fill=POST)

    # --- arm ----------------------------------------------------------------
    arm = _barrier_layer()
    img.alpha_composite(arm)

    # pivot bolt, drawn on top so the arm looks hinged
    d.ellipse([538, 548, 574, 584], fill=GLASS)

    # --- booth --------------------------------------------------------------
    d.rounded_rectangle([116, 208, 476, ground_y], radius=18, fill=BLUE)
    # canopy, slightly wider than the body
    d.rounded_rectangle([84, 120, 508, 214], radius=26, fill=NAVY)

    # window, with a service hatch at the bottom
    d.rounded_rectangle([160, 262, 432, 556], radius=26, fill=GLASS)
    d.rounded_rectangle([258, 452, 334, 560], radius=22, fill=NAVY)

    # lower panel with two slots
    d.rounded_rectangle([170, 626, 422, 842], radius=24, fill=NAVY)
    d.rounded_rectangle([212, 676, 380, 716], radius=20, fill=GREY)
    d.rounded_rectangle([212, 752, 380, 792], radius=20, fill=GREY)

    # --- ground -------------------------------------------------------------
    d.rounded_rectangle([48, ground_y, 976, ground_y + 40], radius=20, fill=GREY)

    # Square with no air at all: the longest side touches the edge and only the
    # shorter axis gets centred, so the subject is as large as a 1:1 icon allows.
    img = img.crop(img.getbbox())
    side = max(img.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return square


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    icon = build()
    for size, name in ((512, "icon@2x.png"), (256, "icon.png")):
        # optimize + max compression: these ship inside the integration, so
        # every kilobyte is downloaded by every user.
        icon.resize((size, size), Image.LANCZOS).save(
            OUT_DIR / name, optimize=True, compress_level=9
        )
        print(f"wrote {OUT_DIR / name} ({size}x{size})")


if __name__ == "__main__":
    main()
