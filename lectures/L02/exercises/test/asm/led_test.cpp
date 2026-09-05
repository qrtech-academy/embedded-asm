/**
 * @brief Tests for drivers/source/led.asm, run in the simulator.
 *
 *        Guarded by HAVE_LED, which this suite's makefile defines when drivers/source/led.asm
 *        exists.
 *
 *        **These pin the driver's behaviour strictly and its cost only loosely**, which is a
 *        deliberate change from L01. There, the specification gave `shift_bits` instruction by
 *        instruction and the test asserted 6n + 10 exactly. A driver is a bigger thing with more
 *        than one reasonable shape, so what is asserted here is not what it costs but how its
 *        cost *changes*: six cycles more per bit for led_on, seven for led_off, and one more for
 *        led_enabled when the answer is yes. Those relationships follow from what the driver has
 *        to do rather than from how you chose to write it, and they are the part the cross-check
 *        exercise is about.
 */
#if defined(HAVE_LED) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/** Where a test puts an LED structure: inside SRAM, well clear of the stack at RAMEND. */
constexpr std::uint16_t Led{0x0200U};

/** A second structure, for the tests about two LEDs at once. */
constexpr std::uint16_t Led2{0x0220U};

/** Field offsets, from the specification. */
constexpr std::uint16_t PinRegOffset{0U};
constexpr std::uint16_t DirRegOffset{2U};
constexpr std::uint16_t PortRegOffset{4U};
constexpr std::uint16_t PinOffset{6U};

/** Data space addresses of the port registers. */
constexpr std::uint16_t PinB{0x23U};
constexpr std::uint16_t DdrB{0x24U};
constexpr std::uint16_t PortB{0x25U};
constexpr std::uint16_t PinD{0x29U};
constexpr std::uint16_t PortD{0x2BU};

/**
 * @brief Read a 16-bit field out of a structure in the simulated data space.
 *
 * @param[in] mcu     The machine.
 * @param[in] address Structure address.
 * @param[in] offset  Field offset.
 *
 * @return The field, low byte first.
 */
[[nodiscard]] std::uint16_t field(const avrsim::Mcu& mcu, const std::uint16_t address,
                                  const std::uint16_t offset)
{
    return static_cast<std::uint16_t>(mcu.data(address + offset) |
                                      (mcu.data(address + offset + 1U) << 8U));
}

/**
 * @brief Call a one-argument driver subroutine on a structure.
 *
 * @param[in] mcu     The machine.
 * @param[in] symbol  Subroutine name.
 * @param[in] address Structure address, passed in r25:r24.
 *
 * @return Cycles consumed.
 */
std::uint64_t call(avrsim::Mcu& mcu, const char* symbol, const std::uint16_t address = Led)
{
    mcu.setRegPair(24U, address);
    return mcu.call(symbol).cycles;
}

/**
 * @brief Initialise an LED on an Arduino pin.
 *
 * @param[in] mcu     The machine.
 * @param[in] pin     Arduino pin number, passed in r22.
 * @param[in] address Structure address, passed in r25:r24.
 *
 * @return The value returned in r24.
 */
std::uint8_t init(avrsim::Mcu& mcu, const std::uint8_t pin, const std::uint16_t address = Led)
{
    mcu.setRegPair(24U, address);
    mcu.setReg(22U, pin);
    mcu.call("led_init");
    return mcu.reg(24U);
}
} // namespace

/**
 * @brief Every subroutine the specification names is defined and global.
 */
TEST(Led, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    for (const char* symbol : {"led_init", "led_on", "led_off", "led_toggle", "led_enabled"})
    {
        EXPECT_TRUE(mcu.has(symbol));
    }
}

/**
 * @brief Initialising a port B pin fills the structure with port B's registers.
 */
TEST(Led, InitBuildsThePortBStructure)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 13U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PinRegOffset)), PinB);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, DirRegOffset)), DdrB);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PortRegOffset)), PortB);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Led + PinOffset)), 5U);
}

/**
 * @brief Initialising a port D pin fills it with port D's registers, and bit numbering restarts.
 */
TEST(Led, InitBuildsThePortDStructure)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 0U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PinRegOffset)), PinD);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PortRegOffset)), PortD);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Led + PinOffset)), 0U);

    EXPECT_EQ(static_cast<unsigned>(init(mcu, 7U)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Led + PinOffset)), 7U);
}

/**
 * @brief Pin 8 is bit 0, not bit 8.
 *
 *        The boundary between the two ports, and the one an implementation that forgets to
 *        subtract gets wrong. Bit 8 of an eight-bit register does not exist, so the mask comes
 *        out zero and the LED never lights, which looks like a wiring fault rather than a bug.
 */
TEST(Led, PinEightIsBitZero)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 8U)), 0U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PinRegOffset)), PinB);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Led + PinOffset)), 0U);
}

/**
 * @brief Initialising makes the pin an output and leaves the LED off.
 */
TEST(Led, InitDrivesTheDirectionAndClearsTheOutput)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(PortB, 0xFFU);
    init(mcu, 13U);

    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB) & 0x20U), 0x20U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0U);
}

