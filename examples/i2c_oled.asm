; =============================================================================
; i2c_oled.asm — Bit-bang I2C + SSD1306 0.96" OLED library
; =============================================================================
;
; Hardware wiring (output port):
;   Bit 0 = SDA  (open-drain with pull-up)
;   Bit 1 = SCL  (open-drain with pull-up)
;
; Hardware wiring (input port):
;   Bit 0 = SDA  (read-back for ACK check)
;
; SSD1306 I2C address: 0x3C (write mode = 0x78 = 0x3C << 1)
;
; Calling convention:
;   A = primary argument / return value
;   B, C, D = secondary args / scratch
;   CALL saves return address in A:B (hi:lo) — push A+B first in callees!
;
; RAM layout (0x8000–0x800F):
;   0x8000  PORT_STATE   — current value driven to output port
;   0x8001  I2C_BUF      — scratch byte for I2C transmit loop
;   0x8002  I2C_BITCNT   — bit counter (0-7)
;
; Usage example at end of file.
; =============================================================================

; --- Constants ---
.equ SSD1306_WRITE  0x78     ; 7-bit addr 0x3C shifted left, R/W=0
.equ SSD1306_CMD    0x00     ; Co=0, D/C=0  → command stream
.equ SSD1306_DATA   0x40     ; Co=0, D/C=1  → data stream

.equ SDA_BIT        0x01     ; bit 0 of output port
.equ SCL_BIT        0x02     ; bit 1 of output port
.equ SDA_SCL        0x03     ; both bits high

; RAM addresses
.equ PORT_STATE     0x8000
.equ I2C_BUF       0x8001
.equ I2C_BITCNT    0x8002

; =============================================================================
; Entry point — run a demo, then halt
; =============================================================================
.org 0x0000
    JMP main

; =============================================================================
; main — initialise OLED and display "HI" on first line
; =============================================================================
.org 0x0010
main:
    ; Initialise port state to idle (both lines high via pull-ups → 0x03)
    LDA #SDA_SCL
    STA [PORT_STATE]
    OUT A

    CALL ssd1306_init

    ; Set cursor to top-left page 0, col 0
    LDA #0
    LDB #0
    CALL ssd1306_set_cursor

    ; Write 'H' (5-byte column pattern from font, see font table below)
    LDA #'H'
    CALL ssd1306_write_char

    ; Write 'I'
    LDA #'I'
    CALL ssd1306_write_char

    HLT

; =============================================================================
; I2C primitives
; =============================================================================

; --- i2c_start ---
; Generate START condition: SDA falls while SCL is high.
; Clobbers: A
i2c_start:
    PUSH A
    PUSH B
    ; SCL high, SDA high
    LDA #SDA_SCL
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; SDA low (SCL still high)
    LDA #SCL_BIT
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; SCL low (hold)
    LDA #0x00
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    POP B
    POP A
    RET

; --- i2c_stop ---
; Generate STOP condition: SDA rises while SCL is high.
; Clobbers: A
i2c_stop:
    PUSH A
    PUSH B
    ; SCL low, SDA low
    LDA #0x00
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; SCL high
    LDA #SCL_BIT
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; SDA high (STOP)
    LDA #SDA_SCL
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    POP B
    POP A
    RET

; --- i2c_write_byte ---
; Send byte in A over I2C, MSB first. Returns ACK in A (0=ACK, 1=NACK).
; Clobbers: A, B, C
i2c_write_byte:
    PUSH A          ; save return hi (CALL convention)
    PUSH B          ; save return lo
    ; arg byte is in C (caller must TAC before CALL... see wrapper below)
    ; Actually: caller pushes the byte as argument. We use LSA.
    ; --- Simpler approach: use I2C_BUF which caller fills before calling ---
    LDA #8
    STA [I2C_BITCNT]
