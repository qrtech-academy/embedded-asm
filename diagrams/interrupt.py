"""L03: what the hardware does when an interrupt fires, and what that costs you.

Two figures. The first is the sequence, with the datasheet's cycle costs on it. The second is the
bug that sequence causes: a sixteen-bit value read in two instructions, with an interrupt landing
between them.

**The cycle figures in the sequence come from the ATmega328P datasheet, not from the simulator.**
That is unusual in this course and it is deliberate. simavr finishes the instruction it was
executing before it takes an interrupt, as a real AVR does, but it then charges nothing for the
push the datasheet says takes four cycles, so every interrupt it runs reaches the handler four
cycles early. The simulator is exact about instruction costs, which is what every other
measurement in this course relies on, and it is not modelling this. Saying so is better than
publishing a number that happens to come out of a tool.
"""

from __future__ import annotations

import flow
import shapes
import style

# ----------------------------------------------------------------------------------------
# A.4: the sequence, top to bottom.
# ----------------------------------------------------------------------------------------
_STEP_W = 8.6
_STEP_H = 1.5
_STEP_PITCH = 2.7
_LABEL_X = _STEP_W / 2 + 0.55

# (label, detail, fill, cost). The cost is the datasheet's, and is drawn beside the arrow that
# leaves the step rather than inside it.
_STEPS = (
    ("The pin changes", "and the flag is set in hardware", "accent2", "0 cycles"),
    ("Finish the current instruction", "however much of it is left", "plain", "0 to 3"),
    ("Push the PC, clear I", "two bytes onto the stack", "plain", "4"),
    ("Take the jump at the vector", "rjmp is 2 cycles, jmp is 3", "plain", "2"),
    ("Your handler runs", "with interrupts globally disabled", "accent", "as long as it is"),
    ("reti", "pop the PC, set I again", "plain", "4"),
    ("One more instruction, then the next", "the AVR guarantees this much progress", "plain",
     ""),
)


def _sequence_nodes() -> list[flow.Node]:
    """One box per step, stacked downwards."""
    return [
        flow.Node(label, (0.0, -index * _STEP_PITCH), detail, fill, _STEP_W, _STEP_H)
        for index, (label, detail, fill, _) in enumerate(_STEPS)
    ]


def _draw_sequence(drawing, ax) -> None:
    """The boxes and arrows, then the cycle costs down the right-hand side."""
    nodes = _sequence_nodes()
    edges = [flow.Edge(index, index + 1) for index in range(len(nodes) - 1)]
    flow.draw(nodes, edges, (), drawing, ax)

    for index, (_, _, _, cost) in enumerate(_STEPS):
        if not cost:
            continue
        _, low, _, high = nodes[index].bounds
        style.text(ax, cost, (_LABEL_X, (low + high) / 2), halign="left",
                   size=style.SMALL_SIZE, color=style.ACCENT_COLOR)

    lowest = min(node.bounds[1] for node in nodes)
    style.caption(ax, _SEQUENCE_CAPTION, 0.0, lowest - 0.65)


_SEQUENCE_CAPTION = (
    "Cycle counts from the ATmega328P datasheet, not measured: the simulator finishes the current",
    "instruction as the device does, but charges nothing for the four-cycle push.",
    "So the shortest possible response is six cycles, and the longest is nine plus your handler.",
)

_SEQ_LOWEST = -(len(_STEPS) - 1) * _STEP_PITCH - _STEP_H / 2
_SEQ_RIGHT = _LABEL_X + style.text_width("as long as it is", style.SMALL_SIZE)
_SEQ_TEXT_LEFT, _SEQ_TEXT_RIGHT = style.caption_bounds(_SEQUENCE_CAPTION, 0.0)

INTERRUPT_SEQUENCE = style.Figure(
    _draw_sequence,
    (min(-_STEP_W / 2, _SEQ_TEXT_LEFT) - 0.5,
     _SEQ_LOWEST - 0.65 - style.caption_height(_SEQUENCE_CAPTION) - 0.5,
     max(_SEQ_RIGHT, _SEQ_TEXT_RIGHT) + 0.5,
     _STEP_H / 2 + 0.5))


