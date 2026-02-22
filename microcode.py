import os

# 24-bit control word fields
# Data Bus Source (bits 0-3, 16 possible sources)
DS_NONE     = 0
DS_A        = 1
DS_B        = 2
DS_C        = 3
DS_D        = 4
DS_ALU      = 5
DS_MEM      = 6
DS_IPL      = 7   # IP low byte -> data bus
DS_IPH      = 8   # IP high byte -> data bus
DS_SP       = 9   # SP -> data bus (low byte)
DS_CONST_FF = 10  # constant 0xFF -> data bus

# Data Bus Dest (bits 4-7, 16 possible dests)
DD_NONE   = 0  << 4
DD_A      = 1  << 4
DD_B      = 2  << 4
DD_C      = 3  << 4
DD_D      = 4  << 4
DD_IR     = 5  << 4
DD_MEM    = 6  << 4
DD_H      = 7  << 4   # -> H register (drives ADDR[15:8])
DD_L      = 8  << 4   # -> L register (drives ADDR[7:0])
DD_IPL    = 9  << 4   # -> IP low byte (load IPL from data bus)
DD_IPH    = 10 << 4   # -> IP high byte (load IPH from data bus)
DD_SP     = 11 << 4   # -> SP load from data bus
DD_OUT    = 12 << 4   # -> OUT port

# Bits 8-9: unused (were AS_IP/AS_CD/AS_SP_IDX)

# ALU Ops (bits 10-12)
ALU_ADD = 0 << 10
ALU_SUB = 1 << 10
ALU_AND = 2 << 10
ALU_OR  = 3 << 10
ALU_XOR = 4 << 10
ALU_NOT = 5 << 10
ALU_SHL = 6 << 10
ALU_SHR = 7 << 10

# Misc Flags (bits 13-18)
FLAGS_IN = 1 << 13
IP_INC_L = 1 << 14  # Increment IPL and latch new value into L register (DD_L must also be set)
SP_INC   = 1 << 15
SP_DEC   = 1 << 16
uIP_RST  = 1 << 17
HLT      = 1 << 18

INSTRUCTIONS = {}

def instruction(opcode, name, *steps):
    INSTRUCTIONS[opcode] = (name, steps)

# ---------------------------------------------------------------------------
# Fetch model: uIP=0,1,2 are ALWAYS the 3-step fetch sequence.
# Instruction bodies start at uIP=3.
#
# FETCH0 (uIP=0): IPL++ and latch into L (IP_INC_L | DD_L)
#   - IP advances, new IPL goes onto data bus, L captures it -> ADDR[7:0] = new IPL
# FETCH1 (uIP=1): IPH -> data bus -> H (DS_IPH | DD_H)
#   - H = IPH -> ADDR[15:8] = IPH. Now HL = full IP address.
# FETCH2 (uIP=2): MEM[H:L] -> IR (DS_MEM | DD_IR)
#   - Reads opcode from memory into IR. uIP continues to 3.
#
# Memory read of immediate/operand bytes (same-page safe):
#   Step A: IP_INC_L | DD_L  -> advance IPL, latch into L (H stays valid = IPH)
#   Step B: DS_MEM | DD_reg  -> read byte from MEM[H:L] into register
#
# Every instruction ends with uIP_RST which resets uIP to 0 -> triggers next FETCH.
# ---------------------------------------------------------------------------

FETCH0 = IP_INC_L | DD_L          # uIP=0: IPL++ -> L
FETCH1 = DS_IPH   | DD_H          # uIP=1: IPH -> H
FETCH2 = DS_MEM   | DD_IR         # uIP=2: MEM[H:L] -> IR (uIP proceeds to 3)

# Shorthand for reading next byte from IP (H already valid for same page)
def READ_NEXT(dest_dd):
    """Two microsteps: advance IPL->L, then read MEM->dest."""
    return (IP_INC_L | DD_L, DS_MEM | dest_dd)

# ---------------------------------------------------------------------------
# Instruction definitions (bodies start at uIP=3)
# ---------------------------------------------------------------------------

# NOP
instruction(0x00, "NOP", uIP_RST)

# 0x01-0x04: Load Immediate into A, B, C, D
instruction(0x01, "LDA #imm", IP_INC_L | DD_L, DS_MEM | DD_A | uIP_RST)
instruction(0x02, "LDB #imm", IP_INC_L | DD_L, DS_MEM | DD_B | uIP_RST)
instruction(0x03, "LDC #imm", IP_INC_L | DD_L, DS_MEM | DD_C | uIP_RST)
instruction(0x04, "LDD #imm", IP_INC_L | DD_L, DS_MEM | DD_D | uIP_RST)

# 0x05: LDA [addr16] - read 16-bit address (lo,hi) then load A from MEM[addr]
# Steps: read low byte -> C, read high byte -> H, move C -> L, MEM[H:L] -> A
#        then restore H = IPH (ready for next fetch)
instruction(0x05, "LDA [addr16]",
    IP_INC_L | DD_L,       # step 3: advance IPL -> L
    DS_MEM   | DD_C,       # step 4: read lo addr byte -> C
    IP_INC_L | DD_L,       # step 5: advance IPL -> L
    DS_MEM   | DD_H,       # step 6: read hi addr byte -> H (ADDR hi now = target hi)
    DS_C     | DD_L,       # step 7: C -> L (ADDR lo = target lo). Now HL = target addr.
    DS_MEM   | DD_A,       # step 8: A = MEM[H:L]
    DS_IPH   | DD_H,       # step 9: restore H = IPH
    uIP_RST)

