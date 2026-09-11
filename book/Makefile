# Build the book: vector figures from diagrams/, then two LuaLaTeX passes for the references.
#
#   make          build embedded-asm.pdf
#   make clean    remove everything the build writes

ROOT    := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
BOOK    := $(ROOT)/book
BUILD   := $(BOOK)/build
PYTHON  ?= $(ROOT)/.venv/bin/python
LATEX   := lualatex -interaction=nonstopmode -halt-on-error -file-line-error \
           -output-directory=$(BUILD)

FIGURES := register_file memory_spaces sreg ldi_encoding toolchain \
           port_states led_circuit button_circuit arduino_pins call_stack register_contract \
           vector_table interrupt_sequence pcint_registers atomicity \
           addressing_modes struct_layout sram_map stack_depth \
           timer_block ctc_waveform timer_registers \
           watchdog_registers timed_write sleep_modes
FIGPDFS := $(FIGURES:%=$(BUILD)/figures/%.pdf)
SOURCES := book.tex asmbook.sty $(wildcard front/*.tex chapters/*/*.tex back/*.tex)

.PHONY: all figures clean

all: embedded-asm.pdf

figures: $(FIGPDFS)

# One figure per run keeps a rebuild to what changed; every figure module is a dependency
# because the builders import each other.
$(BUILD)/figures/%.pdf: figures.py $(wildcard $(ROOT)/diagrams/*.py)
	$(PYTHON) figures.py $(BUILD)/figures $*

embedded-asm.pdf: $(SOURCES) $(FIGPDFS)
	@mkdir -p $(BUILD)
	cd $(BOOK) && $(LATEX) book.tex >/dev/null || (tail -40 $(BUILD)/book.log; exit 1)
	cd $(BOOK) && $(LATEX) book.tex >/dev/null || (tail -40 $(BUILD)/book.log; exit 1)
	cp $(BUILD)/book.pdf $@
	@grep -E "^(Overfull|Underfull)|Warning" $(BUILD)/book.log | sort | uniq -c | sort -rn | head -20 || true

clean:
	rm -rf $(BUILD) embedded-asm.pdf
