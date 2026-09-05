"""L06 figures: the sequence that configures the watchdog, and what sleeping costs you.

The first is a timeline rather than a block diagram, because the whole point of it is *when*
things happen: the hardware gives you four cycles and then closes the door.
"""

from __future__ import annotations

import shapes
import style

# ----------------------------------------------------------------------------------------
# A.4: the timed write sequence.
# ----------------------------------------------------------------------------------------
_STEP_W = 10.4
_STEP_H = 1.45
_STEP_PITCH = 2.3
_WINDOW_PAD = 0.55

# (label, detail, fill, inside the four-cycle window?)
_STEPS = (
    ("in r18, SREG; cli", "save the flag, then stop anything interrupting", "plain", False),
    ("wdr", "reset the counter, so the timeout starts now", "plain", False),
    ("clear WDRF in MCUSR", "or WDE cannot be cleared later", "plain", False),
    ("write WDCE and WDE together", "this opens the window", "accent", True),
    ("write the mode and timeout", "with WDCE clear", "accent", True),
    ("out SREG, r18", "give the caller back the flag it had", "plain", False),
)

_CAPTION = (
    "The two shaded writes must be within four cycles of each other. Not four instructions:",
    "four cycles. An interrupt landing between them takes far longer than that, which is why",
    "the sequence begins by turning interrupts off and not merely by being written carefully.",
    "It ends by restoring SREG rather than by sei, so that a caller which had interrupts off",
    "still has them off afterwards.",
)


def _step_y(index: int) -> tuple[float, float]:
    """(low, high) of one step's box."""
    high = -index * _STEP_PITCH
    return high - _STEP_H, high


def _draw_timed_write(drawing, ax) -> None:
    """The six steps, with the four-cycle window marked across the two that need it."""
    inside = [index for index, step in enumerate(_STEPS) if step[3]]
    top = _step_y(inside[0])[1] + _WINDOW_PAD
    bottom = _step_y(inside[-1])[0] - _WINDOW_PAD
    # shade takes (x_a, x_b, y_a, y_b): both x bounds first, then both y bounds.
    shapes.shade(ax, -_WINDOW_PAD, _STEP_W + _WINDOW_PAD, bottom, top, 0.14)

    for index, (label, detail, fill, _) in enumerate(_STEPS):
        low, high = _step_y(index)
        shapes.cell(ax, 0.0, low, _STEP_W, _STEP_H, fill)
        style.text(ax, label, (_STEP_W / 2, (low + high) / 2 + 0.24), valign="bottom",
                   size=style.SMALL_SIZE)
        style.text(ax, detail, (_STEP_W / 2, (low + high) / 2 - 0.24), valign="top",
                   size=style.TINY_SIZE, color=style.MUTED_COLOR)

        if index + 1 < len(_STEPS):
            shapes.arrow(ax, (_STEP_W / 2, low - 0.08),
                         (_STEP_W / 2, _step_y(index + 1)[1] + 0.08))

    # The window itself, braced down the right-hand side.
    shapes.vbrace(ax, bottom, top, _STEP_W + _WINDOW_PAD + 0.35, "four cycles",
                  size=style.SMALL_SIZE)

    style.caption(ax, _CAPTION, _STEP_W / 2, _step_y(len(_STEPS) - 1)[0] - 0.65)


_RIGHT = (_STEP_W + _WINDOW_PAD + 0.35 + 0.24
          + style.text_width("four cycles", style.SMALL_SIZE))
_BOTTOM = _step_y(len(_STEPS) - 1)[0] - 0.65
_TEXT_LEFT, _TEXT_RIGHT = style.caption_bounds(_CAPTION, _STEP_W / 2)

TIMED_WRITE = style.Figure(
    _draw_timed_write,
    (min(-_WINDOW_PAD, _TEXT_LEFT) - 0.5,
     _BOTTOM - style.caption_height(_CAPTION) - 0.5,
     max(_RIGHT, _TEXT_RIGHT) + 0.5,
     _WINDOW_PAD + 0.5))


