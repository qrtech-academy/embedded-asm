/**
 * @brief Tests for drivers/source/led_array.asm, run in the simulator.
 *
 *        Guarded by HAVE_LED_ARRAY.
 *
 *        The array is the point rather than the LEDs. Everything here is really asking one
 *        question: does your code walk a run of structures by adding LED_SIZE to a pointer, and
 *        does it stop where it was told to. Both halves of that have a characteristic failure,
 *        and both are checked: a stride of the wrong size lands the second structure on top of
 *        the first's last byte, and a loop that runs one iteration too many writes a whole
 *        structure past the end of the array.
 */
#if defined(HAVE_LED_ARRAY) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avr/drivers.hpp"
#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
using namespace avr;

/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/** Where a test puts the array. Well clear of the stack, and of round numbers. */
constexpr std::uint16_t Array{0x0300U};

/** A byte written either side of the array, to catch a walk that runs past its end. */
constexpr std::uint16_t Fence{0x02FFU};
constexpr std::uint8_t FenceValue{0xA5U};

/** Data space addresses of the two ports an Arduino Uno reaches. */
constexpr std::uint16_t PortB{0x25U};
constexpr std::uint16_t PortD{0x2BU};
constexpr std::uint16_t PinB{0x23U};
constexpr std::uint16_t PinD{0x29U};

/**
 * @brief Address of one structure in the array.
 *
 * @param[in] index Which one.
 *
 * @return Its address, at a stride of LedSize.
 */
[[nodiscard]] constexpr std::uint16_t entry(const std::uint16_t index)
{
    return static_cast<std::uint16_t>(Array + index * drivers::LedSize);
}

/**
 * @brief Read a 16-bit field of one structure.
 *
 * @param[in] mcu    The machine.
 * @param[in] index  Which structure.
 * @param[in] offset Field offset.
 *
 * @return The field, low byte first.
 */
[[nodiscard]] std::uint16_t field(const avrsim::Mcu& mcu, const std::uint16_t index,
                                  const std::uint16_t offset)
{
    const auto at = entry(index) + offset;
    return static_cast<std::uint16_t>(mcu.data(at) | (mcu.data(at + 1U) << 8U));
}

/**
 * @brief Initialise an array of LEDs on consecutive pins.
 *
 * @param[in] mcu      The machine.
 * @param[in] count    How many.
 * @param[in] firstPin The Arduino pin of the first.
 *
 * @return The value returned in r24.
 */
std::uint8_t init(avrsim::Mcu& mcu, const std::uint8_t count, const std::uint8_t firstPin)
{
    mcu.setData(Fence, FenceValue);
    mcu.setRegPair(24U, Array);
    mcu.setReg(22U, count);
    mcu.setReg(20U, firstPin);
    mcu.call("led_array_init");
    return mcu.reg(24U);
}

/**
 * @brief Call a two-argument array subroutine.
 *
 * @param[in] mcu    The machine.
 * @param[in] symbol Subroutine name.
 * @param[in] count  How many entries.
 *
 * @return The value returned in r24.
 */
std::uint8_t walk(avrsim::Mcu& mcu, const char* symbol, const std::uint8_t count)
{
    mcu.setRegPair(24U, Array);
    mcu.setReg(22U, count);
    mcu.call(symbol);
    return mcu.reg(24U);
}
} // namespace

/**
 * @brief Every subroutine the specification names is defined and global.
 */
TEST(LedArray, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    for (const char* symbol :
         {"led_array_init", "led_array_all_on", "led_array_all_off", "led_array_toggle_at"})
    {
        EXPECT_TRUE(mcu.has(symbol));
    }
}

/**
 * @brief Six LEDs from pin 8 become bits 0 to 5 of port B, one structure every LedSize bytes.
 *
 *        The stride is what is really under test. A walk that advances by anything but LedSize
 *        puts the second structure somewhere overlapping the first, and the first few fields
 *        still look plausible.
 */
TEST(LedArray, InitWalksAtTheStructureStride)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 6U, 8U)), 0U);

    for (std::uint16_t index{0U}; index < 6U; ++index)
    {
        EXPECT_EQ(static_cast<unsigned>(field(mcu, index, drivers::LedPinReg)), PinB);
        EXPECT_EQ(static_cast<unsigned>(field(mcu, index, drivers::LedPortReg)), PortB);
        EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(index) + drivers::LedPin)), index);
    }
}

