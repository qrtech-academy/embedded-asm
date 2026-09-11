"""Shared drawing style and rendering plumbing for the lecture diagrams.

Every visual constant lives here, so restyling every figure at once is a single edit.
Figure modules only describe geometry; they never touch colors, line weights, or output size.

This is the digital design course's `style.py` with one addition. That course drew circuits,
so everything in it was a line. This course draws mostly *fields*: a register split into eight
named bits, an address space split into labelled regions, a register file split into groups
that behave differently. Those need fills as well as strokes, so there is a small tinted
palette here, and the rule for using it is in FILLS below.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import matplotlib

matplotlib.use("Agg")  # Render straight to file; there is no display in WSL or in CI.

import matplotlib.pyplot as plt  # noqa: E402
import schemdraw  # noqa: E402
from PIL import Image  # noqa: E402

schemdraw.use("matplotlib")

# ----------------------------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------------------------
LINE_COLOR = "black"

# The one ink that means "look here": the bit under discussion, the marked edge, a span
# measurement, the arrow from a caption to the thing it captions.
ACCENT_COLOR = "#c00000"

# A second ink, for the figures that have to tell two things apart at once. Blue rather than
# green because red/green is the pair most colour vision deficiencies confuse.
ACCENT_COLOR_2 = "#0050b3"

# Grey, for what the hardware does not use: a reserved bit, an unimplemented address range,
# a register the current figure is not about.
MUTED_COLOR = "#767676"

BACKGROUND = "white"

# Region fills, as light tints of the inks above. A fill never carries meaning on its own:
# every filled region is also labelled, because a reader printing this in greyscale, or one
# who cannot separate these hues, must lose nothing. The fill is there to group, not to say.
FILLS = {
    "accent": "#f4d7d7",   # The region the surrounding text is about.
    "accent2": "#d6e4f5",  # The one it is being contrasted with.
    "muted": "#e8e8e8",    # Reserved, unimplemented, or not this figure's subject.
    "plain": "#ffffff",    # Ordinary, and drawn white rather than left transparent.
}

# ----------------------------------------------------------------------------------------
# Line weights
# ----------------------------------------------------------------------------------------
WIRE_WIDTH = 2.0     # A single signal: one line, one bit.
BUS_WIDTH = 4.5      # Several bits on one line.
BOX_WIDTH = 2.5      # The boundary of a module, a register, or a memory region.
CELL_WIDTH = 1.4     # The division between two cells inside such a boundary.
ACCENT_WIDTH = 2.0   # Anything drawn in an accent color.

# ----------------------------------------------------------------------------------------
# Text. Register, signal and instruction names are monospace so they read as the identifiers
# they are, which in this course is nearly everything: PORTB, r24, OCR1A, 0xE21A.
# ----------------------------------------------------------------------------------------
FONT = "monospace"
FONT_SIZE = 15
SMALL_SIZE = 11      # Bit names inside a cell, and anything else that must fit one.
TINY_SIZE = 9        # Bit numbers above a field, and address digits beside a region.
TITLE_SIZE = 17
TITLE_WEIGHT = "bold"

# ----------------------------------------------------------------------------------------
# Output geometry, in schemdraw units.
#
# A figure declares the canvas it is rendered onto rather than being cropped to its contents,
# so figures read as a sequence can share one canvas and line up pixel for pixel. One unit is
# INCHES_PER_UNIT inches at every figure size, so a label is the same size in every figure.
# ----------------------------------------------------------------------------------------

# The default canvas, (xmin, ymin, xmax, ymax); sized for a single 8-bit register field.
CANVAS = (-2.0, -1.4, 10.6, 2.6)

INCHES_PER_UNIT = 0.5
DPI = 130  # 12.6 x 4.0 units at 0.5 in/unit and 130 dpi = 819 x 260 px.

# Line art on white uses a few hundred colors at most, so a palette beats 32-bit RGBA: a
# about two fifths of the file size, and lossless for a figure already inside 256 colors.
PALETTE_COLORS = 256

# A figure builder: adds elements to the drawing, and may use the raw matplotlib axes for
# the text, which schemdraw positions less predictably than we want here. Figures with no
# circuit in them ignore the drawing entirely and use the axes alone.
Builder = Callable[[schemdraw.Drawing, "plt.Axes"], None]


@dataclass(frozen=True)
class Figure:
    """One drawable figure: how to draw it, and the canvas it is drawn onto."""

    draw: Builder
    canvas: tuple[float, float, float, float] = field(default=CANVAS)


# The text is monospace, so a string's width is its length times one character. DejaVu Sans
# Mono advances 0.602 em per character; 72 points to the inch.
CHAR_ASPECT = 0.602

# Line spacing inside a multi-line caption, as a multiple of the text height.
CAPTION_LEADING = 1.35


# ----------------------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------------------


def text_width(string: str, size: float = FONT_SIZE) -> float:
    """Width of `string` in canvas units, for laying out around a label."""
    return len(string) * size * CHAR_ASPECT / (72 * INCHES_PER_UNIT)


def text_height(size: float = FONT_SIZE) -> float:
    """Cap-to-descender height of a line of text, in canvas units."""
    return size / (72 * INCHES_PER_UNIT)


def fits(string: str, width: float, size: float = FONT_SIZE) -> bool:
    """Whether `string` at `size` fits inside `width` canvas units.

    Used by the field drawings to drop to a smaller size, or to an abbreviation, rather than
    letting a long bit name run over the cell walls either side of it. Text that overflows a
    cell is the single most common way one of these figures goes wrong, and it is invisible
    from the code that produced it.
    """
    return text_width(string, size) <= width


def caption_bounds(lines: Sequence[str], centre: float,
                   size: float = SMALL_SIZE) -> tuple[float, float]:
    """(left, right) x a centred caption reaches, so a canvas can be widened to clear it.

    Every figure module calls this. A caption wider than the figure it captions is normal
    here, and a canvas pinned to the drawing alone clips it silently: the render succeeds,
    the PNG looks finished, and the sentence explaining the figure has lost both its ends.
    """
    half = max(text_width(line, size) for line in lines) / 2
    return centre - half, centre + half


def caption_height(lines: Sequence[str], size: float = SMALL_SIZE) -> float:
    """How far below its anchor a caption of `lines` reaches."""
    return len(lines) * text_height(size) * CAPTION_LEADING


def caption(ax, lines: Sequence[str], centre: float, top: float,
            size: float = SMALL_SIZE) -> None:
    """Draw a centred caption downwards from `top`, one line at a time."""
    step = text_height(size) * CAPTION_LEADING
    for index, line in enumerate(lines):
        text(ax, line, (centre, top - index * step), valign="top", size=size)


def text(
    ax,
    string: str,
    pos: tuple[float, float],
    halign: str = "center",
    valign: str = "center",
    size: float = FONT_SIZE,
    weight: str = "normal",
    color: str = LINE_COLOR,
    rotation: float = 0.0,
) -> None:
    """Draw text at an exact point on the canvas.

    Goes through matplotlib rather than schemdraw so that a label's position is the point
    given and nothing else, and so that bold is available; schemdraw's text has no weight.
    """
    ax.text(
        pos[0],
        pos[1],
        string,
        fontsize=size,
        family=FONT,
        weight=weight,
        color=color,
        ha=halign,
        va=valign,
        rotation=rotation)


def title(ax, string: str, pos: tuple[float, float]) -> None:
    """Draw a figure's name above it."""
    text(ax, string, pos, size=TITLE_SIZE, weight=TITLE_WEIGHT)


