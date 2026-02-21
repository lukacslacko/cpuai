// multiply_asm.mc - Highly optimized 8-bit to 16-bit shift-and-add multiplier using inline assembly
fun multiply(multiplier, multiplicand) {
    var result_lo = 0;
    var result_hi = 0;
    var mc_lo = multiplicand;
    var mc_hi = 0;
    var i = 8;
    
    asm("
__mult_loop:
        ; Shift multiplier right, lowest bit goes into Carry flag
        LDA [0x{multiplier}]
        SHR
        STA [0x{multiplier}]
        JNC skip_add
        
        ; If Carry was 1, add multiplicand to result
        LDA [0x{result_lo}]
        LDB [0x{mc_lo}]
        ADD
        STA [0x{result_lo}]
        
        ; Manual add-with-carry for high byte
        JNC no_carry_res
        LDA [0x{result_hi}]
        LDB #1
        ADD
        STA [0x{result_hi}]
no_carry_res:
        LDA [0x{result_hi}]
        LDB [0x{mc_hi}]
        ADD
        STA [0x{result_hi}]
        
skip_add:
        ; Shift multiplicand left by 1 (16-bit shift)
        LDA [0x{mc_lo}]
        SHL
        STA [0x{mc_lo}]
        JNC no_carry_mc
        ; If lo byte shift overflowed, shift hi byte and add 1
        LDA [0x{mc_hi}]
        SHL
        LDB #1
        ADD
        STA [0x{mc_hi}]
        JMP mc_shifted
no_carry_mc:
        LDA [0x{mc_hi}]
        SHL
        STA [0x{mc_hi}]
mc_shifted:

        ; Loop 8 times
        LDA [0x{i}]
        LDB #1
        SUB
        STA [0x{i}]
        JNZ __mult_loop
    ");
    
    out(result_hi);
    return result_lo;
}

var x = 7;
var y = 6;
var product_lo = multiply(x, y);
out(product_lo);  // expected output: HI=0, LO=42
