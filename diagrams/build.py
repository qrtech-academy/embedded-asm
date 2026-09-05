#!/usr/bin/env python3
"""Regenerate the lecture diagrams.

    python3 diagrams/build.py                     # every figure, into the lecture trees
    python3 diagrams/build.py sreg                # one figure
    python3 diagrams/build.py --outdir /tmp/x     # preview, without touching the repo

Adding a figure: write a builder in a module next to this one, then add an entry to
FIGURES below naming every path that should receive it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import abi  # noqa: E402
import circuit  # noqa: E402
import core  # noqa: E402
import interrupt  # noqa: E402
import pointers  # noqa: E402
import ports  # noqa: E402
import sram  # noqa: E402
import stack  # noqa: E402
import timer  # noqa: E402
import vectors  # noqa: E402
import watchdog  # noqa: E402
import registers  # noqa: E402
import style  # noqa: E402

# Root directory.
ROOT = Path(__file__).resolve().parent.parent


def images(lecture: str) -> Path:
    """The image directory of one lecture's appendix, e.g. `images("L01")`."""
    return ROOT / "lectures" / lecture / "appendix/images"


# figure name -> (figure, output paths). A figure with several paths is one that several
# lectures embed; listing them here is what keeps those copies identical.
FIGURES: dict[str, tuple[style.Figure, list[Path]]] = {
    "register_file": (
        core.REGISTER_FILE,
        [images("L01") / "register_file.png"]),
    "memory_spaces": (
        core.MEMORY_SPACES,
        [images("L01") / "memory_spaces.png"]),
    "sreg": (
        registers.SREG,
        [images("L01") / "sreg.png"]),
    "ldi_encoding": (
        core.LDI_ENCODING,
        [images("L01") / "ldi_encoding.png"]),
    "toolchain": (
        core.TOOLCHAIN,
        [images("L01") / "toolchain.png"]),
    "port_states": (
        ports.PORT_STATES,
        [images("L02") / "port_states.png"]),
    "arduino_pins": (
        ports.ARDUINO_PINS,
        [images("L02") / "arduino_pins.png"]),
    "led_circuit": (
        circuit.LED_CIRCUIT,
        [images("L02") / "led_circuit.png"]),
    "button_circuit": (
        circuit.BUTTON_CIRCUIT,
        [images("L02") / "button_circuit.png"]),
    "call_stack": (
        stack.CALL_STACK,
        [images("L02") / "call_stack.png"]),
    "interrupt_sequence": (
        interrupt.INTERRUPT_SEQUENCE,
        [images("L03") / "interrupt_sequence.png"]),
    "atomicity": (
        interrupt.ATOMICITY,
        [images("L03") / "atomicity.png"]),
    "addressing_modes": (
        pointers.ADDRESSING_MODES,
        [images("L04") / "addressing_modes.png"]),
    "struct_layout": (
        pointers.STRUCT_LAYOUT,
        [images("L04") / "struct_layout.png"]),
    "sram_map": (
        sram.SRAM_MAP,
        [images("L04") / "sram_map.png"]),
    "stack_depth": (
        sram.STACK_DEPTH,
        [images("L04") / "stack_depth.png"]),
    "timer_block": (
        timer.TIMER_BLOCK,
        [images("L05") / "timer_block.png"]),
    "ctc_waveform": (
        timer.CTC_WAVEFORM,
        [images("L05") / "ctc_waveform.png"]),
    "timer_registers": (
        registers.TIMER_REGISTERS,
        [images("L05") / "timer_registers.png"]),
    "vector_table": (
        vectors.VECTOR_TABLE,
        [images("L03") / "vector_table.png"]),
    "pcint_registers": (
        registers.PCINT_REGISTERS,
        [images("L03") / "pcint_registers.png"]),
    "watchdog_registers": (
        registers.WATCHDOG_REGISTERS,
        [images("L06") / "watchdog_registers.png"]),
    "timed_write": (
        watchdog.TIMED_WRITE,
        [images("L06") / "timed_write.png"]),
    "sleep_modes": (
        watchdog.SLEEP_MODES,
        [images("L06") / "sleep_modes.png"]),
    # One drawing, embedded by the lecture that introduces the contract and by the lecture that
    # needs every detail of it. Writing both copies from one source is what keeps them identical.
    "register_contract": (
        abi.REGISTER_CONTRACT,
        [images("L02") / "register_contract.png",
         images("L06") / "register_contract.png"]),
}


def main() -> int:
    """Build the figures named on the command line, or all of them.

    Exit code 0 on success; argparse exits 2 on an unknown figure or a bad option.
    """
    # The summary line of this file is the usage description.
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "figures",
        nargs="*",
        metavar="FIGURE",
        help="Figures to build. Default: all of them.")
    parser.add_argument(
        "--outdir",
        type=Path,
        help="Write <FIGURE>.png here instead of into the lecture trees.")
    parser.add_argument(
        "--list", action="store_true", help="List the known figures and exit.")
    args = parser.parse_args()

    if args.list:
        for name in FIGURES:
            print(name)
        return 0

    # Check every name before drawing anything, so a typo fails at once instead of halfway
    # through a rebuild with some figures already written.
    names = args.figures or list(FIGURES)
    unknown = [name for name in names if name not in FIGURES]
    if unknown:
        parser.error(
            f"unknown figure(s): {', '.join(unknown)}\nknown: {', '.join(FIGURES)}")

    for name in names:
        # --outdir replaces the lecture paths with one preview file, which is what makes it
        # safe to look at a change before it lands in the lecture trees.
        figure, paths = FIGURES[name]
        if args.outdir:
            args.outdir.mkdir(parents=True, exist_ok=True)
            paths = [args.outdir / f"{name}.png"]

        # Report paths relative to the repo where they are inside it, absolute otherwise.
        style.render(figure, paths)
        for path in paths:
            print(f"wrote {path.relative_to(ROOT) if ROOT in path.parents else path}")

    return 0


# Run only when executed as a script, never on import, and hand the return value to the
# shell as the exit status.
if __name__ == "__main__":
    raise SystemExit(main())
