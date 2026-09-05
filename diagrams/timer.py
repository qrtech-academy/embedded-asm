"""L05 figures: a timer as a block, as a waveform, and as the error it cannot avoid.

The first two describe the hardware. The third is the one the lecture turns on: a timer counts
whole ticks, so most frequencies you ask for are not available, and the figure is a picture of
which ones are and how far off you land.

The arithmetic at the top is here because the figures need the device's real numbers, and because
it is the same arithmetic the reader writes in `avr::timer::Timer`. What it is deliberately *not*
used for is a plot of the frequency error. That was drawn, and it came out an unreadable thicket:
the error oscillates far too quickly against frequency to show as a curve, and every way of
smoothing it into something legible also smoothed away the fact being taught. The material belongs
in a table the reader generates with their own `best()`, which is where the appendix puts it.
"""

from __future__ import annotations

import flow
import shapes
import style

# ----------------------------------------------------------------------------------------
# The device's numbers. From the ATmega328P datasheet.
# ----------------------------------------------------------------------------------------
CLOCK_HZ = 16_000_000
PRESCALERS = (1, 8, 64, 256, 1024)
TIMER1_TOP = 65_536          # A 16-bit counter counts this many values.


def compare_for(hertz: float, prescaler: int) -> int:
    """The compare value that comes nearest a wanted frequency, at one prescaler."""
    ticks = round(CLOCK_HZ / (prescaler * hertz))
    return max(1, ticks) - 1


def achievable(hertz: float) -> tuple[int, int, float]:
    """(prescaler, compare, actual hertz) for the smallest prescaler that fits."""
    for prescaler in PRESCALERS:
        compare = compare_for(hertz, prescaler)
        if compare < TIMER1_TOP:
            return prescaler, compare, CLOCK_HZ / (prescaler * (compare + 1))
    prescaler = PRESCALERS[-1]
    compare = TIMER1_TOP - 1
    return prescaler, compare, CLOCK_HZ / (prescaler * (compare + 1))


# ----------------------------------------------------------------------------------------
# A.2: the timer as a block diagram.
# ----------------------------------------------------------------------------------------
_BLOCK_NODES = (
    flow.Node("The 16 MHz clock", (0.0, 0.0), "one tick per cycle", "accent2", 6.4, 1.5),
    flow.Node("Prescaler", (8.6, 0.0), "divide by 1, 8, 64, 256 or 1024", "plain", 8.2,
              1.5),
    flow.Node("TCNT1", (18.4, 0.0), "counts up, 16 bits wide", "accent", 6.4, 1.5),
    flow.Node("Comparator", (18.4, -3.2), "TCNT1 = OCR1A?", "plain", 6.4, 1.5),
    flow.Node("OCR1A", (9.6, -3.2), "the value you chose", "accent", 6.4, 1.5),
    flow.Node("On a match", (18.4, -6.4), "clear TCNT1, raise the flag", "plain", 8.2,
              1.5),
    flow.Node("Your handler", (18.4, -9.6), "if OCIE1A is set", "accent2", 8.2, 1.5),
)

_BLOCK_EDGES = (
    flow.Edge(0, 1),
    # Lifted clear of the boxes: the label is wider than the gap between them, so at the
    # default offset it would sit across both.
    flow.Edge(1, 2, "one tick per N cycles", label_offset=(0.0, 1.05)),
    flow.Edge(2, 3),
    flow.Edge(4, 3),
    flow.Edge(3, 5),
    flow.Edge(5, 6),
)

TIMER_BLOCK = flow.figure(
    _BLOCK_NODES, _BLOCK_EDGES,
    caption=("Everything above the handler happens in hardware, whether or not any code is",
             "running. That is the whole argument for a timer over a counting loop: the counting",
             "is not done by the processor, so the processor is free to be doing something else."))


