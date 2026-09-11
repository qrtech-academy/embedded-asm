/**
 * @brief Integration tests for drivers/app/main.asm, run in the simulator.
 *
 *        Guarded by three flags at once, and the third one matters. HAVE_APP says a program
 *        exists in drivers/app; HAVE_LED and HAVE_BTN say the drivers its handler is built
 *        out of exist. The program is not new in L03: L01 puts a stack pointer and a call in
 *        it, and that program is complete and correct and has no handler in it at all. Testing
 *        it for one would report failures at a reader who has done everything right.
 *
 *        HAVE_BTN is what says otherwise. The handler cannot exist before `btn.asm` does,
 *        because it calls `btn_pressed`, so the button driver is the honest marker for "the
 *        program this file is about", and a filename never was.
 *
 *        Every other assembly test in this course calls one subroutine and looks at what came
 *        back. These cannot: **an interrupt is not something you can call.** It arrives, or it
 *        does not, and the only way to find out which is to load the whole program, let it run,
 *        change a pin from outside, and see what the program does about it.
 *
 *        So this is the one file that tests the parts a unit test cannot reach: that the vector
 *        table entry points at your handler, that `sei` ran, that the handler reads the button
 *        rather than assuming, and that it ends with `reti` rather than `ret`. None of those is
 *        visible from inside a subroutine, and all four are wrong in real programs.
 *
 *        What is deliberately not here is a cycle count. From L02 onwards the suites check the
 *        relationships a specification forces and leave the constants alone, and a handler is
 *        the most personal routine in the library: yours saves the registers yours uses. A test
 *        asserting "your handler costs 104 cycles" would be pinning your instruction sequence,
 *        which is the exercise's job and not this file's.
 */
#if defined(HAVE_APP) && defined(APP_HEX) && defined(HAVE_LED) && defined(HAVE_BTN)

#include <cstdint>

#include "avrsim/mcu.hpp"
#include "qacademy/test/test.hpp"

namespace
{
/** The whole program, whose path the makefile passes in. */
constexpr const char* AppPath{APP_HEX};

/** Data space address of PORTB, which is where the LED's state actually lives. */
constexpr std::uint16_t PortB{0x25U};

/** Data space address of DDRB. */
constexpr std::uint16_t DdrB{0x24U};

/** The LED is Arduino pin 13, which is PB5. The button is pin 12, which is PB4. */
constexpr unsigned LedBit{5U};
constexpr unsigned ButtonBit{4U};

/** Long enough for the setup to finish, and for any handler in this course to run twice over. */
constexpr std::uint64_t Settle{20000U};

/**
 * @brief Whether the LED's output bit is set.
 *
 *        Read from PORTB rather than from the pin log, because it is the value the driver
 *        wrote and is true whatever the pin is doing electrically.
 *
 * @param[in] mcu The machine.
 *
 * @return True if the LED is on.
 */
[[nodiscard]] bool ledIsOn(const avrsim::Mcu& mcu)
{
    return (mcu.data(PortB) & (1U << LedBit)) != 0U;
}

/**
 * @brief Start the program with the button released, and run until setup has finished.
 *
 *        The button is driven high before the first cycle on purpose. A real board has the
 *        pull-up holding that pin high from the moment the program enables it, and a test that
 *        left the pin undriven would be starting from a state the hardware never has.
 *
 * @param[in] mcu The machine.
 */
void startUp(avrsim::Mcu& mcu)
{
    mcu.drive('B', ButtonBit, true);
    mcu.run(Settle);
}

/**
 * @brief Press the button, let the program deal with it, and release it.
 *
 *        A press here is a momentary pull to ground, which is what the switch on a breadboard
 *        is. Nothing holds the pin down afterwards, so the pull-up takes it back up on its own
 *        and the release edge arrives whether or not this function asks for it; measured, the
 *        pin returns high on the same cycle the handler writes to the port. The release is
 *        driven anyway, because a test should say what it means rather than rely on that.
 *
 *        Which means a single press produces **two** interrupts, one per edge. That is not the
 *        harness being unrealistic; it is the thing Appendix C.7 warns about, arriving early.
 *
 * @param[in] mcu The machine.
 */
void pressAndRelease(avrsim::Mcu& mcu)
{
    mcu.drive('B', ButtonBit, false);
    mcu.run(Settle);
    mcu.drive('B', ButtonBit, true);
    mcu.run(Settle);
}
} // namespace

/**
 * @brief The program links, loads, and defines the handler by the name the specification gives.
 *
 *        Checked first and on its own. A handler under any other name is invisible from
 *        outside, and the measurement exercise in Appendix D finds it by this name too.
 */
TEST(App, DefinesItsHandler)
{
    avrsim::Mcu mcu{AppPath};
    EXPECT_TRUE(mcu.has("isr_pcint0"));
}

/**
 * @brief Setup makes the LED an output and leaves it off.
 *
 *        Before any interrupt, and before anything interesting. If this fails, the program is
 *        not reaching the end of its setup, and every test below would fail for that reason
 *        rather than for the reason it is about.
 */