# 0x06: STA [addr16]
instruction(0x06, "STA [addr16]",
    IP_INC_L | DD_L,
    DS_MEM   | DD_C,
    IP_INC_L | DD_L,
    DS_MEM   | DD_H,
    DS_C     | DD_L,       # HL = target addr
    DS_A     | DD_MEM,     # MEM[H:L] = A
    DS_IPH   | DD_H,       # restore H = IPH
    uIP_RST)

# 0x07: LDB [addr16]
instruction(0x07, "LDB [addr16]",
    IP_INC_L | DD_L,
    DS_MEM   | DD_C,
    IP_INC_L | DD_L,
    DS_MEM   | DD_H,
    DS_C     | DD_L,
    DS_MEM   | DD_B,
    DS_IPH   | DD_H,
    uIP_RST)

# 0x08: STB [addr16]
instruction(0x08, "STB [addr16]",
    IP_INC_L | DD_L,
    DS_MEM   | DD_C,
    IP_INC_L | DD_L,
    DS_MEM   | DD_H,
    DS_C     | DD_L,
    DS_B     | DD_MEM,
    DS_IPH   | DD_H,
    uIP_RST)

# 0x1x: Moves (register to register, 1 byte, single body step)
def make_mov(opcode, name, src, dst):
    instruction(opcode, name, src | dst | uIP_RST)

make_mov(0x18, "TBA", DS_B, DD_A)   # Transfer B -> A
make_mov(0x19, "TCA", DS_C, DD_A)   # Transfer C -> A
make_mov(0x1A, "TDA", DS_D, DD_A)   # Transfer D -> A
make_mov(0x1B, "TAB", DS_A, DD_B)   # Transfer A -> B
make_mov(0x1C, "TAC", DS_A, DD_C)   # Transfer A -> C
make_mov(0x1D, "TAD", DS_A, DD_D)   # Transfer A -> D

# 0x2x: ALU operations (A <- A op B)
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
# CMP only updates flags
instruction(0x28, "CMP", DS_ALU | ALU_SUB | FLAGS_IN | uIP_RST)

# ---------------------------------------------------------------------------
# Stack operations.
# SP is 8-bit. Stack lives at 0xFF00-0xFFFF.
# For MEM access: H = 0xFF (DS_CONST_FF | DD_H), L = SP (DS_SP | DD_L)
# ---------------------------------------------------------------------------

# PSH A: MEM[0xFF:SP] <- A; SP--
instruction(0x30, "PSH A",
    DS_CONST_FF | DD_H,     # H = 0xFF
    DS_SP       | DD_L,     # L = SP -> HL = 0xFF:SP
    DS_A        | DD_MEM,   # MEM[H:L] = A
    SP_DEC,                 # SP--
    DS_IPH      | DD_H,     # restore H = IPH
    uIP_RST)

# POP A: SP++; A <- MEM[0xFF:SP]
instruction(0x40, "POP A",
    SP_INC,
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_MEM      | DD_A,
    DS_IPH      | DD_H,
    uIP_RST)

# PSH B
instruction(0x50, "PSH B",
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_B        | DD_MEM,
    SP_DEC,
    DS_IPH      | DD_H,
    uIP_RST)

# POP B
instruction(0x60, "POP B",
    SP_INC,
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_MEM      | DD_B,
    DS_IPH      | DD_H,
    uIP_RST)

# PSH C
instruction(0x90, "PSH C",
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_C        | DD_MEM,
    SP_DEC,
    DS_IPH      | DD_H,
    uIP_RST)

# POP C
instruction(0xA0, "POP C",
    SP_INC,
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_MEM      | DD_C,
    DS_IPH      | DD_H,
    uIP_RST)

# PSH D
instruction(0xB0, "PSH D",
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_D        | DD_MEM,
    SP_DEC,
    DS_IPH      | DD_H,
    uIP_RST)

# POP D
instruction(0x10, "POP D",
    SP_INC,
    DS_CONST_FF | DD_H,
    DS_SP       | DD_L,
    DS_MEM      | DD_D,
    DS_IPH      | DD_H,
    uIP_RST)

# ---------------------------------------------------------------------------
# SP-relative load/store: LSA imm4, SSA imm4, LSB imm4, SSB imm4
# The imm4 offset is encoded in IR[3:0].
# For SP-relative: address = 0xFF00 + (SP + IR[3:0])
# We use the ALU adder: A = SP, B = IR[3:0] embedded in... wait, we don't 
# have a SP+offset adder anymore. Instead we can precompute: 
#   LDC #offset; then add SP -> use ALU ADD with A=SP, B=imm.
# But these are 1-byte opcodes where the offset is in the opcode itself.
# Without a hardware adder, we need to put SP into A (or B), and the offset
# from IR into B (or A), add, then use result as L.
# We can do: DS_SP | DD_A (put SP in A), DS_IR_LO4 ... but we have no DS_IR.
# 
# Alternative: encode as 2-byte instructions (opcode + offset byte), freeing
# us from the SP+IR offset trick. Let's use 2-byte LSA/SSA/LSB/SSB:
# Opcode 0xC0 = LSA, operand = offset byte, 0xD0 = SSA, 0xE0 = LSB, 0xF0 = SSB
# We now only need 4 opcodes (not 64).
#
# For SP+offset: we'll use A as temp: SP -> A, LDA imm offset -> B, ADD, result -> L
# Actually even simpler - since SP is 8-bit and offset is 0-15 and stack is at 0xFF00:
#   H = 0xFF, compute SP+offset in ALU, L = result
# But ALU inputs are A and B. We need SP in A or B, and offset from somewhere.
# Let's: DS_SP | DD_A (put SP into A), then the offset byte from MEM into B,
# then ALU ADD -> L. That works!
# ---------------------------------------------------------------------------

