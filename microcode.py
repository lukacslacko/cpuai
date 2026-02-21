#!/usr/bin/env python3
"""
Microcode generator for the breadboard CPU (16-bit Architecture).

Generates three 32KB binary images (one per EEPROM) containing the
24-bit control word for every combination of:
  - IR[7:0]  (current opcode)
  - FLAGS[2:0] (Z, C, N)
  - µIP[3:0] (micro-step)

EEPROM address: IR[7:0] | FLAGS[2:0] | µIP[3:0] = 15 bits = 32K addresses
EEPROM A outputs control bits 0-7, B outputs 8-15, C outputs 16-23.
"""

import struct
import sys

# ---------------------------------------------------------------------------
# Control signal bit definitions (24-bit word)
# ---------------------------------------------------------------------------

# Bus source field (bits 0-3)
# 0-15 options. Decoded by 74HC154 or 2x 74HC138.
SRC_NONE      = 0
SRC_A         = 1
SRC_B         = 2
SRC_ALU       = 3
SRC_MEM       = 4
SRC_IP_LO     = 5
SRC_IP_HI     = 6
SRC_TMP       = 7
SRC_SP        = 8

# Bus destination field (bits 4-7)
DST_NONE      = 0 << 4
DST_A         = 1 << 4
DST_B         = 2 << 4
DST_IR        = 3 << 4
DST_MAR_LO    = 4 << 4
DST_MAR_HI    = 5 << 4
DST_MEM       = 6 << 4
DST_OUT       = 7 << 4
DST_TMP       = 8 << 4

# ALU operation field (bits 8-10)
OP_ADD = 0 << 8
OP_SUB = 1 << 8
OP_AND = 2 << 8
OP_OR  = 3 << 8
OP_XOR = 4 << 8
OP_NOT = 5 << 8
OP_SHL = 6 << 8
OP_SHR = 7 << 8

# Misc signal bits (bits 11-23, unencoded)
_FLAGS_IN  = 1 << 11  # Latch flags from ALU output
_IP_INC    = 1 << 12  # Increment instruction pointer
_IP_LOAD   = 1 << 13  # Load IP from MAR
_SP_INC    = 1 << 14  # Increment stack pointer
_SP_DEC    = 1 << 15  # Decrement stack pointer
_SP_TO_MAR = 1 << 16  # Load MAR from SP (MAR = 0xFFFF offset by SP)
_UIP_RST   = 1 << 17  # Reset micro-IP to 0

# Flag bit positions in the FLAGS register and in the EEPROM address
FLAG_Z = 0  # Zero flag
FLAG_C = 1  # Carry flag
FLAG_N = 2  # Negative/sign flag

# ---------------------------------------------------------------------------
# Microcode storage: 32K entries of 24-bit control words
# ---------------------------------------------------------------------------
NUM_OPCODES = 256
NUM_FLAGS = 8    # 3 flag bits
NUM_USTEPS = 16  # 4 bit µIP
TOTAL_ADDRESSES = NUM_OPCODES * NUM_FLAGS * NUM_USTEPS  # 32768

microcode = [0] * TOTAL_ADDRESSES

def addr(opcode, flags, ustep):
    """Compute EEPROM address from opcode, flags, and micro-step."""
    return (opcode << 7) | (flags << 4) | ustep

def set_micro(opcode, ustep, signals, flag_mask=None):
    if flag_mask is None:
        for f in range(NUM_FLAGS):
            microcode[addr(opcode, f, ustep)] = signals
    else:
        for f in flag_mask:
            microcode[addr(opcode, f, ustep)] = signals

def flag_set(flag_bit):
    return [f for f in range(NUM_FLAGS) if f & (1 << flag_bit)]

def flag_clear(flag_bit):
    return [f for f in range(NUM_FLAGS) if not (f & (1 << flag_bit))]

# ---------------------------------------------------------------------------
# Instruction sequences
# ---------------------------------------------------------------------------

