# Architecture Reference

## Block Diagram

```
                    +-------------+
                    | Clock (555) |
                    +------+------+
                           |
              +------------v-----------+
              |   Microcode Control    |
              |  +------------------+  |
              |  | uIP (4-bit ctr)  |  |
              |  +--------+---------+  |
              |           |            |
              |  +--------v---------+  |
              |  | Microcode EEPROM |  |
              |  | (3 x 32KB)       |  |
              |  | Addr: IR|F|uIP   |  |
              |  +--------+---------+  |
              |       24 control       |
              |        signals         |
              +------------+-----------+
                           |
    +----------------------+----------------------+
    |                      |                      |
    v                      v                      v
+-------+  ======== 8-bit Data Bus ========  +--------+
|  IP   |<==+                          +===>| RAM    |
| 16-bit|   |   +---+   +---+   +---+ |    | 32KB   |
+-------+   +==>| A |<=>| B |<=>|TMP|<========+    +--------+
            |   +---+   +---+   +---+ |    +--------+
+-------+   |     |       |       |   +==>| Prog   |
|  MAR  |<==+     v       v       v   |   | EEPROM |
| 16-bit|   |   +-----------+         |   +--------+
+-------+   |   |    ALU    |         |
            |   |(2xGAL22V10|         |   +--------+
+-------+   |   +-----+-----+         +=>| OUT    |
|  SP   |<==+         |                   | port   |
| 8-bit |   |         v                   +--------+
+-------+   |   +-----------+
            |   |  FLAGS    |
+-------+   |   |  Z,C,N   |
|  IR   |<==+   +-----------+
| 8-bit |
+-------+
```

## Control Signal Encoding (24-bit control word)

The microcode EEPROM outputs a 24-bit control word per micro-step.
The word is field-encoded:

### Bits 0-3: Bus Source (what drives the data bus)

| Value | Signal | Description |
|-------|--------|-------------|
| 0000 | NONE | Bus not driven |
| 0001 | A_OUT | A register |
| 0010 | B_OUT | B register |
| 0011 | ALU_OUT | ALU result |
| 0100 | MEM_OUT | Memory read |
| 0101 | IP_LO | IP low byte |
| 0110 | IP_HI | IP high byte |
| 0111 | TMP_OUT | Temporary register |
| 1000 | SP_OUT | Stack pointer |

### Bits 4-7: Bus Destination (what latches from data bus)

| Value | Signal | Description |
|-------|--------|-------------|
| 0000 | NONE | Nothing latches |
| 0001 | A_IN | A register |
| 0010 | B_IN | B register |
| 0011 | IR_IN | Instruction register |
| 0100 | MAR_LO | MAR low byte |
| 0101 | MAR_HI | MAR high byte |
| 0110 | MEM_IN | Memory write |
| 0111 | OUT | Output port |
| 1000 | TMP_IN | Temporary register |

### Bits 8-10: ALU Operation (when ALU_OUT is active)

| Value | Operation |
|-------|-----------|
| 000 | ADD |
| 001 | SUB |
| 010 | AND |
| 011 | OR  |
| 100 | XOR |
| 101 | NOT |
| 110 | SHL |
| 111 | SHR |

### Bits 11-23: Miscellaneous Signals

| Bit | Signal | Description |
|-----|--------|-------------|
| 11 | FLAGS_IN | Latch flags from ALU |
| 12 | IP_INC | Increment IP |
| 13 | IP_LOAD | Load IP from MAR |
| 14 | SP_INC | Increment stack pointer |
| 15 | SP_DEC | Decrement stack pointer |
| 16 | SP_TO_MAR | Copy SP to MAR (MAR = 0xFF00 \| SP) |
| 17 | uIP_RST | Reset micro-step counter (end of instruction) |

## Microcode Addressing

```
EEPROM Address [14:0]:
  [14:7] = IR[7:0]    (8 bits - current opcode)
  [6:4]  = FLAGS[2:0]  (3 bits - Z, C, N)
  [3:0]  = uIP[3:0]   (4 bits - micro-step 0-15)
```

Three EEPROMs provide 8 bits each = 24-bit control word.

## Instruction Fetch Cycle

Every instruction begins with 3 micro-steps:
```
u0: MAR_LO <- IP_LO     (copy IP low byte to MAR)
u1: MAR_HI <- IP_HI     (copy IP high byte to MAR)
u2: IR <- MEM[MAR]; IP++ (fetch opcode, advance IP)
```

Execution-specific micro-steps follow from u3 onward. 16-bit operands are fetched using the `TMP` register to hold the low byte while the high byte is fetched.

## Data Bus Pull-downs

The data bus has pull-down resistors (10K). When no source drives the bus,
it reads as 0x00. This is used for reading unused inputs.

## Hardware Decoding

The 4-bit bus source and destination fields are decoded by 4-to-16 decoders (e.g., **74HC154**)
or pairs of **74HC138** 3-to-8 decoders. One decoder enables the correct bus driver, another
enables the correct bus receiver. The ALU operation bits (8-10) connect directly to the
GAL22V10 ALU operation select inputs.

The miscellaneous signals (bits 11-23) connect directly to the corresponding
hardware (counter enable/load inputs, clock gates, etc.).
