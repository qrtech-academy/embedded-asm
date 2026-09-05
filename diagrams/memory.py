"""Address-space maps: a memory drawn as its labelled regions.

The ATmega328P has three separate address spaces, and the single most common mistake a
reader arriving from C makes is to treat them as one. A figure here is a column of regions
with their addresses down the side, and several columns side by side is how the three spaces
are shown to be three.

**Low addresses at the top**, which is the AVR datasheet's convention and the opposite of the
way memory is usually drawn elsewhere. Following the datasheet is worth more here than
following habit: the reader will have it open beside this figure.

**Not drawn to scale, ever.** The data space runs from a 32-byte register file to a 2048-byte
SRAM, a factor of 64, and a faithful drawing would make the registers a hairline. Region
heights are set by how much there is to say about a region, and every figure built here says
so in as many words.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import schemdraw

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
COL_GAP = 2.30         # Between two address spaces drawn side by side.
ADDRESS_GAP = 0.30     # Between a column's left edge and its address labels.
TITLE_GAP = 0.95       # Between the top of a column and its title.
DETAIL_GAP = 0.20      # Between a region's label and the line under it.
NOTE_GAP = 0.45        # Between the deepest column and the shared note baseline.
CAPTION_GAP = 0.55     # Between the notes and the caption under them all.
MARGIN = 0.45


@dataclass(frozen=True)
class Region:
    """One labelled range of an address space.

    `first` and `last` are printed at the region's top and bottom boundary respectively, so a
    column reads as a run of addresses rather than as a stack of boxes. `detail` is the
    second line inside the box: what lives there, or how big it is.
    """

    label: str
    first: str
    last: str
    detail: str | None = None
    fill: str = "plain"
    height: float = 1.25


@dataclass(frozen=True)
class Column:
    """One address space: a title, its regions from lowest address to highest, and a width."""

    title: str
    regions: Sequence[Region]
    width: float = 5.4
    note: Sequence[str] = ()


@dataclass(frozen=True)
class Layout:
    """Where every column and region landed."""

    columns: Sequence[Column]
    lefts: Sequence[float] = field(default=())

    def bounds(self, column: int) -> tuple[float, float]:
        """(left, right) x of one column."""
        left = self.lefts[column]
        return left, left + self.columns[column].width

    def region_y(self, column: int, index: int) -> tuple[float, float]:
        """(low, high) y of one region. Low addresses at the top, so this walks downwards."""
        high = 0.0
        for region in self.columns[column].regions[:index]:
            high -= region.height
        return high - self.columns[column].regions[index].height, high

    def height(self, column: int) -> float:
        """How far down one column reaches."""
        return sum(region.height for region in self.columns[column].regions)


def _draw(layout: Layout, caption: str | None, drawing: schemdraw.Drawing, ax) -> None:
    """Draw every column: its title, its regions, and the addresses down its left side."""
    for index, column in enumerate(layout.columns):
        left, right = layout.bounds(index)
        style.title(ax, column.title, ((left + right) / 2, TITLE_GAP))

        for position, region in enumerate(column.regions):
            low, high = layout.region_y(index, position)
            shapes.cell(ax, left, low, column.width, region.height, region.fill)

            # The label sits centred when it is alone, and rides above the detail line when
            # there is one, so a region with more to say does not push its own name off
            # centre relative to the regions beside it.
            middle = (low + high) / 2
            if region.detail is None:
                style.text(ax, region.label, ((left + right) / 2, middle),
                           size=style.SMALL_SIZE)
            else:
                style.text(ax, region.label, ((left + right) / 2, middle + DETAIL_GAP),
                           valign="bottom", size=style.SMALL_SIZE)
                style.text(ax, region.detail, ((left + right) / 2, middle - DETAIL_GAP),
                           valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

            # Addresses at the boundaries, outside the column. The first address of every
            # region is printed; the last is printed only for the bottom one, because every
            # other boundary already carries the next region's first address one line down.
            style.text(ax, region.first, (left - ADDRESS_GAP, high), halign="right",
                       valign="center", size=style.TINY_SIZE, color=style.MUTED_COLOR)
            if position == len(column.regions) - 1:
                style.text(ax, region.last, (left - ADDRESS_GAP, low), halign="right",
                           valign="center", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    deepest = max(layout.height(index) for index in range(len(layout.columns)))

    for index, column in enumerate(layout.columns):
        if not column.note:
            continue
        left, right = layout.bounds(index)
        step = style.text_height(style.TINY_SIZE) * style.CAPTION_LEADING
        for line, text in enumerate(column.note):
            style.text(ax, text, ((left + right) / 2, -deepest - NOTE_GAP - line * step),
                       valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    if caption:
        _, right = layout.bounds(len(layout.columns) - 1)
        style.caption(ax, caption, right / 2, -deepest - _notes_depth(layout.columns))


def _notes_depth(columns: Sequence[Column]) -> float:
    """How far below the deepest column the notes reach, before the caption starts."""
    lines = max((len(column.note) for column in columns), default=0)
    if lines == 0:
        return NOTE_GAP
    return NOTE_GAP + lines * style.text_height(
        style.TINY_SIZE) * style.CAPTION_LEADING + CAPTION_GAP


def figure(columns: Sequence[Column], caption: Sequence[str] = ()) -> style.Figure:
    """A ready-to-render map of one or more address spaces, side by side."""
    # Column lefts, allowing each its own width plus room for the next column's addresses.
    lefts: list[float] = []
    cursor = 0.0
    for column in columns:
        lefts.append(cursor)
        cursor += column.width + COL_GAP
    layout = Layout(columns=columns, lefts=lefts)

    deepest = max(layout.height(index) for index in range(len(columns)))
    _, right = layout.bounds(len(columns) - 1)

    bottom = -deepest - _notes_depth(columns)
    if caption:
        bottom -= style.caption_height(caption)

    # The left edge clears the widest address label, which sits outside the first column.
    widest = max(
        (style.text_width(text, style.TINY_SIZE)
         for column in columns for region in column.regions
         for text in (region.first, region.last)),
        default=0.0)
    left, edge = -ADDRESS_GAP - widest, right

    # A note is centred under its own column and a caption under the whole figure, and both
    # routinely reach past what they sit under. Measured rather than hoped for: the outer
    # columns are where a note runs off the canvas, and a clipped note still renders.
    for index, column in enumerate(columns):
        if not column.note:
            continue
        column_left, column_right = layout.bounds(index)
        span_left, span_right = style.caption_bounds(
            column.note, (column_left + column_right) / 2, style.TINY_SIZE)
        left, edge = min(left, span_left), max(edge, span_right)
    if caption:
        span_left, span_right = style.caption_bounds(caption, right / 2)
        left, edge = min(left, span_left), max(edge, span_right)

    return style.Figure(
        draw=lambda d, ax: _draw(layout, caption, d, ax),
        canvas=(left - MARGIN, bottom - MARGIN,
                edge + MARGIN, TITLE_GAP + style.text_height(style.TITLE_SIZE) + MARGIN))
