/**
 * @brief Tests for the pinned timer constants.
 *
 *        This suite's always-on file. What it checks is the small set of device facts every
 *        frequency calculation in this lecture rests on: the five prescaler ratios, the two
 *        counter widths, and where Timer1's registers live.
 *
 *        It also checks the software timer's structure layout, for the reason the LED's and the
 *        button's are checked in L04: the offsets live in `drivers/include/timer.inc` for the
 *        assembly and in `avr/drivers.hpp` for the tests that read a structure out of the
 *        simulator, and two copies of a set of constants is exactly what drifts.
 */
#include <cstdint>

#include "avr/atmega328p.hpp"
#include "avr/drivers.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;
} // namespace

/**
 * @brief There are five prescaler ratios, and they are the datasheet's.
 */
TEST(TimerData, PrescalerRatios)
{
    EXPECT_EQ(atmega328p::TimerPrescalers.size(), 5U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::TimerPrescalers[0]), 1U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::TimerPrescalers[1]), 8U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::TimerPrescalers[2]), 64U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::TimerPrescalers[3]), 256U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::TimerPrescalers[4]), 1024U);
}

/**
 * @brief The ratios ascend, and the step between them is not constant.
 *
 *        Two steps of eight and then two of four: 1 to 8 and 8 to 64 multiply by eight, 64 to 256
 *        and 256 to 1024 by four. That is why "use the next prescaler up" is not a smooth
 *        adjustment: it multiplies your period by eight low down the ladder and by four high up.
 */
TEST(TimerData, PrescalerStepsAreNotUniform)
{
    for (std::size_t index{1U}; index < atmega328p::TimerPrescalers.size(); ++index)
    {
        EXPECT_TRUE(atmega328p::TimerPrescalers[index] > atmega328p::TimerPrescalers[index - 1U]);
    }
    EXPECT_EQ(
        static_cast<unsigned>(atmega328p::TimerPrescalers[1] / atmega328p::TimerPrescalers[0]), 8U);
    EXPECT_EQ(
        static_cast<unsigned>(atmega328p::TimerPrescalers[2] / atmega328p::TimerPrescalers[1]), 8U);
    EXPECT_EQ(
        static_cast<unsigned>(atmega328p::TimerPrescalers[3] / atmega328p::TimerPrescalers[2]), 4U);
    EXPECT_EQ(
        static_cast<unsigned>(atmega328p::TimerPrescalers[4] / atmega328p::TimerPrescalers[3]), 4U);
}

/**
 * @brief A counter holds two to the power of its width, not one less.
 *
 *        256 and 65536, because a counter that counts 0 to 255 has visited 256 values. Off by
 *        one here is off by one tick per period, every period, for ever.
 */
TEST(TimerData, CounterWidths)
{
    EXPECT_EQ(atmega328p::Timer8BitValues, 256U);
    EXPECT_EQ(atmega328p::Timer16BitValues, 65536U);
    EXPECT_EQ(atmega328p::Timer16BitValues / atmega328p::Timer8BitValues, 256U);
}

/**
 * @brief Timer1's registers are where the datasheet puts them.
 */
TEST(TimerData, RegisterAddresses)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Tccr1a), 0x0080U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Tcnt1), 0x0084U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Ocr1a), 0x0088U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Timsk1), 0x006FU);
}

/**
 * @brief Every register this lecture writes is in extended I/O, so in and out cannot reach them.
 *
 *        Not a detail. `out` takes an I/O address of 0 to 63, and all of these are at 0x60 or
 *        above, so the whole timer is `lds` and `sts` territory. Reaching for `out` here is an
 *        assembler error rather than a silent one, which is the good case.
 */
TEST(TimerData, TimerRegistersAreBeyondInAndOut)
{
    for (const auto address :
         {atmega328p::Tccr1a, atmega328p::Tcnt1, atmega328p::Ocr1a, atmega328p::Timsk1})
    {
        EXPECT_TRUE(address >= atmega328p::ExtendedIoBase);
    }
}

/**
 * @brief The bit numbers CTC mode needs.
 */
TEST(TimerData, ControlBits)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Wgm12), 3U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Cs10), 0U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Ocie1a), 1U);
}

/**
 * @brief A 16-bit register is two bytes, low byte first, so its high half is one address up.
 */
TEST(TimerData, SixteenBitRegistersAreTwoBytes)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Ocr1a + 1U), 0x0089U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::Tcnt1 + 1U), 0x0085U);
}

/**
 * @brief The software timer's fields sit end to end, in order, with no gaps and no overlap.
 *
 *        Two 16-bit counters and a byte. The two counters are the reason a driver that compares
 *        only the low byte passes every test with a small target in it: the fields are adjacent,
 *        so a wrong stride reads half of the next one and gets a plausible number.
 */
TEST(TimerData, TimerFieldsAbut)
{
    EXPECT_EQ(static_cast<unsigned>(drivers::TimerTarget), 0U);
    EXPECT_EQ(static_cast<unsigned>(drivers::TimerCount),
              static_cast<unsigned>(drivers::TimerTarget + drivers::WordSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::TimerRunning),
              static_cast<unsigned>(drivers::TimerCount + drivers::WordSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::TimerSize),
              static_cast<unsigned>(drivers::TimerRunning + drivers::ByteSize));
}
