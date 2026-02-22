# Instruction Set Reference

## Registers

| Register | Width | Description |
|----------|-------|-------------|
| A | 8 | Accumulator, ALU left operand |
| B | 8 | ALU right operand |
| C | 8 | General purpose / temp |
| D | 8 | General purpose / temp |
| IP | 16 | Instruction pointer (reset: 0x0000) |
| SP | 8 | Stack pointer (addresses 0xFF00+SP) |
| Flags | 3 | Z (zero), C (carry/borrow), N (negative) |

## Memory Map

| Range | Size | Description |
|-------|------|-------------|
| 0x0000-0x7FFF | 32 KB | Program ROM |
| 0x8000-0xFEFF | 31.75 KB | RAM (general purpose) |
| 0xFF00-0xFFFF | 256 B | Stack (mapped via SP) |

## Encoding

Instructions are 1, 2, or 3 bytes. Multi-byte addresses are little-endian (low byte first).

```
1 byte:  [opcode]
2 bytes: [opcode] [immediate]
3 bytes: [opcode] [addr_lo] [addr_hi]
```

**Page boundary rule:** Instructions must not span 256-byte page boundaries. The assembler automatically inserts NOP padding when needed.

---

## Load / Store

| Opcode | Mnemonic | Bytes | Clocks | Operation | Clobbers |
|--------|----------|-------|--------|-----------|----------|
| `01 ii` | `LDA #imm` | 2 | 6 | A ← imm | — |
| `02 ii` | `LDB #imm` | 2 | 6 | B ← imm | — |
| `03 ii` | `LDC #imm` | 2 | 6 | C ← imm | — |
| `04 ii` | `LDD #imm` | 2 | 6 | D ← imm | — |
| `05 ll hh` | `LDA [addr]` | 3 | 10 | A ← MEM[hh:ll] | C |
| `06 ll hh` | `STA [addr]` | 3 | 10 | MEM[hh:ll] ← A | C |
| `07 ll hh` | `LDB [addr]` | 3 | 10 | B ← MEM[hh:ll] | C |
| `08 ll hh` | `STB [addr]` | 3 | 10 | MEM[hh:ll] ← B | C |

## Register Moves

| Opcode | Mnemonic | Bytes | Clocks | Operation |
|--------|----------|-------|--------|-----------|
| `18` | `TBA` | 1 | 4 | A ← B |
| `19` | `TCA` | 1 | 4 | A ← C |
| `1A` | `TDA` | 1 | 4 | A ← D |
| `1B` | `TAB` | 1 | 4 | B ← A |
| `1C` | `TAC` | 1 | 4 | C ← A |
| `1D` | `TAD` | 1 | 4 | D ← A |

## ALU

All ALU instructions are 1 byte, 4 clocks. They store the result in A and update flags (Z, C, N). CMP discards the result (flags only).

| Opcode | Mnemonic | Operation |
|--------|----------|-----------|
| `20` | `ADD` | A ← A + B |
| `21` | `SUB` | A ← A - B |
| `22` | `AND` | A ← A & B |
| `23` | `OR` | A ← A \| B |
| `24` | `XOR` | A ← A ^ B |
| `25` | `NOT` | A ← ~A |
| `26` | `SHL` | A ← A << 1 (C ← old bit 7) |
| `27` | `SHR` | A ← A >> 1 (C ← old bit 0) |
| `28` | `CMP` | flags ← A - B (A unchanged) |

## Stack

Push/Pop are 1-byte instructions. Stack grows downward from 0xFFFF.

| Opcode | Mnemonic | Bytes | Clocks | Operation |
|--------|----------|-------|--------|-----------|
| `30` | `PSH A` | 1 | 8 | MEM[0xFF:SP] ← A; SP-- |
| `40` | `POP A` | 1 | 8 | SP++; A ← MEM[0xFF:SP] |
| `50` | `PSH B` | 1 | 8 | MEM[0xFF:SP] ← B; SP-- |
| `60` | `POP B` | 1 | 8 | SP++; B ← MEM[0xFF:SP] |
| `90` | `PSH C` | 1 | 8 | MEM[0xFF:SP] ← C; SP-- |
| `A0` | `POP C` | 1 | 8 | SP++; C ← MEM[0xFF:SP] |
| `B0` | `PSH D` | 1 | 8 | MEM[0xFF:SP] ← D; SP-- |
| `10` | `POP D` | 1 | 8 | SP++; D ← MEM[0xFF:SP] |

## SP-Relative Load / Store

2-byte instructions (opcode + offset byte). Address = 0xFF00 + SP + offset. Uses ALU internally.

| Opcode | Mnemonic | Bytes | Clocks | Operation | Clobbers |
|--------|----------|-------|--------|-----------|----------|
| `C0 nn` | `LSA nn` | 2 | 10 | A ← MEM[0xFF:(SP+nn)] | A (overwritten) |
| `D0 nn` | `SSA nn` | 2 | 11 | MEM[0xFF:(SP+nn)] ← A | B, D |
| `E0 nn` | `LSB nn` | 2 | 10 | B ← MEM[0xFF:(SP+nn)] | A |
| `F0 nn` | `SSB nn` | 2 | 11 | MEM[0xFF:(SP+nn)] ← B | A, C |

## Branching

| Opcode | Mnemonic | Bytes | Clocks | Operation |
|--------|----------|-------|--------|-----------|
| `70 ll hh` | `JMP addr` | 3 | 10 | IP ← hh:ll |
| `71 ll hh` | `JZ addr` | 3 | 10/8 | if Z: IP ← hh:ll |
| `72 ll hh` | `JNZ addr` | 3 | 10/8 | if !Z: IP ← hh:ll |
| `73 ll hh` | `JC addr` | 3 | 10/8 | if C: IP ← hh:ll |
| `74 ll hh` | `JNC addr` | 3 | 10/8 | if !C: IP ← hh:ll |
| `75 ll hh` | `JN addr` | 3 | 10/8 | if N: IP ← hh:ll |
| `80 ll hh` | `CAL addr` | 3 | 12 | A:B ← IP (return); IP ← hh:ll |
| `81` | `RET` | 1 | 6 | IP ← A:B |

Conditional jump clocks: taken/not-taken.

**CALL convention:** `CAL` saves the return address in A (high) and B (low). The callee is responsible for saving and restoring A:B if it needs them. `RET` jumps to the address in A:B.

## Miscellaneous

| Opcode | Mnemonic | Bytes | Clocks | Operation |
|--------|----------|-------|--------|-----------|
| `00` | `NOP` | 1 | 4 | No operation |
| `82` | `HLT` | 1 | 4 | Halt processor |
| `83` | `IN` | 1 | 5 | A ← input port |
| `84` | `OUT` | 1 | 4 | output port ← A |

## Assembler Aliases

| Alias | Expands to |
|-------|------------|
| `PUSH A` | `PSA` (0x30) |
| `POP A` | `PPA` (0x40) |
| `PUSH B` | `PSB` (0x50) |
| `POP B` | `PPB` (0x60) |
| `PUSH C` | `PSH C` (0x90) |
| `POP C` | `POP C` (0xA0) |
| `PUSH D` | `PSH D` (0xB0) |
| `POP D` | `POP D` (0x10) |
| `CALL` | `CAL` |
| `MOV A, B` | `TBA` (0x18) |
