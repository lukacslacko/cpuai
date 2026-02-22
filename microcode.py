#!/usr/bin/env python3
"""
Microcode generator for the breadboard CPU.
Produces two 32KB EEPROM images (microcode_a.bin, microcode_b.bin).

16-bit control word layout:
  Bits  0-3 : DS   (data bus source)
  Bits  4-7 : DD   (data bus destination)
  Bits  8-10: ALU_OP
  Bit  11   : FLAGS_IN
  Bit  12   : IP_INC
  Bit  13   : SP_INC
  Bit  14   : SP_DEC
  Bit  15   : uIP_RST

EEPROM address layout (15 bits):
  Bits  0-3 : uIP  (micro-step counter, 4 bits)
  Bits  4-6 : FLAGS (Z, C, N)
  Bits  7-14: IR   (instruction register, 8 bits)
"""

# ============================================================================
# Data Bus Source (bits 0-3)
# ============================================================================
DS_NONE     = 0
DS_A        = 1
DS_B        = 2
DS_C        = 3
DS_D        = 4
DS_ALU      = 5
DS_MEM      = 6
DS_IPL      = 7    # current IPL -> data bus
DS_IPH      = 8    # current IPH -> data bus
DS_SP       = 9    # SP -> data bus
DS_CONST_FF = 10   # constant 0xFF -> data bus

# ============================================================================
# Data Bus Destination (bits 4-7)
# ============================================================================
DD_NONE = 0  << 4
DD_A    = 1  << 4
DD_B    = 2  << 4
DD_C    = 3  << 4
DD_D    = 4  << 4
DD_IR   = 5  << 4
DD_MEM  = 6  << 4
DD_H    = 7  << 4   # latch into H (ADDR[15:8])
DD_L    = 8  << 4   # latch into L (ADDR[7:0])
DD_IPL  = 9  << 4   # load IPL from data bus
DD_IPH  = 10 << 4   # load IPH from data bus
DD_SP   = 11 << 4   # load SP from data bus
DD_OUT  = 12 << 4   # output port
DD_HLT  = 13 << 4   # halt processor

# ============================================================================
# ALU Operation (bits 8-10)
# ============================================================================
ALU_ADD = 0 << 8
ALU_SUB = 1 << 8
ALU_AND = 2 << 8
ALU_OR  = 3 << 8
ALU_XOR = 4 << 8
ALU_NOT = 5 << 8
ALU_SHL = 6 << 8
ALU_SHR = 7 << 8

# ============================================================================
# Control Flags (bits 11-15)
# ============================================================================
FLAGS_IN = 1 << 11
IP_INC   = 1 << 12
SP_INC   = 1 << 13
SP_DEC   = 1 << 14
uIP_RST  = 1 << 15

# For backward compat in instruction definitions
HLT = DD_HLT

# ============================================================================
# Fetch Sequence (uIP = 0, 1, 2)
#
# uIP=0: DS_IPL | DD_L     -> latch current IPL into L
# uIP=1: DS_IPH | DD_H     -> latch IPH into H.  HL = full IP address.
# uIP=2: DS_MEM | DD_IR | IP_INC -> read opcode, advance IP past it.
#
# After fetch, IP points to first operand byte and uIP=3 begins the
# instruction body.
# ============================================================================
FETCH0 = DS_IPL | DD_L
FETCH1 = DS_IPH | DD_H
FETCH2 = DS_MEM | DD_IR | IP_INC

# ============================================================================
# Instruction Table
# ============================================================================
INSTRUCTIONS = {}

def instruction(opcode, name, *steps):
    INSTRUCTIONS[opcode] = (name, steps)

# --- NOP ---
instruction(0x00, "NOP",
    uIP_RST)

# --- Load Immediate ---
def make_ldi(opcode, name, dd):
    instruction(opcode, name,
        DS_IPL | DD_L,
        DS_MEM | dd | IP_INC,
        uIP_RST)

make_ldi(0x01, "LDA #imm", DD_A)
make_ldi(0x02, "LDB #imm", DD_B)
make_ldi(0x03, "LDC #imm", DD_C)
make_ldi(0x04, "LDD #imm", DD_D)

# --- Load/Store [addr16] ---
# Read lo byte -> C, read hi byte -> H, C -> L, MEM[HL] -> reg
def make_ld_addr16(opcode, name, dest_dd):
    instruction(opcode, name,
        DS_IPL | DD_L,
        DS_MEM | DD_C | IP_INC,
        DS_IPL | DD_L,
        DS_MEM | DD_H | IP_INC,
        DS_C   | DD_L,
        DS_MEM | dest_dd,
        uIP_RST)

def make_st_addr16(opcode, name, src_ds):
    instruction(opcode, name,
        DS_IPL | DD_L,
        DS_MEM | DD_C | IP_INC,
        DS_IPL | DD_L,
        DS_MEM | DD_H | IP_INC,
        DS_C   | DD_L,
        src_ds | DD_MEM,
        uIP_RST)