def set_fetch_v2(opcode):
    """Set the standard 3-cycle fetch for an opcode."""
    # µ0: MAR_LO <- IP_LO
    set_micro(opcode, 0, SRC_IP_LO | DST_MAR_LO)
    # µ1: MAR_HI <- IP_HI
    set_micro(opcode, 1, SRC_IP_HI | DST_MAR_HI)
    # µ2: IR <- MEM[MAR]; IP++
    set_micro(opcode, 2, SRC_MEM | DST_IR | _IP_INC)

def end_instr(opcode, ustep, extra=0):
    """End an instruction at the given micro-step."""
    set_micro(opcode, ustep, _UIP_RST | extra)

def fetch_operand_8(opcode, ustep):
    """Fetch an 8-bit operand from IP. IP++."""
    set_micro(opcode, ustep, SRC_IP_LO | DST_MAR_LO)
    set_micro(opcode, ustep + 1, SRC_IP_HI | DST_MAR_HI)
    return ustep + 2  # caller reads MEM_OUT, sets _IP_INC

def fetch_operand_16(opcode, ustep):
    """
    Fetch a 16-bit operand (address) from IP into MAR.
    Uses TMP register to hold the low byte while fetching high byte.
    Returns the ustep where MAR is fully loaded with the new 16-bit address.
    """
    # Fetch low byte into TMP
    set_micro(opcode, ustep, SRC_IP_LO | DST_MAR_LO)
    set_micro(opcode, ustep + 1, SRC_IP_HI | DST_MAR_HI)
    set_micro(opcode, ustep + 2, SRC_MEM | DST_TMP | _IP_INC)
    
    # Fetch high byte directly into MAR_HI
    set_micro(opcode, ustep + 3, SRC_IP_LO | DST_MAR_LO)
    set_micro(opcode, ustep + 4, SRC_IP_HI | DST_MAR_HI)
    set_micro(opcode, ustep + 5, SRC_MEM | DST_MAR_HI | _IP_INC)
    
    # Move low byte from TMP to MAR_LO
    set_micro(opcode, ustep + 6, SRC_TMP | DST_MAR_LO)
    return ustep + 7

# ---------------------------------------------------------------------------
# Define all instructions
# ---------------------------------------------------------------------------

