/**
 * @brief Tests for the pinned ATmega328P constants.
 *
 *        This is the suite's always-on file, and every lecture's suite has one. The reason is
 *        blunt: qacademy::test::runAllTests() returns false when nothing is registered, and
 *        prints nothing while doing it. A suite whose every test sits behind a guard therefore
 *        reports red, in silence, before you have written a line, and looks broken when it is
 *        merely empty. Something has to be here from the first day.
 *
 *        It may as well be something worth having. Every driver you write in this course
 *        derives one register's address from another: handed PINB, it finds DDRB by adding one
 *        and PORTB by adding two, and it does that for whichever port it was given. These tests
 *        are the arithmetic behind that, checked against the datasheet's absolute addresses. If
 *        one of them fails, no driver in the course can work, and you would rather find that
 *        out here than inside a subroutine you are also debugging.
 */
#include <cstdint>

#include "avr/atmega328p.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr::atmega328p;
} // namespace

/**
 * @brief The four data space regions abut, in order, with no gaps.
 *
 *        Each region starts where the previous one ends, which is what makes the data space one
 *        flat space rather than four.
 */
TEST(Device, DataSpaceRegionsAbut)
{
    EXPECT_EQ(IoBase, static_cast<std::uint16_t>(RegisterFileBase + RegisterCount));
    EXPECT_EQ(ExtendedIoBase, static_cast<std::uint16_t>(IoBase + IoCount));
    EXPECT_EQ(SramBase, static_cast<std::uint16_t>(ExtendedIoBase + ExtendedIoCount));
    EXPECT_EQ(RamEnd, static_cast<std::uint16_t>(SramBase + SramSize - 1U));
}

/**
 * @brief The data space regions are the sizes the datasheet gives.
 */
TEST(Device, DataSpaceRegionSizes)
{
    EXPECT_EQ(static_cast<unsigned>(RegisterCount), 32U);
    EXPECT_EQ(static_cast<unsigned>(IoCount), 64U);
    EXPECT_EQ(static_cast<unsigned>(ExtendedIoCount), 160U);
    EXPECT_EQ(static_cast<unsigned>(SramSize), 2048U);
    EXPECT_EQ(static_cast<unsigned>(RamEnd), 0x08FFU);
}

/**
 * @brief An I/O address plus IoOffset is a data space address.
 *
 *        PINB is I/O address 0x03 and data space address 0x23. in and out take the first, lds
 *        and sts the second, and mixing them up is how a first AVR program writes to a register
 *        that is not the one it meant and does nothing observable at all.
 */
TEST(Device, IoOffsetSeparatesTheTwoAddressings)
{
    EXPECT_EQ(static_cast<unsigned>(IoOffset), 0x20U);
    EXPECT_EQ(static_cast<std::uint16_t>(PinB - IoOffset), 0x03U);
    EXPECT_EQ(static_cast<std::uint16_t>(PinC - IoOffset), 0x06U);
    EXPECT_EQ(static_cast<std::uint16_t>(PinD - IoOffset), 0x09U);
    EXPECT_EQ(static_cast<std::uint16_t>(Spl - IoOffset), 0x3DU);
    EXPECT_EQ(static_cast<std::uint16_t>(Sreg - IoOffset), 0x3FU);
}

/**
 * @brief Each port is PIN, then DDR, then PORT, one byte apart.
 *
 *        This is the fact led_init relies on when it stores three pointers into a struct after
 *        being told only one of them.
 */
TEST(Device, PortRegistersAreConsecutive)
{
    EXPECT_EQ(static_cast<unsigned>(DirectionOffset), 1U);
    EXPECT_EQ(static_cast<unsigned>(PortOffset), 2U);

    EXPECT_EQ(static_cast<std::uint16_t>(PinB + DirectionOffset), 0x0024U); // DDRB
    EXPECT_EQ(static_cast<std::uint16_t>(PinB + PortOffset), 0x0025U);      // PORTB
    EXPECT_EQ(static_cast<std::uint16_t>(PinD + DirectionOffset), 0x002AU); // DDRD
    EXPECT_EQ(static_cast<std::uint16_t>(PinD + PortOffset), 0x002BU);      // PORTD
}

/**
 * @brief The three ports are evenly spaced, which is why one driver serves all of them.
 */
TEST(Device, PortsAreEvenlySpaced)
{
    EXPECT_EQ(static_cast<unsigned>(PortStride), 3U);
    EXPECT_EQ(PinC, static_cast<std::uint16_t>(PinB + PortStride));
    EXPECT_EQ(PinD, static_cast<std::uint16_t>(PinC + PortStride));
}

/**
 * @brief The vector table is 26 vectors of two words each, ending at word address 0x32.
 *
 *        Two words, not two bytes. jmp is a two-word instruction on a part with 32 KB of flash,
 *        so each vector slot has to hold one, and that is why PCINT0 sits at word 0x06 rather
 *        than at 0x03. Halving this is the classic way every handler in a program ends up at
 *        the wrong address at once.
 */
TEST(Device, VectorTableGeometry)
{
    EXPECT_EQ(VectorCount, 26U);
    EXPECT_EQ(VectorWords, 2U);
    EXPECT_EQ(ResetVector, 0x0000U);

    // The word address of the last vector, which is where the table ends.
    EXPECT_EQ((VectorCount - 1U) * VectorWords, 0x32U);

    // PCINT0, PCINT1 and PCINT2 are vectors 3, 4 and 5.
    EXPECT_EQ(3U * VectorWords, 0x06U);
    EXPECT_EQ(4U * VectorWords, 0x08U);
    EXPECT_EQ(5U * VectorWords, 0x0AU);
}

/**
 * @brief Flash is 32 KB seen as 16K words, and EEPROM is 1 KB in its own space.
 */
TEST(Device, MemorySizes)
{
    EXPECT_EQ(FlashWords, 16384U);
    EXPECT_EQ(FlashWords * 2U, 32768U);
    EXPECT_EQ(static_cast<unsigned>(EepromSize), 1024U);
}

/**
 * @brief Only the upper half of the register file can take an immediate.
 */
TEST(Device, ImmediateRegistersAreTheUpperHalf)
{
    EXPECT_EQ(static_cast<unsigned>(FirstImmediateRegister), 16U);
    EXPECT_EQ(static_cast<unsigned>(RegisterCount) - FirstImmediateRegister, 16U);
}

/**
 * @brief The clock every timing number in this course is derived from.
 */
TEST(Device, Clocks)
{
    EXPECT_EQ(ArduinoUnoClockHz, 16000000U);
    EXPECT_EQ(FactoryDefaultClockHz, 1000000U);
}
