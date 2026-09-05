/**
 * @brief Tests for the driver structure layouts.
 *
 *        This suite's always-on file. The offsets live in two places, the .inc files under
 * drivers/include for the assembly and `avr/drivers.hpp` for the tests that read a structure out of
 * the simulator, and two copies of a set of constants is exactly what drifts.
 *
 *        So what is checked here is not the numbers one at a time, which would just be the list
 *        written a third time. It is the relationships that make them a layout: that fields do
 *        not overlap, that each structure is exactly as big as its fields, and that a button's
 *        first three fields are an LED's.
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
 * @brief The LED's fields sit end to end, in order, with no gaps and no overlap.
 */
TEST(StructData, LedFieldsAbut)
{
    EXPECT_EQ(static_cast<unsigned>(drivers::LedPinReg), 0U);
    EXPECT_EQ(static_cast<unsigned>(drivers::LedDirReg),
              static_cast<unsigned>(drivers::LedPinReg + drivers::PointerSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::LedPortReg),
              static_cast<unsigned>(drivers::LedDirReg + drivers::PointerSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::LedPin),
              static_cast<unsigned>(drivers::LedPortReg + drivers::PointerSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::LedSize),
              static_cast<unsigned>(drivers::LedPin + drivers::ByteSize));
}

/**
 * @brief The button's fields do the same, and its two extra ones come after the LED's four.
 */
TEST(StructData, ButtonFieldsAbut)
{
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnPcmskReg),
              static_cast<unsigned>(drivers::BtnPortReg + drivers::PointerSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnPcieBit),
              static_cast<unsigned>(drivers::BtnPcmskReg + drivers::PointerSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnPin),
              static_cast<unsigned>(drivers::BtnPcieBit + drivers::ByteSize));
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnSize),
              static_cast<unsigned>(drivers::BtnPin + drivers::ByteSize));
}

/**
 * @brief A button structure begins with an LED structure's three register pointers.
 *
 *        Deliberate, and a trap. Nothing stops you passing a button to led_on: the first six
 *        bytes are laid out identically, so it finds three perfectly sensible port registers.
 *        The seventh is where they part -- the LED's pin number against the low byte of the
 *        button's PCMSK address -- so led_on shifts by 0x6B, gets a zero mask, and quietly does
 *        nothing. That is what the three equalities below pin, and what the size inequality
 *        says is not pinned.
 */
TEST(StructData, AButtonStartsWithAnLed)
{
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnPinReg), static_cast<unsigned>(drivers::LedPinReg));
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnDirReg), static_cast<unsigned>(drivers::LedDirReg));
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnPortReg),
              static_cast<unsigned>(drivers::LedPortReg));
    EXPECT_TRUE(drivers::BtnSize > drivers::LedSize);
}

/**
 * @brief The pin field is a byte, so a bit number and not an Arduino pin number.
 *
 *        Both fit in a byte, which is why this is worth a test rather than being obvious: the
 *        field would hold 13 just as happily as 5, and the driver would then shift by 13.
 */
TEST(StructData, PinFieldsAreOneByte)
{
    EXPECT_EQ(static_cast<unsigned>(drivers::LedSize - drivers::LedPin), 1U);
    EXPECT_EQ(static_cast<unsigned>(drivers::BtnSize - drivers::BtnPin), 1U);
}

/**
 * @brief Both structures fit in SRAM many times over, which is the whole reason they can exist.
 *
 *        2048 bytes holds 292 LEDs. The constraint on how many drivers a program can have is
 *        never the structures; it is the 14 pins.
 */
TEST(StructData, StructuresAreSmallAgainstSram)
{
    EXPECT_TRUE(drivers::LedSize < atmega328p::SramSize);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SramSize / drivers::LedSize), 292U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::SramSize / drivers::BtnSize), 204U);
}