# ----------------------------------------------------------------------------------------
# L03 B.4: a sixteen-bit read, torn.
#
# The counter holds 0x00FF. The main loop reads the low byte, an interrupt increments the whole
# counter to 0x0100, and then the main loop reads the high byte. The value it assembles is
# 0x01FF, which the counter has never held and never will.
# ----------------------------------------------------------------------------------------
_SLOT_W = 6.4
_SLOT_H = 1.35
_SLOT_GAP = 0.55
_ROW_GAP = 2.15

_TIMELINE = (
    ("lds r24, count", "reads the low byte: 0xFF", "plain"),
    ("the interrupt lands", "the handler increments count", "accent"),
    ("lds r25, count + 1", "reads the high byte: 0x01", "plain"),
)

_VALUES = (
    ("count = 0x00FF", "255", "accent2"),
    ("count = 0x0100", "256", "accent2"),
    ("count = 0x0100", "256", "accent2"),
)

_ATOMIC_CAPTION = (
    "r25:r24 now holds 0x01FF, which is 511. The counter was 255 before and 256 after, and was",
    "never 511 at any instant. Nothing has gone wrong with either read; each is correct about a",
    "different moment. The window is exactly the gap between the two instructions.",
)


def _slot_x(index: int) -> float:
    """Left edge of one time slot."""
    return index * (_SLOT_W + _SLOT_GAP)


def _draw_atomicity(drawing, ax) -> None:
    """Three moments in a row, with what the main loop did and what the counter held."""
    for index, (title, detail, fill) in enumerate(_TIMELINE):
        left = _slot_x(index)
        shapes.cell(ax, left, 0.0, _SLOT_W, _SLOT_H, fill)
        style.text(ax, title, (left + _SLOT_W / 2, _SLOT_H / 2 + 0.24), valign="bottom",
                   size=style.SMALL_SIZE)
        style.text(ax, detail, (left + _SLOT_W / 2, _SLOT_H / 2 - 0.24), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

    for index, (value, decimal, fill) in enumerate(_VALUES):
        left = _slot_x(index)
        low = -_ROW_GAP
        shapes.cell(ax, left, low, _SLOT_W, _SLOT_H, fill)
        style.text(ax, value, (left + _SLOT_W / 2, low + _SLOT_H / 2 + 0.24), valign="bottom",
                   size=style.SMALL_SIZE)
        style.text(ax, decimal, (left + _SLOT_W / 2, low + _SLOT_H / 2 - 0.24), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

    style.text(ax, "the main loop", (-0.4, _SLOT_H / 2), halign="right", size=style.SMALL_SIZE)
    style.text(ax, "in memory", (-0.4, -_ROW_GAP + _SLOT_H / 2), halign="right",
               size=style.SMALL_SIZE)

    # The window, braced across the gap the interrupt fits into.
    shapes.brace(ax, _slot_x(0) + _SLOT_W, _slot_x(2), _SLOT_H + 0.35,
                 "the window: one instruction wide, and always there")

    style.caption(ax, _ATOMIC_CAPTION, _RIGHT / 2, -_ROW_GAP - 0.65)


_LEFT = -0.4 - style.text_width("the main loop", style.SMALL_SIZE)
_RIGHT = _slot_x(2) + _SLOT_W
_ATOMIC_TEXT_LEFT, _ATOMIC_TEXT_RIGHT = style.caption_bounds(_ATOMIC_CAPTION, _RIGHT / 2)

ATOMICITY = style.Figure(
    _draw_atomicity,
    (min(_LEFT, _ATOMIC_TEXT_LEFT) - 0.45,
     -_ROW_GAP - 0.65 - style.caption_height(_ATOMIC_CAPTION) - 0.45,
     max(_RIGHT, _ATOMIC_TEXT_RIGHT) + 0.45,
     _SLOT_H + 0.35 + 0.30 + style.text_height(style.SMALL_SIZE) + 0.45))
