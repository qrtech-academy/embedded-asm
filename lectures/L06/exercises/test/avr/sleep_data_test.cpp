/**
 * @brief Tests for the pinned sleep constants.
 *
 *        Always on, like the watchdog's. These are the six modes' oscillator restart costs, and
 *        they are the one part of this lecture's sleep material that is a number rather than a
 *        description -- so they are the part that can go stale without anybody noticing.
 *
 *        Nothing here simulates sleeping. The course does not test sleep at all, for the reason
 *        B.5 gives: the interaction between clock domains and wake sources is what a datasheet
 *        specifies and a simulator approximates. What is checked is that the table the appendix
 *        prints is the table the header holds.
 */
#include <cstdint>

#include "avr/atmega328p.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;

/** Index of each mode in SM2:SM0 order, which is the order the table is written in. */
constexpr std::size_t Idle{0U};
constexpr std::size_t AdcNoiseReduction{1U};
constexpr std::size_t PowerDown{2U};
constexpr std::size_t PowerSave{3U};
constexpr std::size_t Standby{4U};
constexpr std::size_t ExtendedStandby{5U};
} // namespace

/**
 * @brief Six modes, and the restart cost of each.
 */
TEST(SleepData, OscillatorRestartCycles)
{
    EXPECT_EQ(atmega328p::SleepModes.size(), static_cast<std::size_t>(atmega328p::SleepModeCount));

    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[Idle]), 0U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[AdcNoiseReduction]), 0U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[PowerDown]), 16384U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[PowerSave]), 16384U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[Standby]), 6U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[ExtendedStandby]), 6U);
}

/**
 * @brief Standby is power-down with the oscillator left running, and the table says so.
 *
 *        The pairing is the whole argument of B.6, and it is a relationship rather than a list:
 *        each standby mode costs the same six cycles as an idle wake-up plus nothing, where the
 *        deep mode beside it costs three orders of magnitude more.
 */
TEST(SleepData, StandbyBuysBackTheOscillator)
{
    EXPECT_TRUE(atmega328p::SleepModes[Standby] < atmega328p::SleepModes[PowerDown]);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[ExtendedStandby]),
              static_cast<unsigned>(atmega328p::SleepModes[Standby]));
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SleepModes[PowerSave]),
              static_cast<unsigned>(atmega328p::SleepModes[PowerDown]));
}

/**
 * @brief SE is bit 0 and the mode sits above it, so a mode byte is its encoding shifted left.
 */
TEST(SleepData, SmcrLayout)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Se), 0U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Sm0), 1U);

    // Power-down is SM2:SM0 = 010, which is 0x04 in the register and 0x05 with SE set.
    EXPECT_EQ(static_cast<unsigned>(2U << atmega328p::Sm0), 0x04U);
    EXPECT_EQ(static_cast<unsigned>((2U << atmega328p::Sm0) | (1U << atmega328p::Se)), 0x05U);
}

/**
 * @brief SMCR is inside the I/O window, unlike WDTCSR, so in and out reach it.
 */
TEST(SleepData, SmcrIsReachableByInAndOut)
{
    EXPECT_TRUE(atmega328p::Smcr < atmega328p::ExtendedIoBase);
    EXPECT_TRUE(atmega328p::Wdtcsr >= atmega328p::ExtendedIoBase);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Smcr - atmega328p::IoOffset), 0x33U);
}
