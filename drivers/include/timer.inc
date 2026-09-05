;********************************************************************************
;* @file Field offsets of the software timer structure, and its size.
;*
;*       typedef struct
;*       {
;*           uint16_t target;
;*           uint16_t count;
;*           uint8_t running;
;*       } timer_t;
;********************************************************************************
.ifndef TIMER_INC
.equ TIMER_INC = 1

.equ TIMER_TARGET  = 0 ; Target count, low byte first. Never 0.
.equ TIMER_COUNT   = 2 ; Internal counter, low byte first.
.equ TIMER_RUNNING = 4 ; True if the timer is running, false otherwise.
.equ TIMER_SIZE    = 5 ; Size of the timer structure in bytes.

.endif
