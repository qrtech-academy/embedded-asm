"""L04: the pointer addressing modes, and a structure as the bytes it really is.

Two figures. The first shows what each addressing mode does to memory and to the pointer, side by
side, because the difference between them is entirely about the pointer and entirely invisible in
the value that comes back. The second shows an LED structure as seven bytes at real addresses,
holding the values `led_init` actually leaves there for Arduino pin 13.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# A.3: the four ways to reach memory through a pointer.
#
# Four panels, one per mode, each a short strip of memory with the pointer before and after.
# Panels rather than one strip with four annotations: the point is the comparison, and things
# being compared should be the same shape in the same places.
# ----------------------------------------------------------------------------------------
_MODE_CELL_W = 1.55
_MODE_CELL_H = 1.05
_MODE_CELLS = 5
_MODE_GAP = 1.9
# Stacked upwards from the cells: the arrow, then its label, then the instruction above both.
# Computed rather than chosen, so that changing the arrow length cannot silently put the title
# through it.
_MODE_ARROW_TOP = 1.05 + 0.95          # cell height plus arrow length
_MODE_LABEL_TOP = _MODE_ARROW_TOP + 0.12 + style.text_height(style.TINY_SIZE)
_MODE_TITLE_GAP = _MODE_LABEL_TOP + 0.35
_MODE_ARROW = 0.95
_BASE_INDEX = 1  # Where Z points before the instruction, counting from the left.

# (instruction, index read or written, index the pointer ends at, note)
_MODES = (
    ("ld r16, Z", 1, 1, "reads at Z, and leaves Z alone"),
    ("ld r16, Z+", 1, 2, "reads at Z, then adds one"),
    ("ld r16, -Z", 0, 0, "subtracts one, then reads"),
    ("ldd r16, Z+3", 4, 1, "reads at Z plus 3, Z unmoved"),
)

_MODE_CAPTION = (
    "All four cost two cycles and all four put a byte in r16. What differs is where the byte came",
    "from and where the pointer is afterwards, and neither of those is visible in r16. Note that",
    "-Z decrements first and Z+ increments last: the sign is on the side the change happens.",
)


def _mode_left(panel: int) -> float:
    """x of the left edge of one panel."""
    return panel * (_MODE_CELLS * _MODE_CELL_W + _MODE_GAP)


def _draw_modes(drawing, ax) -> None:
    """One strip per mode, with the pointer before in grey and after in red."""
    for panel, (instruction, target, ends, note) in enumerate(_MODES):
        left = _mode_left(panel)
        style.text(ax, instruction, (left + _MODE_CELLS * _MODE_CELL_W / 2, _MODE_TITLE_GAP),
                   valign="bottom", size=style.SMALL_SIZE)

        for index in range(_MODE_CELLS):
            fill = "accent" if index == target else "plain"
            shapes.cell(ax, left + index * _MODE_CELL_W, 0.0, _MODE_CELL_W, _MODE_CELL_H, fill)

        # Where the pointer was, above the strip, and where it ends, below it.
        start_x = left + (_BASE_INDEX + 0.5) * _MODE_CELL_W
        end_x = left + (ends + 0.5) * _MODE_CELL_W
        shapes.arrow(ax, (start_x, _MODE_CELL_H + _MODE_ARROW), (start_x, _MODE_CELL_H + 0.1),
                     color=style.MUTED_COLOR)
        style.text(ax, "Z before", (start_x, _MODE_CELL_H + _MODE_ARROW + 0.12),
                   valign="bottom", size=style.TINY_SIZE, color=style.MUTED_COLOR)

        shapes.arrow(ax, (end_x, -_MODE_ARROW), (end_x, -0.1), color=style.ACCENT_COLOR_2)
        style.text(ax, "Z after", (end_x, -_MODE_ARROW - 0.12), valign="top",
                   size=style.TINY_SIZE, color=style.ACCENT_COLOR_2)

        style.text(ax, note, (left + _MODE_CELLS * _MODE_CELL_W / 2, -_MODE_ARROW - 0.72),
                   valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    style.caption(ax, _MODE_CAPTION, _MODE_RIGHT / 2, _MODE_BOTTOM)


_MODE_RIGHT = _mode_left(len(_MODES) - 1) + _MODE_CELLS * _MODE_CELL_W
_MODE_BOTTOM = -_MODE_ARROW - 0.72 - style.text_height(style.TINY_SIZE) - 0.55
_MODE_TEXT_LEFT, _MODE_TEXT_RIGHT = style.caption_bounds(_MODE_CAPTION, _MODE_RIGHT / 2)

ADDRESSING_MODES = style.Figure(
    _draw_modes,
    (min(0.0, _MODE_TEXT_LEFT) - 0.45,
     _MODE_BOTTOM - style.caption_height(_MODE_CAPTION) - 0.45,
     max(_MODE_RIGHT, _MODE_TEXT_RIGHT) + 0.45,
     _MODE_TITLE_GAP + style.text_height(style.SMALL_SIZE) + 0.45))


# ----------------------------------------------------------------------------------------
# A.5: an LED structure, as the seven bytes it actually is.
#
# The values are the ones led_init leaves for Arduino pin 13, read out of the simulator: the
# three port register addresses of port B, low byte first, and the bit number.
# ----------------------------------------------------------------------------------------
_BYTE_W = 2.35
_BYTE_H = 1.15
_STRUCT_BASE = 0x0200

# (value, field this byte belongs to)
_BYTES = (
    ("0x23", "pin_reg"), ("0x00", "pin_reg"),
    ("0x24", "dir_reg"), ("0x00", "dir_reg"),
    ("0x25", "port_reg"), ("0x00", "port_reg"),
    ("0x05", "pin"),
)

# (field, first byte index, last byte index, what ldd reaches it with)
_FIELDS = (
    ("pin_reg", 0, 1, "ldd r26, Z+0"),
    ("dir_reg", 2, 3, "ldd r26, Z+2"),
    ("port_reg", 4, 5, "ldd r26, Z+4"),
    ("pin", 6, 6, "ldd r24, Z+6"),
)

_STRUCT_CAPTION = (
    "Seven bytes, and every one of them is reachable in a single two-cycle instruction because",
    "ldd takes a constant displacement from Z. A 16-bit field is two bytes, low byte first, so",
    "0x23 followed by 0x00 is the address 0x0023, which is PINB.",
)


def _draw_struct(drawing, ax) -> None:
    """Seven byte cells, their addresses, and the four fields braced over them."""
    for index, (value, _) in enumerate(_BYTES):
        left = index * _BYTE_W
        shapes.cell(ax, left, 0.0, _BYTE_W, _BYTE_H, "accent2" if index == 6 else "plain")
        style.text(ax, value, (left + _BYTE_W / 2, _BYTE_H / 2), size=style.SMALL_SIZE)
        style.text(ax, f"0x{_STRUCT_BASE + index:04X}", (left + _BYTE_W / 2, -0.22),
                   valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    for name, first, last, reach in _FIELDS:
        left = first * _BYTE_W
        right = (last + 1) * _BYTE_W
        shapes.brace(ax, left, right, _BYTE_H + 0.32, name, size=style.SMALL_SIZE)
        style.text(ax, reach, ((left + right) / 2, _BYTE_H + 1.32), valign="bottom",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

    style.caption(ax, _STRUCT_CAPTION, _STRUCT_RIGHT / 2, _STRUCT_BOTTOM)


_STRUCT_RIGHT = len(_BYTES) * _BYTE_W
_STRUCT_BOTTOM = -0.22 - style.text_height(style.TINY_SIZE) - 0.55
_STRUCT_TEXT_LEFT, _STRUCT_TEXT_RIGHT = style.caption_bounds(_STRUCT_CAPTION, _STRUCT_RIGHT / 2)

STRUCT_LAYOUT = style.Figure(
    _draw_struct,
    (min(0.0, _STRUCT_TEXT_LEFT) - 0.45,
     _STRUCT_BOTTOM - style.caption_height(_STRUCT_CAPTION) - 0.45,
     max(_STRUCT_RIGHT, _STRUCT_TEXT_RIGHT) + 0.45,
     _BYTE_H + 1.32 + style.text_height(style.TINY_SIZE) + 0.45))