# ----------------------------------------------------------------------------------------
# A.6: what each sleep mode leaves running.
#
# The datasheet gives this as a table of a dozen clock domains. This keeps the four that decide
# whether a given program can use a given mode, which is the question a reader actually has.
# ----------------------------------------------------------------------------------------
_MODE_W = 6.0
_COL_W = 3.5
_ROW_H = 1.25
_HEADER_H = 1.5

_COLUMNS = ("CPU", "Timers", "Watchdog", "Pin change")

# (mode, four yes/no flags, note)
_MODES = (
    ("Idle", (False, True, True, True), "everything but the CPU"),
    ("ADC noise reduction", (False, False, True, True), "the ADC, with the I/O clock stopped"),
    ("Power-down", (False, False, True, True), "the deepest one anything wakes from"),
    ("Power-save", (False, False, True, True), "as power-down, plus Timer2"),
    ("Standby", (False, False, True, True), "power-down with the crystal left running"),
)

_SLEEP_CAPTION = (
    "The watchdog and pin change interrupts survive every mode, which is what makes them the",
    "two ways back. A timer does not survive power-down, so a program that sleeps deeply and",
    "expects a timer to wake it does not wake up.",
)


def _draw_sleep(drawing, ax) -> None:
    """One row per mode, one column per thing that might still be running."""
    for column, name in enumerate(_COLUMNS):
        left = _MODE_W + column * _COL_W
        style.text(ax, name, (left + _COL_W / 2, 0.3), valign="bottom",
                   size=style.SMALL_SIZE)

    for row, (mode, flags, note) in enumerate(_MODES):
        low = -(row + 1) * _ROW_H
        style.text(ax, mode, (_MODE_W - 0.35, low + _ROW_H / 2 + 0.2), halign="right",
                   valign="bottom", size=style.SMALL_SIZE)
        style.text(ax, note, (_MODE_W - 0.35, low + _ROW_H / 2 - 0.2), halign="right",
                   valign="top", size=style.TINY_SIZE, color=style.MUTED_COLOR)

        for column, running in enumerate(flags):
            left = _MODE_W + column * _COL_W
            shapes.cell(ax, left, low, _COL_W, _ROW_H, "accent2" if running else "muted")
            style.text(ax, "runs" if running else "stopped",
                       (left + _COL_W / 2, low + _ROW_H / 2), size=style.SMALL_SIZE,
                       color=style.LINE_COLOR if running else style.MUTED_COLOR)

    style.caption(ax, _SLEEP_CAPTION, (_MODE_W + len(_COLUMNS) * _COL_W) / 2,
                  -len(_MODES) * _ROW_H - 0.6)


_SLEEP_RIGHT = _MODE_W + len(_COLUMNS) * _COL_W
_SLEEP_BOTTOM = -len(_MODES) * _ROW_H - 0.6
_SLEEP_TEXT_LEFT, _SLEEP_TEXT_RIGHT = style.caption_bounds(_SLEEP_CAPTION, _SLEEP_RIGHT / 2)

# The row labels hang off the left of the grid, and the notes under them are the longest text in
# the figure. Measured rather than assumed: the widest of them reaches further left than the
# caption does, and a canvas sized to the caption alone clips it by a character.
_SLEEP_LABEL_LEFT = _MODE_W - 0.35 - max(
    max(style.text_width(mode, style.SMALL_SIZE), style.text_width(note, style.TINY_SIZE))
    for mode, _, note in _MODES)

SLEEP_MODES = style.Figure(
    _draw_sleep,
    (min(_SLEEP_LABEL_LEFT, _SLEEP_TEXT_LEFT) - 0.45,
     _SLEEP_BOTTOM - style.caption_height(_SLEEP_CAPTION) - 0.45,
     max(_SLEEP_RIGHT, _SLEEP_TEXT_RIGHT) + 0.45,
     0.3 + style.text_height(style.SMALL_SIZE) + 0.45))