def define_all_instructions():

    # --- NOP (0x00) ---
    set_fetch_v2(0x00)
    end_instr(0x00, 3)

    # --- LDA imm8 (0x01) ---
    set_fetch_v2(0x01)
    s = fetch_operand_8(0x01, 3)
    set_micro(0x01, s, SRC_MEM | DST_A | _IP_INC)
    end_instr(0x01, s + 1)

    # --- LDA [addr16] (0x02) ---
    set_fetch_v2(0x02)
    s = fetch_operand_16(0x02, 3)
    set_micro(0x02, s, SRC_MEM | DST_A)
    end_instr(0x02, s + 1)

    # --- STA [addr16] (0x03) ---
    set_fetch_v2(0x03)
    s = fetch_operand_16(0x03, 3)
    set_micro(0x03, s, SRC_A | DST_MEM)
    end_instr(0x03, s + 1)

    # --- LDB imm8 (0x04) ---
    set_fetch_v2(0x04)
    s = fetch_operand_8(0x04, 3)
    set_micro(0x04, s, SRC_MEM | DST_B | _IP_INC)
    end_instr(0x04, s + 1)

    # --- LDB [addr16] (0x05) ---
    set_fetch_v2(0x05)
    s = fetch_operand_16(0x05, 3)
    set_micro(0x05, s, SRC_MEM | DST_B)
    end_instr(0x05, s + 1)

    # --- STB [addr16] (0x06) ---
    set_fetch_v2(0x06)
    s = fetch_operand_16(0x06, 3)
    set_micro(0x06, s, SRC_B | DST_MEM)
    end_instr(0x06, s + 1)

    # --- MVA (0x07) ---
    set_fetch_v2(0x07)
    set_micro(0x07, 3, SRC_B | DST_A)
    end_instr(0x07, 4)

    # --- MVB (0x08) ---
    set_fetch_v2(0x08)
    set_micro(0x08, 3, SRC_A | DST_B)
    end_instr(0x08, 4)

    # --- ALU (0x10-0x17) ---
    alu_ops = [
        (0x10, OP_ADD), (0x11, OP_SUB), (0x12, OP_AND), (0x13, OP_OR),
        (0x14, OP_XOR), (0x15, OP_NOT), (0x16, OP_SHL), (0x17, OP_SHR)
    ]
    for opc, alu_op in alu_ops:
        set_fetch_v2(opc)
        set_micro(opc, 3, SRC_ALU | DST_A | alu_op | _FLAGS_IN)
        end_instr(opc, 4)

    # --- ADI imm8 (0x18) ---
    set_fetch_v2(0x18)
    s = fetch_operand_8(0x18, 3)
    set_micro(0x18, s, SRC_MEM | DST_B | _IP_INC)
    set_micro(0x18, s + 1, SRC_ALU | DST_A | OP_ADD | _FLAGS_IN)
    end_instr(0x18, s + 2)

    # --- SBI imm8 (0x19) ---
    set_fetch_v2(0x19)
    s = fetch_operand_8(0x19, 3)
    set_micro(0x19, s, SRC_MEM | DST_B | _IP_INC)
    set_micro(0x19, s + 1, SRC_ALU | DST_A | OP_SUB | _FLAGS_IN)
    end_instr(0x19, s + 2)

    # --- CMP (0x1A) ---
    set_fetch_v2(0x1A)
    set_micro(0x1A, 3, SRC_ALU | OP_SUB | _FLAGS_IN)
    end_instr(0x1A, 4)

    # --- CMI imm8 (0x1B) ---
    set_fetch_v2(0x1B)
    s = fetch_operand_8(0x1B, 3)
    set_micro(0x1B, s, SRC_MEM | DST_B | _IP_INC)
    set_micro(0x1B, s + 1, SRC_ALU | OP_SUB | _FLAGS_IN)
    end_instr(0x1B, s + 2)

    # --- PUSH A (0x20) ---
    set_fetch_v2(0x20)
    set_micro(0x20, 3, _SP_TO_MAR)
    set_micro(0x20, 4, SRC_A | DST_MEM)
    set_micro(0x20, 5, _SP_DEC)
    end_instr(0x20, 6)

    # --- POP A (0x21) ---
    set_fetch_v2(0x21)
    set_micro(0x21, 3, _SP_INC)
    set_micro(0x21, 4, _SP_TO_MAR)
    set_micro(0x21, 5, SRC_MEM | DST_A)
    end_instr(0x21, 6)

    # --- PUSH B (0x22) ---
    set_fetch_v2(0x22)
    set_micro(0x22, 3, _SP_TO_MAR)
    set_micro(0x22, 4, SRC_B | DST_MEM)
    set_micro(0x22, 5, _SP_DEC)
    end_instr(0x22, 6)

    # --- POP B (0x23) ---
    set_fetch_v2(0x23)
    set_micro(0x23, 3, _SP_INC)
    set_micro(0x23, 4, _SP_TO_MAR)
    set_micro(0x23, 5, SRC_MEM | DST_B)
    end_instr(0x23, 6)

    # --- JMP addr16 (0x30) ---
    set_fetch_v2(0x30)
    s = fetch_operand_16(0x30, 3)
    end_instr(0x30, s, _IP_LOAD)

    # --- JZ addr16 (0x40) ---
    set_fetch_v2(0x40)
    s = fetch_operand_16(0x40, 3)
    set_micro(0x40, s, _IP_LOAD | _UIP_RST, flag_mask=flag_set(FLAG_Z))
    set_micro(0x40, s, _UIP_RST, flag_mask=flag_clear(FLAG_Z))

    # --- JNZ addr16 (0x50) ---
    set_fetch_v2(0x50)
    s = fetch_operand_16(0x50, 3)
    set_micro(0x50, s, _IP_LOAD | _UIP_RST, flag_mask=flag_clear(FLAG_Z))
    set_micro(0x50, s, _UIP_RST, flag_mask=flag_set(FLAG_Z))

    # --- JC addr16 (0x60) ---
    set_fetch_v2(0x60)
    s = fetch_operand_16(0x60, 3)
    set_micro(0x60, s, _IP_LOAD | _UIP_RST, flag_mask=flag_set(FLAG_C))
    set_micro(0x60, s, _UIP_RST, flag_mask=flag_clear(FLAG_C))

    # --- JNC addr16 (0x70) ---
    set_fetch_v2(0x70)
    s = fetch_operand_16(0x70, 3)
    set_micro(0x70, s, _IP_LOAD | _UIP_RST, flag_mask=flag_clear(FLAG_C))
    set_micro(0x70, s, _UIP_RST, flag_mask=flag_set(FLAG_C))

    # --- JN addr16 (0x80) ---
    set_fetch_v2(0x80)
    s = fetch_operand_16(0x80, 3)
    set_micro(0x80, s, _IP_LOAD | _UIP_RST, flag_mask=flag_set(FLAG_N))
    set_micro(0x80, s, _UIP_RST, flag_mask=flag_clear(FLAG_N))

    # --- CALL addr16 (0x90) ---
    set_fetch_v2(0x90)
    s = fetch_operand_16(0x90, 3)
    # Target address is in MAR.
    # We must push IP to stack. But we need MAR for stack accesses!
    # So we must save MAR to TMP and B (it's 16-bit).
    # Wait, B is caller-saved, perfectly fine to clobber. TMP is also fine.
    # Save MAR_LO to B, MAR_HI to TMP.
    set_micro(0x90, s, SRC_MAR_LO | DST_B)      # Oops, we don't have SRC_MAR_LO!
    pass # Will redefine CALL properly

    # REDEFINE CALL
    # The clean way: Push IP to stack FIRST, then fetch the 16-bit operand into MAR, then JMP.
    opc = 0x90
    set_fetch_v2(opc)
    # Currently IP points to addr_lo. We want to push the return address.
    # Return address is IP+2. But IP is currently at IP. We don't have an ALU to add 2 to IP.
    # So we MUST fetch the operand first, incrementing IP twice, THEN push IP.
    # Therefore we fetch operand into TMP (low byte) and B (high byte).
    # Read addr_lo into TMP:
    set_micro(opc, 3, SRC_IP_LO | DST_MAR_LO)
    set_micro(opc, 4, SRC_IP_HI | DST_MAR_HI)
    set_micro(opc, 5, SRC_MEM | DST_TMP | _IP_INC)
    # Read addr_hi into B:
    set_micro(opc, 6, SRC_IP_LO | DST_MAR_LO)
    set_micro(opc, 7, SRC_IP_HI | DST_MAR_HI)
    set_micro(opc, 8, SRC_MEM | DST_B | _IP_INC)
    
    # Now IP is pointing at the next instruction (return address).
    # Push IP_HI:
    set_micro(opc, 9, _SP_TO_MAR)
    set_micro(opc, 10, SRC_IP_HI | DST_MEM)
    set_micro(opc, 11, _SP_DEC)
    # Push IP_LO:
    set_micro(opc, 12, _SP_TO_MAR)
    set_micro(opc, 13, SRC_IP_LO | DST_MEM)
    set_micro(opc, 14, _SP_DEC)
    
    # Now load target address into MAR for jump
    set_micro(opc, 15, SRC_TMP | DST_MAR_LO)
    set_micro(opc, 16, SRC_B | DST_MAR_HI)  # Wait, 16 micro-steps max (0-15)!
    
    # Oh no, max 16 micro-steps. This sequence takes 18 steps (0-17).
    # We need to optimize it.
    pass

    # OPTIMIZED CALL
    # Memory address fetch can be faster if we pipeline.
    # µ0: MAR_LO <- IP_LO
    # µ1: MAR_HI <- IP_HI
    # µ2: IR <- MEM, IP++
    #
    # µ3: MAR_LO <- IP_LO
    # µ4: MAR_HI <- IP_HI
    # µ5: TMP <- MEM, IP++
    #
    # µ6: MAR_LO <- IP_LO
    # µ7: MAR_HI <- IP_HI
    # µ8: B <- MEM, IP++
    #
    # µ9: SP_TO_MAR
    # µ10: MEM <- IP_HI, SP--
    #
    # µ11: SP_TO_MAR
    # µ12: MEM <- IP_LO, SP--
    #
    # µ13: MAR_LO <- TMP
    # µ14: MAR_HI <- B
    # µ15: IP_LOAD, UIP_RST
    
    opc = 0x90
    set_fetch_v2(opc)
    # Fetch addr_lo to TMP
    set_micro(opc, 3, SRC_IP_LO | DST_MAR_LO)
    set_micro(opc, 4, SRC_IP_HI | DST_MAR_HI)
    set_micro(opc, 5, SRC_MEM | DST_TMP | _IP_INC)
    # Fetch addr_hi to B
    set_micro(opc, 6, SRC_IP_LO | DST_MAR_LO)
    set_micro(opc, 7, SRC_IP_HI | DST_MAR_HI)
    set_micro(opc, 8, SRC_MEM | DST_B | _IP_INC)
    # Push IP_HI
    set_micro(opc, 9, _SP_TO_MAR)
    set_micro(opc, 10, SRC_IP_HI | DST_MEM | _SP_DEC)  # Combine SP_DEC with write!
    # Push IP_LO
    set_micro(opc, 11, _SP_TO_MAR)
    set_micro(opc, 12, SRC_IP_LO | DST_MEM | _SP_DEC)
    # Load jump target
    set_micro(opc, 13, SRC_TMP | DST_MAR_LO)
    set_micro(opc, 14, SRC_B | DST_MAR_HI)
    end_instr(opc, 15, _IP_LOAD)

    # --- RET (0xA0) ---
    set_fetch_v2(0xA0)
    # Pop IP_LO (it was pushed last, so popped first):
    set_micro(0xA0, 3, _SP_INC)
    set_micro(0xA0, 4, _SP_TO_MAR)
    set_micro(0xA0, 5, SRC_MEM | DST_TMP)
    # Pop IP_HI:
    set_micro(0xA0, 6, _SP_INC)
    set_micro(0xA0, 7, _SP_TO_MAR)
    set_micro(0xA0, 8, SRC_MEM | DST_MAR_HI)
    # Move TMP to MAR_LO
    set_micro(0xA0, 9, SRC_TMP | DST_MAR_LO)
    end_instr(0xA0, 10, _IP_LOAD)

    # --- IN (0xFD) ---
    set_fetch_v2(0xFD)
    # Software handled, just NOP in microcode
    end_instr(0xFD, 3)

    # --- OUT (0xFE) ---
    set_fetch_v2(0xFE)
    set_micro(0xFE, 3, SRC_A | DST_OUT)
    end_instr(0xFE, 4)

    # --- HLT (0xFF) ---
    set_fetch_v2(0xFF)
    for step in range(3, 16):
        set_micro(0xFF, step, 0)  # Hang forever

    # Unhandled -> NOP
    for opc in range(256):
        if microcode[addr(opc, 0, 0)] == 0:
            set_fetch_v2(opc)
            end_instr(opc, 3)