# 0xC0: LSA offset  (2-byte: opcode + offset)
instruction(0xC0, "LSA off",
    IP_INC_L    | DD_L,        # advance IPL -> L (addr = IP+1)
    DS_MEM      | DD_B,        # B = offset byte
    DS_SP       | DD_A,        # A = SP (clobbers A!)
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset (ALU A+B)
    DS_CONST_FF | DD_H,        # H = 0xFF
    DS_MEM      | DD_A,        # A = MEM[0xFF:(SP+offset)]
    DS_IPH      | DD_H,        # restore H
    uIP_RST)

# 0xD0: SSA offset  (2-byte: opcode + offset) - stores A into SP+offset
# But we just clobbered A above... we need to save A first. Actually for SSA
# the value we want to store IS A, so we need a different order. Let's save
# the mem addr first, then write A.
instruction(0xD0, "SSA off",
    IP_INC_L    | DD_L,        # advance IPL -> L
    DS_MEM      | DD_B,        # B = offset byte
    DS_SP       | DD_D,        # D = SP (use D as temp, save A!)
    DS_D        | DD_A,        # A = SP (now A=SP, D=SP)
    # Wait, we need A=SP to do ALU ADD, but A holds the store value.
    # Better: save A -> D first, compute addr, store D.
    uIP_RST)
# Actually this is getting complex. Let's rethink SSA:
# Save A -> C (temp). A = SP. B = offset. ADD -> L. H=0xFF. MEM[HL] = C.
# But we only have A,B,C,D and we clobber them. Users of SSA know it clobbers.
# Let's use: D = A (save), A = SP, B = offset, L = ALU(A+B), H=0xFF, MEM=D, restore H
instruction(0xD0, "SSA off",
    DS_A        | DD_D,        # D = A (save store value)
    IP_INC_L    | DD_L,        # advance IPL -> L
    DS_MEM      | DD_B,        # B = offset byte
    DS_SP       | DD_A,        # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,        # H = 0xFF
    DS_D        | DD_MEM,      # MEM[H:L] = D (= original A)
    DS_IPH      | DD_H,        # restore H
    uIP_RST)

# 0xE0: LSB offset  (2-byte) - load B from SP+offset. Clobbers A.
instruction(0xE0, "LSB off",
    IP_INC_L    | DD_L,
    DS_MEM      | DD_B,        # B = offset (will be overwritten by result)
    DS_SP       | DD_A,        # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_MEM      | DD_B,        # B = MEM[0xFF:(SP+offset)]
    DS_IPH      | DD_H,
    uIP_RST)

# 0xF0: SSB offset  (2-byte) - store B to SP+offset. Clobbers A.
instruction(0xF0, "SSB off",
    IP_INC_L    | DD_L,
    DS_MEM      | DD_A,        # A = offset byte (clobbers A)
    DS_SP       | DD_D,        # D = SP (save SP; clobbers D)
    DS_D        | DD_A,
    # Ugh, still awkward. Let's: B=offset, A=SP, add, then store original B.
    # Save B -> C first.
    uIP_RST)
# Redo SSB properly:
instruction(0xF0, "SSB off",
    DS_B        | DD_C,        # C = B (save store value)
    IP_INC_L    | DD_L,
    DS_MEM      | DD_B,        # B = offset
    DS_SP       | DD_A,        # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_C        | DD_MEM,      # MEM[H:L] = C (= original B)
    DS_IPH      | DD_H,
    uIP_RST)

# ---------------------------------------------------------------------------
# Jumps
# ---------------------------------------------------------------------------

