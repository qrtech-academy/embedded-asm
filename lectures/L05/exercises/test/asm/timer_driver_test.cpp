/**
 * @brief Tests for drivers/source/timer.asm, run in the simulator.
 *
 *        Guarded by HAVE_TIMER.
 *
 *        This driver is the software half of a timer: the hardware interrupts at a rate it can
 *        reach, and this counts those interrupts so a program can have events slower than the
 *        hardware manages, and several of them at different rates from one timer.
 *
 *        Almost every test here is about *when* it fires. Firing one interrupt early or one late
 *        is a 1% error on a target of 100 and a 100% error on a target of 1, and neither shows up
 *        as anything but a rate that is slightly wrong.
 */
#if defined(HAVE_TIMER) && defined(DRIVERS_HEX)

#include <cstdint>

#include "avr/drivers.hpp"
#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The assembled driver library, whose path the makefile passes in. */
constexpr const char* HexPath{DRIVERS_HEX};

/** Where a test puts a timer structure, and a second one. */
constexpr std::uint16_t Timer{0x0280U};
constexpr std::uint16_t Timer2{0x02A0U};

/** Field offsets, from `avr/drivers.hpp`, which the always-on suite ties to `timer.inc`. */
constexpr std::uint16_t TargetOffset{avr::drivers::TimerTarget};
constexpr std::uint16_t CountOffset{avr::drivers::TimerCount};
constexpr std::uint16_t RunningOffset{avr::drivers::TimerRunning};

/**
 * @brief Read a 16-bit field of a structure.
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
 * @brief Initialise a timer with a target.
 *
 * @param[in] mcu     The machine.
 * @param[in] target  Interrupts per event.
 * @param[in] address Structure address.
 *
 * @return The value returned in r24.
 */
std::uint8_t init(avrsim::Mcu& mcu, const std::uint16_t target, const std::uint16_t address = Timer)
{
    mcu.setRegPair(24U, address);
    mcu.setRegPair(22U, target);
    mcu.call("timer_init");
    return mcu.reg(24U);
}

/**
 * @brief Call a one-argument timer subroutine.
 *
 * @param[in] mcu     The machine.
 * @param[in] symbol  Subroutine name.
 * @param[in] address Structure address.
 *
 * @return The value returned in r24.
 */
std::uint8_t call(avrsim::Mcu& mcu, const char* symbol, const std::uint16_t address = Timer)
{
    mcu.setRegPair(24U, address);
    mcu.call(symbol);
    return mcu.reg(24U);
}
} // namespace

/**
 * @brief Every subroutine the specification names is defined and global.
 */
TEST(TimerDriver, SubroutinesAreDefined)
{
    avrsim::Mcu mcu{HexPath};
    for (const char* symbol :
         {"timer_init", "timer_on", "timer_off", "timer_enabled", "timer_tick"})
    {
        EXPECT_TRUE(mcu.has(symbol));
    }
}

/**
 * @brief Initialising stores the target, clears the count, and leaves the timer off.
 *
 *        Off, not on. A timer that starts running the moment it is created begins counting
 *        before the rest of the program is ready, and the first event arrives at a time nobody
 *        chose.
 */
TEST(TimerDriver, InitStoresTheTargetAndStartsOff)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 250U)), 0U);

    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, TargetOffset)), 250U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 0U);
    EXPECT_EQ(static_cast<unsigned>(mcu.data(Timer + RunningOffset)), 0U);
}

/**
 * @brief A target of zero is refused, because it can never be reached.
 *
 *        A count that starts at zero and is compared against zero either fires on every single
 *        interrupt or never fires at all, depending on where in the subroutine you compare. Both
 *        are wrong and neither is obviously wrong, so the value is rejected instead.
 */
TEST(TimerDriver, InitRejectsATargetOfZero)
{
    avrsim::Mcu mcu{HexPath};
    EXPECT_EQ(static_cast<unsigned>(init(mcu, 0U)), 1U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, TargetOffset)), 0U);
}

/**
 * @brief A 16-bit target survives being stored and read back.
 *
 *        1000 interrupts is a second at 1 kHz, which is the whole reason the field is two bytes.
 *        A driver that stored only the low byte would work perfectly up to 255.
 */
