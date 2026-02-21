// fibonacci.mc - Compute first 13 Fibonacci numbers
var prev = 1;
var curr = 1;
var next = 0;
var count = 11;

out(prev);
out(curr);

while (count > 0) {
    next = prev + curr;
    out(next);
    prev = curr;
    curr = next;
    count = count - 1;
}