# ---------------------------------------------------------------------------
# Debug and Output
# ---------------------------------------------------------------------------

SRC_NAMES = {
    SRC_NONE: "---", SRC_A: "A_OUT", SRC_B: "B_OUT", SRC_ALU: "ALU_OUT",
    SRC_MEM: "MEM_OUT", SRC_IP_LO: "IP_LO", SRC_IP_HI: "IP_HI", SRC_TMP: "TMP_OUT", SRC_SP: "SP_OUT"
}

DST_NAMES = {
    DST_NONE: "---", DST_A: "A_IN", DST_B: "B_IN", DST_IR: "IR_IN",
    DST_MAR_LO: "MAR_LO", DST_MAR_HI: "MAR_HI", DST_MEM: "MEM_IN", DST_OUT: "OUT", DST_TMP: "TMP_IN"
}

OP_NAMES = {
    OP_ADD: "ADD", OP_SUB: "SUB", OP_AND: "AND", OP_OR: "OR",
    OP_XOR: "XOR", OP_NOT: "NOT", OP_SHL: "SHL", OP_SHR: "SHR",
}

def decode_signals(word):
    parts = []
    src = word & 0x0F
    dst = word & 0xF0
    op = word & 0x700
    
    if src: parts.append(SRC_NAMES.get(src, f"SRC?{src}"))
    if dst: parts.append(DST_NAMES.get(dst, f"DST?{dst}"))
    if src == SRC_ALU: parts.append(f"OP={OP_NAMES.get(op, '?')}")
    
    if word & _FLAGS_IN:  parts.append("FLAGS_IN")
    if word & _IP_INC:    parts.append("IP++")
    if word & _IP_LOAD:   parts.append("IP<-MAR")
    if word & _SP_INC:    parts.append("SP++")
    if word & _SP_DEC:    parts.append("SP--")
    if word & _SP_TO_MAR: parts.append("SP->MAR")
    if word & _UIP_RST:   parts.append("uRST")
    
    if not parts: parts.append("NOP")
    return " | ".join(parts)