# ----------------------------------------------------------------------------------------
# A.4: what CTC mode looks like in time.
# ----------------------------------------------------------------------------------------
_OCR = 4.2                # Height of the OCR1A line, in canvas units.
_PERIOD = 5.0             # Width of one count-up, in canvas units.
_PERIODS = 3
_PULSE_H = 1.1
_LABEL_GAP = 0.35         # Between the traces and the names to their left.
_PULSE_BASE = -2.6
_WAVE_CAPTION_DROP = 0.7

_WAVE_CAPTION = (
    "The counter is cleared by the hardware on a match, so the period is exactly",
    "N x (OCR1A + 1) cycles and never drifts. OCR1A + 1, not OCR1A, because the count",
    "starts at zero and the match happens at the end of the value's own tick.",
)


def _draw_ctc(drawing, ax) -> None:
    """The counter's sawtooth against OCR1A, and the interrupts it produces."""
    # The counter: up to OCR1A, then straight back to zero.
    xs: list[float] = []
    ys: list[float] = []
    for period in range(_PERIODS):
        left = period * _PERIOD
        xs += [left, left + _PERIOD, left + _PERIOD]
        ys += [0.0, _OCR, 0.0]
    ax.plot(xs, ys, color=style.LINE_COLOR, lw=style.WIRE_WIDTH, clip_on=False)

    # OCR1A, the line the counter is compared against.
    ax.plot([0.0, _PERIODS * _PERIOD], [_OCR, _OCR], color=style.ACCENT_COLOR,
            lw=style.ACCENT_WIDTH, linestyle=(0, (5, 3)))
    style.text(ax, "OCR1A", (-_LABEL_GAP, _OCR), halign="right", color=style.ACCENT_COLOR)
    style.text(ax, "0", (-_LABEL_GAP, 0.0), halign="right", color=style.MUTED_COLOR)
    style.text(ax, "TCNT1", (-_LABEL_GAP, _OCR / 2), halign="right")

    # A pulse per match, on its own row underneath.
    base = _PULSE_BASE
    pulse: list[tuple[float, float]] = []
    for period in range(_PERIODS):
        edge = (period + 1) * _PERIOD
        pulse += [(edge - 0.02, base), (edge, base + _PULSE_H), (edge + 0.35, base + _PULSE_H),
                  (edge + 0.37, base)]
    ax.plot([0.0] + [x for x, _ in pulse] + [_PERIODS * _PERIOD],
            [base] + [y for _, y in pulse] + [base],
            color=style.ACCENT_COLOR_2, lw=style.WIRE_WIDTH, clip_on=False)
    style.text(ax, "compare match", (-_LABEL_GAP, base + _PULSE_H / 2), halign="right",
               color=style.ACCENT_COLOR_2)

    # The period, measured across one count-up.
    shapes.span(ax, _PERIOD, 2 * _PERIOD, _OCR + 1.0, "N x (OCR1A + 1) cycles")

    style.caption(ax, _WAVE_CAPTION, _PERIODS * _PERIOD / 2,
                  _PULSE_BASE - _WAVE_CAPTION_DROP)


# Computed from the geometry above rather than chosen, because the two things that overhang a
# waveform are the row names on its left and the caption underneath it, and both are text whose
# width follows from what it says.
_WAVE_LABEL_LEFT = -_LABEL_GAP - max(
    style.text_width(name) for name in ("compare match", "OCR1A", "TCNT1"))
_WAVE_TEXT_LEFT, _WAVE_TEXT_RIGHT = style.caption_bounds(
    _WAVE_CAPTION, _PERIODS * _PERIOD / 2)

CTC_WAVEFORM = style.Figure(
    _draw_ctc,
    (min(_WAVE_LABEL_LEFT, _WAVE_TEXT_LEFT) - 0.5,
     _PULSE_BASE - _WAVE_CAPTION_DROP - style.caption_height(_WAVE_CAPTION) - 0.5,
     max(_PERIODS * _PERIOD + 0.5, _WAVE_TEXT_RIGHT) + 0.5,
     _OCR + 1.0 + 0.28 + style.text_height(style.SMALL_SIZE) + 0.5))
