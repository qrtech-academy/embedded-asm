"""L02 figures: what the three port registers do, and which pin is which.

Two figures, answering the two questions a reader has when they first meet DDRx, PORTx and PINx.
The first is what a combination of DDR and PORT actually does to a pin, which the datasheet
answers in prose spread over three pages. The second is which port bit an Arduino pin number
means, which the datasheet does not answer at all, because Arduino pin numbers are not the
device's idea.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# A.2: the four states of a pin.
#
# A two-by-two grid, because there are exactly two control bits and the reader's question is
# always "what does this combination do". Drawn as a matrix rather than as a four-row table so
# that the two inputs sit above the two outputs and the structure is visible before the text
# is read.
# ----------------------------------------------------------------------------------------
_STATE_W = 6.6
_STATE_H = 2.1
_STATE_GAP = 0.30
_HEADER_GAP = 0.45
_ROW_LABEL_GAP = 0.45

# (column, row) -> (heading, detail, fill). Row 0 is DDRx = 0, the input row.
_STATES = {
    (0, 0): ("Input, high impedance", "floating: reads whatever is on the wire", "plain"),
    (1, 0): ("Input, pull-up enabled", "reads 1 until something pulls it down", "accent2"),
    (0, 1): ("Output, driven low", "sinks current, holds the pin at 0 V", "accent"),
    (1, 1): ("Output, driven high", "sources current, holds the pin at 5 V", "accent"),
}


def _state_bounds(column: int, row: int) -> tuple[float, float]:
    """(left, low) of one cell of the matrix. Row 0 is the top row."""
    return (column * (_STATE_W + _STATE_GAP),
            -(row + 1) * _STATE_H - row * _STATE_GAP)


def _draw_port_states(drawing, ax) -> None:
    """The two control bits against the four things they can mean."""
    for (column, row), (heading, detail, fill) in _STATES.items():
        left, low = _state_bounds(column, row)
        shapes.cell(ax, left, low, _STATE_W, _STATE_H, fill)

        middle = left + _STATE_W / 2
        style.text(ax, heading, (middle, low + _STATE_H / 2 + 0.24), valign="bottom",
                   size=style.SMALL_SIZE)
        style.text(ax, detail, (middle, low + _STATE_H / 2 - 0.24), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

    # Column headings, above the top row.
    for column, text in ((0, "PORTx = 0"), (1, "PORTx = 1")):
        left, _ = _state_bounds(column, 0)
        style.text(ax, text, (left + _STATE_W / 2, _HEADER_GAP), valign="bottom")

    # Row headings, to the left, each naming the direction it sets.
    for row, (text, detail) in ((0, ("DDRx = 0", "input")), (1, ("DDRx = 1", "output"))):
        left, low = _state_bounds(0, row)
        style.text(ax, text, (-_ROW_LABEL_GAP, low + _STATE_H / 2 + 0.22), halign="right",
                   valign="bottom")
        style.text(ax, detail, (-_ROW_LABEL_GAP, low + _STATE_H / 2 - 0.22), halign="right",
                   valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

    # The third register, which is not in the grid because it is not a control bit.
    _, bottom = _state_bounds(0, 1)
    style.caption(ax, _STATE_CAPTION, _STATE_RIGHT / 2, bottom - _CAPTION_DROP)


_STATE_CAPTION = (
    "PINx is the third register and is not part of this grid: reading it gives the pin's",
    "actual level, and writing a 1 to it toggles PORTx. Writing a 0 to it does nothing.")

_CAPTION_DROP = 0.55
_STATE_RIGHT = _STATE_W * 2 + _STATE_GAP

# The caption is wider than the grid it sits under, so it sets the canvas rather than fitting
# inside it. Measured with caption_bounds rather than guessed: a canvas pinned to the drawing
# clips the caption in silence, and the render succeeds either way.
_STATE_TEXT_LEFT, _STATE_TEXT_RIGHT = style.caption_bounds(_STATE_CAPTION, _STATE_RIGHT / 2)
_STATE_LEFT = min(-_ROW_LABEL_GAP - style.text_width("DDRx = 0"), _STATE_TEXT_LEFT)
_STATE_BOTTOM = (_state_bounds(0, 1)[1] - _CAPTION_DROP
                 - style.caption_height(_STATE_CAPTION))

PORT_STATES = style.Figure(
    _draw_port_states,
    (_STATE_LEFT - 0.45, _STATE_BOTTOM - 0.45,
     max(_STATE_RIGHT, _STATE_TEXT_RIGHT) + 0.45,
     _HEADER_GAP + style.text_height() + 0.45))


# ----------------------------------------------------------------------------------------
# A.4: Arduino pin numbers against port bits.
#
# The mapping the LED driver has to perform, and the reason led_init takes a number from 0 to
# 13 rather than a port and a bit. Fourteen cells in a row, because the numbering really is
# one flat run across two ports, and the break between them is the whole point.
# ----------------------------------------------------------------------------------------
_PIN_W = 1.62
_PIN_H = 1.25
_PIN_COUNT = 14
_PORTD_PINS = 8  # Arduino 0 to 7 are port D; 8 to 13 are port B.


def _draw_arduino_pins(drawing, ax) -> None:
    """One cell per Arduino pin, carrying the port bit it actually is."""
    for pin in range(_PIN_COUNT):
        left = pin * _PIN_W
        port = "D" if pin < _PORTD_PINS else "B"
        bit = pin if pin < _PORTD_PINS else pin - _PORTD_PINS
        fill = "accent2" if port == "D" else "accent"

        shapes.cell(ax, left, 0.0, _PIN_W, _PIN_H, fill)
        style.text(ax, str(pin), (left + _PIN_W / 2, _PIN_H + 0.16), valign="bottom",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)
        style.text(ax, f"P{port}{bit}", (left + _PIN_W / 2, _PIN_H / 2),
                   size=style.SMALL_SIZE)

    # Brace each port's run, because the split is the fact the figure exists to carry.
    shapes.brace(ax, 0.0, _PORTD_PINS * _PIN_W, -0.30, "port D, bits 0 to 7", below=True,
                 color=style.ACCENT_COLOR_2)
    shapes.brace(ax, _PORTD_PINS * _PIN_W, _PIN_COUNT * _PIN_W, -0.30,
                 "port B, bits 0 to 5", below=True)

    style.caption(ax, _PIN_CAPTION, _PIN_RIGHT / 2, -_PIN_CAPTION_DROP)


_PIN_CAPTION = (
    "Arduino pin 13, the one with the LED soldered to it, is bit 5 of port B.",
    "The device has never heard of pin 13; the mapping is the board's, and yours to do.")

_PIN_CAPTION_DROP = 1.30
_PIN_RIGHT = _PIN_COUNT * _PIN_W
_PIN_TEXT_LEFT, _PIN_TEXT_RIGHT = style.caption_bounds(_PIN_CAPTION, _PIN_RIGHT / 2)

ARDUINO_PINS = style.Figure(
    _draw_arduino_pins,
    (min(0.0, _PIN_TEXT_LEFT) - 0.45,
     -_PIN_CAPTION_DROP - style.caption_height(_PIN_CAPTION) - 0.45,
     max(_PIN_RIGHT, _PIN_TEXT_RIGHT) + 0.45,
     _PIN_H + 0.16 + style.text_height(style.TINY_SIZE) + 0.45))
