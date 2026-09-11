"""The AVR register file, drawn as its 32 registers.

One figure shape, reused by three lectures, because the same 32 cells answer three different
questions and the reader should recognize the picture each time:

* L01 asks which registers `ldi` can reach, and which pairs are the pointer registers.
* L02 asks which registers a subroutine may clobber and which it must give back.
* L06 asks where the C compiler puts arguments and return values.

Laid out as two columns of sixteen, r0 to r15 on the left and r16 to r31 on the right. That
is not an arbitrary split: the immediate instructions (`ldi`, `andi`, `ori`, `subi`, `cpi`)
encode their register in four bits and can therefore only name the upper half. Drawing the
file this way makes the most consequential fact about it a fact about where things are.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import schemdraw

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
CELL_W = 4.05
CELL_H = 0.66
COL_GAP = 1.50         # Between the two columns of sixteen.
ROWS = 16
MARGIN = 0.40
CAPTION_DROP = 0.55    # Between the bottom of the columns and the first caption line.


@dataclass(frozen=True)
class Layout:
    """Where every register cell landed."""

    top: float = 0.0

    def column_x(self, column: int) -> tuple[float, float]:
        """(left, right) x of one column."""
        left = column * (CELL_W + COL_GAP)
        return left, left + CELL_W

    def cell(self, number: int) -> tuple[float, float, float, float]:
        """(left, low, right, high) of register `number`, 0 to 31."""
        column, row = divmod(number, ROWS)
        left, right = self.column_x(column)
        high = self.top - row * CELL_H
        return left, high - CELL_H, right, high

    def centre(self, number: int) -> tuple[float, float]:
        """The middle of one register's cell, for a callout to aim at."""
        left, low, right, high = self.cell(number)
        return (left + right) / 2, (low + high) / 2


Annotator = Callable[["object", Layout], None]


def _draw(fills: dict[int, str], labels: dict[int, str], caption: Sequence[str],
          annotate: Annotator | None, layout: Layout, drawing: schemdraw.Drawing, ax) -> None:
    """Draw all 32 cells, then let the figure add its braces and captions on top."""
    for number in range(32):
        left, low, right, high = layout.cell(number)
        shapes.cell(ax, left, low, CELL_W, CELL_H, fills.get(number, "plain"),
                    lw=style.CELL_WIDTH)

        # The register's own name on the left of its cell, and whatever this figure wants to
        # say about it on the right. Two columns inside one cell, so a role never displaces
        # the name: the reader must always be able to find r24 by looking for "r24".
        style.text(ax, f"r{number}", (left + 0.28, (low + high) / 2), halign="left",
                   size=style.SMALL_SIZE)
        role = labels.get(number)
        if role is not None:
            style.text(ax, role, (right - 0.28, (low + high) / 2), halign="right",
                       size=style.TINY_SIZE, color=style.ACCENT_COLOR)

    # A heavier outline around each column, so the file reads as two blocks of sixteen
    # rather than as thirty-two loose boxes.
    for column in (0, 1):
        left, right = layout.column_x(column)
        _, low, _, _ = layout.cell(column * ROWS + ROWS - 1)
        _, _, _, high = layout.cell(column * ROWS)
        ax.plot([left, right, right, left, left], [low, low, high, high, low],
                color=style.LINE_COLOR, lw=style.BOX_WIDTH, solid_joinstyle="miter",
                zorder=2)

    if caption:
        _, low, _, _ = layout.cell(ROWS - 1)
        _, right = layout.column_x(1)
        style.caption(ax, caption, right / 2, low - CAPTION_DROP)

    if annotate is not None:
        annotate(ax, layout)


def figure(fills: dict[int, str] | None = None, labels: dict[int, str] | None = None,
           caption: Sequence[str] = (), annotate: Annotator | None = None,
           pad: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)) -> style.Figure:
    """A ready-to-render register file, filled and labelled for one lecture's question.

    `fills` and `labels` are keyed by register number. `pad` widens the canvas by
    (left, bottom, right, top) for braces and captions drawn outside the cells.
    """
    layout = Layout()
    fills = fills or {}
    labels = labels or {}

    _, low, _, _ = layout.cell(ROWS - 1)
    _, right = layout.column_x(1)

    # The caption is centred under the two columns and is routinely wider than they are, so
    # it sets the canvas rather than fitting inside it.
    bottom, left, edge = low, 0.0, right
    if caption:
        bottom = low - CAPTION_DROP - style.caption_height(caption)
        span_left, span_right = style.caption_bounds(caption, right / 2)
        left, edge = min(left, span_left), max(edge, span_right)

    return style.Figure(
        draw=lambda d, ax: _draw(fills, labels, caption, annotate, layout, d, ax),
        canvas=(left - MARGIN - pad[0], bottom - MARGIN - pad[1],
                edge + MARGIN + pad[2], MARGIN + pad[3]))