# JMP addr16: read lo byte -> C, read hi byte -> H, then C -> L, H = high
# Then load: C -> IPL, H(already in H from DS_MEM)--> IPH
# Wait, we need to load IPH and IPL from the fetched bytes.
# lo byte -> C, hi byte -> D (temp), then D -> IPH, C -> IPL
# After loading IPL, IPH: next fetch will do IPL++ and latch to L.
# But we want next instruction to be at the jump target, so:
#   IPH = hi byte (already in H, but IP_HI register needs loading via DD_IPH)
#   IPL = lo byte (via DD_IPL)
# Then do the LAST part of fetch manually? No - uIP_RST -> uIP goes to 0 -> 
# FETCH0 will do IPL++ -> L, FETCH1 does IPH -> H, FETCH2 reads MEM.
# So after setting IPL and IPH to jump target, the next instruction's PC
# will be incremented by 1 (FETCH0 does IPL++). That means we should set 
# IPL = target_low - 1. But that's awkward.
#
# BETTER APPROACH: Don't use IP_INC_L in FETCH0. Instead, FETCH0 just reads IPL
# onto data bus (DS_IPL | DD_L) without incrementing. Then FETCH1 does IPH->H.
# FETCH2 does MEM->IR. THEN the first step of every instruction body THAT READS
# AN OPERAND does IP_INC_L | DD_L.
# 
# But then NOP and single-byte instructions need to increment IP themselves at
# the END (before uIP_RST) to advance past their own opcode.
#
# Even simpler and cleanest: keep the current model where the FIRST fetch step
# increments IP. Since instructions are responsible for advancing IP past their
# operands, and the fetch of the OPCODE itself happened in the previous FETCH
# sequence (which already incremented past the previous instruction's last byte
# to land on this opcode), everything works as long as we track carefully.
#
# Current FETCH0 does: IPL++ -> L. This means when the CPU is at address X,
# FETCH0 increments IP to X+1 and reads from X+1. That's wrong - we want to 
# read from X (the current PC).
#
# CORRECT FETCH sequence: 
# - FETCH0: DS_IPL | DD_L    (put current IPL on bus -> L, no increment)
# - FETCH1: DS_IPH | DD_H    (put IPH on bus -> H)
# - FETCH2: DS_MEM | DD_IR | IP_INC_L | DD_L  (read MEM[IPL:IPH] -> IR, then IPL++)
#   But we can't combine DS_MEM with IP_INC_L in the same step cleanly because
#   IPL++ changes the address DURING the memory read.
#
# OR: 
# - FETCH0: DS_IPL | DD_L    (latch current IPL into L without increment)
# - FETCH1: DS_IPH | DD_H    (latch IPH into H)
# - FETCH2: DS_MEM | DD_IR   (read opcode from MEM[H:L])
# Then AFTER FETCH2, increment IP. But uIP_RST resets to 0 which would re-fetch.
# We need IP_INC somewhere. Put it at uIP=3 (first body step)?
# That means EVERY instruction body must start with IP_INC_L | DD_L as its first step.
# This is messy.
#
# CLEANEST SOLUTION (matches user's example):
# IPL++->L is a COMBINED operation: increment IPL (advancing IP past what we're about
# to read) AND latch new value into L. Then MEM[H:L] reads the NEXT byte.
# So: FETCH0 = IP_INC_L | DD_L -> incr IPL, L = new IPL, H = IPH (from last time)
#              -> reads from NEW address (the opcode location)
# Wait - but that means we need H to ALREADY be set to IPH before FETCH0!
# That's exactly the case! The previous instruction ends by restoring H = IPH.
# And on reset: H=0, IPH=0 initially, so FETCH0 reads from IP=0x0001?
# 
# No wait. At reset, IP=0x0000. FETCH0 does IPL++->L: IPL becomes 0x01, L=0x01.
# Then FETCH1: IPH->H: H=0x00. Then FETCH2: MEM[0x0001] -> IR. That reads byte 1,
# not byte 0! We've skipped the first byte.
#
# So the correct approach: on RESET, set L=0 and H=0 directly, and set IP=0xFFFF
# so that the first IPL++ wraps to 0x00, giving address 0x0000.
# OR: reset IP to 0xFFFF hardware-level. This is what many real CPUs do 
# (reset vector at top of memory, JMP to real start).
# 
# Actually the simplest fix: set the INITIAL IP = 0xFFFF via the reset logic.
# Then FETCH0: IPL (0xFF) ++ -> 0x00 -> L=0x00, FETCH1: IPH=0x00->H (but wait, 
# IPH was 0xFF if IP=0xFFFF). Hmm that doesn't work either.
#
# REAL CLEANEST: IP_INC increments before read (like x86 CS:IP model).
# Set reset IP = 0xFFFF. IP counts up. FETCH: IP++ first (becomes 0x0000), 
# then H=IPH=0x00 (the high byte wraps separately), read MEM[0x0000].
# But then FETCH0 is IPL++ (0xFF->0x00), carry propagates to IPH(0xFF->0x00)?
# With ripple counters this is fine. So reset IP to 0xFFFF = start-1.
# 
# This is actually the approach used! Let's implement it correctly.
# Reset sets all IP counters to 0xFF (all bits 1). The ~CLR pin on 74HC161 
# clears to 0, so we use ~LOAD with 0xFF loaded from the reset state.
# Actually the hardware currently resets to 0 via ~CLR. We need to change
# reset behavior to load 0xFFFF, or change IP start to 0xFFFF, or...
#
# SIMPLEST HARDWARE FIX: Change FETCH to NOT use IP_INC in FETCH0.
# Instead: FETCH0: DS_IPL|DD_L, FETCH1: DS_IPH|DD_H, FETCH2: DS_MEM|DD_IR.
# Then IP increment is done as the LAST step of FETCH, BEFORE uIP_RST:
# We add a 4th fetch step: uIP=3: IP_INC_L|DD_L (advance IP, L now points to byte AFTER opcode)
# Then uIP=4+: instruction body.
# But then NOP (no body) would need uIP=4: uIP_RST. Fine!
#
# This means:
# FETCH0(uIP=0): DS_IPL | DD_L  - latch current IPL into L (no increment)
# FETCH1(uIP=1): DS_IPH | DD_H  - latch IPH into H
# FETCH2(uIP=2): DS_MEM | DD_IR - read opcode from MEM[H:L]
# FETCH3(uIP=3): IP_INC_L | DD_L - advance IP, L = new IPL (ready for operand read)
# Then next steps are the instruction body starting at uIP=4.
# 
# Now every instruction body starts at uIP=4, and IP points ONE PAST the opcode.
# Reading operands: IP_INC_L|DD_L (advance), DS_MEM|DD_reg.
# After last operand, restore DS_IPH|DD_H before uIP_RST.
# 
# NOP: uIP=4: uIP_RST (just resets, IP already advanced in fetch3)
# LDA #imm: uIP=4: DS_MEM|DD_A (read from current IP), uIP=5: IP_INC_L|DD_L (advance), 
# Wait, IP already points to operand (FETCH3 advanced it). So:
# LDA #imm: uIP=4: DS_MEM|DD_A, uIP=5: IP_INC_L|DD_L (advance past operand), uIP_RST
# But we also need H restored after LDA [addr16] sets H to something else.
# 
# CRUCIAL INSIGHT: H is only used by memory operations. Reg-to-reg ops don't 
# need H. H becomes invalid after any addr manipulation but MUST equal IPH 
# before the next FETCH that does DS_IPH|DD_H anyway.
# Wait -- FETCH1 always does DS_IPH|DD_H! So H is restored at the START of 
# every fetch. So instructions DON'T need to restore H at the end!
# The only case where H needs to be restored WITHIN an instruction is when 
# the instruction does multiple memory accesses and needs to switch between 
# "target addr" and "IP addr" within the same sequence.
# 
# For LDA [addr16]:
# FETCH(0-3) completes, IP points to first operand byte.
# uIP=4: DS_MEM|DD_C  - C = lo byte (but we need L to point here first!)
# Wait - after FETCH3, L = IPL (pointing past opcode). So MEM[H:L] = first operand byte. Good.
# uIP=4: DS_MEM|DD_C - C = lo addr byte (from current H:L = IP)
# uIP=5: IP_INC_L|DD_L - advance IP -> L (now points to 2nd operand)
# uIP=6: DS_MEM|DD_H - H = hi addr byte. Now H is target-hi.
# uIP=7: IP_INC_L|DD_L - advance IP past operands. BUT WAIT: IP_INC_L puts new IPL 
#         on bus AND saves to L. But L should be target-lo (C), not new IPL!
#         We need: IP++ (advance counter only) + L = C (target lo). That's two 
#         separate operations. We can't do IP++ without setting L via IP_INC_L.
# 
# Hmm. Let's separate "IP increment" from "L latch":
# Maybe IP_INC just increments IP (like old behavior), separate from DD_L.
# And DS_IPL just puts current IPL on data bus (no increment).
# Then IP_INC_L = IP_INC | DD_IPL_AUTO... this is getting complicated.
#
# FINAL CLEAN DESIGN:
# Separate IP_INC (pure increment, bit 14) from the L-load.
# FETCH0: DS_IPL|DD_L (latch current IPL into L)
# FETCH1: DS_IPH|DD_H (latch IPH into H)  
# FETCH2: DS_MEM|DD_IR|IP_INC (read opcode AND increment IP - IP now points past opcode)
# Then uIP=3+: instruction body, IP already points to first operand byte.
# 
# To read operand bytes:
# uIP=3: DS_IPL|DD_L - latch updated IPL into L
# uIP=4: DS_MEM|DD_A - read operand into A from MEM[H:L]
# uIP=5: IP_INC - advance IP past operand
# uIP=6: uIP_RST
# 
# For LDA [addr16]:
# uIP=3: DS_IPL|DD_L                   - L = IPL (pointing to lo operand)
# uIP=4: DS_MEM|DD_C|IP_INC            - C = lo byte, IP++
# uIP=5: DS_IPL|DD_L                   - L = new IPL (pointing to hi operand)  
# uIP=6: DS_MEM|DD_H|IP_INC            - H = hi byte, IP++. Now HL = target addr.
#                                         IP now points past both operands.
# uIP=7: DS_C|DD_L                     - L = C (lo byte). HL = target addr.
# uIP=8: DS_MEM|DD_A                   - A = MEM[target]
# (no need to restore H - FETCH1 will do it)
# uIP=9: uIP_RST
# 
# This is clean! 7 body steps for LDA [addr16].
# 
# For CALL addr16 (user's example, adapted):
# uIP=3: DS_IPL|DD_L, uIP=4: DS_MEM|DD_C|IP_INC  - C = lo jump addr
# uIP=5: DS_IPL|DD_L, uIP=6: DS_MEM|DD_D|IP_INC  - D = hi jump addr
# (IP now points past CALL instruction)
# uIP=7: DS_IPL|DD_B   - B = return addr low (current IPL)
# uIP=8: DS_IPH|DD_A   - A = return addr high (current IPH)
# Then push A and B onto stack? No - CALL in original doesn't push!
# Looking at original: DS_IP_HI|DD_A, DS_IP_LO|DD_B then jump.
# So CALL stores return addr in A and B (caller saves convention).
# uIP=7: DS_IPL|DD_B   - B = current IPL (return addr lo)
# uIP=8: DS_IPH|DD_A   - A = current IPH (return addr hi)
# uIP=9: DS_C|DD_IPL   - IPL = C (jump lo)
# uIP=10: DS_D|DD_IPH  - IPH = D (jump hi)
# uIP=11: uIP_RST      - -> FETCH: reads from new IP
# But FETCH0 will do DS_IPL|DD_L: L = new IPL. That correctly addresses the jump target!
# Total body steps: 9. Plus 3 fetch = 12. Fits in 16. 
# 
# Wait in user's example: "(IPL++->L, MEM->C, IPL++->L, MEM->D, IPL->B, IPH->A, 
# C->IPL, D->IPH, IPL++->L, IPH->H, MEM->I)" = 11 steps
# That's with IP_INC_L model (where fetch doesn't exist separately - each instruction
# ends with its own 3-step fetch). But our model separates fetch. Let me count my steps:
# FETCH(0-2) = 3, body uIP=3-11 = 9. Total = 12. User said 11 for full sequence in 
# their model - roughly equivalent.
#
# KEY DECISION: Use IP_INC as a separate control bit (not combined with DD_L).
# DS_IPL reads current IPL (AFTER any pending increment).
# IP_INC increments IPL on the clock edge.
# We can combine them: DS_IPL|DD_L|IP_INC to read-then-increment.
#
# Let's finalize this model and rewrite everything cleanly below.
# ---------------------------------------------------------------------------

