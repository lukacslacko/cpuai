import os

# 24-bit control word fields
# Data Bus Source (0-3)
DS_NONE = 0
DS_A = 1
DS_B = 2
DS_C = 3
DS_D = 4
DS_ALU = 5
DS_MEM = 6
DS_IP_LO = 7
DS_IP_HI = 8
DS_SP = 9

# Data Bus Dest (4-7)
DD_NONE = 0 << 4
DD_A = 1 << 4
DD_B = 2 << 4
DD_C = 3 << 4
DD_D = 4 << 4
DD_IR = 5 << 4
DD_MEM = 6 << 4
DD_IP_LO = 7 << 4
DD_IP_HI = 8 << 4
DD_SP = 9 << 4
DD_OUT = 10 << 4

# Address Source (8-9)
AS_IP = 0 << 8
AS_CD = 1 << 8
AS_SP_IDX = 2 << 8

# ALU Ops (10-12)
ALU_ADD = 0 << 10
ALU_SUB = 1 << 10
ALU_AND = 2 << 10
ALU_OR  = 3 << 10
ALU_XOR = 4 << 10
ALU_NOT = 5 << 10
ALU_SHL = 6 << 10
ALU_SHR = 7 << 10

# Misc Flags (13-18)
FLAGS_IN = 1 << 13
IP_INC   = 1 << 14
SP_INC   = 1 << 15
SP_DEC   = 1 << 16
uIP_RST  = 1 << 17
HLT      = 1 << 18

INSTRUCTIONS = {}

def instruction(opcode, name, *steps):
    INSTRUCTIONS[opcode] = (name, steps)

# Fetch cycle is always the same for every instruction
FETCH = AS_IP | DS_MEM | DD_IR | IP_INC

# Opcode map
# 0x00: NOP
instruction(0x00, "NOP", uIP_RST)

# 0x01-0x04: Load Immediate into A, B, C, D
instruction(0x01, "LDA #imm", AS_IP | DS_MEM | DD_A | IP_INC, uIP_RST)
instruction(0x02, "LDB #imm", AS_IP | DS_MEM | DD_B | IP_INC, uIP_RST)
instruction(0x03, "LDC #imm", AS_IP | DS_MEM | DD_C | IP_INC, uIP_RST)
instruction(0x04, "LDD #imm", AS_IP | DS_MEM | DD_D | IP_INC, uIP_RST)

# 0x05, 0x06: LDA [addr16], STA [addr16] - Wait, we can do these with C/D directly but let's provide macros using C/D as temps
# No wait! [addr16] fetches a 16-bit address. We can just clobber C and D.
instruction(0x05, "LDA [addr16]", 
    AS_IP | DS_MEM | DD_C | IP_INC, # fetch low addr byte -> C
    AS_IP | DS_MEM | DD_D | IP_INC, # fetch high addr byte -> D
    AS_CD | DS_MEM | DD_A,          # A <- MEM[C:D]
    uIP_RST)

instruction(0x06, "STA [addr16]", 
    AS_IP | DS_MEM | DD_C | IP_INC, 
    AS_IP | DS_MEM | DD_D | IP_INC, 
    AS_CD | DS_A | DD_MEM,          # MEM[C:D] <- A
    uIP_RST)

instruction(0x07, "LDB [addr16]", 
    AS_IP | DS_MEM | DD_C | IP_INC, 
    AS_IP | DS_MEM | DD_D | IP_INC, 
    AS_CD | DS_MEM | DD_B,          
    uIP_RST)

instruction(0x08, "STB [addr16]", 
    AS_IP | DS_MEM | DD_C | IP_INC, 
    AS_IP | DS_MEM | DD_D | IP_INC, 
    AS_CD | DS_B | DD_MEM,          
    uIP_RST)

# 0x1x: Moves
def make_mov(opcode, name, src, dst):
    instruction(opcode, name, src | dst, uIP_RST)

