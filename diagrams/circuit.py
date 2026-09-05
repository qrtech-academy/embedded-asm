"""The two figures in this course that are actually circuits.

Everything else here is a map of something inside the chip. These two are what is outside it: an
LED with its series resistor, and a button against the pin's internal pull-up. They are drawn
because the reader has to wire them, or at least picture them, and because the pull-up in
particular is impossible to reason about from the register description alone.

Two rules, both learned the hard way, and both of which produce a wrong figure rather than an
error when broken:

**Every element is placed at an explicit coordinate**, and every device is added before any wire
or one-terminal symbol. schemdraw's `.right()`, `.left()` and `.reverse()` are relative to the
drawing's current direction, and adding a `Ground` or a `Vdd` changes that direction, so a device
added afterwards comes out mirrored while its anchor coordinates still read correctly. The symptom
is a diagonal wire across the figure.

**A boundary is drawn with `shapes.dashed_box`, never with `elm.Rect`.** schemdraw's rectangle
places itself at the drawing's current position; the absolute corners handed to it are treated as
an offset from wherever the last element left the cursor. The box lands somewhere else entirely
and nothing reports a problem.

Every coordinate below is a named constant, so the canvas and the drawing are computed from the
same numbers and cannot disagree.
"""

from __future__ import annotations

import schemdraw.elements as elm

import shapes
import style

# ----------------------------------------------------------------------------------------
# Geometry, in schemdraw units. A two-terminal element is 3.0 units long by default, and every
# position downstream of one follows from that.
# ----------------------------------------------------------------------------------------
DEVICE = 3.0           # Length of a resistor, an LED or a button.
PIN_X = 0.0            # Where the pin leaves the chip.
CHIP_W = 3.6           # Width of the chip boundary.
LEAD = 1.2             # Wire between the pin and the first device, and after the last.
GROUND_DROP = 0.9      # How far below the wire a ground symbol reaches.
CAPTION_DROP = 1.5     # Between the wire and the first caption line.
MARGIN = 0.55


def _canvas(caption: tuple[str, ...], centre: float, left: float, right: float,
            top: float, bottom: float) -> tuple[float, float, float, float]:
    """A canvas holding the drawing and the caption underneath it.

    The caption is routinely wider than the circuit it describes, so it is measured rather than
    assumed to fit: a canvas pinned to the drawing clips it in silence.
    """
    text_left, text_right = style.caption_bounds(caption, centre)
    return (min(left, text_left) - MARGIN,
            bottom - CAPTION_DROP - style.caption_height(caption) - MARGIN,
            max(right, text_right) + MARGIN,
            top + MARGIN)


# ----------------------------------------------------------------------------------------
# A.5: an LED, driven high.
#
# Drawn in the source configuration, where the pin at 5 V lights the LED, because that is what
# `led_on` writing a 1 to PORTB means and the arrangement the reader will predict. The sink
# configuration, where the LED lights when the pin goes low, is the other half of A.5's prose.
# ----------------------------------------------------------------------------------------
_LED_RESISTOR_X = PIN_X + LEAD
_LED_LED_X = _LED_RESISTOR_X + DEVICE
_LED_GROUND_X = _LED_LED_X + DEVICE + LEAD
_LED_TOP = 1.7
_LED_BOTTOM = -GROUND_DROP

_LED_CAPTION = (
    "PORTB bit 5 high lights it, low turns it off. The resistor is not optional: the pin will",
    "happily deliver enough current to destroy the LED, and then itself.")


def _draw_led(drawing, ax) -> None:
    """Pin, series resistor, LED, ground."""
    # Devices first, at absolute positions.
    drawing.add(elm.Resistor().at((_LED_RESISTOR_X, 0)).right().label("220 Ohm", loc="top"))
    drawing.add(elm.LED().at((_LED_LED_X, 0)).right().label("LED", loc="top"))

    # Then the wires, and the one-terminal symbol last of all.
    drawing.add(elm.Line().at((PIN_X, 0)).to((_LED_RESISTOR_X, 0)))
    drawing.add(elm.Line().at((_LED_LED_X + DEVICE, 0)).to((_LED_GROUND_X, 0)))
    drawing.add(elm.Ground().at((_LED_GROUND_X, 0)))

    shapes.dashed_box(ax, PIN_X - CHIP_W, _LED_BOTTOM, PIN_X, _LED_TOP, "ATmega328P")
    style.text(ax, "PB5", (PIN_X - 0.25, 0.28), halign="right", valign="bottom",
               size=style.SMALL_SIZE)

    style.caption(ax, _LED_CAPTION, (PIN_X - CHIP_W + _LED_GROUND_X) / 2,
                  _LED_BOTTOM - CAPTION_DROP)


LED_CIRCUIT = style.Figure(
    _draw_led,
    _canvas(_LED_CAPTION, (PIN_X - CHIP_W + _LED_GROUND_X) / 2,
            PIN_X - CHIP_W, _LED_GROUND_X + 0.8, _LED_TOP, _LED_BOTTOM))