def render(figure: Figure, paths: list[Path]) -> None:
    """Draw a figure and write it to every path in `paths`.

    A figure with more than one path is one that several lectures embed; writing all the
    copies from a single source is what keeps them identical.
    """
    # Size the page from the canvas, so one unit is INCHES_PER_UNIT inches in every figure.
    xmin, ymin, xmax, ymax = figure.canvas
    fig, ax = plt.subplots(
        figsize=((xmax - xmin) * INCHES_PER_UNIT, (ymax - ymin) * INCHES_PER_UNIT))
    try:
        # Hand the builder a drawing that renders onto our axes, so it can mix schemdraw
        # elements with the direct matplotlib text that `text` draws.
        drawing = schemdraw.Drawing(canvas=ax)
        drawing.config(
            fontsize=FONT_SIZE, font=FONT, color=LINE_COLOR, lw=WIRE_WIDTH)
        figure.draw(drawing, ax)
        drawing.draw(show=False, canvas=ax)

        # Pin the view to the declared canvas instead of letting matplotlib fit the
        # content, and drop every margin so the saved pixels are exactly the canvas.
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.subplots_adjust(left=0, bottom=0, right=1, top=1)

        # Render to memory rather than to disk: the palette pass below still has to run,
        # and the figure is written once per path afterwards.
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=DPI, facecolor=BACKGROUND)
    finally:
        # Close even on failure; matplotlib figures are a process-wide resource.
        plt.close(fig)

    # The background is opaque, so dropping the alpha channel costs nothing. Median cut is
    # deterministic, which keeps a rebuild byte-identical.
    image = Image.open(buffer).convert("RGB").quantize(colors=PALETTE_COLORS)

    # One drawing, written to every lecture that embeds it, which is what keeps the copies
    # identical. Directories are created on demand so a new lecture needs no setup.
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "PNG", optimize=True)
