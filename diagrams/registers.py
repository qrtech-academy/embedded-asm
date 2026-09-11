"""Figures drawn as register bit fields, across every lecture that configures hardware.

Each one names its lecture and the appendix section it belongs to, because a figure whose
only home is a dictionary in `build.py` is a figure nobody notices has gone stale.
"""

from __future__ import annotations

import shapes
import style
from bitfield import BRACE_LIFT, Bit, Register, figure

# ----------------------------------------------------------------------------------------
# L01: the status register.
#
# Drawn first among the register figures because it is the one register the reader never
# writes and always has to reason about: every arithmetic instruction leaves marks here, and
# every conditional branch reads them.
# ----------------------------------------------------------------------------------------
_SREG = Register(
    "SREG",
    [
        Bit("I", "accent"),
        Bit("T"),
        Bit("H"),
        Bit("S"),
        Bit("V"),
        Bit("N"),
        Bit("Z", "accent2"),
        Bit("C", "accent2"),
    ],
    address="0x5F")


def _annotate_sreg(ax, layout) -> None:
    """Mark the global interrupt enable, and the two flags nearly every branch reads."""
    # The I bit, which is the only one in this register set by an instruction of its own.
    left, right = layout.cell_x(layout.bit_index(0, "I"))
    _, high = layout.row_y(0)
    shapes.brace(ax, left, right, high + BRACE_LIFT, "sei / cli", size=style.TINY_SIZE)

    # Z and C, which is where a comparison leaves its answer.
    left, _ = layout.cell_x(layout.bit_index(0, "Z"))
    _, right = layout.cell_x(layout.bit_index(0, "C"))
    low, _ = layout.row_y(0)
    shapes.brace(ax, left, right, low - 0.30, "breq / brne",
                 below=True, color=style.ACCENT_COLOR_2, size=style.TINY_SIZE)


SREG = figure(
    [_SREG],
    caption=("Set by arithmetic and logic, read by the conditional branches.",),
    annotate=_annotate_sreg,
    caption_drop=1.32,
    pad=(0.0, 0.30, 0.0, 1.05))


# ----------------------------------------------------------------------------------------
# L03 A.5: the two registers that switch a pin change interrupt on.
#
# Both live at 0x68 and above, which is extended I/O, so `in` and `out` cannot reach either of
# them and `lds` and `sts` are the only way in. That is the first place in this course where
# L01's distinction between the two addressings stops being trivia.
# ----------------------------------------------------------------------------------------
_PCICR = Register(
    "PCICR",
    [Bit.reserved(), Bit.reserved(), Bit.reserved(), Bit.reserved(), Bit.reserved(),
     Bit("PCIE2"), Bit("PCIE1"), Bit("PCIE0", "accent")],
    address="0x68")

_PCMSK0 = Register(
    "PCMSK0",
    [Bit("PCINT7", "muted"), Bit("PCINT6", "muted"), Bit("PCINT5"), Bit("PCINT4", "accent"),
     Bit("PCINT3"), Bit("PCINT2"), Bit("PCINT1"), Bit("PCINT0")],
    address="0x6B")


def _annotate_pcint(ax, layout) -> None:
    """Mark the two bits an Arduino Uno button on pin 12 actually needs."""
    left, right = layout.cell_x(layout.bit_index(0, "PCIE0"))
    _, high = layout.row_y(0)
    shapes.brace(ax, left, right, high + BRACE_LIFT, "one whole port", size=style.TINY_SIZE)

    left, right = layout.cell_x(layout.bit_index(1, "PCINT4"))
    low, _ = layout.row_y(1)
    shapes.brace(ax, left, right, low - 0.30, "one pin of it", below=True,
                 size=style.TINY_SIZE)

    # The two bits that exist on the device and not on the board.
    left, _ = layout.cell_x(layout.bit_index(1, "PCINT7"))
    _, right = layout.cell_x(layout.bit_index(1, "PCINT6"))
    shapes.brace(ax, left, right, low - 0.30, "crystal pins", below=True,
                 color=style.MUTED_COLOR, size=style.TINY_SIZE)


PCINT_REGISTERS = figure(
    [_PCICR, _PCMSK0],
    caption=("Enabling one pin takes both: PCICR turns on the port's single vector, and PCMSK0",
             "says which of its eight pins may raise it. Neither is reachable by in or out."),
    annotate=_annotate_pcint,
    caption_drop=1.32,
    pad=(0.0, 0.30, 0.0, 1.05))


# ----------------------------------------------------------------------------------------
# L05 A.5: the three registers that make Timer1 do anything.
#
# TCCR1B carries both the waveform mode and the prescaler, which is the arrangement that makes
# a single careless write turn the timer off: the clock select bits are in the same byte as
# everything else, and writing zero to them stops the counter dead.
# ----------------------------------------------------------------------------------------
_TCCR1A = Register(
    "TCCR1A",
    [Bit("COM1A1"), Bit("COM1A0"), Bit("COM1B1"), Bit("COM1B0"),
     Bit.reserved(), Bit.reserved(), Bit("WGM11"), Bit("WGM10")],
    address="0x80")