# ----------------------------------------------------------------------------------------
# A.6: a button, against the internal pull-up.
#
# The pull-up is drawn inside the chip boundary on purpose. It is the single most useful thing
# to understand about this circuit: there is a resistor, you did not fit it, and it is switched
# on by writing a 1 to PORTx on a pin whose DDRx is 0.
# ----------------------------------------------------------------------------------------
# The chip is wider here than in the LED figure, because there is something inside it: the
# pull-up, its value, and room for neither to touch the boundary.
_BUTTON_CHIP_W = 5.6
_PULLUP_X = PIN_X - _BUTTON_CHIP_W + 1.7
_PULLUP_TOP = 3.2
_PULLUP_BOTTOM = _PULLUP_TOP - DEVICE
_BUTTON_X = PIN_X + LEAD
_BUTTON_GROUND_X = _BUTTON_X + DEVICE + LEAD

# Clear of the Vdd symbol and the "5 V" above it, so the boundary does not run through either.
_CHIP_TOP = _PULLUP_TOP + 1.7
_CHIP_BOTTOM = -2.1

_BUTTON_CAPTION = (
    "Not pressed, the pull-up holds the pin at 5 V and PINB reads 1. Pressed, the button shorts",
    "it to ground and PINB reads 0. A pressed button reads zero, which is the wrong way round",
    "from every intuition, and is the whole reason button_pressed has to invert what it read.")


def _draw_button(drawing, ax) -> None:
    """The internal pull-up inside the chip, the button outside it, and ground."""
    # Devices first: the pull-up inside the chip, the button outside it. The resistor's value
    # is placed by hand rather than with schemdraw's label, whose offset for a vertical element
    # put it across the chip boundary.
    drawing.add(elm.Resistor().at((_PULLUP_X, _PULLUP_TOP)).down()
                .color(style.ACCENT_COLOR_2))
    drawing.add(elm.Button().at((_BUTTON_X, 0)).right().label("button", loc="top"))
    style.text(ax, "20-50 kOhm", (_PULLUP_X + 0.45, (_PULLUP_TOP + _PULLUP_BOTTOM) / 2),
               halign="left", size=style.SMALL_SIZE, color=style.ACCENT_COLOR_2)

    # Then the wires, then the one-terminal symbols.
    drawing.add(elm.Line().at((_PULLUP_X, _PULLUP_BOTTOM)).to((_PULLUP_X, 0))
                .color(style.ACCENT_COLOR_2))
    drawing.add(elm.Line().at((_PULLUP_X, 0)).to((_BUTTON_X, 0)))
    drawing.add(elm.Line().at((_BUTTON_X + DEVICE, 0)).to((_BUTTON_GROUND_X, 0)))
    drawing.add(elm.Ground().at((_BUTTON_GROUND_X, 0)))
    drawing.add(elm.Vdd().at((_PULLUP_X, _PULLUP_TOP)).label("5 V"))

    # The label sits at the bottom of the box here, because the top of it is occupied.
    shapes.dashed_box(ax, PIN_X - _BUTTON_CHIP_W, _CHIP_BOTTOM, PIN_X, _CHIP_TOP, "")
    style.text(ax, "ATmega328P", (PIN_X - _BUTTON_CHIP_W / 2, _CHIP_BOTTOM + 0.42),
               valign="bottom", size=style.SMALL_SIZE, color=style.MUTED_COLOR)
    style.text(ax, "PB5", (PIN_X - 0.25, 0.28), halign="right", valign="bottom",
               size=style.SMALL_SIZE)

    # The one thing about this figure that a register description cannot tell you.
    shapes.callout(ax, (_CALLOUT_X, 1.35), (_PULLUP_X - 0.35, 1.8))
    for index, line in enumerate(("switched on by", "PORTB bit 5 = 1", "with DDRB bit 5 = 0")):
        style.text(ax, line, (_CALLOUT_X, 1.15 - index * 0.42), valign="top",
                   size=style.TINY_SIZE, color=style.ACCENT_COLOR)

    style.caption(ax, _BUTTON_CAPTION, (PIN_X - _BUTTON_CHIP_W + _BUTTON_GROUND_X) / 2,
                  _CHIP_BOTTOM - CAPTION_DROP)


# Outside the chip, far enough left that the three lines of it clear the boundary.
_CALLOUT_X = PIN_X - _BUTTON_CHIP_W - 2.3

BUTTON_CIRCUIT = style.Figure(
    _draw_button,
    _canvas(_BUTTON_CAPTION, (PIN_X - _BUTTON_CHIP_W + _BUTTON_GROUND_X) / 2,
            _CALLOUT_X - 2.0, _BUTTON_GROUND_X + 0.8, _CHIP_TOP + 0.9, _CHIP_BOTTOM))