TEST(TimerDriver, TargetIsSixteenBitsWide)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 1000U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, TargetOffset)), 1000U);

    init(mcu, 60000U);
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, TargetOffset)), 60000U);
}

/**
 * @brief on and off switch it, and enabled reports which.
 */
TEST(TimerDriver, OnOffAndEnabled)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 10U);

    EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_enabled")), 0U);
    call(mcu, "timer_on");
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_enabled")), 1U);
    call(mcu, "timer_off");
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_enabled")), 0U);
}

/**
 * @brief Switching off clears the count, so restarting begins a whole period.
 *
 *        The alternative, leaving the count where it was, means a timer switched off and on again
 *        fires almost immediately, which is not what "start it again" means to anybody.
 */
TEST(TimerDriver, OffClearsTheCount)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 10U);
    call(mcu, "timer_on");
    for (int tick{0}; tick < 5; ++tick)
    {
        call(mcu, "timer_tick");
    }
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 5U);

    call(mcu, "timer_off");
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 0U);
}

/**
 * @brief A disabled timer counts nothing and never fires.
 */
TEST(TimerDriver, CountingDoesNothingWhileOff)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 3U);

    for (int tick{0}; tick < 10; ++tick)
    {
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 0U);
    }
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 0U);
}

/**
 * @brief It fires on the target-th call and not before, then starts again.
 *
 *        The single most important test here. A target of 4 means the fourth call returns 1 and
 *        the three before it return 0; firing on the third or the fifth is an off-by-one that
 *        shows up as a rate 25% wrong.
 */
TEST(TimerDriver, FiresOnTheTargetCall)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 4U);
    call(mcu, "timer_on");

    for (int period{0}; period < 3; ++period)
    {
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 0U);
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 0U);
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 0U);
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 1U);
    }
}

/**
 * @brief After firing, the count starts from zero rather than from one.
 *
 *        So every period is the same length. A driver that clears the count *before* the compare
 *        rather than after, or that resets it to 1, gives a first period of the right length and
 *        every one after it off by one.
 */
TEST(TimerDriver, CountRestartsAtZero)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 4U);
    call(mcu, "timer_on");

    for (int tick{0}; tick < 4; ++tick)
    {
        call(mcu, "timer_tick");
    }
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 0U);

    call(mcu, "timer_tick");
    EXPECT_EQ(static_cast<unsigned>(field(mcu, Timer, CountOffset)), 1U);
}

/**
 * @brief A target of one fires on every call.
 *
 *        The smallest legal target, and the one where an off-by-one is a factor of two rather
 *        than a percentage.
 */
TEST(TimerDriver, ATargetOfOneFiresEveryTime)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 1U);
    call(mcu, "timer_on");

    for (int tick{0}; tick < 5; ++tick)
    {
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 1U);
    }
}

/**
 * @brief A 16-bit target really counts past 255.
 *
 *        A driver comparing only the low bytes fires 300 times too often here, and passes every
 *        test above.
 */
TEST(TimerDriver, CountsPastTwoHundredAndFiftyFive)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 300U);
    call(mcu, "timer_on");

    for (int tick{0}; tick < 299; ++tick)
    {
        EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 0U);
    }
    EXPECT_EQ(static_cast<unsigned>(call(mcu, "timer_tick")), 1U);
}

/**
 * @brief Two timers at different rates from the same interrupt do not interfere.
 *
 *        The whole reason this is a structure rather than a global. One hardware timer, two
 *        events, two rates.
 */
TEST(TimerDriver, TwoTimersAreIndependent)
{
    avrsim::Mcu mcu{HexPath};
    init(mcu, 2U, Timer);
    init(mcu, 3U, Timer2);
    call(mcu, "timer_on", Timer);
    call(mcu, "timer_on", Timer2);

    // Six ticks: the first fires three times, the second twice.
    int first{0};
    int second{0};
    for (int tick{0}; tick < 6; ++tick)
    {
        first += call(mcu, "timer_tick", Timer);
        second += call(mcu, "timer_tick", Timer2);
    }
    EXPECT_EQ(first, 3);
    EXPECT_EQ(second, 2);
}

#endif // defined(HAVE_TIMER) && defined(DRIVERS_HEX)