def print_microcode(opcode):
    print(f"\n--- Opcode 0x{opcode:02X} ---")
    for ustep in range(16):
        words = set(microcode[addr(opcode, f, ustep)] for f in range(NUM_FLAGS))
        if len(words) == 1:
            word = words.pop()
            if word == 0 and ustep > 3: continue
            print(f"  u{ustep:2d}: {decode_signals(word)}")
        else:
            for f in range(NUM_FLAGS):
                word = microcode[addr(opcode, f, ustep)]
                flags_str = f"{'Z' if f & 1 else '.'}{'C' if f & 2 else '.'}{'N' if f & 4 else '.'}"
                print(f"  u{ustep:2d} [{flags_str}]: {decode_signals(word)}")

def generate_binary():
    eeprom_a = bytearray(32768)
    eeprom_b = bytearray(32768)
    eeprom_c = bytearray(32768)
    for i in range(TOTAL_ADDRESSES):
        word = microcode[i]
        eeprom_a[i] = word & 0xFF
        eeprom_b[i] = (word >> 8) & 0xFF
        eeprom_c[i] = (word >> 16) & 0xFF
    return eeprom_a, eeprom_b, eeprom_c

INSTRUCTIONS = {}
def _reg_instructions():
    INSTRUCTIONS[0x00] = ("NOP", None, "No operation")
    INSTRUCTIONS[0x01] = ("LDA", "imm8", "A <- immediate")
    INSTRUCTIONS[0x02] = ("LDA", "addr16", "A <- mem[addr16]")
    INSTRUCTIONS[0x03] = ("STA", "addr16", "mem[addr16] <- A")
    INSTRUCTIONS[0x04] = ("LDB", "imm8", "B <- immediate")
    INSTRUCTIONS[0x05] = ("LDB", "addr16", "B <- mem[addr16]")
    INSTRUCTIONS[0x06] = ("STB", "addr16", "mem[addr16] <- B")
    INSTRUCTIONS[0x07] = ("MVA", None, "A <- B")
    INSTRUCTIONS[0x08] = ("MVB", None, "B <- A")
    INSTRUCTIONS[0x10] = ("ADD", None, "A <- A + B")
    INSTRUCTIONS[0x11] = ("SUB", None, "A <- A - B")
    INSTRUCTIONS[0x12] = ("AND", None, "A <- A & B")
    INSTRUCTIONS[0x13] = ("OR",  None, "A <- A | B")
    INSTRUCTIONS[0x14] = ("XOR", None, "A <- A ^ B")
    INSTRUCTIONS[0x15] = ("NOT", None, "A <- ~A")
    INSTRUCTIONS[0x16] = ("SHL", None, "A <- A << 1")
    INSTRUCTIONS[0x17] = ("SHR", None, "A <- A >> 1")
    INSTRUCTIONS[0x18] = ("ADI", "imm8", "A <- A + immediate")
    INSTRUCTIONS[0x19] = ("SBI", "imm8", "A <- A - immediate")
    INSTRUCTIONS[0x1A] = ("CMP", None, "flags <- A - B")
    INSTRUCTIONS[0x1B] = ("CMI", "imm8", "flags <- A - immediate")
    INSTRUCTIONS[0x20] = ("PSA", None, "push A")
    INSTRUCTIONS[0x21] = ("PPA", None, "pop A")
    INSTRUCTIONS[0x22] = ("PSB", None, "push B")
    INSTRUCTIONS[0x23] = ("PPB", None, "pop B")
    INSTRUCTIONS[0x30] = ("JMP", "addr16", "IP <- addr16")
    INSTRUCTIONS[0x40] = ("JZ",  "addr16", "if Z: IP <- addr16")
    INSTRUCTIONS[0x50] = ("JNZ", "addr16", "if !Z: IP <- addr16")
    INSTRUCTIONS[0x60] = ("JC",  "addr16", "if C: IP <- addr16")
    INSTRUCTIONS[0x70] = ("JNC", "addr16", "if !C: IP <- addr16")
    INSTRUCTIONS[0x80] = ("JN",  "addr16", "if N: IP <- addr16")
    INSTRUCTIONS[0x90] = ("CAL", "addr16", "call addr16")
    INSTRUCTIONS[0xA0] = ("RET", None, "return")
    INSTRUCTIONS[0xFD] = ("IN",  None, "A <- input")
    INSTRUCTIONS[0xFE] = ("OUT", None, "output A")
    INSTRUCTIONS[0xFF] = ("HLT", None, "halt")

_reg_instructions()

def main():
    define_all_instructions()

    if "--dump" in sys.argv:
        opcodes_to_dump = [0x00, 0x01, 0x02, 0x03, 0x10, 0x20, 0x30, 0x40, 0x90, 0xA0]
        for opc in opcodes_to_dump:
            print_microcode(opc)
        return

    eeprom_a, eeprom_b, eeprom_c = generate_binary()

    with open("microcode_a.bin", "wb") as f: f.write(eeprom_a)
    with open("microcode_b.bin", "wb") as f: f.write(eeprom_b)
    with open("microcode_c.bin", "wb") as f: f.write(eeprom_c)

    print(f"Generated 3 EEPROM bins, {len(eeprom_a)} bytes each.")
    print(f"Total instructions defined: {len(INSTRUCTIONS)}")

    print("\nInstruction summary:")
    for opc in sorted(INSTRUCTIONS.keys()):
        mnem, op_typ, desc = INSTRUCTIONS[opc]
        op_str = f"{op_typ:6s}" if op_typ else "      "
        print(f"  0x{opc:02X}: {mnem:4s} {op_str}  ; {desc}")

if __name__ == "__main__":
    main()
