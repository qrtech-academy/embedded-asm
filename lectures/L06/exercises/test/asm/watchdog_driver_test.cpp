/**
 * @brief Tests for drivers/source/watchdog.asm, run in the simulator.
 *
 *        Guarded by HAVE_WATCHDOG.
 *
 *        This is the one driver in the course whose *timing* is checked rather than only its
 *        effect, because the hardware checks it too: the two writes that configure the watchdog
 *        must be within four cycles of each other, and the simulator enforces that faithfully.
 *
 *        What makes it worth testing is what a botched sequence leaves behind. The window is
 *        opened by writing WDCE and WDE together; if the second write arrives too late it is
 *        ignored, and WDE stays set with the timeout bits at zero. The device is then in system
 *        reset mode with the **shortest** timeout, resetting every sixteen milliseconds, which
 *        for most programs is for ever.
 */
#if defined(HAVE_WATCHDOG) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/** Data space addresses. */
constexpr std::uint16_t Wdtcsr{0x60U};
constexpr std::uint16_t Mcusr{0x54U};

/** Bits. */
constexpr std::uint8_t Wde{1U << 3U};
constexpr std::uint8_t Wdrf{1U << 3U};

/**
 * @brief Configure the watchdog with a control byte.
 *
 * @param[in] mcu  The machine.
 * @param[in] byte The WDTCSR value wanted.
 *
 * @return What WDTCSR actually holds afterwards.
 */
std::uint8_t configure(avrsim::Mcu& mcu, const std::uint8_t byte)
{
    mcu.setReg(24U, byte);
    mcu.call("watchdog_init");
    return mcu.data(Wdtcsr);
}
} // namespace

/**
 * @brief Every subroutine the specification names is defined and global.
 */
TEST(WatchdogDriver, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    for (const char* symbol :
         {"watchdog_init", "watchdog_reset", "watchdog_disable", "watchdog_caused_reset"})
    {
        EXPECT_TRUE(mcu.has(symbol));
    }
}

/**
 * @brief The control byte you asked for is the one that ends up in the register.
 *
 *        This is the test that says your timed sequence was fast enough. If it fails with
 *        WDTCSR reading 0x08, the second write missed the window: the value is not merely wrong,
 *        it is the most dangerous setting the register has.
 */
TEST(WatchdogDriver, InitWritesTheByteAsked)
{
    avrsim::Mcu mcu{HexPath};

    EXPECT_EQ(static_cast<unsigned>(configure(mcu, 0x0EU)), 0x0EU); // 1 s, reset mode
    EXPECT_EQ(static_cast<unsigned>(configure(mcu, 0x29U)), 0x29U); // 8 s, reset mode
    EXPECT_EQ(static_cast<unsigned>(configure(mcu, 0x46U)), 0x46U); // 1 s, interrupt mode
}

/**
 * @brief A sequence that missed its window leaves 0x08, and this is what that looks like.
 *
 *        Not a test of your code: a demonstration, using the value the hardware is left holding,
 *        that the failure is silent and specific. If InitWritesTheByteAsked ever reports 0x08,
 *        this is the state your device is in.
 */
TEST(WatchdogDriver, TheDangerousValueIsRecognisable)
{
    EXPECT_EQ(static_cast<unsigned>(Wde), 0x08U);
    EXPECT_EQ(static_cast<unsigned>(0x08U) & 0x07U, 0U);
}

/**
 * @brief Configuring the watchdog leaves interrupts as it found them.
 *
 *        The sequence has to run with interrupts off, because an interrupt landing between the
 *        two writes takes far longer than four cycles. Turning them off is necessary; leaving
 *        them off is a bug, and one that shows up as every other interrupt in the program
 *        quietly stopping.
 */
