SHELL := /bin/bash

# Path to this Makefile's directory, so `make -f ../path/to/Makefile` finds the scripts. A path
# containing a space would break every recipe below, and make has no way to quote one, so it is
# named as a limitation rather than papered over: check this repository out somewhere without.
ROOT := $(dir $(firstword $(MAKEFILE_LIST)))

PYTHON := $(ROOT).venv/bin/python

.DEFAULT_GOAL := help
.PHONY: help build test measure check lint links markdown format format-check diagrams clean

help: ## Show this help.
	@echo "Targets:"
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) \
	  | sed -e 's/:.*## / /' -e 's/^/  /' \
	  | awk '{ printf "  %-14s %s\n", $$1, substr($$0, index($$0, $$2)) }'
	@echo
	@echo "Every target above runs from the very first commit, when almost nothing exists."
	@echo "Anything that cannot run yet says so by name and does not pretend to have passed."
	@echo
	@echo "Build one thing instead of all of them:"
	@echo "  make build TARGET=drivers"
	@echo "  make diagrams FIGURE=sreg"
	@echo "  make measure SYMBOL=shift_bits ARG=5"
	@echo "  make measure CALLS=\"led_init:0x0200:13 led_on:0x0200\""

build: ## Assemble the drivers and build the simulator harness. Optional: TARGET=<name>
	$(ROOT)ci/build.sh $(TARGET)

test: ## Build and run every lecture test suite.
	$(ROOT)ci/test.sh

measure: ## Measure cycles. SYMBOL=<name> [ARG=.. ARG2=..] or CALLS="sym:a:b ..." [IMAGE=app]
	IMAGE=$(IMAGE) $(ROOT)ci/measure.sh $(if $(CALLS),$(CALLS),$(SYMBOL) $(ARG) $(ARG2))

# This target *is* the CI lint job: the workflow runs `make lint` rather than restating the four
# checks, so a green "make lint" locally means a green lint in CI by construction rather than by
# two lists being kept in step by hand.
lint: check links markdown format-check ## Run every check that needs no toolchain.

# ARG2 is the second byte argument a measured call may take; see ci/measure.sh.

check: ## Check the conventions: layout, titles, sections, appendix letters, tests, figures.
	$(ROOT)ci/check.sh

links: ## Check that every relative link in the Markdown resolves.
	$(ROOT)ci/links.sh

markdown: ## Check that the Markdown prose is hard-wrapped at 100 columns.
	$(ROOT)ci/markdown.sh

format: ## Format the C++ sources and strip trailing whitespace from the assembly.
	$(ROOT)ci/format.sh

format-check: ## Fail if any source is unformatted or carries trailing whitespace.
	$(ROOT)ci/format.sh --check

# Deliberately not part of build or lint: the generated PNGs are committed, and redrawing them
# needs a Python environment this repo does not otherwise require. CI has its own, in a separate
# job that redraws every figure and diffs it. See diagrams/README.md for the one-time venv setup.
# The existence check comes before the environment check on purpose: until the pipeline exists
# there is nothing a Python environment could draw, and demanding one first would report a setup
# problem the reader does not have.
diagrams: ## Redraw the generated lecture figures. Optional: FIGURE=<name>
	@if [ ! -f $(ROOT)diagrams/build.py ]; then \
	  echo "SKIP  diagrams: diagrams/build.py does not exist yet."; \
	elif [ ! -x $(PYTHON) ]; then \
	  echo "No Python environment at $(PYTHON). Create it once with:"; \
	  echo "  python3 -m venv .venv"; \
	  echo "  .venv/bin/pip install -r diagrams/requirements.txt"; \
	  exit 1; \
	else \
	  $(PYTHON) $(ROOT)diagrams/build.py $(FIGURE); \
	fi

clean: ## Remove assembled hex, listings, maps, test binaries, and other generated files.
	$(ROOT)ci/clean.sh
