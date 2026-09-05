/**
 * @brief Tests for drivers/source/btn.asm, run in the simulator.
 *
 *        Guarded by HAVE_BTN, which this suite's makefile defines when
 *        drivers/source/btn.asm exists.
 *
 *        Two of the tests here exist because the mistakes they catch are the ones this driver
 *        actually attracts, and both produce code that assembles, runs, and looks right:
 *        returning the wrong way round from `btn_interrupt_enabled`, and reaching for the
 *        wrong field of the structure in `btn_disable_interrupt`. Neither shows up until
 *        there are two buttons, or until somebody trusts the answer.
 */
#if defined(HAVE_BTN) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/** Where a test puts a button structure, and a second one. */
constexpr std::uint16_t Button{0x0240U};
constexpr std::uint16_t Button2{0x0260U};

/** Field offsets, from the specification. */
constexpr std::uint16_t PinRegOffset{0U};
constexpr std::uint16_t DirRegOffset{2U};
constexpr std::uint16_t PortRegOffset{4U};
constexpr std::uint16_t PcmskRegOffset{6U};
constexpr std::uint16_t PcieBitOffset{8U};
constexpr std::uint16_t PinOffset{9U};

/** Data space addresses this driver touches. */
constexpr std::uint16_t PinB{0x23U};
constexpr std::uint16_t DdrB{0x24U};
constexpr std::uint16_t PortB{0x25U};
constexpr std::uint16_t PinD{0x29U};
constexpr std::uint16_t Pcicr{0x68U};
constexpr std::uint16_t Pcmsk0{0x6BU};
constexpr std::uint16_t Pcmsk2{0x6DU};

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
 * @param[in] address Structure address.
 *
 * @return The value returned in r24.
 */
std::uint8_t call(avrsim::Mcu& mcu, const char* symbol, const std::uint16_t address = Button)
{
    mcu.setRegPair(24U, address);
    mcu.call(symbol);
    return mcu.reg(24U);
}

/**
 * @brief Initialise a button on an Arduino pin.
 *
 * @param[in] mcu     The machine.
 * @param[in] pin     Arduino pin number.
 * @param[in] address Structure address.
 *
 * @return The value returned in r24.
 */
std::uint8_t init(avrsim::Mcu& mcu, const std::uint8_t pin, const std::uint16_t address = Button)
{
    mcu.setRegPair(24U, address);
    mcu.setReg(22U, pin);
    mcu.call("btn_init");
    return mcu.reg(24U);
}
} // namespace

/**
 * @brief Every subroutine the specification names is defined and global.
 */
TEST(Btn, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    for (const char* symbol :
         {"btn_init", "btn_pressed", "btn_enable_interrupt", "btn_disable_interrupt",
          "btn_interrupt_enabled", "btn_toggle_interrupt"})
    {
        EXPECT_TRUE(mcu.has(symbol));
    }
}

/**
 * @brief A port B button gets port B's registers, PCMSK0 and PCIE0.
 */
TEST(Btn, InitBuildsThePortBStructure)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 13U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PinRegOffset)), PinB);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, DirRegOffset)), DdrB);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PortRegOffset)), PortB);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PcmskRegOffset)), Pcmsk0);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Button + PcieBitOffset)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Button + PinOffset)), 5U);
}

/**
 * @brief A port D button gets port D's registers, PCMSK2 and PCIE2.
 *
 *        Note that the mask register and the enable bit are not the same distance apart as the
 *        port registers are: PCMSK0 and PCMSK2 differ by two, and PCIE0 and PCIE2 by two as
 *        well, but there is no port C in between for this driver because Arduino digital pins
 *        do not reach it.
 */
TEST(Btn, InitBuildsThePortDStructure)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 3U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PinRegOffset)), PinD);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PcmskRegOffset)), Pcmsk2);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Button + PcieBitOffset)), 2U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Button + PinOffset)), 3U);
}

/**
 * @brief Initialising makes the pin an input and switches its pull-up on.
 *
 *        The opposite of what led_init does with the same two registers, which is the whole
 *        difference between the two drivers' first halves.
 */
TEST(Btn, InitMakesAnInputWithItsPullUpOn)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(DdrB, 0xFFU);
    init(mcu, 13U);

    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB) & 0x20U), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x20U), 0x20U);
}

/**
 * @brief Initialising one pin leaves the other seven alone.
 */
TEST(Btn, InitLeavesTheRestOfThePortAlone)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(DdrB, 0x03U);
    mcu.setData(PortB, 0x03U);
    init(mcu, 13U);

    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB) & 0x03U), 0x03U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(PortB) & 0x03U), 0x03U);
}

/**
 * @brief An out-of-range pin is refused before anything is written.
 */
TEST(Btn, InitRejectsPinsAboveThirteen)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 14U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Button, PinRegOffset)), 0U);
}

