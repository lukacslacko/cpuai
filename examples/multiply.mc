// multiply.mc - Multiply two numbers using repeated addition
fun multiply(a, b) {
    var result = 0;
    while (b > 0) {
        result = result + a;
        b = b - 1;
    }
    return result;
}

var x = 7;
var y = 6;
var product = multiply(x, y);
out(product);  // outputs 42
