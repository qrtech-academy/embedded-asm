/**
 * @file The driver structures' field offsets and sizes, as the C++ side sees them.
 */
#pragma once

#include <cstdint>

namespace avr::drivers
{
/** Data space address of the LED's PINx pointer, low byte first. */
inline constexpr std::uint16_t LedPinReg{0U};

/** Data space address of the LED's DDRx pointer. */
inline constexpr std::uint16_t LedDirReg{2U};

/** Data space address of the LED's PORTx pointer. */
inline constexpr std::uint16_t LedPortReg{4U};

/** The LED's bit number within its port. */
inline constexpr std::uint16_t LedPin{6U};

/** Bytes one LED structure occupies. */
inline constexpr std::uint16_t LedSize{7U};

/** Data space address of the button's PINx pointer. */
inline constexpr std::uint16_t BtnPinReg{0U};

/** Data space address of the button's DDRx pointer. */
inline constexpr std::uint16_t BtnDirReg{2U};

/** Data space address of the button's PORTx pointer. */
inline constexpr std::uint16_t BtnPortReg{4U};

/** Data space address of the button's pin change mask register. */
inline constexpr std::uint16_t BtnPcmskReg{6U};

/** The button's bit number in PCICR. */
inline constexpr std::uint16_t BtnPcieBit{8U};

/** The button's bit number within its port. */
inline constexpr std::uint16_t BtnPin{9U};

/** Bytes one button structure occupies. */
inline constexpr std::uint16_t BtnSize{10U};

/** The software timer's target: interrupts that make one event, low byte first. Never zero. */
inline constexpr std::uint16_t TimerTarget{0U};

/** The software timer's count of interrupts since its last event, low byte first. */
inline constexpr std::uint16_t TimerCount{2U};

/** Whether the software timer is counting at all: 0 or 1. */
inline constexpr std::uint16_t TimerRunning{4U};

/** Bytes one software timer structure occupies. */
inline constexpr std::uint16_t TimerSize{5U};

/** Bytes a 16-bit pointer field occupies. */
inline constexpr std::uint16_t PointerSize{2U};

/** Bytes a byte-wide field occupies. */
inline constexpr std::uint16_t ByteSize{1U};

/** Bytes a 16-bit counter field occupies. The same two as a pointer, for a different reason. */
inline constexpr std::uint16_t WordSize{2U};

} // namespace avr::drivers
