/**
 * @file ATmega328P definitions.
 */
#pragma once

#include <array>
#include <cstdint>

/**
 * @brief Pinned constants for the ATmega328P.
 */
namespace avr::atmega328p
{
/** The Arduino Uno's crystal, and this course's assumption everywhere. */
inline constexpr std::uint32_t ArduinoUnoClockHz{16000000U};

/** The factory default: the internal 8 MHz oscillator divided by 8. */
inline constexpr std::uint32_t FactoryDefaultClockHz{1000000U};

// ---------------------------------------------------------------------------------------
// Data space. One flat address space, in this order.
// ---------------------------------------------------------------------------------------

/** Data space address of r0. The register file really is addressable. */
inline constexpr std::uint16_t RegisterFileBase{0x0000U};

/** How many general-purpose registers there are. */
inline constexpr std::uint16_t RegisterCount{32U};

/** Lowest register reachable by ldi, andi, ori, subi and cpi. */
inline constexpr std::uint8_t FirstImmediateRegister{16U};

/** Data space address of the first I/O register, which is I/O address 0x00. */
inline constexpr std::uint16_t IoBase{0x0020U};

/** How many I/O registers in and out can reach. */
inline constexpr std::uint16_t IoCount{64U};

/** What to add to an I/O address to get a data space address. */
inline constexpr std::uint16_t IoOffset{0x0020U};

/** Data space address of the first extended I/O register, reachable only by lds and sts. */
inline constexpr std::uint16_t ExtendedIoBase{0x0060U};

/** How many extended I/O registers there are. */
inline constexpr std::uint16_t ExtendedIoCount{160U};

/** Data space address of the first byte of internal SRAM. */
inline constexpr std::uint16_t SramBase{0x0100U};

/** How many bytes of internal SRAM the device has. */
inline constexpr std::uint16_t SramSize{2048U};

/** Data space address of the last byte of internal SRAM, and the stack's starting point. */
inline constexpr std::uint16_t RamEnd{0x08FFU};

// ---------------------------------------------------------------------------------------
// Program memory. Word addresses, because that is what the vector table and .org use.
// ---------------------------------------------------------------------------------------

/** How many 16-bit words of flash the device has. */
inline constexpr std::uint32_t FlashWords{16384U};

/** How many interrupt vectors the vector table holds. */
inline constexpr std::uint32_t VectorCount{26U};

/** How many words each vector occupies, because jmp is two words on a part this size. */
inline constexpr std::uint32_t VectorWords{2U};

/** Word address of the reset vector. */
inline constexpr std::uint32_t ResetVector{0x0000U};

/**
 * @brief The interrupt vectors, in the order the table holds them.
 */
enum class Vector : std::uint8_t
{
    Reset       = 0U,
    Int0        = 1U,
    Int1        = 2U,
    PcInt0      = 3U,
    PcInt1      = 4U,
    PcInt2      = 5U,
    Wdt         = 6U,
    Timer2CompA = 7U,
    Timer2CompB = 8U,
    Timer2Ovf   = 9U,
    Timer1Capt  = 10U,
    Timer1CompA = 11U,
    Timer1CompB = 12U,
    Timer1Ovf   = 13U,
    Timer0CompA = 14U,
    Timer0CompB = 15U,
    Timer0Ovf   = 16U,
    SpiStc      = 17U,
    UsartRx     = 18U,
    UsartUdre   = 19U,
    UsartTx     = 20U,
    Adc         = 21U,
    EeReady     = 22U,
    AnalogComp  = 23U,
    Twi         = 24U,
    SpmReady    = 25U,
};

/** How many bytes of EEPROM the device has. */
inline constexpr std::uint16_t EepromSize{1024U};

/** Data space address of PINB. DDRB and PORTB follow it. */
inline constexpr std::uint16_t PinB{0x0023U};

/** Data space address of PINC. */
inline constexpr std::uint16_t PinC{0x0026U};

/** Data space address of PIND. */
inline constexpr std::uint16_t PinD{0x0029U};

/** Offset from a port's PIN register to its DDR register. */
inline constexpr std::uint16_t DirectionOffset{1U};

/** Offset from a port's PIN register to its PORT register. */
inline constexpr std::uint16_t PortOffset{2U};

/** How many bytes apart two neighbouring ports' registers are. */
inline constexpr std::uint16_t PortStride{3U};

/** Data space address of the stack pointer's low byte. SPH is the byte above it. */
inline constexpr std::uint16_t Spl{0x005DU};

/** Data space address of the status register. */
inline constexpr std::uint16_t Sreg{0x005FU};

/** Number of timer prescalers. */
inline constexpr std::uint32_t TimerPscCount{5U};

/** Timer prescaler list. */
using TimerPscList = std::array<std::uint16_t, TimerPscCount>;

/** The prescaler ratios the clock select bits select, smallest first. */
inline constexpr TimerPscList TimerPrescalers{1U, 8U, 64U, 256U, 1024U};

/** How many values an 8-bit counter holds. Timer0 and Timer2. */
inline constexpr std::uint32_t Timer8BitValues{256U};

/** How many values a 16-bit counter holds. Timer1. */
inline constexpr std::uint32_t Timer16BitValues{65536U};

/** Data space address of TCCR1A. TCCR1B is the byte above it. */
inline constexpr std::uint16_t Tccr1a{0x0080U};

/** Data space address of TCNT1's low byte. The high byte is above it. */
inline constexpr std::uint16_t Tcnt1{0x0084U};

/** Data space address of OCR1A's low byte. The high byte is above it. */
inline constexpr std::uint16_t Ocr1a{0x0088U};

/** Data space address of TIMSK1. In extended I/O, so lds and sts only. */
inline constexpr std::uint16_t Timsk1{0x006FU};

/** Bit in TCCR1B that selects CTC mode, with WGM13, WGM11 and WGM10 clear. */
inline constexpr std::uint8_t Wgm12{3U};

/** Lowest of the three clock select bits in TCCR1B. */
inline constexpr std::uint8_t Cs10{0U};

/** Bit in TIMSK1 that lets a compare match raise an interrupt. */
inline constexpr std::uint8_t Ocie1a{1U};

/** Data space address of WDTCSR. In extended I/O, so lds and sts only. */
inline constexpr std::uint16_t Wdtcsr{0x0060U};

/** Data space address of MCUSR, which says what caused the last reset. */
inline constexpr std::uint16_t Mcusr{0x0054U};

/** Data space address of SMCR, which selects a sleep mode and enables sleeping. */
inline constexpr std::uint16_t Smcr{0x0053U};

/** Bit in WDTCSR that enables the system reset. */
inline constexpr std::uint8_t Wde{3U};

/** Bit in WDTCSR that opens the four-cycle window in which the rest may be changed. */
inline constexpr std::uint8_t Wdce{4U};

/** Bit in WDTCSR that lets a timeout raise an interrupt instead of resetting. */
inline constexpr std::uint8_t Wdie{6U};

/** The three low timeout selector bits, at bits 2 to 0 of WDTCSR. */
inline constexpr std::uint8_t Wdp0{0U};

/** The fourth timeout selector bit, which is at bit 5 rather than bit 3. */
inline constexpr std::uint8_t Wdp3{5U};

/** Bit in MCUSR that is set when the watchdog caused the last reset. */
inline constexpr std::uint8_t Wdrf{3U};

/** Bit in SMCR that must be set for the sleep instruction to do anything. */
inline constexpr std::uint8_t Se{0U};

/** Lowest of the three mode selector bits in SMCR, which occupy bits 3 to 1. */
inline constexpr std::uint8_t Sm0{1U};

/** The number of sleep modes SM2:SM0 selects between. */
inline constexpr std::uint8_t SleepModeCount{6U};

/** Sleep mode list. */
using SleepModeList = std::array<std::uint32_t, SleepModeCount>;

/** Cycles the oscillator needs to restart, per sleep mode, in SM2:SM0 order. */
inline constexpr SleepModeList SleepModes{0U, 0U, 16384U, 16384U, 6U, 6U};

} // namespace avr::atmega328p