make_mov(0x18, "MVA B", DS_B, DD_A)
make_mov(0x19, "MVA C", DS_C, DD_A)
make_mov(0x1A, "MVA D", DS_D, DD_A)
make_mov(0x1B, "MVB A", DS_A, DD_B)
make_mov(0x1C, "MVC A", DS_A, DD_C)
make_mov(0x1D, "MVD A", DS_A, DD_D)

# 0x2x: ALU operations (A <- A op B)
def make_alu(opcode, name, alu_op):
    instruction(opcode, name, DS_ALU | alu_op | DD_A | FLAGS_IN, uIP_RST)

make_alu(0x20, "ADD", ALU_ADD)
make_alu(0x21, "SUB", ALU_SUB)
make_alu(0x22, "AND", ALU_AND)
make_alu(0x23, "OR",  ALU_OR)
make_alu(0x24, "XOR", ALU_XOR)
make_alu(0x25, "NOT", ALU_NOT)
make_alu(0x26, "SHL", ALU_SHL)
make_alu(0x27, "SHR", ALU_SHR)
# CMP only updates flags
instruction(0x28, "CMP", DS_ALU | ALU_SUB | FLAGS_IN, uIP_RST)

# 0x3x: Stack Ops (Push A, Pop A) -> SP mapped directly.
# PSH A: MEM[0xFF00 + SP] <- A; SP--
# SP_IDX automatically prepends 0xFF to high byte.
instruction(0x30, "PSH A", 
    # To use SP without index, ensure IR[3:0] is 0! So opcode must end in 0. 0x30 ends in 0.
    AS_SP_IDX | DS_A | DD_MEM,
    SP_DEC,
    uIP_RST)

instruction(0x31, "POP A",
    SP_INC,
    AS_SP_IDX | DS_MEM | DD_A,
    uIP_RST)

instruction(0x32, "PSH B", 
    AS_SP_IDX | DS_B | DD_MEM,
    SP_DEC,
    uIP_RST)

# Let's cleanly separate PUSH and POP
instruction(0x30, "PSH A", AS_SP_IDX | DS_A | DD_MEM, SP_DEC, uIP_RST)
instruction(0x40, "POP A", SP_INC, AS_SP_IDX | DS_MEM | DD_A, uIP_RST)
instruction(0x50, "PSH B", AS_SP_IDX | DS_B | DD_MEM, SP_DEC, uIP_RST)
instruction(0x60, "POP B", SP_INC, AS_SP_IDX | DS_MEM | DD_B, uIP_RST)
instruction(0x90, "PSH C", AS_SP_IDX | DS_C | DD_MEM, SP_DEC, uIP_RST)
instruction(0xA0, "POP C", SP_INC, AS_SP_IDX | DS_MEM | DD_C, uIP_RST)
instruction(0xB0, "PSH D", AS_SP_IDX | DS_D | DD_MEM, SP_DEC, uIP_RST)
instruction(0x10, "POP D", SP_INC, AS_SP_IDX | DS_MEM | DD_D, uIP_RST)

# 0xC0-0xCF: LSA imm4 (Load SP-relative to A)
# Opcode provides IR[3:0] as index.
for i in range(16):
    instruction(0xC0 + i, f"LSA {i}", AS_SP_IDX | DS_MEM | DD_A, uIP_RST)

# 0xD0-0xDF: SSA imm4 (Store SP-relative from A)
for i in range(16):
    instruction(0xD0 + i, f"SSA {i}", AS_SP_IDX | DS_A | DD_MEM, uIP_RST)

# 0xE0-0xEF: LSB imm4 
for i in range(16):
    instruction(0xE0 + i, f"LSB {i}", AS_SP_IDX | DS_MEM | DD_B, uIP_RST)

# 0xF0-0xFF: SSB imm4
for i in range(16):
    instruction(0xF0 + i, f"SSB {i}", AS_SP_IDX | DS_B | DD_MEM, uIP_RST)