make_ld_addr16(0x05, "LDA [addr16]", DD_A)
make_st_addr16(0x06, "STA [addr16]", DS_A)
make_ld_addr16(0x07, "LDB [addr16]", DD_B)
make_st_addr16(0x08, "STB [addr16]", DS_B)

# --- Register Moves (1 byte) ---
def make_mov(opcode, name, src, dst):
    instruction(opcode, name, src | dst | uIP_RST)

make_mov(0x18, "TBA", DS_B, DD_A)   # A <- B
make_mov(0x19, "TCA", DS_C, DD_A)   # A <- C
make_mov(0x1A, "TDA", DS_D, DD_A)   # A <- D
make_mov(0x1B, "TAB", DS_A, DD_B)   # B <- A
make_mov(0x1C, "TAC", DS_A, DD_C)   # C <- A
make_mov(0x1D, "TAD", DS_A, DD_D)   # D <- A

# --- ALU (1 byte, result -> A, updates flags) ---
def make_alu(opcode, name, alu_op):
    instruction(opcode, name, DS_ALU | alu_op | DD_A | FLAGS_IN | uIP_RST)

make_alu(0x20, "ADD", ALU_ADD)
make_alu(0x21, "SUB", ALU_SUB)
make_alu(0x22, "AND", ALU_AND)
make_alu(0x23, "OR",  ALU_OR)
make_alu(0x24, "XOR", ALU_XOR)
make_alu(0x25, "NOT", ALU_NOT)
make_alu(0x26, "SHL", ALU_SHL)
make_alu(0x27, "SHR", ALU_SHR)

# CMP: ALU SUB but result is discarded (DD_NONE), only flags update
instruction(0x28, "CMP", DS_ALU | ALU_SUB | FLAGS_IN | uIP_RST)

# --- Stack (push/pop) ---
# Stack lives at 0xFF00-0xFFFF.  H=0xFF, L=SP for stack address.
# PSH: write MEM[0xFF:SP], then SP--
# POP: SP++, then read MEM[0xFF:SP]
def make_psh(opcode, name, src_ds):
    instruction(opcode, name,
        DS_CONST_FF | DD_H,
        DS_SP       | DD_L,
        src_ds      | DD_MEM,
        SP_DEC,
        uIP_RST)

def make_pop(opcode, name, dest_dd):
    instruction(opcode, name,
        SP_INC,
        DS_CONST_FF | DD_H,
        DS_SP       | DD_L,
        DS_MEM      | dest_dd,
        uIP_RST)

make_psh(0x30, "PSH A", DS_A)
make_pop(0x40, "POP A", DD_A)
make_psh(0x50, "PSH B", DS_B)
make_pop(0x60, "POP B", DD_B)
make_psh(0x90, "PSH C", DS_C)
make_pop(0xA0, "POP C", DD_C)
make_psh(0xB0, "PSH D", DS_D)
make_pop(0x10, "POP D", DD_D)

# --- SP-Relative Load/Store (2-byte: opcode + offset) ---
# Uses ALU to compute SP+offset, then addresses 0xFF:result.

# LSA offset: A = MEM[0xFF:(SP+offset)].  Clobbers A (used for ALU input).
instruction(0xC0, "LSA off",
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,            # H = 0xFF
    DS_MEM      | DD_A,            # A = MEM[0xFF:(SP+offset)]
    uIP_RST)

# SSA offset: MEM[0xFF:(SP+offset)] = A.  Clobbers B, D.
instruction(0xD0, "SSA off",
    DS_A        | DD_D,            # save A -> D
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,            # H = 0xFF
    DS_D        | DD_MEM,          # MEM = D (original A)
    uIP_RST)

# LSB offset: B = MEM[0xFF:(SP+offset)].  Clobbers A.
instruction(0xE0, "LSB off",
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_MEM      | DD_B,            # B = MEM[0xFF:(SP+offset)]
    uIP_RST)

# SSB offset: MEM[0xFF:(SP+offset)] = B.  Clobbers A, C.
instruction(0xF0, "SSB off",
    DS_B        | DD_C,            # save B -> C
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_C        | DD_MEM,          # MEM = C (original B)
    uIP_RST)

# --- Jumps ---
# JMP addr16: fetch lo->C, hi->D, set IPL=C, IPH=D
instruction(0x70, "JMP addr16",
    DS_IPL | DD_L,
    DS_MEM | DD_C | IP_INC,
    DS_IPL | DD_L,
    DS_MEM | DD_D | IP_INC,
    DS_C   | DD_IPL,
    DS_D   | DD_IPH,
    uIP_RST)

