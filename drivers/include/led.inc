;********************************************************************************
;* @file Field offsets of the LED structure, and its size.
;*
;*       typedef struct
;*       {
;*           volatile uint8_t* pin_reg;
;*           volatile uint8_t* dir_reg;
;*           volatile uint8_t* port_reg;
;*           uint8_t pin;
;*       } led_t;
;********************************************************************************
.ifndef LED_INC
.equ LED_INC = 1

.equ LED_PIN_REG  = 0 ; Data space address of PINx, low byte first.
.equ LED_DIR_REG  = 2 ; Data space address of DDRx.
.equ LED_PORT_REG = 4 ; Data space address of PORTx.
.equ LED_PIN      = 6 ; Bit number within the port, 0 to 7. Not the Arduino pin number.
.equ LED_SIZE     = 7 ; Size of the LED structure in bytes.

.endif
