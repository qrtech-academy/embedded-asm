"""L04: where things live in SRAM, and how far down the stack reaches.

**High addresses at the top in both figures**, the same way up as L02's stack diagram and the
opposite way up from L01's memory map. L01 followed the datasheet, which draws the data space with
0x0000 at the top; these follow the reader, because "the stack grows downwards" is a statement
about addresses and it should be a downward movement on the page as well. Neither convention can
be right for both figures, so each says which it is using.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# B.4: the map, with the one address that is not memory at all.
# ----------------------------------------------------------------------------------------
_MAP_W = 9.2
_ADDRESS_GAP = 0.35
_NOTE_GAP = 0.45
_MARGIN = 0.45

# (label, detail, height, fill, top address, bottom address)
#
# A boundary carries one label, not two. The line between "Not memory" and "The stack" is both
# the bottom of 0x0900 and the top of 0x08FF, and printing both puts two addresses on top of each
# other; the region that owns the boundary is the one below it, so 0x08FF is what appears.
_REGIONS = (
    ("Not memory", "0x0900 upwards: reads give nothing, writes go nowhere", 1.35, "muted",
     "0x0FFF", ""),
    ("The stack", "grows downwards from RAMEND", 1.55, "accent", "0x08FF", ""),
    ("Free", "and nothing is watching the gap close", 2.30, "plain", "", ""),
    ("The data segment", ".dseg and .byte, at addresses the assembler chose\n"
     "and with nothing to initialise them", 2.20, "accent2", "", "0x0100"),
)

_MAP_CAPTION = (
    "RAMEND + 1 is 0x0900, and on an ATmega328P it is not memory. On a device with external RAM",
    "it would be where that begins, which is why you will find AVR code allocating driver",
    "structures there. Here, storing to it writes nothing and loading from it reads nothing.",
)


def _region_y(index: int) -> tuple[float, float]:
    """(low, high) y of one region, stacked downwards from zero."""
    high = -sum(region[2] for region in _REGIONS[:index])
    return high - _REGIONS[index][2], high


def _draw_map(drawing, ax) -> None:
    """The regions, their addresses, and an arrow showing which way the stack moves."""
    for index, (label, detail, _, fill, top, bottom) in enumerate(_REGIONS):
        low, high = _region_y(index)
        shapes.cell(ax, 0.0, low, _MAP_W, high - low, fill)

        middle = (low + high) / 2
        style.text(ax, label, (_MAP_W / 2, middle + 0.22), valign="bottom",
                   size=style.SMALL_SIZE)
        style.text(ax, detail, (_MAP_W / 2, middle - 0.22), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

        if top:
            style.text(ax, top, (-_ADDRESS_GAP, high), halign="right", size=style.TINY_SIZE,
                       color=style.MUTED_COLOR)
        if bottom:
            style.text(ax, bottom, (-_ADDRESS_GAP, low), halign="right", size=style.TINY_SIZE,
                       color=style.MUTED_COLOR)

    # Which way the stack moves, drawn beside the region it moves through.
    low, high = _region_y(1)
    shapes.arrow(ax, (_MAP_W + 0.5, high - 0.15), (_MAP_W + 0.5, low - 0.9),
                 color=style.ACCENT_COLOR)
    style.text(ax, "every push", (_MAP_W + 0.75, high - 0.35), halign="left",
               size=style.TINY_SIZE, color=style.ACCENT_COLOR)
    style.text(ax, "and every call", (_MAP_W + 0.75, high - 0.77), halign="left",
               size=style.TINY_SIZE, color=style.ACCENT_COLOR)

    style.caption(ax, _MAP_CAPTION, _MAP_W / 2, _MAP_BOTTOM)


_MAP_BOTTOM = _region_y(len(_REGIONS) - 1)[0] - _NOTE_GAP
_MAP_RIGHT = _MAP_W + 0.75 + style.text_width("and every call", style.TINY_SIZE)
_MAP_LEFT = -_ADDRESS_GAP - style.text_width("0x0FFF", style.TINY_SIZE)
_MAP_TEXT_LEFT, _MAP_TEXT_RIGHT = style.caption_bounds(_MAP_CAPTION, _MAP_W / 2)

SRAM_MAP = style.Figure(
    _draw_map,
    (min(_MAP_LEFT, _MAP_TEXT_LEFT) - _MARGIN,
     _MAP_BOTTOM - style.caption_height(_MAP_CAPTION) - _MARGIN,
     max(_MAP_RIGHT, _MAP_TEXT_RIGHT) + _MARGIN,
     style.text_height(style.TINY_SIZE) / 2 + _MARGIN))


# ----------------------------------------------------------------------------------------
# C.2: how deep the stack gets, one frame at a time.
#
# The worst case of L03's program: the main loop calls nothing, so the depth is all the
# interrupt's: the program counter, the handler's nine saves, and two calls inside it. Every number
# here is bytes, and all of them were measured.
# ----------------------------------------------------------------------------------------
_STEP_H = 0.95
_STEP_W = 11.0
_BYTE_SCALE = 0.62     # Canvas units per byte of stack, for the bar beside each step.
_BAR_GAP = 0.6

# (what happened, bytes this adds, running total)
_FRAMES = (
    ("the main loop, which calls nothing", 0, 0),
    ("an interrupt lands: the PC is pushed", 2, 2),
    ("the handler saves eight registers and SREG", 9, 11),
    ("rcall btn_pressed", 2, 13),
    ("rcall shift_bits, from inside that", 2, 15),
)

# How many of those rows are the main program's; the rest are the interrupt's.
_MAIN_ROWS = 1

_DEPTH_CAPTION = (
    "Fifteen bytes at the deepest. The lowest byte used is 0x08F1, and the stack pointer ends at",
    "0x08F0, one below it, because SP always points at the next free byte rather than the last",
    "used one. Compute this before running anything: nothing here notices a stack meeting a",
    "variable, and RAMEND minus SP is the count you want.",
)


def _draw_depth(drawing, ax) -> None:
    """One row per frame, with a bar whose length is the running total in bytes."""
    for index, (label, added, total) in enumerate(_FRAMES):
        low = -(index + 1) * _STEP_H
        style.text(ax, label, (-_BAR_GAP, low + _STEP_H / 2), halign="right",
                   size=style.SMALL_SIZE)

        if total > 0:
            shapes.cell(ax, 0.0, low + 0.12, total * _BYTE_SCALE, _STEP_H - 0.24,
                        "accent" if index >= _MAIN_ROWS else "accent2")
        style.text(ax, f"{total} bytes" + (f"  (+{added})" if added else ""),
                   (total * _BYTE_SCALE + 0.3, low + _STEP_H / 2), halign="left",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

    # Where the two halves divide: everything from the interrupt down is the handler's.
    divider = -_MAIN_ROWS * _STEP_H
    ax.plot([-_BAR_GAP - _LABEL_W, _RIGHT_EDGE], [divider, divider],
            color=style.MUTED_COLOR, lw=1.2, linestyle=(0, (4, 3)), zorder=0)

    style.caption(ax, _DEPTH_CAPTION, _DEPTH_CENTRE, _DEPTH_BOTTOM)


_LABEL_W = max(style.text_width(label, style.SMALL_SIZE) for label, _, _ in _FRAMES)
_MAX_TOTAL = max(total for _, _, total in _FRAMES)
_RIGHT_EDGE = (_MAX_TOTAL * _BYTE_SCALE + 0.3
               + style.text_width("15 bytes  (+2)", style.TINY_SIZE))
_DEPTH_LEFT = -_BAR_GAP - _LABEL_W
_DEPTH_CENTRE = (_DEPTH_LEFT + _RIGHT_EDGE) / 2
_DEPTH_BOTTOM = -len(_FRAMES) * _STEP_H - 0.55
_DEPTH_TEXT_LEFT, _DEPTH_TEXT_RIGHT = style.caption_bounds(_DEPTH_CAPTION, _DEPTH_CENTRE)

STACK_DEPTH = style.Figure(
    _draw_depth,
    (min(_DEPTH_LEFT, _DEPTH_TEXT_LEFT) - _MARGIN,
     _DEPTH_BOTTOM - style.caption_height(_DEPTH_CAPTION) - _MARGIN,
     max(_RIGHT_EDGE, _DEPTH_TEXT_RIGHT) + _MARGIN,
     _MARGIN))