/**
 * @brief An array may span the boundary between the two ports.
 *
 *        Pins 6 and 7 are port D bits 6 and 7; pins 8 and 9 are port B bits 0 and 1. Nothing in
 *        the array knows that, because each entry is initialised by the same led_init that
 *        already knew.
 */
TEST(LedArray, InitSpansThePortBoundary)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 4U, 6U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, 0U, drivers::LedPinReg)), PinD);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(0U) + drivers::LedPin)), 6U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, 1U, drivers::LedPinReg)), PinD);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(1U) + drivers::LedPin)), 7U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, 2U, drivers::LedPinReg)), PinB);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(2U) + drivers::LedPin)), 0U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, 3U, drivers::LedPinReg)), PinB);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(3U) + drivers::LedPin)), 1U);
}

/**
 * @brief An array that would run past pin 13 is refused.
 */
TEST(LedArray, InitRejectsAnArrayThatRunsOffTheEnd)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 4U, 12U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 2U, 12U)), 0U);
}

/**
 * @brief An empty array is not an error, and writes nothing.
 *
 *        A count of zero is the input that separates a loop testing its condition at the top
 *        from one testing it at the bottom. The second kind initialises one LED anyway.
 */
TEST(LedArray, InitAcceptsAnEmptyArrayAndWritesNothing)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 0U, 8U)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(0U) + drivers::LedPinReg)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(0U) + drivers::LedPin)), 0U);
}

/**
 * @brief The walk stops where it was told, and does not write a structure past the end.
 *
 *        Checked with a fence byte below the array rather than above it, because a loop that
 *        runs one iteration too many walks *upwards*; the byte just past the last structure is
 *        the one at risk, and it is inside the region this test owns.
 */
TEST(LedArray, InitStopsAtTheCount)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 3U, 8U);

    // The fourth structure's space was never touched.
    for (std::uint16_t offset{0U}; offset < drivers::LedSize; ++offset)
    {
        EXPECT_EQ(static_cast<unsigned>(mcu.data(entry(3U) + offset)), 0U);
    }
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Fence)), FenceValue);
}

/**
 * @brief all_on lights every LED in the array and all_off clears them.
 */
TEST(LedArray, AllOnAndAllOff)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 6U, 8U);

    walk(mcu, "led_array_all_on", 6U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x3FU), 0x3FU);

    walk(mcu, "led_array_all_off", 6U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x3FU), 0U);
}

/**
 * @brief all_on drives every entry and no more than the entries.
 *
 *        With four LEDs of six initialised, the other two bits of the port must not move. A walk
 *        that ignores the count would light them, because the structures are there.
 */
TEST(LedArray, AllOnRespectsTheCount)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 6U, 8U);
    walk(mcu, "led_array_all_off", 6U);

    walk(mcu, "led_array_all_on", 4U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x3FU), 0x0FU);
}

/**
 * @brief toggle_at flips one LED and leaves the others where they were.
 */
TEST(LedArray, ToggleAtFlipsOne)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 6U, 8U);
    walk(mcu, "led_array_all_on", 6U);

    mcu.setRegPair(24U, Array);
    mcu.setReg(22U, 6U);
    mcu.setReg(20U, 2U);
    mcu.call("led_array_toggle_at");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x3FU), 0x3BU);
}

/**
 * @brief An index at or past the count is refused, and nothing is written.
 *
 *        Index 6 of a six-entry array is the one that matters: it is the first address past the
 *        end, it looks like a valid structure, and the driver would happily initialise from it.
 */
TEST(LedArray, ToggleAtRejectsAnIndexPastTheEnd)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 6U, 8U);
    walk(mcu, "led_array_all_on", 6U);
    const auto before = mcu.data(PortB);

    for (const std::uint8_t index : {6U, 7U, 200U})
    {
        mcu.setRegPair(24U, Array);
        mcu.setReg(22U, 6U);
        mcu.setReg(20U, index);
        mcu.call("led_array_toggle_at");
        EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 1U);
    }
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB)), static_cast<unsigned>(before));
}

#endif // defined(HAVE_LED_ARRAY) && defined(DRIVERS_HEX)