TEST(App, SetupLeavesTheLedOffAndDriven)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    EXPECT_EQ(static_cast<unsigned>(mcu.data(DdrB) & (1U << LedBit)), 1U << LedBit);
    EXPECT_FALSE(ledIsOn(mcu));
}

/**
 * @brief Setup enables interrupts, and does it once at the end rather than in a driver.
 */
TEST(App, SetupEnablesInterrupts)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    EXPECT_TRUE(mcu.interruptsEnabled());
}

/**
 * @brief A press reaches the handler and toggles the LED.
 *
 *        The whole point of the file. Nothing calls the handler here: the pin changes, and if
 *        the vector table entry is missing, points at the wrong place, or was written as a
 *        two-word `jmp` into a one-word slot, the LED does not move and nothing else reports
 *        anything at all.
 */
TEST(App, APressTogglesTheLed)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);
    EXPECT_FALSE(ledIsOn(mcu));

    mcu.drive('B', ButtonBit, false);
    mcu.run(Settle);

    EXPECT_TRUE(ledIsOn(mcu));
}

/**
 * @brief Releasing the button interrupts too, and must not toggle anything.
 *
 *        A pin change interrupt fires on both edges, so a handler that toggles unconditionally
 *        toggles twice per press and appears to do nothing at all. That is why the
 *        specification has the handler ask the button whether it is pressed rather than assume.
 *
 *        The button pin is watched as well as the LED, so that this test cannot pass by the
 *        release never happening. Two edges on the button, one on the LED: that pair is the
 *        whole assertion, and neither half means much without the other.
 */
TEST(App, ReleasingDoesNotToggle)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    auto& button = mcu.watch('B', ButtonBit);
    auto& led    = mcu.watch('B', LedBit);
    pressAndRelease(mcu);

    EXPECT_TRUE(button.count() >= 2U);
    EXPECT_EQ(led.count(), 1U);
    EXPECT_TRUE(ledIsOn(mcu));
}

/**
 * @brief A second press toggles it back, which is what `reti` buys you.
 *
 *        A handler ending in `ret` returns correctly and passes every test above: the first
 *        press works perfectly. What `ret` does not do is set the global interrupt enable
 *        again, so no interrupt is ever served afterwards, and the LED never moves again. It is
 *        a one-letter difference that turns a program into one that works exactly once.
 */
TEST(App, TheSecondPressStillArrives)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    pressAndRelease(mcu);
    EXPECT_TRUE(ledIsOn(mcu));

    pressAndRelease(mcu);
    EXPECT_FALSE(ledIsOn(mcu));

    pressAndRelease(mcu);
    EXPECT_TRUE(ledIsOn(mcu));
}

/**
 * @brief With nobody pressing anything, the LED stays where setup left it.
 *
 *        Half a second of simulated time. A program whose main loop touches the LED, or whose
 *        handler runs on a flag nobody cleared, fails here and passes everything above.
 */
TEST(App, NothingHappensOnItsOwn)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    auto& led = mcu.watch('B', LedBit);
    mcu.run(8000000U);

    EXPECT_EQ(led.count(), 0U);
    EXPECT_FALSE(ledIsOn(mcu));
}

/**
 * @brief The pin follows the register, so the LED is genuinely driven.
 *
 *        PORTB says what the driver asked for; the pin log says what the outside world would
 *        see. They agree only if `led_init` actually set the direction bit, and a program that
 *        skipped that would light nothing on a real board while passing every test that reads
 *        PORTB alone.
 */
TEST(App, ThePinFollowsTheRegister)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);

    auto& led = mcu.watch('B', LedBit);
    mcu.drive('B', ButtonBit, false);
    mcu.run(Settle);

    EXPECT_EQ(led.count(), 1U);
    EXPECT_TRUE(led.level());
}

/**
 * @brief The stack stays in the part of SRAM the program left for it.
 *
 *        A bound rather than a figure: an interrupt landing on top of two nested calls costs a
 *        handful of bytes, and anything using more than sixty-four of them is a handler calling
 *        itself, a stack pointer that was never initialised, or a `ret` with nothing pushed.
 *        Nothing on this device would report any of the three.
 */
TEST(App, TheStackStaysWhereItShould)
{
    avrsim::Mcu mcu{AppPath};
    startUp(mcu);
    pressAndRelease(mcu);

    // Not NoStackMark: the program ran, so the watermark is a real address rather than the
    // sentinel the harness returns when nothing has touched the stack at all.
    EXPECT_TRUE(mcu.lowestStackPtr() != avrsim::Mcu::NoStackMark);
    EXPECT_TRUE(mcu.lowestStackPtr() > 0x08BFU);
    EXPECT_TRUE(mcu.lowestStackPtr() <= 0x08FFU);
}

#endif // defined(HAVE_APP) && defined(HAVE_LED) && defined(HAVE_BTN)
