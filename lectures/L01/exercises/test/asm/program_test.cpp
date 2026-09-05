/**
 * @brief Tests for drivers/app/main.asm, run in the simulator.
 *
 *        Guarded by HAVE_APP, which this suite's makefile defines when drivers/app holds at
 *        least one .asm file, and by HAVE_UTILS, because the program calls shift_bits.
 *
 *        **These tests work differently from every other test in this suite, and the difference
 *        is the point.** A subroutine can be called: utils_test.cpp sets the program counter to
 *        `shift_bits`, puts a number in r24, runs until it returns, and reads r24 back. A
 *        program cannot. It takes no arguments, it never returns, and asking what it does means
 *        letting it run for a while and then looking at the machine it left behind.
 *
 *        **This suite is the only one that tests the L01 program.** From L02 onwards main.asm is
 *        rewritten around the driver library, and by L03 it initialises the LED through
 *        `led_init` and deliberately leaves it *off* so that a button press can toggle it. So
 *        these expectations are not carried forward into the later suites, and that is not a
 *        cumulative rule being broken: the library only ever grows, and the program is replaced.
 *
 *        **What is deliberately not tested here.** Two of L01's exercises describe mistakes that
 *        the finished state of the machine cannot distinguish. Writing `PORTB` before `DDRB`
 *        leaves the pin pulled up rather than driven for one instruction and then arrives at the
 *        same place, and a program with no final loop runs off the end, wraps through flash back
 *        to the reset vector and lights the LED again on the way past. Both are real, both are
 *        in Appendix E, and both are answered by reading rather than by running. A test that
 *        appeared to check them would be worse than no test at all.
 */
#if defined(HAVE_APP) && defined(APP_HEX) && defined(HAVE_UTILS)

#include <cstdint>

#include "avr/atmega328p.hpp"
#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;

/** The assembled program, whose path the makefile passes in. */
constexpr const char* AppPath{APP_HEX};

/** The LED this course lights first: PB5, which is Arduino pin 13. */
constexpr unsigned LedBit{5U};

/** Long enough for any plausible setup to have finished, and short enough to stay quick. */
constexpr std::uint64_t Settle{2000U};

/** Data space address of DDRB, which the program reaches by its I/O address instead. */
constexpr std::uint16_t Ddrb{atmega328p::PinB + atmega328p::DirectionOffset};

/** Data space address of PORTB. */
constexpr std::uint16_t Portb{atmega328p::PinB + atmega328p::PortOffset};

/** Whether one bit of a data space register is set. */
[[nodiscard]] bool bitSet(const avrsim::Mcu& mcu, const std::uint16_t address, const unsigned bit)
{
    return 0U != (mcu.data(address) & static_cast<std::uint8_t>(1U << bit));
}
} // namespace

/**
 * @brief The program makes PB5 an output and drives it high.
 *
 *        Note the addresses. The program wrote the I/O addresses 0x04 and 0x05 with `sbi`, and
 *        this reads the data space addresses 0x24 and 0x25. Both are correct, because they are
 *        two names for one register, and the 0x20 between them is the whole of A.5.
 *
 *        The two expectations fail separately on purpose, because they mean different things.
 *        Only the second failing is a program that set the level and never made the pin an
 *        output, which is not a dark LED but a pin with its pull-up on. Only the first failing
 *        is the reverse: an output driving low. And `sts DDRB, r16`, which is the mistake A.5
 *        spends a paragraph on, fails the first, because it wrote the register r4 instead.
 */
TEST(Program, LightsTheLed)
{
    avrsim::Mcu mcu{AppPath};
    mcu.run(Settle);

    EXPECT_TRUE(bitSet(mcu, Ddrb, LedBit));
    EXPECT_TRUE(bitSet(mcu, Portb, LedBit));
}

/**
 * @brief It leaves the other seven pins of port B alone.
 *
 *        Trivially true of the two-instruction program L01 asks for, because `sbi` sets one bit
 *        and touches no other. It is here for what happens next: from L02 there is more than one
 *        thing wired to a port, and a driver that assigns a whole byte where it meant to set a
 *        bit turns every other output off. This test passes now and keeps passing, which is what
 *        makes it worth the four lines.
 */
TEST(Program, TouchesNoOtherPinOfPortB)
{
    avrsim::Mcu mcu{AppPath};
    mcu.run(Settle);

    const auto others = static_cast<std::uint8_t>(~(1U << LedBit));

    EXPECT_EQ(static_cast<unsigned>(mcu.data(Ddrb) & others), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Portb) & others), 0U);
}

#endif // HAVE_APP && APP_HEX && HAVE_UTILS