# Jumps
# We use opcodes ending in 0-9 for JMPs
instruction(0x70, "JMP addr16",
    AS_IP | DS_MEM | DD_C | IP_INC, # fetch low
    AS_IP | DS_MEM | DD_IP_HI,      # fetch high right into IP_HI
    DS_C | DD_IP_LO,                # C to IP_LO (changes IP entirely)
    uIP_RST)

def make_jx(opcode, name, flag_cond_func):
    # Instead of defining conditional microcode dynamically, we generate the full 32KB array.
    pass

# We will handle JX in the ROM generation explicitly based on FLAGS (A4-A6).
# FLAGS mapping: Z=A4, C=A5, N=A6

# CALL and RET
instruction(0x80, "CALL addr16",
    AS_IP | DS_MEM | DD_C | IP_INC, # C <- low addr
    AS_IP | DS_MEM | DD_D | IP_INC, # D <- high addr
    DS_IP_HI | DD_A,                # A <- return addr high
    DS_IP_LO | DD_B,                # B <- return addr low
    DS_D | DD_IP_HI,                # IP_HI <- D
    DS_C | DD_IP_LO,                # IP_LO <- C
    uIP_RST)

instruction(0x81, "RET",
    DS_D | DD_IP_HI,
    DS_C | DD_IP_LO,
    uIP_RST)

instruction(0x82, "HLT", HLT)

instruction(0x83, "IN A", DS_NONE, DD_A, uIP_RST) # Assuming IN port is mapped to DS_NONE? No, we didn't define DS_IN. Let's ignore IN/OUT for now or map OUT.
instruction(0x84, "OUT A", DS_A | DD_OUT, uIP_RST)

# Conditionals mapping
# Z=bit 0, C=bit 1, N=bit 2
JUMP_MAP = {
    0x71: lambda flags: (flags & 1) != 0, # JZ
    0x72: lambda flags: (flags & 1) == 0, # JNZ
    0x73: lambda flags: (flags & 2) != 0, # JC
    0x74: lambda flags: (flags & 2) == 0, # JNC
    0x75: lambda flags: (flags & 4) != 0, # JN
}

def generate_microcode():
    rom1 = bytearray(32768)
    rom2 = bytearray(32768)
    rom3 = bytearray(32768)
    
    # Pre-fill with NOP
    for i in range(32768):
        rom1[i] = uIP_RST & 0xFF
        rom2[i] = (uIP_RST >> 8) & 0xFF
        rom3[i] = (uIP_RST >> 16) & 0xFF

    for addr in range(32768):
        uip = addr & 0x0F
        flags = (addr >> 4) & 0x07
        ir = (addr >> 7) & 0xFF
        
        cw = 0
        if uip == 0:
            cw = FETCH
        else:
            if ir in JUMP_MAP:
                if JUMP_MAP[ir](flags):
                    # Condition true: perform jump
                    steps = [
                        AS_IP | DS_MEM | DD_C | IP_INC, 
                        AS_IP | DS_MEM | DD_IP_HI,      
                        DS_C | DD_IP_LO,                
                        uIP_RST
                    ]
                else:
                    # Condition false: skip 2 bytes (the 16-bit address)
                    steps = [
                        IP_INC,
                        IP_INC,
                        uIP_RST
                    ]
                
                if uip - 1 < len(steps):
                    cw = steps[uip - 1]
                else:
                    cw = uIP_RST
            elif ir in INSTRUCTIONS:
                _, steps = INSTRUCTIONS[ir]
                if uip - 1 < len(steps):
                    cw = steps[uip - 1]
                else:
                    cw = uIP_RST
            else:
                cw = uIP_RST
                
        rom1[addr] = cw & 0xFF
        rom2[addr] = (cw >> 8) & 0xFF
        rom3[addr] = (cw >> 16) & 0xFF

    with open('microcode_a.bin', 'wb') as f: f.write(rom1)
    with open('microcode_b.bin', 'wb') as f: f.write(rom2)
    with open('microcode_c.bin', 'wb') as f: f.write(rom3)
    print("Generated microcode_a.bin, microcode_b.bin, microcode_c.bin")

if __name__ == "__main__":
    generate_microcode()
    print("Done")