# Clear previous and restart with clean model
INSTRUCTIONS = {}  # reset

# ============================================================================
# FINAL CONTROL WORD DEFINITIONS
# ============================================================================

# Data Bus Source (bits 0-3)
DS_NONE     = 0
DS_A        = 1
DS_B        = 2
DS_C        = 3
DS_D        = 4
DS_ALU      = 5
DS_MEM      = 6
DS_IPL      = 7   # current IPL -> data bus
DS_IPH      = 8   # current IPH -> data bus
DS_SP       = 9   # SP -> data bus
DS_CONST_FF = 10  # constant 0xFF -> data bus

# Data Bus Dest (bits 4-7)
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

# bits 8-9: unused

# ALU ops (bits 10-12)
ALU_ADD = 0 << 10
ALU_SUB = 1 << 10
ALU_AND = 2 << 10
ALU_OR  = 3 << 10
ALU_XOR = 4 << 10
ALU_NOT = 5 << 10
ALU_SHL = 6 << 10
ALU_SHR = 7 << 10

# Control bits (13-18)
FLAGS_IN = 1 << 13
IP_INC   = 1 << 14  # increment IP counter (IPL++, carry to IPH)
SP_INC   = 1 << 15
SP_DEC   = 1 << 16
uIP_RST  = 1 << 17
HLT      = 1 << 18

