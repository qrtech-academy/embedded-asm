/**
 * @brief Tests for drivers/source/utils.asm, run in the simulator.
 *
 *        Guarded by HAVE_UTILS, which this suite's makefile defines when drivers/source/utils.asm
 *        exists. Assembly has no equivalent of __has_include, so the makefile derives one flag
 *        per .asm file from what is actually in that directory; create the file and these tests
 *        start running, with nothing to switch on.
 *
 *        These are the first tests in the course that run your code on the device rather than
 *        on your laptop. What they do is what a debugger would: set r24, call one subroutine,
 *        and look at r24 and the cycle counter afterwards.
 */
#if defined(HAVE_UTILS) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/**
 * @brief Call shift_bits with an argument and give back what it returned and what it cost.
 *
 * @param[in] mcu    The machine to run it on.
 * @param[in] symbol Name of the subroutine.
 * @param[in] shifts The argument, passed in r24.
 *
 * @return The result in r24, and the cycles the call took.
 */
struct Outcome
{
    std::uint8_t result;
    std::uint64_t cycles;
    bool returned;
};

[[nodiscard]] Outcome shift(avrsim::Mcu& mcu, const char* symbol, const std::uint8_t shifts)
{
    mcu.setReg(24U, shifts);
    const auto call = mcu.call(symbol);
    return {mcu.reg(24U), call.cycles, call.returned};
}
} // namespace

/**
 * @brief The library assembles, loads, and defines both subroutines.
 *
 *        Checked first and on its own, so that a missing .global reads as a missing .global
 *        rather than as sixteen failures about wrong return values.
 */
TEST(Utils, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_TRUE(mcu.has("shift_bits"));
    EXPECT_TRUE(mcu.has("shift_bits_inverted"));
}

/**
 * @brief shift_bits returns 1 shifted left by its argument.
 */
TEST(Utils, ShiftBitsReturnsTheShiftedValue)
{
    avrsim::Mcu mcu{HexPath};
    for (std::uint8_t shifts{0U}; shifts < 8U; ++shifts)
    {
        const auto outcome = shift(mcu, "shift_bits", shifts);
        EXPECT_TRUE(outcome.returned);
        EXPECT_EQ(outcome.result, static_cast<std::uint8_t>(1U << shifts));
    }
}

/**
 * @brief Shifting eight times shifts the bit out entirely.
 *
 *        The result is 0, not 1 and not 0x80. Nothing in the routine says so; it falls out of
 *        the register being eight bits wide, and it is the answer a reader who has been
 *        thinking in C is least likely to predict.
 */
TEST(Utils, ShiftBitsShiftsTheBitOffTheEnd)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(shift(mcu, "shift_bits", 8U).result, 0x00U);
}

/**
 * @brief shift_bits_inverted returns the complement of the same value.
 */
TEST(Utils, ShiftBitsInvertedReturnsTheComplement)
{
    avrsim::Mcu mcu{HexPath};
    for (std::uint8_t shifts{0U}; shifts < 8U; ++shifts)
    {
        const auto outcome = shift(mcu, "shift_bits_inverted", shifts);
        EXPECT_TRUE(outcome.returned);
        EXPECT_EQ(outcome.result, static_cast<std::uint8_t>(~(1U << shifts)));
    }
}

/**
 * @brief Shifting the inverted value eight times leaves every bit set.
 */
TEST(Utils, ShiftBitsInvertedShiftsTheZeroOffTheEnd)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(shift(mcu, "shift_bits_inverted", 8U).result, 0xFFU);
}

/**
 * @brief Calling twice with the same argument gives the same answer.
 *
 *        A routine that initialises its accumulator once, outside the loop it meant to put it
 *        in, passes every test above on the first call and fails this one.
 */
TEST(Utils, ShiftBitsIsRepeatable)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(shift(mcu, "shift_bits", 5U).result, 0x20U);
    EXPECT_EQ(shift(mcu, "shift_bits", 5U).result, 0x20U);
    EXPECT_EQ(shift(mcu, "shift_bits", 3U).result, 0x08U);
    EXPECT_EQ(shift(mcu, "shift_bits", 5U).result, 0x20U);
}

/**
 * @brief shift_bits costs 6n + 10 cycles, measured.
 *
 *        **This test pins the specification's instruction sequence, not merely its behaviour.**
 *        The appendix gives that sequence line by line, and 6n + 10 is what it costs: two ldi
 *        to set up, then per trip a cp, a breq that falls through, an lsl, an inc and an rjmp,
 *        then a final cp with the breq taken, then a mov and a ret.
 *
 *        So a different routine that returns all the right values will fail here, and that is
 *        deliberate: the cross-check exercise asks you to predict this number by hand and with
 *        your own toolkit before you ever run it, and a test that accepted any cost would have
 *        nothing to say about whether your prediction was right. If you deliberately rewrite
 *        the routine, this is the number to update, and updating it is a decision rather than
 *        an accident.
 *
 *        Note what is *not* here: the three cycles of the rcall that got you into the routine.
 *        A test calls the subroutine directly, so the cost of reaching it is not in this
 *        figure. That is the first term of the discrepancy the cross-check asks you to explain.
 */
TEST(Utils, ShiftBitsCostsSixCyclesPerShiftPlusTen)
{
    avrsim::Mcu mcu{HexPath};
    for (std::uint8_t shifts{0U}; shifts <= 8U; ++shifts)
    {
        EXPECT_EQ(shift(mcu, "shift_bits", shifts).cycles, 6U * shifts + 10U);
    }
}

/**
 * @brief shift_bits_inverted costs 7n + 10 cycles, measured.
 *
 *        One cycle per trip more than shift_bits, and exactly one: the extra inc that turns a
 *        shifted zero back into a shifted one. Two routines that differ by a single instruction
 *        differ in cost by that instruction, every time round the loop, which is the whole
 *        argument for counting cycles rather than estimating them.
 */
TEST(Utils, ShiftBitsInvertedCostsSevenCyclesPerShiftPlusTen)
{
    avrsim::Mcu mcu{HexPath};
    for (std::uint8_t shifts{0U}; shifts <= 8U; ++shifts)
    {
        EXPECT_EQ(shift(mcu, "shift_bits_inverted", shifts).cycles, 7U * shifts + 10U);
    }
}

/**
 * @brief The cost does not depend on anything but the argument.
 *
 *        Filling the register file with a pattern first changes nothing, which is worth
 *        checking once: a routine that branches on a register it never initialised would pass
 *        every test above from a machine that happens to start with zeros everywhere.
 */
TEST(Utils, CostDependsOnlyOnTheArgument)
{
    avrsim::Mcu mcu{HexPath};
    const auto clean = shift(mcu, "shift_bits", 4U);

    for (unsigned number{0U}; number < 32U; ++number)
    {
        mcu.setReg(number, 0xA5U);
    }
    const auto dirty = shift(mcu, "shift_bits", 4U);

    EXPECT_EQ(dirty.result, clean.result);
    EXPECT_EQ(dirty.cycles, clean.cycles);
}

#endif // defined(HAVE_UTILS) && defined(DRIVERS_HEX)
