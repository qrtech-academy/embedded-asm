# Test suite target.
TARGET := testsuite

# Repository root. ci/test.sh overrides this with an absolute path; the default is what makes
# `make` work when you are standing in this directory.
ROOT_DIR ?= ../../../..

# The QAcademy Test framework, checked out as a submodule at the repository root. Run
# 'git submodule update --init' once if libs/test is empty.
QACADEMY_TEST_DIR ?= $(ROOT_DIR)/libs/test
QACADEMY_TEST_LIB := $(QACADEMY_TEST_DIR)/libqacademy_test.a

# The simavr harness this course ships, which is what runs your assembly.
AVRSIM_DIR := $(ROOT_DIR)/tools/avrsim
AVRSIM_LIB := $(AVRSIM_DIR)/libavrsim.a

# The pinned device facts the tests check against, and the AVR assembly library you write.
DEVICE_DIR := $(ROOT_DIR)/device
DRIVERS_DIR := $(ROOT_DIR)/drivers
DRIVERS_HEX := $(DRIVERS_DIR)/build/drivers.hex

# Every suite is cumulative: it runs this lecture's tests and every earlier lecture's as well,
# so that work added here which breaks something L01 built fails here rather than nowhere.
#
# The earlier files are referenced where they live rather than copied. A copy would be a second
# thing to keep in step, and the copy is the one that rots.
L01_TESTS := $(ROOT_DIR)/lectures/L01/exercises/test
L02_TESTS := $(ROOT_DIR)/lectures/L02/exercises/test
L03_TESTS := $(ROOT_DIR)/lectures/L03/exercises/test

# Test files - update this list as new test files are added to this directory.
TEST_FILES := $(L01_TESTS)/avr/device_test.cpp \
              $(L01_TESTS)/asm/utils_test.cpp \
              $(L02_TESTS)/avr/board_test.cpp \
              $(L02_TESTS)/asm/led_test.cpp \
              $(L03_TESTS)/avr/vector_data_test.cpp \
              $(L03_TESTS)/asm/btn_test.cpp \
              $(L03_TESTS)/asm/app_test.cpp \
              avr/struct_data_test.cpp \
              asm/led_array_test.cpp \
              testsuite.cpp \

# --------------------------------------------------------------------------------------------
# Switching the assembly tests on.
#
# A test for a subroutine you have not written cannot compile, let alone pass. A C++ header can
# be detected with #if __has_include, which needs no help from a makefile. Assembly has no
# equivalent, so this is it: one -DHAVE_<NAME> for every .asm in drivers/source, derived from what
# is actually there. Write drivers/source/utils.asm and HAVE_UTILS appears; there is no list here
# to keep in step, and no way to forget.
# --------------------------------------------------------------------------------------------
ASM_SOURCES := $(wildcard $(DRIVERS_DIR)/source/*.asm)
ASM_NAMES   := $(notdir $(basename $(ASM_SOURCES)))

# What this suite expects to find, so that a file written under the wrong name is reported by
# name instead of silently compiling its tests out. Deriving the flags from the directory is what
# makes the mechanism work with no list to edit; this list is what makes its *absence* audible.
EXPECTED_ASM := utils led btn led_array
MISSING_ASM  := $(filter-out $(ASM_NAMES),$(EXPECTED_ASM))
HAVE_FLAGS  := $(foreach name,$(ASM_NAMES),-DHAVE_$(shell echo $(name) | tr '[:lower:]' '[:upper:]'))

# The whole program, which is a different thing from the library. drivers/app/main.asm has a
# vector table, a stack pointer and a main loop; the library is subroutines and nothing else.
# An interrupt cannot be called, so the integration test loads this image and lets it run.
#
# HAVE_APP does not depend on what the file is called, unlike the flags above. The library is a
# set of independent subroutines, so which of them exist is a real question; the program is one
# program however you choose to split it up.
APP_SOURCES := $(wildcard $(DRIVERS_DIR)/app/*.asm)
APP_HEX     := $(DRIVERS_DIR)/build/app.hex

ifneq ($(strip $(ASM_SOURCES)),)
ifneq ($(strip $(APP_SOURCES)),)
HAVE_FLAGS += -DHAVE_APP -DAPP_HEX='"$(abspath $(APP_HEX))"'
endif
endif

# The tests are handed the hex's path rather than finding it themselves, so that a suite run
# from somewhere else still loads the right one. The map avra wrote sits beside it under the same
# stem, and Mcu finds it from this path.
ifneq ($(ASM_SOURCES),)
HEX_DEPENDENCY := $(DRIVERS_HEX)
HAVE_FLAGS     += -DDRIVERS_HEX='"$(abspath $(DRIVERS_HEX))"'
endif

# C++ compiler.
CXX_COMPILER := g++

# C++ compiler flags.
CXX_FLAGS := -std=c++17 -Wall -Werror \
             -I$(DEVICE_DIR)/include \
             -I$(AVRSIM_DIR)/include \
             -I$(QACADEMY_TEST_DIR)/include \
             $(HAVE_FLAGS)

# Libraries. simavr and elf come from the distribution; see the README for the apt line.
LD_FLAGS := -L$(QACADEMY_TEST_DIR) -lqacademy_test -lsimavr -lelf

# Build and run the test suite as default. `run` needs `build` to have finished, which a
# prerequisite list does not promise under `make -j`, so the ordering is stated rather than
# assumed. ci/test.sh relies on it too: it asks for `clean build run` in one invocation.
.NOTPARALLEL:

default: build run

# Build the QAcademy Test framework and the simavr harness.
#
# Forced rather than guarded on the .a existing: a rule with no prerequisites is satisfied for
# ever once its target is there, so an edit to a harness header would never be picked up here.
# The sub-make is the thing that knows whether anything actually needs rebuilding.
.PHONY: FORCE
FORCE:

$(QACADEMY_TEST_LIB): FORCE
	@$(MAKE) -s -C $(QACADEMY_TEST_DIR) lib

$(AVRSIM_LIB): FORCE
	@$(MAKE) -s -C $(AVRSIM_DIR) lib

# Assemble the driver library, through the same script the top-level build uses, so there is
# only ever one definition of how this repository assembles anything.
# One invocation assembles both images, so the app's sources are prerequisites here rather than
# in a second rule that would run the same script twice.
$(DRIVERS_HEX): $(ASM_SOURCES) $(APP_SOURCES)
	@$(ROOT_DIR)/ci/build.sh drivers

# Build the test suite.
build: $(QACADEMY_TEST_LIB) $(AVRSIM_LIB) $(HEX_DEPENDENCY)
	@$(foreach name,$(MISSING_ASM),\
	   echo "SKIP  drivers/source/$(name).asm not written yet; its tests are compiled out.";) true
	@$(CXX_COMPILER) $(TEST_FILES) $(AVRSIM_LIB) -o $(TARGET) \
	  $(CXX_FLAGS) $(LD_FLAGS)

# Run the test suite.
run:
	@./$(TARGET)

# Clean the test suite.
clean:
	@rm -f $(TARGET)

.PHONY: default build run clean
