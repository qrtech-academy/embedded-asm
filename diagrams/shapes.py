"""Matplotlib primitives shared by the figure modules.

Only the shapes that more than one module needs: a filled cell, a brace over a run of cells,
a measured span, and a callout arrow from a caption to the thing it captions. Anything used
by a single figure module stays in that module.

Everything here takes canvas units and reads its colors from `style`.
"""

from __future__ import annotations

from matplotlib.patches import FancyArrowPatch, Rectangle

import style


def cell(ax, x: float, y: float, width: float, height: float, fill: str = "plain",
         lw: float = style.BOX_WIDTH, edge: str | None = None) -> None:
    """A filled, outlined rectangle with its lower-left corner at (x, y).

    `fill` is a key into `style.FILLS` rather than a color, so a figure never names a hue and
    restyling stays a single edit in `style.py`.
    """
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor=style.FILLS[fill],
            edgecolor=edge or style.LINE_COLOR,
            lw=lw,
            zorder=1))


def shade(ax, x_a: float, x_b: float, y_a: float, y_b: float, alpha: float,
          color: str | None = None) -> None:
    """A translucent accent rectangle, for marking an interval rather than bounding it.

    Drawn at zorder 0, behind everything, so it reads as shading and not as a shape.
    """
    ax.add_patch(
        Rectangle(
            (x_a, y_a),
            x_b - x_a,
            y_b - y_a,
            facecolor=color or style.ACCENT_COLOR,
            edgecolor="none",
            alpha=alpha,
            zorder=0))


def brace(ax, x_a: float, x_b: float, y: float, label: str, below: bool = False,
          color: str | None = None, size: float = style.SMALL_SIZE) -> None:
    """A square brace spanning [x_a, x_b] at height `y`, labelled outside it.

    Square rather than curly on purpose: a curly brace at this line weight turns to mush at
    the sizes these figures are read at, and a square one reads as "these cells, together",
    which is all it has to say.
    """
    ink = color or style.ACCENT_COLOR
    tick = 0.22 if not below else -0.22

    # Two short verticals and the horizontal between them.
    ax.plot([x_a, x_a, x_b, x_b], [y + tick, y, y, y + tick],
            color=ink, lw=style.ACCENT_WIDTH, clip_on=False, solid_joinstyle="miter")

    gap = 0.30
    style.text(ax, label, ((x_a + x_b) / 2, y - gap if below else y + gap),
               valign="top" if below else "bottom", size=size, color=ink)


def span(ax, x_a: float, x_b: float, y: float, label: str,
         size: float = style.SMALL_SIZE) -> None:
    """A double-headed measurement arrow between two x positions, labelled above it."""
    # An empty annotation, so all that is drawn is the arrow between the two points.
    ax.annotate(
        "",
        xy=(x_a, y),
        xytext=(x_b, y),
        arrowprops=dict(arrowstyle="<->", color=style.ACCENT_COLOR,
                        lw=style.ACCENT_WIDTH, shrinkA=0, shrinkB=0))
    style.text(ax, label, ((x_a + x_b) / 2, y + 0.28), valign="bottom", size=size)


def callout(ax, caption: tuple[float, float], target: tuple[float, float]) -> None:
    """An arrow from a caption to the thing it is about.

    Worth the ink whenever a caption sits more than a cell away from its subject. A reader
    should never have to guess which of eight bits a sentence underneath them refers to.
    """
    ax.annotate(
        "",
        xy=target,
        xytext=caption,
        arrowprops=dict(arrowstyle="->", color=style.ACCENT_COLOR, lw=style.ACCENT_WIDTH,
                        shrinkA=2, shrinkB=2))


def arrow(ax, start: tuple[float, float], end: tuple[float, float],
          color: str | None = None, lw: float | None = None,
          dashed: bool = False) -> None:
    """A plain single-headed arrow, for a flow diagram's edges."""
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            color=color or style.LINE_COLOR,
            lw=lw or style.WIRE_WIDTH,
            linestyle=(0, (4, 3)) if dashed else "-",
            shrinkA=0,
            shrinkB=0,
            zorder=2))


def vbrace(ax, y_a: float, y_b: float, x: float, label: str, left: bool = False,
           color: str | None = None, size: float = style.SMALL_SIZE) -> None:
    """A square brace spanning [y_a, y_b] at `x`, labelled outside it.

    The vertical twin of `brace`, for the figures whose runs are stacked rather than laid out
    in a row: a pointer register pair inside the register file, an address range inside a
    memory map.
    """
    ink = color or style.ACCENT_COLOR
    tick = -0.22 if left else 0.22

    ax.plot([x + tick, x, x, x + tick], [y_a, y_a, y_b, y_b],
            color=ink, lw=style.ACCENT_WIDTH, clip_on=False, solid_joinstyle="miter")

    gap = 0.24
    style.text(ax, label, (x - gap if left else x + gap, (y_a + y_b) / 2),
               halign="right" if left else "left", size=size, color=ink)


def dashed_box(ax, x_a: float, y_a: float, x_b: float, y_b: float, label: str,
               color: str | None = None) -> None:
    """A dashed outline with a label inside its top edge, for a boundary that is not a wire.

    Drawn with matplotlib rather than with schemdraw's Rect, which places itself at the
    drawing's current position rather than at the coordinates given to it: passing absolute
    corners to that puts the box wherever the last element happened to leave the cursor, and
    the figure renders without complaint somewhere it does not belong.
    """
    ink = color or style.MUTED_COLOR
    ax.plot([x_a, x_b, x_b, x_a, x_a], [y_a, y_a, y_b, y_b, y_a],
            color=ink, lw=style.BOX_WIDTH, linestyle=(0, (5, 3)), solid_joinstyle="miter",
            zorder=0)
    style.text(ax, label, ((x_a + x_b) / 2, y_b - 0.5), size=style.SMALL_SIZE, color=ink)
