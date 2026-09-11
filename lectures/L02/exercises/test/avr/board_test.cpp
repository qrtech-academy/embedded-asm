/**
 * @brief Tests for the pinned Arduino Uno pin numbering.
 *
 *        This suite's always-on file. Every lecture's suite has one, because
 *        qacademy::test::runAllTests() returns false when nothing is registered and prints
 *        nothing while doing it, so a suite whose every test sat behind a guard would report
 *        red in silence on a fresh clone.
 *
 *        What it checks is the translation this lecture is built around: that Arduino pin 13
 *        really is bit 5 of port B, and that the register addresses which follow from that are
 *        the ones the datasheet gives. Your assembly has to agree with these, and if this file
 *        fails then it cannot be right either.
 */
#include <cstdint>

#include "avr/arduino_uno.hpp"
#include "avr/atmega328p.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;
} // namespace

/**
 * @brief The two ports account for every pin, with none left over and none counted twice.
 */
TEST(Board, PinsDivideBetweenTwoPorts)
{
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::PortDPins) + arduino_uno::PortBPins,
              static_cast<unsigned>(arduino_uno::PinCount));
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::PinCount), 14U);
}

/**
 * @brief Port B carries only six of the eight bits, and the reason is physical.
 *
 *        Bits 6 and 7 of port B are the crystal pins on an Arduino Uno. They exist on the
 *        device and are not available on the board, which is why the pin numbering stops at 13
 *        rather than at 15.
 */
TEST(Board, PortBOffersSixBitsNotEight)
{
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::PortBPins), 6U);
    EXPECT_TRUE(arduino_uno::PortBPins < 8U);
}

/**
 * @brief The board's LED pin is bit 5 of port B.
 *
 *        The one translation every example in this lecture depends on. A driver told to light
 *        pin 13 has to shift by 5, not by 13, and shifting by 13 in an eight-bit register gives
 *        zero, so the symptom is an LED that never comes on and a mask that is not obviously
 *        wrong.
 */
TEST(Board, LedPinIsPortBBitFive)
{
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::LedPin), 13U);
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::LedBit), 5U);
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::LedPin) - arduino_uno::PortDPins,
              static_cast<unsigned>(arduino_uno::LedBit));
}

/**
 * @brief The registers that follow from that pin are port B's, at the datasheet's addresses.
 */
TEST(Board, LedPinResolvesToPortBRegisters)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::PinB), 0x0023U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::PinB + atmega328p::DirectionOffset), 0x0024U);
    EXPECT_EQ(static_cast<unsigned>(atmega328p::PinB + atmega328p::PortOffset), 0x0025U);
}

/**
 * @brief The first port B pin is pin 8, which is bit 0, and so the cheapest mask to compute.
 *
 *        Not a curiosity: shift_bits costs six cycles per shift, so pin 8 costs 30 cycles less
 *        than pin 13 does. The cross-check exercise measures exactly that.
 */
TEST(Board, FirstPortBPinIsBitZero)
{
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::FirstPortBPin), 8U);
    EXPECT_EQ(static_cast<unsigned>(arduino_uno::FirstPortBPin) - arduino_uno::PortDPins, 0U);
}
