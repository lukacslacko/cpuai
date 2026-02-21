# Instruction Set Architecture Reference

## Overview

8-bit data/16-bit address CPU with dedicated split bus architecture.

## Memory Map

| Range | Size | Description |
|-------|------|-------------|
| `0x0000-0x7FFF` | 32 KB | Program ROM |
| `0x8000-0xFFFF` | 32 KB | RAM (variables, stack) |
| `0xFF00-0xFFFF` | 256 B | Stack space (mapped by SP + offset) |

## Registers

| Register | Width | Description |
|----------|-------|-------------|
| A | 8 | Accumulator (primary operand) |
| B | 8 | Secondary operand |
| C | 8 | General purpose / address low / return low |
| D | 8 | General purpose / address high / return high |
| IP | 16 | Instruction pointer (reset: 0x0000) |
| SP | 8 | Stack pointer |
| Flags | 3 | Z (zero), C (carry/borrow), N (negative) |

## Instruction Encoding

Most instructions are 1 byte (opcode only), 2 bytes (opcode + immediate), or 3 bytes (opcode + 16-bit address).

Addresses in instructions are encoded in little-endian format:
```
Opcode:  [PPPP PPPP]
Byte 2:  [LLLL LLLL]   address[7:0]
Byte 3:  [HHHH HHHH]   address[15:8]
```

## Instructions

### Load/Store

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `01 ii` | `LDA #imm` | 2 | A <- imm |
| `02 ii` | `LDB #imm` | 2 | B <- imm |
| `03 ii` | `LDC #imm` | 2 | C <- imm |
| `04 ii` | `LDD #imm` | 2 | D <- imm |
| `05 ll hh` | `LDA [addr16]` | 3 | A <- MEM[addr] |
| `06 ll hh` | `STA [addr16]` | 3 | MEM[addr] <- A |
| `07 ll hh` | `LDB [addr16]` | 3 | B <- MEM[addr] |
| `08 ll hh` | `STB [addr16]` | 3 | MEM[addr] <- B |
| `18` | `MVA B` | 1 | A <- B |
| `19` | `MVA C` | 1 | A <- C |
| `1A` | `MVA D` | 1 | A <- D |
| `1B` | `MVB A` | 1 | B <- A |
| `1C` | `MVC A` | 1 | C <- A |
| `1D` | `MVD A` | 1 | D <- A |

### ALU

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `20` | `ADD` | 1 | A <- A + B |
| `21` | `SUB` | 1 | A <- A - B |
| `22` | `AND` | 1 | A <- A & B |
| `23` | `OR` | 1 | A <- A \| B |
| `24` | `XOR` | 1 | A <- A ^ B |
| `25` | `NOT` | 1 | A <- ~A |
| `26` | `SHL` | 1 | A <- A << 1 |
| `27` | `SHR` | 1 | A <- A >> 1 |
| `28` | `CMP` | 1 | flags <- A - B |

*All ALU instructions except CMP store their result in A. They all update flags Z, C, N.*

### Stack

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `30` | `PSH A` | 1 | push A |
| `40` | `POP A` | 1 | pop A |
| `50` | `PSH B` | 1 | push B |
| `60` | `POP B` | 1 | pop B |
| `90` | `PSH C` | 1 | push C |
| `A0` | `POP C` | 1 | pop C |
| `B0` | `PSH D` | 1 | push D |
| `10` | `POP D` | 1 | pop D |
| `Cx` | `LSA x` | 1 | A <- MEM[SP + x] (x is 0-15) |
| `Dx` | `SSA x` | 1 | MEM[SP + x] <- A |
| `Ex` | `LSB x` | 1 | B <- MEM[SP + x] |
| `Fx` | `SSB x` | 1 | MEM[SP + x] <- B |

### Branching

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `70 ll hh` | `JMP addr16` | 3 | IP <- hh:ll |
| `71 ll hh` | `JZ addr16` | 3 | if Z: IP <- hh:ll |
| `72 ll hh` | `JNZ addr16` | 3 | if !Z: IP <- hh:ll |
| `73 ll hh` | `JC addr16` | 3 | if C: IP <- hh:ll |
| `74 ll hh` | `JNC addr16` | 3 | if !C: IP <- hh:ll |
| `75 ll hh` | `JN addr16` | 3 | if N: IP <- hh:ll |
| `80 ll hh` | `CAL addr16` | 3 | A:B <- IP; IP <- hh:ll |
| `81` | `RET` | 1 | IP <- D:C |

*(Functions should pop return address into D:C before calling RET).*

### Misc

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `00` | `NOP` | 1 | no-op |
| `82` | `HLT` | 1 | halt |
| `83` | `IN`  | 1 | A <- input port |
| `84` | `OUT` | 1 | output port <- A |