INSTRUCTIONS = {}

def instruction(opcode, name, *steps):
    INSTRUCTIONS[opcode] = (name, steps)

# ============================================================================
# FETCH SEQUENCE (uIP = 0, 1, 2)
# uIP=0: DS_IPL | DD_L          -> latch current IPL into L
# uIP=1: DS_IPH | DD_H          -> latch IPH into H. Now H:L = full IP address.
# uIP=2: DS_MEM | DD_IR | IP_INC -> read opcode from MEM[H:L] -> IR, increment IP.
#                                    After this: IP points to first operand byte.
# uIP=3+: instruction body.
#
# To read operand byte: DS_IPL|DD_L (update L to new IPL), DS_MEM|DD_reg|IP_INC (read & advance).
# Or as shorthand, 2 steps:
#   LATCH_IPL = DS_IPL | DD_L
#   READ_ADV  = DS_MEM | DD_reg | IP_INC
#
# Note: H needs no refresh between operand reads OF SAME INSTRUCTION as long as
# no page boundary is crossed (same IPH throughout). Assembler ensures this.
# ============================================================================

FETCH0 = DS_IPL | DD_L                    # uIP=0
FETCH1 = DS_IPH | DD_H                    # uIP=1
FETCH2 = DS_MEM | DD_IR | IP_INC          # uIP=2 (also advances IP past opcode)

# Shorthand: two-step read of next IP byte into a destination register
# (Step 1: update L from IPL, Step 2: read MEM and advance IP)
def READ_IMM(dd):
    return (DS_IPL | DD_L, DS_MEM | dd | IP_INC)

# ============================================================================
# INSTRUCTIONS (bodies start at uIP=3)
# ============================================================================

# NOP (1 byte, no operands)
instruction(0x00, "NOP",
    uIP_RST)

# Load Immediate
def make_ldi(opcode, name, dd):
    instruction(opcode, name,
        DS_IPL | DD_L,            # step 3: L = IPL (points to operand)
        DS_MEM | dd | IP_INC,     # step 4: reg = MEM[H:L], IP++
        uIP_RST)

make_ldi(0x01, "LDA #imm", DD_A)
make_ldi(0x02, "LDB #imm", DD_B)
make_ldi(0x03, "LDC #imm", DD_C)
make_ldi(0x04, "LDD #imm", DD_D)

# Load/Store [addr16] helper
# Read lo byte -> C, read hi byte -> D (temp for IPH save if needed)
# Then set HL = addr, do mem op, no explicit H restore needed (FETCH will fix)
def make_ld_addr16(opcode, name, dest_dd):
    instruction(opcode, name,
        DS_IPL | DD_L,            # step 3: L = IPL
        DS_MEM | DD_C | IP_INC,   # step 4: C = lo addr byte, IP++
        DS_IPL | DD_L,            # step 5: L = new IPL
        DS_MEM | DD_H | IP_INC,   # step 6: H = hi addr byte, IP++ (H now = target hi)
        DS_C   | DD_L,            # step 7: L = C (target lo). HL = target addr.
        DS_MEM | dest_dd,         # step 8: reg = MEM[H:L]
        uIP_RST)