/**
 * @brief Initialising one pin leaves every other bit of the port alone.
 *
 *        The reason the driver reads, modifies and writes rather than simply storing a mask.
 *        A driver that assigns instead of ORing passes every test above and turns off every
 *        other LED on the port, which is a bug that only appears once there are two.
 */
TEST(Led, InitLeavesTheRestOfThePortAlone)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(DdrB, 0x03U);
    init(mcu, 13U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB) & 0x03U), 0x03U);
}

/**
 * @brief An out-of-range pin is refused, and refused before anything is written.
 */
TEST(Led, InitRejectsPinsAboveThirteen)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(DdrB, 0x00U);

    EXPECT_EQ(static_cast<unsigned>(init(mcu, 14U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 200U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB)), 0U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Led, PinRegOffset)), 0U);
}

/**
 * @brief on, off and toggle drive the right bit of PORTB.
 */
TEST(Led, OnOffAndToggle)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    call(mcu, "led_on");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0x20U);

    call(mcu, "led_off");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0U);

    call(mcu, "led_toggle");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0x20U);

    call(mcu, "led_toggle");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0U);
}

/**
 * @brief Driving one LED leaves the rest of the port alone.
 */
TEST(Led, DrivingOneBitLeavesTheOthers)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);
    mcu.setData(PortB, 0x0FU);

    call(mcu, "led_on");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x0FU), 0x0FU);

    call(mcu, "led_off");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x0FU), 0x0FU);
}

/**
 * @brief led_enabled reports what the pin is actually doing.
 */
TEST(Led, EnabledReportsTheState)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    call(mcu, "led_on");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 32U);
    EXPECT_EQ(static_cast<unsigned>((call(mcu, "led_enabled"), mcu.reg(24U))), 1U);

    call(mcu, "led_off");
    EXPECT_EQ(static_cast<unsigned>((call(mcu, "led_enabled"), mcu.reg(24U))), 0U);
}

/**
 * @brief Two LEDs on the same port do not interfere with each other.
 *
 *        The point of putting the registers in a structure rather than in the code. Nothing in
 *        the driver knows how many LEDs exist.
 */
TEST(Led, TwoLedsAreIndependent)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U, Led);
    init(mcu, 8U, Led2);

    call(mcu, "led_on", Led);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x21U), 0x20U);

    call(mcu, "led_on", Led2);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x21U), 0x21U);

    call(mcu, "led_off", Led);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x21U), 0x01U);
}

/**
 * @brief Two LEDs on different ports do not interfere either.
 */
TEST(Led, TwoLedsOnDifferentPorts)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U, Led);
    init(mcu, 3U, Led2);

    call(mcu, "led_on", Led);
    call(mcu, "led_on", Led2);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0x20U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortD) & 0x08U), 0x08U);
}

/**
 * @brief led_on costs exactly six cycles more per bit, because of the shift loop inside it.
 *
 *        The relationship rather than the number: whatever the fixed part of your driver costs,
 *        the variable part is `shift_bits`, and `shift_bits` costs six cycles per shift. Pin 13
 *        is bit 5, so it costs thirty cycles more than pin 8.
 */
TEST(Led, OnCostsSixCyclesMorePerBit)
{
    avrsim::Mcu mcu{HexPath};

    init(mcu, 8U);
    const auto base = call(mcu, "led_on");

    for (std::uint8_t bit{0U}; bit < 6U; ++bit)
    {
        init(mcu, static_cast<std::uint8_t>(8U + bit));
        EXPECT_EQ(call(mcu, "led_on"), base + 6U * bit);
    }
}

/**
 * @brief led_off costs seven cycles more per bit, because its shift loop has one more inc in it.
 *
 *        Two routines differing by a single instruction differ in cost by that instruction on
 *        every trip, and here that is visible from outside as a different slope.
 */
TEST(Led, OffCostsSevenCyclesMorePerBit)
{
    avrsim::Mcu mcu{HexPath};

    init(mcu, 8U);
    const auto base = call(mcu, "led_off");

    for (std::uint8_t bit{0U}; bit < 6U; ++bit)
    {
        init(mcu, static_cast<std::uint8_t>(8U + bit));
        EXPECT_EQ(call(mcu, "led_off"), base + 7U * bit);
    }
}

/**
 * @brief led_enabled costs one cycle more when the answer is yes.
 *
 *        Because a conditional branch costs two cycles when it is taken and one when it falls
 *        through, and this routine has exactly one of them. A subroutine whose running time
 *        depends on the value it is reporting is not a curiosity: it is the reason
 *        constant-time code has to be written deliberately, and it is visible here in a routine
 *        of eleven instructions.
 */
TEST(Led, EnabledCostsOneCycleMoreWhenTheLedIsOn)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    call(mcu, "led_off");
    const auto whenOff = call(mcu, "led_enabled");

    call(mcu, "led_on");
    const auto whenOn = call(mcu, "led_enabled");

    EXPECT_EQ(whenOn, whenOff + 1U);
}

#endif // defined(HAVE_LED) && defined(DRIVERS_HEX)