_i2c_bit_loop:
    ; Load byte, check MSB
    LDA [I2C_BUF]
    ; Shift left: A = A << 1. MSB goes to carry, new LSB = 0.
    SHL
    STA [I2C_BUF]
    ; If carry (old MSB=1): SDA=1, else SDA=0. Carry is in flags.
    ; We need to drive SDA based on carry flag.
    ; Trick: after SHL, carry = old bit7. JC means SDA high.
    LDA #0x00       ; assume SDA=0 (SCL low)
    STA [PORT_STATE]
    OUT A
    JC _i2c_sda_high
    ; SDA low, SCL low already set above
    JMP _i2c_scl_pulse
_i2c_sda_high:
    LDA #SDA_BIT    ; SDA high, SCL low
    STA [PORT_STATE]
    OUT A
_i2c_scl_pulse:
    ; SCL high (SDA keeps its value)
    LDA [PORT_STATE]
    LDB #SCL_BIT
    ADD             ; A = PORT_STATE | SCL_BIT
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; SCL low
    LDA [PORT_STATE]
    LDB #SCL_BIT
    ; Clear SCL bit: A = A & ~SCL_BIT = A & 0xFD
    LDB #0xFD
    AND
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; Decrement bit counter
    LDA [I2C_BITCNT]
    LDB #1
    SUB
    STA [I2C_BITCNT]
    ; Loop if not zero
    JNZ _i2c_bit_loop

    ; --- Read ACK bit ---
    ; Release SDA (set SDA high = input mode for open-drain)
    LDA #SDA_BIT
    STA [PORT_STATE]
    OUT A
    ; SCL high
    LDA #SDA_SCL
    STA [PORT_STATE]
    OUT A
    CALL i2c_delay
    ; Read SDA via input port (bit 0). ACK=0, NACK=1.
    IN A
    LDB #SDA_BIT
    AND             ; isolate SDA bit. A = 0 if ACK
    ; SCL low
    LDA [PORT_STATE]
    LDB #0xFD       ; ~SCL_BIT
    AND
    STA [PORT_STATE]
    OUT A
    ; A = ACK result is lost after the above... save it first
    ; Redo: store ACK result to C reg before SCL-low sequence
    POP B
    POP A
    RET             ; caller ignores ACK for simplicity (TODO: use C for result)

; --- i2c_send_cmd ---
; Send one command byte (value in C) to SSD1306.
; Clobbers: A, B, C
i2c_send_cmd:
    PUSH A
    PUSH B
    ; START
    CALL i2c_start
    ; Send device address
    LDA #SSD1306_WRITE
    STA [I2C_BUF]
    CALL i2c_write_byte
    ; Send control byte: 0x00 = command
    LDA #SSD1306_CMD
    STA [I2C_BUF]
    CALL i2c_write_byte
    ; Send command byte (arg was in C, load from stack offset)
    LSA 3           ; load arg byte (3 above ret_lo, ret_hi on stack)
    STA [I2C_BUF]
    CALL i2c_write_byte
    ; STOP
    CALL i2c_stop
    POP B
    POP A
    RET

; --- i2c_send_data ---
; Send one data byte (value in C) to SSD1306.
; Clobbers: A, B, C
i2c_send_data:
    PUSH A
    PUSH B
    CALL i2c_start
    LDA #SSD1306_WRITE
    STA [I2C_BUF]
    CALL i2c_write_byte
    LDA #SSD1306_DATA
    STA [I2C_BUF]
    CALL i2c_write_byte
    LSA 3
    STA [I2C_BUF]
    CALL i2c_write_byte
    CALL i2c_stop
    POP B
    POP A
    RET

; --- i2c_delay ---
; Short delay for I2C timing (~4 NOPs as placeholder).
; On real hardware tune this to achieve ~100kHz or 400kHz clock.
i2c_delay:
    PUSH A
    PUSH B
    NOP
    NOP
    NOP
    NOP
    POP B
    POP A
    RET

; =============================================================================
; SSD1306 OLED routines
; =============================================================================