TEST(WatchdogDriver, InitRestoresTheInterruptFlag)
{
    avrsim::Mcu mcu{HexPath};

    // Set through setSreg rather than by writing 0x5F: the simulator keeps the flags apart
    // from the data space, so a write to the address would not change the flag the processor
    // acts on and this test would be checking nothing.
    mcu.setSreg(static_cast<std::uint8_t>(mcu.sreg() | 0x80U));
    configure(mcu, 0x0EU);
    EXPECT_TRUE(mcu.interruptsEnabled());

    mcu.setSreg(static_cast<std::uint8_t>(mcu.sreg() & 0x7FU));
    configure(mcu, 0x0EU);
    EXPECT_FALSE(mcu.interruptsEnabled());
}

/**
 * @brief Configuring clears WDRF, because otherwise WDE can never be cleared again.
 *
 *        The datasheet's rule, and the reason a program that has just been reset by the watchdog
 *        cannot switch it off until it clears the flag recording that fact. A driver that
 *        forgets works perfectly on the first run and cannot be disabled on the second.
 */
TEST(WatchdogDriver, InitClearsTheResetFlag)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(Mcusr, static_cast<std::uint8_t>(mcu.data(Mcusr) | Wdrf));

    configure(mcu, 0x0EU);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Mcusr) & Wdrf), 0U);
}

/**
 * @brief Disabling leaves the register empty, with the timeout bits and both mode bits clear.
 */
TEST(WatchdogDriver, DisableClearsTheRegister)
{
    avrsim::Mcu mcu{HexPath};
    configure(mcu, 0x29U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Wdtcsr)), 0x29U);

    mcu.call("watchdog_disable");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Wdtcsr)), 0x00U);
}

/**
 * @brief Disabling works even straight after a watchdog reset.
 *
 *        The case the WDRF rule exists for: the flag is set, and a driver that does not clear it
 *        first finds that WDE refuses to go.
 */
TEST(WatchdogDriver, DisableWorksWithTheResetFlagSet)
{
    avrsim::Mcu mcu{HexPath};
    configure(mcu, 0x0EU);
    mcu.setData(Mcusr, static_cast<std::uint8_t>(mcu.data(Mcusr) | Wdrf));

    mcu.call("watchdog_disable");
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Wdtcsr)), 0x00U);
}

/**
 * @brief caused_reset reports whether the watchdog was the cause, and then clears the record.
 */
TEST(WatchdogDriver, CausedResetReportsAndClears)
{
    avrsim::Mcu mcu{HexPath};

    mcu.setData(Mcusr, static_cast<std::uint8_t>(mcu.data(Mcusr) & ~Wdrf));
    mcu.call("watchdog_caused_reset");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 0U);

    mcu.setData(Mcusr, static_cast<std::uint8_t>(mcu.data(Mcusr) | Wdrf));
    mcu.call("watchdog_caused_reset");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Mcusr) & Wdrf), 0U);

    // Asking twice reports no the second time, because the record is gone.
    mcu.call("watchdog_caused_reset");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 0U);
}

/**
 * @brief caused_reset leaves the other reset causes alone.
 *
 *        MCUSR records four different reasons in four bits, and clearing all of them because you
 *        only cared about one destroys information nobody can recover.
 */
TEST(WatchdogDriver, CausedResetLeavesTheOtherCauses)
{
    avrsim::Mcu mcu{HexPath};
    mcu.setData(Mcusr, 0x0FU); // all four causes recorded

    mcu.call("watchdog_caused_reset");
    EXPECT_EQ(static_cast<unsigned>(mcu.reg(24U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Mcusr) & 0x07U), 0x07U);
}

/**
 * @brief Petting the watchdog does not disturb the configuration.
 *
 *        `watchdog_reset` is the one that runs in your main loop, thousands of times, and it must
 *        do exactly one thing.
 */
TEST(WatchdogDriver, ResetLeavesTheConfigurationAlone)
{
    avrsim::Mcu mcu{HexPath};
    configure(mcu, 0x29U);

    for (int pet{0}; pet < 5; ++pet)
    {
        mcu.call("watchdog_reset");
    }
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Wdtcsr)), 0x29U);
}

#endif // defined(HAVE_WATCHDOG) && defined(DRIVERS_HEX)
