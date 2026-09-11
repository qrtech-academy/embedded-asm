/**
 * @brief Tests for the pinned watchdog and sleep constants.
 *
 *        This suite's always-on file, and the last one in the course.
 *
 *        What it checks is the one piece of arithmetic in this lecture that nothing else will
 *        catch: the four timeout selector bits are **not adjacent** in WDTCSR, so a selector and
 *        the byte that selects it are different numbers. Writing the selector where the byte
 *        belongs does not merely choose the wrong timeout; for selector 8 it sets WDE, and the
 *        device then resets every 16 milliseconds for ever.
 */
#include <cstdint>

#include "avr/atmega328p.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;

/** Assemble a selector into the byte the register wants, the way the hardware reads it. */
[[nodiscard]] constexpr std::uint8_t byteFor(const std::uint8_t selector)
{
    return static_cast<std::uint8_t>((((selector & 0x08U) != 0U) ? (1U << atmega328p::Wdp3) : 0U) |
                                     ((selector & 0x07U) << atmega328p::Wdp0));
}
} // namespace

/**
 * @brief The registers are where the datasheet puts them.
 */
TEST(WatchdogData, RegisterAddresses)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdtcsr), 0x0060U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Mcusr), 0x0054U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Smcr), 0x0053U);
}

/**
 * @brief WDTCSR is in extended I/O and the other two are not.
 *
 *        So the watchdog needs `lds` and `sts`, and MCUSR and SMCR can use `in` and `out`. Three
 *        registers in one lecture, two different addressings, and the assembler will tell you
 *        which is which only for the one you get wrong in the loud direction.
 */
TEST(WatchdogData, AddressingDiffersBetweenTheThree)
{
    EXPECT_TRUE(atmega328p::Wdtcsr >= atmega328p::ExtendedIoBase);
    EXPECT_TRUE(atmega328p::Mcusr < atmega328p::ExtendedIoBase);
    EXPECT_TRUE(atmega328p::Smcr < atmega328p::ExtendedIoBase);
}

/**
 * @brief The bit numbers are the datasheet's.
 */
TEST(WatchdogData, BitNumbers)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wde), 3U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdce), 4U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdie), 6U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdrf), 3U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Se), 0U);
}

/**
 * @brief The four selector bits are not adjacent, and WDCE and WDE sit between them.
 *
 *        WDP3 is bit 5 and WDP2 to WDP0 are bits 2 to 0. That gap is the whole reason the
 *        byte has to be worked out rather than copied.
 */
TEST(WatchdogData, SelectorBitsAreScattered)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdp0), 0U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wdp3), 5U);
    EXPECT_TRUE(atmega328p::Wdce > atmega328p::Wdp0 + 2U);
    EXPECT_TRUE(atmega328p::Wdce < atmega328p::Wdp3);
    EXPECT_TRUE(atmega328p::Wde < atmega328p::Wdp3);
}

/**
 * @brief A selector below 8 is its own byte, and a selector of 8 or more is not.
 */
TEST(WatchdogData, SelectorToByte)
{
    for (std::uint8_t selector{0U}; selector < 8U; ++selector)
    {
        EXPECT_EQ(static_cast<unsigned>(byteFor(selector)), static_cast<unsigned>(selector));
    }
    EXPECT_EQ(static_cast<unsigned>(byteFor(8U)), 0x20U);
    EXPECT_EQ(static_cast<unsigned>(byteFor(9U)), 0x21U);
}

/**
 * @brief Writing selector 8 as a byte sets WDE instead of choosing a four second timeout.
 *
 *        The most expensive typo available in this lecture. The byte 0x08 is WDE with the
 *        selector left at zero, so instead of "reset me if I go quiet for four seconds" it means
 *        "reset me if I go quiet for sixteen milliseconds", which for most programs is
 *        immediately and for ever. A device in that state is awkward to reprogram, because the
 *        bootloader has to win a race against it.
 */
TEST(WatchdogData, TheSelectorIsNotTheByte)
{
    constexpr std::uint8_t selector{8U};
    EXPECT_NE(static_cast<unsigned>(byteFor(selector)), static_cast<unsigned>(selector));

    // What the wrong write actually means.
    EXPECT_EQ(static_cast<unsigned>(selector), 1U << atmega328p::Wde);
    EXPECT_EQ(static_cast<unsigned>(selector) & 0x07U, 0U);
}
