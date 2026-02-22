; test_jmp.asm - Test JMP and conditional jumps
.org 0x0000

    JMP main        ; Jump over data area

.org 0x0010
main:
    LDA #0xAA       ; A = 0xAA (170)
    OUT A           ; Output 170

    LDA #5          ; A = 5
    LDB #3          ; B = 3
    CMP             ; Compute A-B = 2, Z=0 (not zero)
    JNZ nonzero     ; Should jump (Z=0)
    LDA #0xFF       ; SKIPPED
    OUT A           ; SKIPPED
nonzero:
    LDA #0xBB       ; A = 0xBB (187)
    OUT A           ; Output 187

    LDA #7          ; A = 7
    LDB #7          ; B = 7
    CMP             ; A-B = 0, Z=1
    JZ zero         ; Should jump (Z=1)
    LDA #0xFF       ; SKIPPED
    OUT A           ; SKIPPED
zero:
    LDA #0xCC       ; A = 0xCC (204)
    OUT A           ; Output 204
    HLT
