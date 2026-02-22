; test_hl.asm - Test program for H/L register CPU
; Tests: LDA #imm, LDB #imm, ADD, OUT A, HLT

.org 0x0000

    LDA #10        ; A = 10
    LDB #20        ; B = 20
    ADD            ; A = A + B = 30
    OUT A          ; Output 30
    LDA #0xFF      ; A = 255
    LDB #0x01      ; B = 1
    ADD            ; A = 0 (overflow), flags: Z=1, C=1
    OUT A          ; Output 0
    HLT
