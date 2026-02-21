// multiply.mc - Multiply two 8-bit numbers to get a 16-bit result using shift-and-add
fun multiply(multiplier, multiplicand) {
    var result_lo = 0;
    var result_hi = 0;
    var mc_lo = multiplicand;
    var mc_hi = 0;
    
    while (multiplier > 0) {
        if ((multiplier & 1) == 1) {
            // Add multiplicand to result
            result_lo = result_lo + mc_lo;
            
            // Basic manual carry handling for 8-bit (if addition wraps)
            // The compiler currently does 8-bit math, so we approximate the carry out.
            // If result_lo < mc_lo, a carry occurred.
            if (result_lo < mc_lo) {
                result_hi = result_hi + 1;
            }
            result_hi = result_hi + mc_hi;
        }
        
        // Shift multiplier right by 1
        multiplier = multiplier >> 1;
        
        // Shift multiplicand left by 1 (16-bit shift)
        var old_mc_lo = mc_lo;
        mc_lo = mc_lo << 1;
        mc_hi = mc_hi << 1;
        
        // Handle carry from lo to hi
        if (old_mc_lo > 127) {
            mc_hi = mc_hi + 1;
        }
    }
    
    // We can only return an 8-bit value from functions in our simple MiniC right now, 
    // or output it to a port. Let's return the LO byte and OUT the HI byte to visualize it.
    out(result_hi);
    return result_lo;
}

var x = 7;
var y = 6;
var product_lo = multiply(x, y);
out(product_lo);  // expected output: HI=0, LO=42