def make_st_addr16(opcode, name, src_ds):
    instruction(opcode, name,
        DS_IPL | DD_L,
        DS_MEM | DD_C | IP_INC,
        DS_IPL | DD_L,
        DS_MEM | DD_H | IP_INC,
        DS_C   | DD_L,
        src_ds | DD_MEM,          # step 8: MEM[H:L] = reg
        uIP_RST)

make_ld_addr16(0x05, "LDA [addr16]", DD_A)
make_st_addr16(0x06, "STA [addr16]", DS_A)
make_ld_addr16(0x07, "LDB [addr16]", DD_B)
make_st_addr16(0x08, "STB [addr16]", DS_B)

# Moves (register to register, 1 byte)
def make_mov(opcode, name, src, dst):
    instruction(opcode, name, src | dst | uIP_RST)

make_mov(0x18, "MVA B", DS_B, DD_A)
make_mov(0x19, "MVA C", DS_C, DD_A)
make_mov(0x1A, "MVA D", DS_D, DD_A)
make_mov(0x1B, "MVB A", DS_A, DD_B)
make_mov(0x1C, "MVC A", DS_A, DD_C)
make_mov(0x1D, "MVD A", DS_A, DD_D)

# ALU operations (1 byte)
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
instruction(0x28, "CMP", DS_ALU | ALU_SUB | FLAGS_IN | uIP_RST)

# ============================================================================
# Stack operations. Stack lives at 0xFF00 to 0xFFFF.
# For stack memory: H = 0xFF (DS_CONST_FF | DD_H), L = SP (DS_SP | DD_L)
# SP points to current top of stack (pre-decrement on push, post-increment on pop... 
# actually: PSH: write MEM[SP], then SP--. POP: SP++, then read MEM[SP]).
# ============================================================================

# PSH reg: MEM[0xFF:SP] <- reg; SP--
def make_psh(opcode, name, src_ds):
    instruction(opcode, name,
        DS_CONST_FF | DD_H,    # H = 0xFF
        DS_SP       | DD_L,    # L = SP. HL = stack addr.
        src_ds      | DD_MEM,  # MEM[H:L] = reg
        SP_DEC,                # SP--
        uIP_RST)

# POP reg: SP++; reg <- MEM[0xFF:SP]
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

# ============================================================================
# SP-relative load/store (2-byte: opcode + offset byte)
# These use ALU to compute SP + offset, then address 0xFF:result
# LSA: clobbers A (result goes into A). SSA: saves/restores A via D.
# LSB: clobbers A (uses A for addition). SSB: saves B via C.
# ============================================================================

# LSA offset: A = MEM[0xFF:(SP+offset)]. Clobbers A.
instruction(0xC0, "LSA off",
    DS_IPL      | DD_L,            # step 3: L = IPL
    DS_MEM      | DD_B | IP_INC,   # step 4: B = offset byte, IP++
    DS_SP       | DD_A,            # step 5: A = SP
    DS_ALU      | ALU_ADD | DD_L,  # step 6: L = A+B = SP+offset
    DS_CONST_FF | DD_H,            # step 7: H = 0xFF
    DS_MEM      | DD_A,            # step 8: A = MEM[0xFF:(SP+offset)]
    uIP_RST)

# SSA offset: MEM[0xFF:(SP+offset)] = A. Clobbers B, D.
instruction(0xD0, "SSA off",
    DS_A        | DD_D,            # step 3: save A -> D
    DS_IPL      | DD_L,            # step 4: L = IPL
    DS_MEM      | DD_B | IP_INC,   # step 5: B = offset, IP++
    DS_SP       | DD_A,            # step 6: A = SP
    DS_ALU      | ALU_ADD | DD_L,  # step 7: L = SP+offset
    DS_CONST_FF | DD_H,            # step 8: H = 0xFF
    DS_D        | DD_MEM,          # step 9: MEM[H:L] = D (orig A)
    uIP_RST)

# LSB offset: B = MEM[0xFF:(SP+offset)]. Clobbers A.
instruction(0xE0, "LSB off",
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_MEM      | DD_B,            # B = MEM[0xFF:(SP+offset)]
    uIP_RST)

# SSB offset: MEM[0xFF:(SP+offset)] = B. Clobbers A, C.
instruction(0xF0, "SSB off",
    DS_B        | DD_C,            # save B -> C
    DS_IPL      | DD_L,
    DS_MEM      | DD_B | IP_INC,   # B = offset
    DS_SP       | DD_A,            # A = SP
    DS_ALU      | ALU_ADD | DD_L,  # L = SP+offset
    DS_CONST_FF | DD_H,
    DS_C        | DD_MEM,          # MEM[H:L] = C (orig B)
    uIP_RST)

# ============================================================================
# Jumps
# ============================================================================

# JMP addr16: set IPL = lo, IPH = hi (from fetched operands)
# After uIP_RST, FETCH0 does DS_IPL|DD_L -> L = new IPL. Correct!
instruction(0x70, "JMP addr16",
    DS_IPL | DD_L,              # step 3: L = IPL
    DS_MEM | DD_C | IP_INC,     # step 4: C = lo addr, IP++ (doesn't matter, we overwrite)
    DS_IPL | DD_L,              # step 5: L = IPL
    DS_MEM | DD_D | IP_INC,     # step 6: D = hi addr
    DS_C   | DD_IPL,            # step 7: IPL = C (jump lo)
    DS_D   | DD_IPH,            # step 8: IPH = D (jump hi)
    uIP_RST)