_TCCR1B = Register(
    "TCCR1B",
    [Bit("ICNC1"), Bit("ICES1"), Bit.reserved(), Bit("WGM13"), Bit("WGM12", "accent"),
     Bit("CS12", "accent2"), Bit("CS11", "accent2"), Bit("CS10", "accent2")],
    address="0x81")

_TIMSK1 = Register(
    "TIMSK1",
    [Bit.reserved(), Bit.reserved(), Bit.reserved(), Bit.reserved(), Bit.reserved(),
     Bit("ICIE1"), Bit("OCIE1A", "accent"), Bit("TOIE1")],
    address="0x6F")


def _annotate_timer(ax, layout) -> None:
    """Mark the two fields CTC mode needs, and the one bit that lets it interrupt."""
    # Braced under the *bottom* row rather than under TCCR1B's own: the rows are 0.5 units
    # apart and a brace with a label under it is taller than that, so bracing row 1 directly
    # draws it straight through row 2.
    left, _ = layout.cell_x(layout.bit_index(1, "CS12"))
    _, right = layout.cell_x(layout.bit_index(1, "CS10"))
    low, _ = layout.row_y(2)
    shapes.brace(ax, left, right, low - 0.30, "CS12:CS10 in TCCR1B: the prescaler, and the on "
                 "switch", below=True, color=style.ACCENT_COLOR_2, size=style.TINY_SIZE)

    left, right = layout.cell_x(layout.bit_index(1, "WGM12"))
    _, high = layout.row_y(0)
    shapes.brace(ax, left, right, high + BRACE_LIFT, "CTC mode", size=style.TINY_SIZE)


TIMER_REGISTERS = figure(
    [_TCCR1A, _TCCR1B, _TIMSK1],
    caption=("CTC with a prescaler of 64 is WGM12 set in TCCR1B and CS11 and CS10 with it.",
             "All three bits are in one byte, so a careless write to TCCR1B stops the timer."),
    annotate=_annotate_timer,
    caption_drop=1.32,
    pad=(0.0, 0.30, 0.0, 1.05))


# ----------------------------------------------------------------------------------------
# L06 A.3: the watchdog's control register, and where a reset records its cause.
#
# The four prescaler bits are the thing to look at: WDP2, WDP1 and WDP0 are the bottom three
# bits, and WDP3 is bit 5, with WDCE and WDE in between them. So a "timeout number" of 9 is not
# the byte 0x09; it is 0x21, and nothing about the register's name warns you.
# ----------------------------------------------------------------------------------------
_WDTCSR = Register(
    "WDTCSR",
    [Bit("WDIF"), Bit("WDIE", "accent2"), Bit("WDP3", "accent"), Bit("WDCE"),
     Bit("WDE", "accent2"), Bit("WDP2", "accent"), Bit("WDP1", "accent"),
     Bit("WDP0", "accent")],
    address="0x60")

_MCUSR = Register(
    "MCUSR",
    [Bit.reserved(), Bit.reserved(), Bit.reserved(), Bit.reserved(),
     Bit("WDRF", "accent2"), Bit("BORF"), Bit("EXTRF"), Bit("PORF")],
    address="0x54")


def _annotate_watchdog(ax, layout) -> None:
    """Show that the four timeout bits are not next to each other."""
    _, high = layout.row_y(0)
    left, right = layout.cell_x(layout.bit_index(0, "WDP3"))
    shapes.brace(ax, left, right, high + BRACE_LIFT, "WDP3", size=style.TINY_SIZE)

    left, _ = layout.cell_x(layout.bit_index(0, "WDP2"))
    _, right = layout.cell_x(layout.bit_index(0, "WDP0"))
    shapes.brace(ax, left, right, high + BRACE_LIFT, "WDP2 to WDP0", size=style.TINY_SIZE)

    low, _ = layout.row_y(1)
    left, right = layout.cell_x(layout.bit_index(1, "WDRF"))
    shapes.brace(ax, left, right, low - 0.30, "set when the watchdog was the cause",
                 below=True, color=style.ACCENT_COLOR_2, size=style.TINY_SIZE)


WATCHDOG_REGISTERS = figure(
    [_WDTCSR, _MCUSR],
    caption=("The four timeout bits are not adjacent: WDP3 is bit 5, with WDCE and WDE between",
             "it and the other three. A timeout number of 9 is the byte 0x21, not 0x09."),
    annotate=_annotate_watchdog,
    caption_drop=1.32,
    pad=(0.0, 0.30, 0.0, 1.05))
