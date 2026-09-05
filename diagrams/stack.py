"""L02: what rcall pushes, and what ret does not undo.

Three snapshots of the same four bytes of SRAM, before a call, inside the subroutine, and after
the return. Everything in this figure was read out of the simulator rather than taken from the
datasheet's prose, because three of the facts in it are ones people routinely get backwards:

* the return address pushed is a **word** address, not the byte address the disassembler prints;
* it is pushed **low byte first**, so the low byte ends up at the *higher* address;
* `ret` moves the stack pointer and **erases nothing**.

**Note the axis.** This figure has high addresses at the top, the opposite way up from the memory
map in L01. That is deliberate: "the stack grows downwards" is a statement about addresses, and
drawing it this way makes it a downward movement on the page as well. The memory map follows the
datasheet's convention and this follows the reader's; there is no way to satisfy both at once, so
the figure says which it is doing.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
CELL_W = 3.5
CELL_H = 0.95
PANEL_GAP = 3.4
ADDRESS_GAP = 0.32     # Between a cell's left edge and its address.
POINTER_GAP = 0.35     # Between a cell's right edge and the stack pointer arrow.
POINTER_LEN = 1.15
TITLE_GAP = 0.55
CAPTION_DROP = 0.75
MARGIN = 0.50

# Top address of the strip, and how many bytes of it are drawn.
TOP_ADDRESS = 0x08FF
ROWS = 4

# (title, {address: (text, fill)}, stack pointer address). Read out of the simulator: an rcall
# at byte address 0x0A returns to byte 0x0C, which is word 0x06, and that word is what is pushed.
PANELS = (
    ("Before rcall",
     {},
     0x08FF),
    ("Inside the subroutine",
     {0x08FF: ("0x06", "accent"), 0x08FE: ("0x00", "accent")},
     0x08FD),
    ("After ret",
     {0x08FF: ("0x06", "muted"), 0x08FE: ("0x00", "muted")},
     0x08FF),
)

CAPTION = (
    "The return address is a word address, and 0x06 is the low byte of it. ret moves the stack",
    "pointer back and erases nothing: the two bytes are still there, and are simply no longer",
    "anybody's. Every push you do not pop leaves the stack pointer somewhere you did not mean.",
)


def _panel_left(index: int) -> float:
    """x of the left edge of one panel."""
    return index * (CELL_W + PANEL_GAP)


def _row_y(address: int) -> tuple[float, float]:
    """(low, high) y of one byte's cell. The top address is the top row."""
    row = TOP_ADDRESS - address
    high = -row * CELL_H
    return high - CELL_H, high


def _draw(drawing, ax) -> None:
    """Three snapshots of the same four bytes, side by side."""
    for index, (title, contents, pointer) in enumerate(PANELS):
        left = _panel_left(index)
        style.text(ax, title, (left + CELL_W / 2, TITLE_GAP), valign="bottom",
                   size=style.SMALL_SIZE)

        for row in range(ROWS):
            address = TOP_ADDRESS - row
            low, high = _row_y(address)
            text, fill = contents.get(address, ("", "plain"))
            shapes.cell(ax, left, low, CELL_W, CELL_H, fill)

            if text:
                colour = style.MUTED_COLOR if fill == "muted" else style.LINE_COLOR
                style.text(ax, text, (left + CELL_W / 2, (low + high) / 2),
                           size=style.SMALL_SIZE, color=colour)

            # Addresses down the left of the first panel only; the other two are the same
            # bytes, and repeating the column three times would say otherwise.
            if index == 0:
                style.text(ax, f"0x{address:04X}", (left - ADDRESS_GAP, (low + high) / 2),
                           halign="right", size=style.TINY_SIZE, color=style.MUTED_COLOR)

        # The stack pointer, as an arrow into the byte it points at from the right.
        low, high = _row_y(pointer)
        middle = (low + high) / 2
        shapes.arrow(ax, (left + CELL_W + POINTER_GAP + POINTER_LEN, middle),
                     (left + CELL_W + POINTER_GAP, middle), color=style.ACCENT_COLOR_2)
        style.text(ax, "SP", (left + CELL_W + POINTER_GAP + POINTER_LEN + 0.25, middle),
                   halign="left", size=style.SMALL_SIZE, color=style.ACCENT_COLOR_2)

    bottom, _ = _row_y(TOP_ADDRESS - ROWS + 1)
    style.caption(ax, CAPTION, _CENTRE, bottom - CAPTION_DROP)


_LEFT = -ADDRESS_GAP - style.text_width("0x08FF", style.TINY_SIZE)
_RIGHT = (_panel_left(len(PANELS) - 1) + CELL_W + POINTER_GAP + POINTER_LEN + 0.25
          + style.text_width("SP", style.SMALL_SIZE))
_CENTRE = (_LEFT + _RIGHT) / 2
_BOTTOM = (_row_y(TOP_ADDRESS - ROWS + 1)[0] - CAPTION_DROP
           - style.caption_height(CAPTION))
_TEXT_LEFT, _TEXT_RIGHT = style.caption_bounds(CAPTION, _CENTRE)

CALL_STACK = style.Figure(
    _draw,
    (min(_LEFT, _TEXT_LEFT) - MARGIN, _BOTTOM - MARGIN,
     max(_RIGHT, _TEXT_RIGHT) + MARGIN,
     TITLE_GAP + style.text_height(style.SMALL_SIZE) + MARGIN))
