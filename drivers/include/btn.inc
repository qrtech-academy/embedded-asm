;********************************************************************************
;* @file Field offsets of the button structure, and its size.
;*
;*       typedef struct
;*       {
;*           volatile uint8_t* pin_reg;
;*           volatile uint8_t* dir_reg;
;*           volatile uint8_t* port_reg;
;*           volatile uint8_t* pcmsk_reg;
;*           uint8_t pcie_bit;
;*           uint8_t pin;
;*       } btn_t;
;********************************************************************************
.ifndef BTN_INC
.equ BTN_INC = 1

.equ BTN_PIN_REG   = 0  ; Data space address of PINx, low byte first.
.equ BTN_DIR_REG   = 2  ; Data space address of DDRx.
.equ BTN_PORT_REG  = 4  ; Data space address of PORTx.
.equ BTN_PCMSK_REG = 6  ; Data space address of PCMSK0 for port B, PCMSK2 for port D.
.equ BTN_PCIE_BIT  = 8  ; Bit number in PCICR: PCIE0 for port B, PCIE2 for port D.
.equ BTN_PIN       = 9  ; Bit number within the port, 0 to 7. Not the Arduino pin number.
.equ BTN_SIZE      = 10 ; Size of the button structure in bytes.

.endif