/**
 * @brief A pressed button reads 1 from the driver, and 0 from the pin.
 *
 *        The inversion the whole circuit forces. The pull-up holds the pin high when nothing is
 *        pressing it, so PINB reads 1 for "not pressed", and the driver has to say the opposite.
 */
TEST(Btn, PressedInvertsWhatThePinReads)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    mcu.drive('B', 5U, true);
    mcu.run(4U);
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "btn_pressed")), 0U);

    mcu.drive('B', 5U, false);
    mcu.run(4U);
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "btn_pressed")), 1U);
}

/**
 * @brief Enabling sets one bit of PCICR and one bit of the port's mask register.
 */
TEST(Btn, EnableSetsBothRegisters)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);
    call(mcu, "btn_enable_interrupt");

    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcicr) & 0x01U), 0x01U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0x20U);
}

/**
 * @brief The driver does not switch global interrupts on behind your back.
 *
 *        A driver that runs `sei` as a side effect of configuring one pin decides, on your
 *        behalf, that the whole program is now ready to be interrupted. You will find AVR
 *        drivers that do it. This one does not: `sei` belongs in your setup code, once, when
 *        everything else is configured.
 */
TEST(Btn, EnableDoesNotTouchTheGlobalInterruptFlag)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    // Read through the accessor rather than from 0x5F: the simulator keeps the flags in its
    // own storage and only materialises the packed byte when a program reads it.
    const bool before = mcu.interruptsEnabled();
    call(mcu, "btn_enable_interrupt");
    EXPECT_TRUE(before == mcu.interruptsEnabled());
}

/**
 * @brief Disabling clears the pin's mask bit and leaves the port's enable alone.
 *
 *        PCICR enables a whole port's vector, and other buttons on that port may still want it.
 *        A driver that cleared PCICR here would silently switch off every other button sharing
 *        the port, which is a bug that cannot appear until there are two.
 */
TEST(Btn, DisableClearsOnlyTheMaskBit)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);
    call(mcu, "btn_enable_interrupt");
    call(mcu, "btn_disable_interrupt");

    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcicr) & 0x01U), 0x01U);
}

/**
 * @brief Disabling one button leaves another button on the same port enabled.
 *
 *        This is the test that catches a `btn_disable_interrupt` which shifts by the wrong
 *        field of the structure. Reading the pin *register* pointer where the pin *number*
 *        belongs gives a shift count of 0x23, which produces a mask of zero, which clears
 *        nothing at all; with one button, "nothing happened" and "the right thing happened" look
 *        identical from outside.
 */
TEST(Btn, DisablingOneButtonLeavesAnother)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U, Button);
    init(mcu, 12U, Button2);
    call(mcu, "btn_enable_interrupt", Button);
    call(mcu, "btn_enable_interrupt", Button2);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x30U), 0x30U);

    call(mcu, "btn_disable_interrupt", Button);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x10U), 0x10U);
}

/**
 * @brief interrupt_enabled reports yes when it is enabled, and no when it is not.
 *
 *        Stated that plainly because the classic mistake here is to return the two the wrong way
 *        round. Nothing about the code looks wrong: the branch is there, both constants are
 *        there, and they are simply swapped. Every caller then does the opposite of what it
 *        meant, including `btn_toggle_interrupt`, which stops toggling and starts latching.
 */
TEST(Btn, InterruptEnabledReportsTheTruth)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    EXPECT_EQ(static_cast<unsigned>(call(mcu, "btn_interrupt_enabled")), 0U);

    call(mcu, "btn_enable_interrupt");
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "btn_interrupt_enabled")), 1U);

    call(mcu, "btn_disable_interrupt");
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "btn_interrupt_enabled")), 0U);
}

/**
 * @brief Toggling switches it on, then off, then on again.
 *
 *        Built on interrupt_enabled, so an inverted answer there turns this into a subroutine
 *        that leaves the interrupt in the same state every time and is named toggle.
 */
TEST(Btn, ToggleAlternates)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U);

    call(mcu, "btn_toggle_interrupt");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0x20U);

    call(mcu, "btn_toggle_interrupt");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0U);

    call(mcu, "btn_toggle_interrupt");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0x20U);
}

/**
 * @brief Two buttons on different ports use different mask registers and different enable bits.
 */
TEST(Btn, TwoButtonsOnDifferentPorts)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 13U, Button);
    init(mcu, 3U, Button2);
    call(mcu, "btn_enable_interrupt", Button);
    call(mcu, "btn_enable_interrupt", Button2);

    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcicr) & 0x05U), 0x05U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk0) & 0x20U), 0x20U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Pcmsk2) & 0x08U), 0x08U);
}

#endif // defined(HAVE_BTN) && defined(DRIVERS_HEX)