# Conditional jumps: dispatched by flags in generate_microcode()
JUMP_MAP = {
    0x71: lambda flags: (flags & 1) != 0,  # JZ:  jump if Z set
    0x72: lambda flags: (flags & 1) == 0,  # JNZ: jump if Z clear
    0x73: lambda flags: (flags & 2) != 0,  # JC:  jump if C set
    0x74: lambda flags: (flags & 2) == 0,  # JNC: jump if C clear
    0x75: lambda flags: (flags & 4) != 0,  # JN:  jump if N set
}

JMP_TAKEN_STEPS = [
    DS_IPL | DD_L,
    DS_MEM | DD_C | IP_INC,
    DS_IPL | DD_L,
    DS_MEM | DD_D | IP_INC,
    DS_C   | DD_IPL,
    DS_D   | DD_IPH,
    uIP_RST,
]

JMP_NOT_TAKEN_STEPS = [
    DS_IPL | DD_L,
    IP_INC,             # skip lo byte
    DS_IPL | DD_L,
    IP_INC,             # skip hi byte
    uIP_RST,
]

# --- CALL / RET ---
# CALL addr16: fetch lo->C, hi->D, save return IP in A(hi):B(lo), jump
instruction(0x80, "CALL addr16",
    DS_IPL | DD_L,
    DS_MEM | DD_C | IP_INC,     # C = lo jump addr
    DS_IPL | DD_L,
    DS_MEM | DD_D | IP_INC,     # D = hi jump addr, IP now = return addr
    DS_IPL | DD_B,              # B = return lo
    DS_IPH | DD_A,              # A = return hi
    DS_C   | DD_IPL,            # jump lo
    DS_D   | DD_IPH,            # jump hi
    uIP_RST)

# RET: jump to A:B (A=hi, B=lo)
instruction(0x81, "RET",
    DS_B | DD_IPL,
    DS_A | DD_IPH,
    uIP_RST)

# --- Misc ---
instruction(0x82, "HLT", HLT)
instruction(0x83, "IN A",  DD_A, uIP_RST)        # placeholder
instruction(0x84, "OUT A", DS_A | DD_OUT | uIP_RST)

# ============================================================================
# Microcode ROM Generation
# ============================================================================

def generate_microcode():
    rom_lo = bytearray(32768)   # EEPROM A: control word bits 0-7
    rom_hi = bytearray(32768)   # EEPROM B: control word bits 8-15

    # Pre-fill with uIP_RST (safe default)
    for i in range(32768):
        rom_lo[i] = uIP_RST & 0xFF
        rom_hi[i] = (uIP_RST >> 8) & 0xFF

    for addr in range(32768):
        uip   = addr & 0x0F
        flags = (addr >> 4) & 0x07
        ir    = (addr >> 7) & 0xFF

        cw = uIP_RST  # default

        if uip == 0:
            cw = FETCH0
        elif uip == 1:
            cw = FETCH1
        elif uip == 2:
            cw = FETCH2
        else:
            body_step = uip - 3

            if ir in JUMP_MAP:
                steps = JMP_TAKEN_STEPS if JUMP_MAP[ir](flags) else JMP_NOT_TAKEN_STEPS
                cw = steps[body_step] if body_step < len(steps) else uIP_RST
            elif ir in INSTRUCTIONS:
                _, steps = INSTRUCTIONS[ir]
                cw = steps[body_step] if body_step < len(steps) else uIP_RST
            else:
                cw = uIP_RST

        rom_lo[addr] = cw & 0xFF
        rom_hi[addr] = (cw >> 8) & 0xFF

    with open('microcode_a.bin', 'wb') as f: f.write(rom_lo)
    with open('microcode_b.bin', 'wb') as f: f.write(rom_hi)
    print("Generated microcode_a.bin, microcode_b.bin")

    # Instruction summary
    print("\nInstruction summary:")
    max_body = 0
    for opc in sorted(INSTRUCTIONS.keys()):
        name, steps = INSTRUCTIONS[opc]
        total = len(steps) + 3
        max_body = max(max_body, len(steps))
        print(f"  0x{opc:02X} {name:20s}  {total:2d} clocks (3 fetch + {len(steps)} body)")
    for opc in sorted(JUMP_MAP.keys()):
        total_t = 3 + len(JMP_TAKEN_STEPS)
        total_n = 3 + len(JMP_NOT_TAKEN_STEPS)
        max_body = max(max_body, len(JMP_TAKEN_STEPS), len(JMP_NOT_TAKEN_STEPS))
        print(f"  0x{opc:02X} cond jump            {total_t:2d}/{total_n:2d} clocks (taken/not)")

    print(f"\nMax body steps: {max_body}  (must be <= 13 for 4-bit uIP)")
    assert max_body <= 13, f"ERROR: {max_body} body steps exceeds uIP capacity!"

    # Verify all control words fit in 16 bits
    for opc, (name, steps) in INSTRUCTIONS.items():
        for s in steps:
            assert s < 65536, f"Control word overflow in {name}: 0x{s:X}"

    print("All control words verified: fit in 16 bits (2 EEPROMs)")

if __name__ == "__main__":
    generate_microcode()
    print("Done")