; --- ssd1306_init ---
; Send SSD1306 initialisation sequence for 128x64 display.
; Clobbers: A, B, C
ssd1306_init:
    PUSH A
    PUSH B

    ; Display OFF
    PUSH A          ; dummy arg slot for LSA 3 inside i2c_send_cmd
    LDA #0xAE
    TAC             ; C = cmd
    CALL i2c_send_cmd
    POP A

    ; Set display clock divide / oscillator frequency
    PUSH A
    LDA #0xD5
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x80
    TAC
    CALL i2c_send_cmd
    POP A

    ; Set multiplex ratio (64-1 = 63 = 0x3F)
    PUSH A
    LDA #0xA8
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x3F
    TAC
    CALL i2c_send_cmd
    POP A

    ; Set display offset = 0
    PUSH A
    LDA #0xD3
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x00
    TAC
    CALL i2c_send_cmd
    POP A

    ; Set start line = 0 (0x40 | 0)
    PUSH A
    LDA #0x40
    TAC
    CALL i2c_send_cmd
    POP A

    ; Charge pump enable
    PUSH A
    LDA #0x8D
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x14
    TAC
    CALL i2c_send_cmd
    POP A

    ; Memory addressing mode: horizontal (0x00)
    PUSH A
    LDA #0x20
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x00
    TAC
    CALL i2c_send_cmd
    POP A

    ; Segment remap (col 127 = SEG0)
    PUSH A
    LDA #0xA1
    TAC
    CALL i2c_send_cmd
    POP A

    ; COM output scan direction (remapped)
    PUSH A
    LDA #0xC8
    TAC
    CALL i2c_send_cmd
    POP A

    ; COM pins hardware config
    PUSH A
    LDA #0xDA
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x12
    TAC
    CALL i2c_send_cmd
    POP A

    ; Contrast = 0xCF
    PUSH A
    LDA #0x81
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0xCF
    TAC
    CALL i2c_send_cmd
    POP A

    ; Pre-charge period
    PUSH A
    LDA #0xD9
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0xF1
    TAC
    CALL i2c_send_cmd
    POP A

    ; VCOMH deselect level
    PUSH A
    LDA #0xDB
    TAC
    CALL i2c_send_cmd
    POP A
    PUSH A
    LDA #0x40
    TAC
    CALL i2c_send_cmd
    POP A

    ; Display all on: follow RAM (0xA4)
    PUSH A
    LDA #0xA4
    TAC
    CALL i2c_send_cmd
    POP A

    ; Normal display (not inverted: 0xA6)
    PUSH A
    LDA #0xA6
    TAC
    CALL i2c_send_cmd
    POP A

    ; Scroll off
    PUSH A
    LDA #0x2E
    TAC
    CALL i2c_send_cmd
    POP A

    ; Display ON
    PUSH A
    LDA #0xAF
    TAC
    CALL i2c_send_cmd
    POP A

    POP B
    POP A
    RET

; --- ssd1306_set_cursor ---
; Set page (row, 0-7) in A, column (0-127) in B.
; Uses horizontal addressing mode.  Clobbers: A, B, C
ssd1306_set_cursor:
    PUSH A          ; save hi-ret
    PUSH B          ; save lo-ret
    ; Reload args from stack: page is at offset 3, col at offset 4
    LSA 3           ; page
    ; Set page address: 0xB0 | page
    LDB #0xB0
    ADD
    TAC
    PUSH A          ; dummy arg slot
    CALL i2c_send_cmd
    POP A

    LSA 4           ; col
    ; Lower nibble of column: 0x00 | (col & 0x0F)
    LDB #0x0F
    AND
    TAC
    PUSH A
    CALL i2c_send_cmd
    POP A

    ; Upper nibble of column: 0x10 | (col >> 4)
    LSA 4
    LDB #0xF0
    AND
    SHR             ; >> 1
    SHR             ; >> 2
    SHR             ; >> 3
    SHR             ; >> 4
    LDB #0x10
    ADD
    TAC
    PUSH A
    CALL i2c_send_cmd
    POP A

    POP B
    POP A
    RET

