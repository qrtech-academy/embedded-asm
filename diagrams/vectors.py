"""L03: the ATmega328P interrupt vector table.

All twenty-six of them, in two columns, with the ones this course actually uses marked. The
addresses are **word** addresses, which is what `.org` takes and what the datasheet's table gives,
and the reason PCINT0 sits at 0x06 rather than at 0x03: each slot is two words wide, because a
`jmp` on a part with 32 KB of flash is a two-word instruction.

Every entry was read out of avr-libc's `iom328p.h` rather than typed from the datasheet, because a
table of twenty-six numbers transcribed by hand is a table with a mistake in it.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in canvas units.
# ----------------------------------------------------------------------------------------
CELL_W = 8.2
CELL_H = 0.68
COL_GAP = 1.6
ROWS = 13
ADDRESS_PAD = 0.3
MARGIN = 0.45
TITLE_GAP = 0.5
CAPTION_DROP = 0.55

# Vector number to name, from iom328p.h. Vector 0 is the reset vector, which is not an interrupt
# and is the only entry the hardware reaches without anything having been enabled.
NAMES = (
    "RESET", "INT0", "INT1", "PCINT0", "PCINT1", "PCINT2", "WDT",
    "TIMER2_COMPA", "TIMER2_COMPB", "TIMER2_OVF",
    "TIMER1_CAPT", "TIMER1_COMPA", "TIMER1_COMPB", "TIMER1_OVF",
    "TIMER0_COMPA", "TIMER0_COMPB", "TIMER0_OVF",
    "SPI_STC", "USART_RX", "USART_UDRE", "USART_TX",
    "ADC", "EE_READY", "ANALOG_COMP", "TWI", "SPM_READY",
)

# Words per vector slot, which is what turns a vector number into an address.
WORDS_PER_VECTOR = 2

# The ones this course writes a handler for, and the one it starts from.
USED = {"RESET", "PCINT0", "PCINT1", "PCINT2", "WDT", "TIMER1_COMPA"}

CAPTION = (
    "Word addresses, not byte addresses. Each slot is two words wide, so vector n is at 2n, and",
    "PCINT0 is at 0x06 rather than at 0x03. Halving these puts every handler in a program at the",
    "wrong address at once, which produces behaviour strange enough that people blame the chip.",
)


def _cell(index: int) -> tuple[float, float]:
    """(left, low) of the cell for vector `index`."""
    column, row = divmod(index, ROWS)
    return column * (CELL_W + COL_GAP), -(row + 1) * CELL_H


def _draw(drawing, ax) -> None:
    """Two columns of thirteen, address on the left of each cell and name in the middle."""
    for index, name in enumerate(NAMES):
        left, low = _cell(index)
        fill = "accent" if name in USED else "plain"
        shapes.cell(ax, left, low, CELL_W, CELL_H, fill, lw=style.CELL_WIDTH)

        style.text(ax, f"0x{index * WORDS_PER_VECTOR:04X}", (left + ADDRESS_PAD, low + CELL_H / 2),
                   halign="left", size=style.TINY_SIZE, color=style.MUTED_COLOR)
        style.text(ax, name, (left + CELL_W - ADDRESS_PAD, low + CELL_H / 2), halign="right",
                   size=style.SMALL_SIZE)

    # A heavier outline round each column, so the table reads as two blocks rather than as
    # twenty-six loose boxes.
    for column in range(2):
        left = column * (CELL_W + COL_GAP)
        last = min(column * ROWS + ROWS, len(NAMES)) - 1
        _, low = _cell(last)
        ax.plot([left, left + CELL_W, left + CELL_W, left, left],
                [low, low, 0.0, 0.0, low],
                color=style.LINE_COLOR, lw=style.BOX_WIDTH, solid_joinstyle="miter", zorder=2)

    style.text(ax, "Written in this course", (_RIGHT / 2, TITLE_GAP), valign="bottom",
               size=style.SMALL_SIZE, color=style.ACCENT_COLOR)
    style.caption(ax, CAPTION, _RIGHT / 2, _BOTTOM_ROW - CAPTION_DROP)


_RIGHT = 2 * CELL_W + COL_GAP
_BOTTOM_ROW = -ROWS * CELL_H
_TEXT_LEFT, _TEXT_RIGHT = style.caption_bounds(CAPTION, _RIGHT / 2)

VECTOR_TABLE = style.Figure(
    _draw,
    (min(0.0, _TEXT_LEFT) - MARGIN,
     _BOTTOM_ROW - CAPTION_DROP - style.caption_height(CAPTION) - MARGIN,
     max(_RIGHT, _TEXT_RIGHT) + MARGIN,
     TITLE_GAP + style.text_height(style.SMALL_SIZE) + MARGIN))
