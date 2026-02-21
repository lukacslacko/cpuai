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
               |  | (3 x 32KB)       |  |
               |  | Addr: IR|F|uIP   |  |
               |  +--------+---------+  |
               |       24 control       |
               |        signals         |
               +------------+-----------+
                            |
   +------------------------+------------------------+
   |                        |                        |
   v                        v                        v
            ======== 8-bit Data Bus ========  
                 |   |   |   |   |   |   
   +---------+   |   |   |   |   |   |   +--------+
   |   IP    |===+   |   |   |   |   +==>| RAM    |
   | 16-bit  |       |   |   |   |   |   | 32KB   |
   +----+----+   +---+---+---+---+---+   +----+---+
        |        |   |   |   |   |   |        |
        v        v   v   v   v   v   v        |
   ======== 16-bit Address Bus =======        |
        ^        ^           ^   |   ^        |
   +----+----+   |           |   |   |   +----+---+
   | CD Regs |===+           |   |   +==>| Prog   |
   | 16-bit  |               |   |   |   | EEPROM |
   +---------+     +---------v---+   |   +--------+
                   |  SP + IR    |   |
  +--------+       | (Index Add) |   |   +--------+
  |  ALU   |       +-------------+   +==>| OUT    |
  |(GALs)  |                         |   | port   |
  +--------+                         |   +--------+
```

## Control Signal Encoding (24-bit control word)

### Bits 0-3: Bus Source

| Value | Signal | Description |
|-------|--------|-------------|
| 0000 | NONE | Bus not driven |
| 0001 | A_OE | A register |
| 0010 | B_OE | B register |
| 0011 | C_OE | C register |
| 0100 | D_OE | D register |
| 0101 | ALU_OE | ALU result |
| 0110 | MEM_OE | Memory read |
| 0111 | IP_LO_OE | IP low byte |
| 1000 | IP_HI_OE | IP high byte |
| 1001 | SP_OE | Stack pointer |

### Bits 4-7: Bus Destination

| Value | Signal | Description |
|-------|--------|-------------|
| 0000 | NONE | Nothing latches |
| 0001 | A_IN | A register |
| 0010 | B_IN | B register |
| 0011 | C_IN | C register |
| 0100 | D_IN | D register |
| 0101 | IR_IN | Instruction register |
| 0110 | MEM_IN | Memory write |
| 0111 | IP_LO_IN | IP low byte load |
| 1000 | IP_HI_IN | IP high byte load |
| 1001 | SP_IN | Stack pointer load |
| 1010 | OUT | Output port |

### Bits 8-9: Address Source

| Value | Source |
|-------|-----------|
| 00 | IP (Instruction Pointer) |
| 01 | CD (C and D Registers) |
| 10 | SP + IR[3:0] (Stack Offset Addressing) |

### Bits 10-12: ALU Operation

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

### Bits 13-18: Miscellaneous Signals

| Bit | Signal | Description |
|-----|--------|-------------|
| 13 | FLAGS_IN | Latch flags from ALU |
| 14 | IP_INC | Increment IP |
| 15 | SP_INC | Increment stack pointer |
| 16 | SP_DEC | Decrement stack pointer |
| 17 | uIP_RST | Reset micro-step counter |
| 18 | HLT | Halt processor execution |

## Instruction Fetch Cycle

Every instruction begins with 1 universal micro-step:
```
u0: AS_IP | DS_MEM | DD_IR | IP_INC
```
Because the structural emulator has dedicated dual-buses, the instruction fetch is fully pipelined in a single clock cycle, saving extensive cycles compared to MAR/TMP multiplexing.

## Stack Hardware

The Stack Pointer (`SP`) uses two cascaded `74HC193` up/down counters.
When the address bus source is `AS_SP_IDX`, two `74HC283` adders compute `SP + (IR & 0x0F)`. The top byte of the address is hardcoded to `0xFF`. This yields physical stack space in Ram from `0xFF00` to `0xFFFF` with instantaneous localized offsetting.