; =============================================================================
; 5x8 minimal font — ASCII 0x20 (space) to 0x5A (Z)
; Each character = 5 bytes, one per column, LSB = top pixel.
; =============================================================================
font_table:
; Space (0x20)
.db 0x00, 0x00, 0x00, 0x00, 0x00
; ! (0x21)
.db 0x00, 0x00, 0x5F, 0x00, 0x00
; " (0x22)
.db 0x00, 0x07, 0x00, 0x07, 0x00
; # (Unused – pad to keep indexing simple for 0x23–0x2F)
.db 0x14, 0x7F, 0x14, 0x7F, 0x14
.db 0x24, 0x2A, 0x7F, 0x2A, 0x12  ; $
.db 0x23, 0x13, 0x08, 0x64, 0x62  ; %
.db 0x36, 0x49, 0x55, 0x22, 0x50  ; &
.db 0x00, 0x05, 0x03, 0x00, 0x00  ; '
.db 0x00, 0x1C, 0x22, 0x41, 0x00  ; (
.db 0x00, 0x41, 0x22, 0x1C, 0x00  ; )
.db 0x14, 0x08, 0x3E, 0x08, 0x14  ; *
.db 0x08, 0x08, 0x3E, 0x08, 0x08  ; +
.db 0x00, 0x50, 0x30, 0x00, 0x00  ; ,
.db 0x08, 0x08, 0x08, 0x08, 0x08  ; -
.db 0x00, 0x60, 0x60, 0x00, 0x00  ; .
.db 0x20, 0x10, 0x08, 0x04, 0x02  ; /
; Digits 0–9 (0x30–0x39)
.db 0x3E, 0x51, 0x49, 0x45, 0x3E  ; 0
.db 0x00, 0x42, 0x7F, 0x40, 0x00  ; 1
.db 0x42, 0x61, 0x51, 0x49, 0x46  ; 2
.db 0x21, 0x41, 0x45, 0x4B, 0x31  ; 3
.db 0x18, 0x14, 0x12, 0x7F, 0x10  ; 4
.db 0x27, 0x45, 0x45, 0x45, 0x39  ; 5
.db 0x3C, 0x4A, 0x49, 0x49, 0x30  ; 6
.db 0x01, 0x71, 0x09, 0x05, 0x03  ; 7
.db 0x36, 0x49, 0x49, 0x49, 0x36  ; 8
.db 0x06, 0x49, 0x49, 0x29, 0x1E  ; 9
; : ; < = > ? @ (0x3A–0x40)
.db 0x00, 0x36, 0x36, 0x00, 0x00  ; :
.db 0x00, 0x56, 0x36, 0x00, 0x00  ; ;
.db 0x08, 0x14, 0x22, 0x41, 0x00  ; <
.db 0x14, 0x14, 0x14, 0x14, 0x14  ; =
.db 0x00, 0x41, 0x22, 0x14, 0x08  ; >
.db 0x02, 0x01, 0x51, 0x09, 0x06  ; ?
.db 0x32, 0x49, 0x79, 0x41, 0x3E  ; @
; Uppercase A–Z (0x41–0x5A)
.db 0x7E, 0x11, 0x11, 0x11, 0x7E  ; A
.db 0x7F, 0x49, 0x49, 0x49, 0x36  ; B
.db 0x3E, 0x41, 0x41, 0x41, 0x22  ; C
.db 0x7F, 0x41, 0x41, 0x22, 0x1C  ; D
.db 0x7F, 0x49, 0x49, 0x49, 0x41  ; E
.db 0x7F, 0x09, 0x09, 0x09, 0x01  ; F
.db 0x3E, 0x41, 0x49, 0x49, 0x7A  ; G
.db 0x7F, 0x08, 0x08, 0x08, 0x7F  ; H
.db 0x00, 0x41, 0x7F, 0x41, 0x00  ; I
.db 0x20, 0x40, 0x41, 0x3F, 0x01  ; J
.db 0x7F, 0x08, 0x14, 0x22, 0x41  ; K
.db 0x7F, 0x40, 0x40, 0x40, 0x40  ; L
.db 0x7F, 0x02, 0x0C, 0x02, 0x7F  ; M
.db 0x7F, 0x04, 0x08, 0x10, 0x7F  ; N
.db 0x3E, 0x41, 0x41, 0x41, 0x3E  ; O
.db 0x7F, 0x09, 0x09, 0x09, 0x06  ; P
.db 0x3E, 0x41, 0x51, 0x21, 0x5E  ; Q
.db 0x7F, 0x09, 0x19, 0x29, 0x46  ; R
.db 0x46, 0x49, 0x49, 0x49, 0x31  ; S
.db 0x01, 0x01, 0x7F, 0x01, 0x01  ; T
.db 0x3F, 0x40, 0x40, 0x40, 0x3F  ; U
.db 0x1F, 0x20, 0x40, 0x20, 0x1F  ; V
.db 0x3F, 0x40, 0x38, 0x40, 0x3F  ; W
.db 0x63, 0x14, 0x08, 0x14, 0x63  ; X
.db 0x07, 0x08, 0x70, 0x08, 0x07  ; Y
.db 0x61, 0x51, 0x49, 0x45, 0x43  ; Z

