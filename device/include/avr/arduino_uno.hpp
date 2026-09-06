/**
 * @file Arduino Uno definitions.
 */
#pragma once

#include <cstdint>

#include "avr/atmega328p.hpp"

namespace avr::arduino_uno
{
/** The number of digital pins this course uses, numbered 0 upwards. */
inline constexpr std::uint8_t PinCount{14U};

/** Pins 0 to 7 are port D, bits 0 to 7. */
inline constexpr std::uint8_t PortDPins{8U};

/** Pins 8 to 13 are port B, bits 0 to 5. Bits 6 and 7 of port B carry the crystal. */
inline constexpr std::uint8_t PortBPins{6U};

/** The pin with an LED already soldered to it, which is why every example uses it. */
inline constexpr std::uint8_t LedPin{13U};

/** The port bit that pin is, which is the number the driver actually shifts by. */
inline constexpr std::uint8_t LedBit{5U};

/** The lowest pin on port B, and so the cheapest one for the driver to compute a mask for. */
inline constexpr std::uint8_t FirstPortBPin{8U};

} // namespace avr::arduino_uno
