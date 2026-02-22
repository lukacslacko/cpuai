# Architecture Reference

## Block Diagram

```text
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
               |  | (2 x 32KB)       |  |
               |  | Addr: IR|F|uIP   |  |
               |  +--------+---------+  |
               |       16 control       |
               |        signals         |
               +------------+-----------+
                            |
   +---+---+---+---+---+---+---+---+---+---+
   |   |   |   |   |   |   |   |   |   |   |
   v   v   v   v   v   v   v   v   v   v   v
        ============ 8-bit Data Bus ============
   |       |       |     |     |     |       |
+--+--+ +--+--+ +--+--+ | +--+--+ +--+--+ +--+--+
|  A  | |  B  | |  C  | | |  IP | |  SP | | ALU |
+-----+ +-----+ +--+--+ | |(16b)| |(8b) | |(GAL)|
                |  D  |  | +--+--+ +--+--+ +-----+
                +-----+  |    |buf    |buf
                          |    |       |
                +--+--+ +--+--+     +--+--+
                |  H  | |  L  |     | 0xFF|
                +--+--+ +--+--+     +-----+
                   |       |         const
                   v       v
          ===== 16-bit Address Bus =====
                   |               |
              +----+----+     +----+----+
              | Program |     |  RAM    |
              | EEPROM  |     | 32KB    |
              | 32KB    |     |         |
              +---------+     +---------+
              0x0000-7FFF     0x8000-FFFF
```

**Key design principle:** The address bus is **always** driven by H (high byte) and L (low byte) registers. There are no direct address buffers from IP, SP, or any other source. IP and SP are read onto the data bus via tri-state buffers when needed (DS_IPL, DS_IPH, DS_SP), then latched into H/L to form an address.

## Control Word (16 bits, 2 EEPROMs)

### Bits 0-3: Data Bus Source (DS)

| Value | Source | Description |
|-------|--------|-------------|
| 0 | NONE | Bus not driven |
| 1 | A | A register |
| 2 | B | B register |
| 3 | C | C register |
| 4 | D | D register |
| 5 | ALU | ALU result |
| 6 | MEM | Memory read MEM[H:L] |
| 7 | IPL | IP low byte |
| 8 | IPH | IP high byte |
| 9 | SP | Stack pointer (8-bit) |
| 10 | 0xFF | Constant 0xFF |

### Bits 4-7: Data Bus Destination (DD)

| Value | Dest | Description |
|-------|------|-------------|
| 0 | NONE | Nothing latches |
| 1 | A | A register |
| 2 | B | B register |
| 3 | C | C register |
| 4 | D | D register |
| 5 | IR | Instruction register |
| 6 | MEM | Memory write MEM[H:L] |
| 7 | H | H register → ADDR[15:8] |
| 8 | L | L register → ADDR[7:0] |
| 9 | IPL | IP low byte load |
| 10 | IPH | IP high byte load |
| 11 | SP | Stack pointer load |
| 12 | OUT | Output port |
| 13 | HLT | Halt processor |

### Bits 8-10: ALU Operation

| Value | Op | Description |
|-------|-----|-------------|
| 0 | ADD | A + B |
| 1 | SUB | A - B |
| 2 | AND | A & B |
| 3 | OR | A \| B |
| 4 | XOR | A ^ B |
| 5 | NOT | ~A |
| 6 | SHL | A << 1 |
| 7 | SHR | A >> 1 |

### Bits 11-15: Control Flags

| Bit | Signal | Description |
|-----|--------|-------------|
| 11 | FLAGS_IN | Latch Z/C/N from ALU into flags register |
| 12 | IP_INC | Increment IP counter (carry cascades to IPH) |
| 13 | SP_INC | Increment stack pointer |
| 14 | SP_DEC | Decrement stack pointer |
| 15 | uIP_RST | Reset micro-step counter (→ next fetch) |

## EEPROM Address Layout

Each microcode EEPROM has 15 address lines:

| Bits | Width | Source |
|------|-------|--------|
| A0-A3 | 4 | uIP counter (micro-step 0-15) |
| A4-A6 | 3 | Flags register (Z, C, N) |
| A7-A14 | 8 | Instruction register (opcode) |

## Instruction Fetch Cycle

Every instruction begins with a 3-step fetch:

| uIP | Control Word | Effect |
|-----|-------------|--------|
| 0 | `DS_IPL \| DD_L` | L ← current IPL |
| 1 | `DS_IPH \| DD_H` | H ← current IPH. Now H:L = IP. |
| 2 | `DS_MEM \| DD_IR \| IP_INC` | IR ← MEM[H:L] (opcode), IP++ |

After fetch, IP points to the first operand byte and uIP=3 starts the instruction body.

To read an operand byte from instruction stream:
1. `DS_IPL | DD_L` — update L to current IPL
2. `DS_MEM | DD_reg | IP_INC` — read byte into register, advance IP

## Stack Hardware

The stack pointer is an 8-bit up/down counter (2× 74HC193). The stack occupies addresses 0xFF00-0xFFFF. To form a stack address, H is loaded with 0xFF (`DS_CONST_FF | DD_H`) and L is loaded with SP (`DS_SP | DD_L`).

- **Push**: write MEM[0xFF:SP], then SP--
- **Pop**: SP++, then read MEM[0xFF:SP]

## Reset

On hardware reset (`~RESET` low), uIP and IP are cleared to 0. The first fetch reads from address 0x0000.