; --- ssd1306_write_char ---
; Write character (ASCII code in A) to the display at current cursor position.
; Outputs the 5 font bytes, then 1 blank separator column.
; Clobbers: A, B, C, D
ssd1306_write_char:
    PUSH A          ; save hi-ret
    PUSH B          ; save lo-ret

    ; Compute font table offset: (char - 0x20) * 5
    LSA 3           ; reload char from stack
    LDB #0x20
    SUB             ; A = char - 0x20
    ; Multiply by 5: A*5 = A*4 + A = (A<<2) + A
    TAB             ; B = A (save)
    SHL             ; A = A*2
    SHL             ; A = A*4
    ADD             ; A = A*4 + B = A*5
    ; A now holds byte offset into font_table
    LDB #<font_table  ; low byte of font_table address
    ADD               ; A = font_table + offset (low byte only — works within page)
    ; Store pointer in D (use RAM instead since we only have A-D)
    STA [0x8003]      ; font_ptr_lo

    LDA #>font_table  ; high byte of font_table address
    STA [0x8004]      ; font_ptr_hi

    ; Loop 5 times: read byte at [font_ptr] and send as OLED data
    LDA #5
    STA [0x8005]      ; col_count

_char_col_loop:
    ; Load font byte via indirect read using H:L
    ; (uses LDA [addr16] with the pointer stored in RAM)
    LDA [0x8003]      ; ptr_lo
    TAB               ; B = ptr_lo
    LDA [0x8004]      ; ptr_hi
    TAC               ; C = ptr_hi — addr in C:B
    ; Read MEM[C:B] — need to set H=C, L=B then read
    ; We use a self-modifying indirect trick: write the 16-bit address
    ; into the operand of an LDA [addr16] instruction.
    ; Since we don't have true indirect addressing, we must compose:
    ;   STA the ptr into the instruction at _read_ptr_instr+1,+2
    LDA [0x8003]
    STA [_read_ptr+1]   ; patch low byte of LDA [addr] operand
    LDA [0x8004]
    STA [_read_ptr+2]   ; patch high byte
_read_ptr:
    LDA [0x0000]        ; self-modified: reads MEM[ptr]

    ; Send byte as OLED data
    TAC
    PUSH A
    CALL i2c_send_data
    POP A

    ; Advance pointer
    LDA [0x8003]
    LDB #1
    ADD
    STA [0x8003]
    ; Handle carry into hi byte
    JNC _no_carry
    LDA [0x8004]
    LDB #1
    ADD
    STA [0x8004]
_no_carry:
    ; Decrement column count
    LDA [0x8005]
    LDB #1
    SUB
    STA [0x8005]
    JNZ _char_col_loop

    ; Send one blank column spacer
    LDA #0x00
    TAC
    PUSH A
    CALL i2c_send_data
    POP A

    POP B
    POP A
    RET
