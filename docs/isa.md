# Instruction Set Architecture Reference

## Overview

8-bit CPU with 16-bit address space (64 KB). Instructions are 1, 2, or 3 bytes.

## Memory Map

| Range | Size | Description |
|-------|------|-------------|
| `0x0000-0x7FFF` | 32 KB | Program ROM |
| `0x8000-0xFFFF` | 32 KB | RAM (variables, stack) |
| `0xFF00-0xFFFF` | 256 B | Stack (SP-relative) |

## Registers

| Register | Width | Description |
|----------|-------|-------------|
| A | 8 | Accumulator (primary operand & result) |
| B | 8 | Secondary operand |
| IP | 16 | Instruction pointer (reset: 0x0000) |
| SP | 8 | Stack pointer (reset: 0xFF, grows down from 0xFFFF) |
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
| `02 ll hh` | `LDA [addr16]` | 3 | A <- MEM[addr] |
| `03 ll hh` | `STA [addr16]` | 3 | MEM[addr] <- A |
| `04 ii` | `LDB #imm` | 2 | B <- imm |
| `05 ll hh` | `LDB [addr16]` | 3 | B <- MEM[addr] |
| `06 ll hh` | `STB [addr16]` | 3 | MEM[addr] <- B |
| `07` | `MVA` | 1 | A <- B |
| `08` | `MVB` | 1 | B <- A |

### ALU

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `10` | `ADD` | 1 | A <- A + B |
| `11` | `SUB` | 1 | A <- A - B |
| `12` | `AND` | 1 | A <- A & B |
| `13` | `OR` | 1 | A <- A \| B |
| `14` | `XOR` | 1 | A <- A ^ B |
| `15` | `NOT` | 1 | A <- ~A |
| `16` | `SHL` | 1 | A <- A << 1 (C <- A[7]) |
| `17` | `SHR` | 1 | A <- A >> 1 (C <- A[0]) |
| `18 ii` | `ADI #imm` | 2 | A <- A + imm |
| `19 ii` | `SBI #imm` | 2 | A <- A - imm |
| `1A` | `CMP` | 1 | flags <- A - B (discard) |
| `1B ii` | `CMI #imm` | 2 | flags <- A - imm (discard) |

All ALU instructions update flags (Z, C, N).

### Stack

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `20` | `PSA` | 1 | push A |
| `21` | `PPA` | 1 | pop A |
| `22` | `PSB` | 1 | push B |
| `23` | `PPB` | 1 | pop B |

### Branching

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `30 ll hh` | `JMP addr16` | 3 | IP <- hh:ll |
| `40 ll hh` | `JZ addr16` | 3 | if Z: IP <- hh:ll |
| `50 ll hh` | `JNZ addr16` | 3 | if !Z: IP <- hh:ll |
| `60 ll hh` | `JC addr16` | 3 | if C: IP <- hh:ll |
| `70 ll hh` | `JNC addr16` | 3 | if !C: IP <- hh:ll |
| `80 ll hh` | `JN addr16` | 3 | if N: IP <- hh:ll |
| `90 ll hh` | `CAL addr16` | 3 | push IP; IP <- hh:ll |
| `A0` | `RET` | 1 | pop IP |

### Misc

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| `00` | `NOP` | 1 | no-op |
| `FD` | `IN` | 1 | A <- input port |
| `FE` | `OUT` | 1 | output port <- A |
| `FF` | `HLT` | 1 | halt |

## Assembly Syntax

```asm
label:              ; label definition
    LDA #42         ; immediate with # prefix
    LDA [0x8010]    ; 16-bit memory address in []
    JMP label       ; jump to label (16-bit)
    .org 0x0000     ; set origin
    .db 0x42, "hi"  ; define bytes
    .equ MAX 255    ; define constant
```

## Flag Behavior

| Flag | Set when |
|------|----------|
| Z | Result is zero |
| C | Unsigned overflow (ADD) or borrow (SUB: A < B) |
| N | Result bit 7 is set (negative in signed) |
