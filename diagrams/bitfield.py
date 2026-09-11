"""Register bit-field diagrams: a register drawn as its named bits.

This is the workhorse of the course. Almost everything the ATmega328P does is configured by
writing a bit pattern into a named register, and almost every appendix has to show one. A
figure here is a row of cells, MSB on the left, each cell carrying the datasheet's name for
that bit, with the register's own name to the left of the row and its address to the right.

Several registers can share one figure, stacked, which is how a peripheral's control
registers are shown together: TCCR1A above TCCR1B, or WDTCSR above MCUSR.

Conventions:

* Bit numbers run above the top row only. Every register in this course is eight bits wide,
  so repeating 7..0 over each row would be noise.
* A reserved or unimplemented bit is filled `muted` and named `-`. The datasheet calls these
  "Res"; drawing them grey and unnamed says the same thing without the reader looking it up.
* A bit the surrounding text is about is filled `accent`. Nothing is *only* colored: the
  fill groups, and the name in the cell says what it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

import schemdraw

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
CELL_W = 1.75
CELL_H = 1.05
ROW_PITCH = 1.55       # Centre-to-centre between two stacked registers.
NAME_GAP = 0.35        # Between the register name and the leftmost cell.
ADDRESS_GAP = 0.40     # Between the rightmost cell and the address.
NUMBER_GAP = 0.16      # Between the top row and the bit numbers above it.
MARGIN = 0.40          # Blank canvas around everything.

# A bit name that does not fit its cell at SMALL_SIZE drops to TINY_SIZE rather than running
# over the cell walls. Six characters at SMALL_SIZE is about the limit at CELL_W; the AVR's
# longest names (WDCE, TOIE1, OCIE1A, PCINT23) sit right on it, so this is not hypothetical.
NAME_FIT_PAD = 0.12

# How far below the bottom row a caption sits when nothing else is drawn down there.
CAPTION_DROP = 0.62

# How far above the top row a brace must start to clear the bit numbers that sit there. A
# brace drawn any lower is struck straight through them, and the render succeeds regardless.
BRACE_LIFT = NUMBER_GAP + 0.44


@dataclass(frozen=True)
class Bit:
    """One bit of a register: what the datasheet calls it, and how to fill its cell."""

    name: str
    fill: str = "plain"

    @staticmethod
    def reserved() -> "Bit":
        """A bit the device does not implement. Reads as zero, and writing it does nothing."""
        return Bit("-", "muted")


@dataclass(frozen=True)
class Register:
    """One register: its name, its bits from MSB to LSB, and where it lives."""

    name: str
    bits: Sequence[Bit]
    address: str | None = None


@dataclass(frozen=True)
class Layout:
    """Where everything landed, so an annotation can point at a cell by number."""

    registers: Sequence[Register]
    width: int
    top: float = 0.0
    cell_w: float = CELL_W

    @property
    def right(self) -> float:
        """The x of the rightmost cell wall."""
        return self.width * self.cell_w

    def row_y(self, row: int) -> tuple[float, float]:
        """(low, high) y of the register `row` rows down from the top."""
        high = self.top - row * ROW_PITCH
        return high - CELL_H, high

    def cell_x(self, index: int) -> tuple[float, float]:
        """(left, right) x of the cell `index` places right of the MSB."""
        return index * self.cell_w, (index + 1) * self.cell_w

    def centre(self, row: int, index: int) -> tuple[float, float]:
        """The middle of one cell, for a callout to aim at."""
        low, high = self.row_y(row)
        left, right = self.cell_x(index)
        return (left + right) / 2, (low + high) / 2

    def bit_index(self, row: int, name: str) -> int:
        """Where a named bit sits, so an annotation names the bit rather than counting cells.

        Counting cells by hand in the figure module is how an annotation ends up pointing at
        the wrong bit after somebody inserts one, and the drawing still looks plausible.
        """
        for index, bit in enumerate(self.registers[row].bits):
            if bit.name == name:
                return index
        raise KeyError(f"{self.registers[row].name} has no bit named {name!r}")


# An annotation pass: braces, callouts and captions drawn once the cells are in place.
Annotator = Callable[["object", Layout], None]


def _fit(name: str, cell_w: float) -> float:
    """The largest size at which `name` fits inside a cell of width `cell_w`."""
    for size in (style.SMALL_SIZE, style.TINY_SIZE):
        if style.fits(name, cell_w - NAME_FIT_PAD, size):
            return size
    return style.TINY_SIZE


def _draw(registers: Sequence[Register], caption: Sequence[str], caption_drop: float,
          annotate: Annotator | None, layout: Layout, drawing: schemdraw.Drawing, ax) -> None:
    """Draw every register, then let the figure add whatever it wants on top."""
    for row, register in enumerate(registers):
        low, high = layout.row_y(row)

        # The register's own name, right-aligned into the label column.
        style.text(ax, register.name, (-NAME_GAP, (low + high) / 2), halign="right")

        for index, bit in enumerate(register.bits):
            left, _ = layout.cell_x(index)
            shapes.cell(ax, left, low, layout.cell_w, CELL_H, bit.fill)

            # A reserved bit is grey and its dash is grey too, so the row reads as "these
            # ones are not yours" at a glance rather than after reading eight names.
            colour = style.MUTED_COLOR if bit.fill == "muted" else style.LINE_COLOR
            style.text(ax, bit.name, (left + layout.cell_w / 2, (low + high) / 2),
                       size=_fit(bit.name, layout.cell_w), color=colour)

        if register.address is not None:
            style.text(ax, register.address, (layout.right + ADDRESS_GAP,
                                              (low + high) / 2),
                       halign="left", size=style.SMALL_SIZE, color=style.MUTED_COLOR)

    # Bit numbers, above the top row only.
    _, high = layout.row_y(0)
    for index in range(layout.width):
        left, right = layout.cell_x(index)
        style.text(ax, str(layout.width - 1 - index), ((left + right) / 2,
                                                       high + NUMBER_GAP),
                   valign="bottom", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    if caption:
        low, _ = layout.row_y(len(registers) - 1)
        style.caption(ax, caption, layout.right / 2, low - caption_drop)

    if annotate is not None:
        annotate(ax, layout)


def figure(registers: Sequence[Register], caption: Sequence[str] = (),
           annotate: Annotator | None = None, caption_drop: float = CAPTION_DROP,
           cell_w: float = CELL_W,
           pad: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)) -> style.Figure:
    """A ready-to-render figure for one or more registers.

    `pad` widens the canvas by (left, bottom, right, top) for an annotation that reaches
    outside the cells: a brace above the top row, or a caption below the bottom one. A figure
    declares the room it needs rather than being cropped to its contents, so two figures read
    one after another line up.

    `caption_drop` is how far below the bottom row the caption sits. It exists because this
    module lays the cells out and the figure's own `annotate` draws whatever it likes
    underneath them, and neither can see the other: a register with a brace below it needs
    the caption pushed past that brace's label, and nothing here can work out how far. The
    default clears a bare row. Anything drawn below one has to say so.
    """
    width = max(len(register.bits) for register in registers)
    layout = Layout(registers=registers, width=width, cell_w=cell_w)

    # The label column is as wide as the longest register name; the right edge clears the
    # widest address. Both are measured rather than guessed, so a long name cannot clip.
    names = max(style.text_width(register.name) for register in registers)
    addresses = max(
        (style.text_width(r.address or "", style.SMALL_SIZE) for r in registers), default=0.0)

    bottom, _ = layout.row_y(len(registers) - 1)
    left, right, up = -(NAME_GAP + names), layout.right, NUMBER_GAP + style.text_height(
        style.TINY_SIZE)
    if addresses:
        right += ADDRESS_GAP + addresses
    if caption:
        bottom -= caption_drop + style.caption_height(caption)
        span_left, span_right = style.caption_bounds(caption, layout.right / 2)
        left, right = min(left, span_left), max(right, span_right)

    return style.Figure(
        draw=lambda d, ax: _draw(registers, caption, caption_drop, annotate, layout, d, ax),
        canvas=(left - MARGIN - pad[0], bottom - MARGIN - pad[1],
                right + MARGIN + pad[2], up + MARGIN + pad[3]))
