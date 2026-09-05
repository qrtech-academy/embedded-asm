/**
 * @brief Tests for the pinned interrupt vector numbering.
 *
 *        This suite's always-on file. What it checks is the twenty-six numbers the whole lecture
 *        rests on, taken from avr-libc's device header rather than transcribed from the
 *        datasheet, and the arithmetic that turns one into an address.
 *
 *        Getting a vector number wrong is not like getting an ordinary constant wrong. The
 *        program still assembles, the handler still exists, and it is simply never reached,
 *        while some other vector now points into the middle of your code.
 */
#include <cstdint>

#include "avr/atmega328p.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;

/** The number the enumeration gives a vector. */
[[nodiscard]] unsigned numberOf(const atmega328p::Vector vector)
{
    return static_cast<unsigned>(vector);
}
} // namespace

/**
 * @brief Reset is vector 0, and is in the table despite not being an interrupt.
 *
 *        This is why a program's first instruction has to be a jump: the reset address is the
 *        first slot of the vector table, not the beginning of your code.
 */
TEST(VectorData, ResetIsVectorZero) { EXPECT_EQ(numberOf(atmega328p::Vector::Reset), 0U); }

/**
 * @brief The three pin change vectors are 3, 4 and 5, in port order B, C, D.
 *
 *        The ones this lecture uses. One vector per *port*, not per pin, which is the fact the
 *        whole button driver is shaped around.
 */
TEST(VectorData, PinChangeVectors)
{
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt0), 3U);
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt1), 4U);
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt2), 5U);
}

/**
 * @brief The vectors later lectures need are where the datasheet says.
 */
TEST(VectorData, LaterLecturesVectors)
{
    EXPECT_EQ(numberOf(atmega328p::Vector::Wdt), 6U);
    EXPECT_EQ(numberOf(atmega328p::Vector::Timer1CompA), 11U);
    EXPECT_EQ(numberOf(atmega328p::Vector::Timer0Ovf), 16U);
}

/**
 * @brief The table ends at vector 25, so there are 26 of them.
 */
TEST(VectorData, TableEndsAtTwentyFive)
{
    EXPECT_EQ(numberOf(atmega328p::Vector::SpmReady), 25U);
    EXPECT_EQ(numberOf(atmega328p::Vector::SpmReady) + 1U,
              static_cast<unsigned>(atmega328p::VectorCount));
}

/**
 * @brief A slot is two words, so the word address of vector n is 2n.
 *
 *        PCINT0 is at word 0x06 rather than at 0x03, and halving these puts every handler in a
 *        program at the wrong address at once.
 */
TEST(VectorData, SlotsAreTwoWordsApart)
{
    EXPECT_EQ(static_cast<unsigned>(atmega328p::VectorWords), 2U);
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt0) * atmega328p::VectorWords, 0x06U);
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt1) * atmega328p::VectorWords, 0x08U);
    EXPECT_EQ(numberOf(atmega328p::Vector::PcInt2) * atmega328p::VectorWords, 0x0AU);
    EXPECT_EQ(numberOf(atmega328p::Vector::SpmReady) * atmega328p::VectorWords, 0x32U);
}

/**
 * @brief The whole table fits below the application section.
 *
 *        26 vectors of 2 words each is 52 words, so the first word your own code may occupy is
 *        0x34. A program whose first instruction lands inside the table has overwritten a vector
 *        with an instruction, and nothing says so.
 */
TEST(VectorData, TableEndsWhereCodeMayBegin)
{
    EXPECT_EQ(atmega328p::VectorCount * atmega328p::VectorWords, 52U);
    EXPECT_EQ(atmega328p::VectorCount * atmega328p::VectorWords, 0x34U);
}