# Conditional jumps (handled in generate_microcode based on FLAGS)
# JUMP_MAP defines condition -> jump taken (steps match JMP) or not (skip 2 bytes)
# JZ=0x71, JNZ=0x72, JC=0x73, JNC=0x74, JN=0x75

JUMP_MAP = {
    0x71: lambda flags: (flags & 1) != 0,  # JZ
    0x72: lambda flags: (flags & 1) == 0,  # JNZ
    0x73: lambda flags: (flags & 2) != 0,  # JC
    0x74: lambda flags: (flags & 2) == 0,  # JNC
    0x75: lambda flags: (flags & 4) != 0,  # JN
}

JMP_TAKEN_STEPS = [
    DS_IPL | DD_L,
    DS_MEM | DD_C | IP_INC,
    DS_IPL | DD_L,
    DS_MEM | DD_D | IP_INC,
    DS_C   | DD_IPL,
    DS_D   | DD_IPH,
    uIP_RST
]

JMP_NOT_TAKEN_STEPS = [
    # Skip 2 bytes (the address operand)
    DS_IPL | DD_L,
    IP_INC,            # skip lo byte
    DS_IPL | DD_L,
    IP_INC,            # skip hi byte
    uIP_RST
]

# CALL addr16: fetch lo->C, hi->D, save return IP in A(hi),B(lo), jump to C:D
# After fetching both bytes, IP points past the CALL instruction (= return address).
instruction(0x80, "CALL addr16",
    DS_IPL | DD_L,              # step 3: L = IPL
    DS_MEM | DD_C | IP_INC,     # step 4: C = lo jump addr, IP++ (IP -> hi operand)
    DS_IPL | DD_L,              # step 5: L = IPL
    DS_MEM | DD_D | IP_INC,     # step 6: D = hi jump addr, IP++ (IP -> return addr)
    DS_IPL | DD_B,              # step 7: B = return addr lo (current IPL)
    DS_IPH | DD_A,              # step 8: A = return addr hi (current IPH)
    DS_C   | DD_IPL,            # step 9: IPL = C (jump lo)
    DS_D   | DD_IPH,            # step 10: IPH = D (jump hi)
    uIP_RST)

# RET: jump to A:B (A=hi, B=lo)
instruction(0x81, "RET",
    DS_B   | DD_IPL,            # step 3: IPL = B (return lo)
    DS_A   | DD_IPH,            # step 4: IPH = A (return hi)
    uIP_RST)

instruction(0x82, "HLT", HLT)
instruction(0x83, "IN A",  DD_A,        uIP_RST)  # placeholder
instruction(0x84, "OUT A", DS_A | DD_OUT | uIP_RST)

# ============================================================================
# Microcode ROM generation
# ============================================================================

def generate_microcode():
    rom1 = bytearray(32768)
    rom2 = bytearray(32768)
    rom3 = bytearray(32768)

    # Pre-fill with uIP_RST (safe default)
    for i in range(32768):
        rom1[i] = uIP_RST & 0xFF
        rom2[i] = (uIP_RST >> 8) & 0xFF
        rom3[i] = (uIP_RST >> 16) & 0xFF

    for addr in range(32768):
        uip   = addr & 0x0F
        flags = (addr >> 4) & 0x07
        ir    = (addr >> 7) & 0xFF

        cw = uIP_RST  # default: reset uIP

        if uip == 0:
            cw = FETCH0
        elif uip == 1:
            cw = FETCH1
        elif uip == 2:
            cw = FETCH2
        else:
            # Instruction body at uip >= 3
            body_step = uip - 3  # 0-indexed into instruction body

            if ir in JUMP_MAP:
                steps = JMP_TAKEN_STEPS if JUMP_MAP[ir](flags) else JMP_NOT_TAKEN_STEPS
                cw = steps[body_step] if body_step < len(steps) else uIP_RST
            elif ir in INSTRUCTIONS:
                _, steps = INSTRUCTIONS[ir]
                cw = steps[body_step] if body_step < len(steps) else uIP_RST
            else:
                cw = uIP_RST

        rom1[addr] = cw & 0xFF
        rom2[addr] = (cw >> 8) & 0xFF
        rom3[addr] = (cw >> 16) & 0xFF

    with open('microcode_a.bin', 'wb') as f: f.write(rom1)
    with open('microcode_b.bin', 'wb') as f: f.write(rom2)
    with open('microcode_c.bin', 'wb') as f: f.write(rom3)
    print("Generated microcode_a.bin, microcode_b.bin, microcode_c.bin")

    # Print instruction summary
    print("\nInstruction summary:")
    for opc in sorted(INSTRUCTIONS.keys()):
        name, steps = INSTRUCTIONS[opc]
        print(f"  0x{opc:02X} {name:20s}  {len(steps)+3} uIP steps (3 fetch + {len(steps)} body)")
    for opc in sorted(JUMP_MAP.keys()):
        print(f"  0x{opc:02X} conditional jump   {3+len(JMP_TAKEN_STEPS)} / {3+len(JMP_NOT_TAKEN_STEPS)} uIP steps")

if __name__ == "__main__":
    generate_microcode()
    print("Done")
