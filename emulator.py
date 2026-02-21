#!/usr/bin/env python3
"""
Emulator for the breadboard CPU.

Simulates the CPU at the instruction level (not micro-step level) for
speed and simplicity. Uses the same ISA definitions as the microcode
generator.

Memory map:
  0x0000 - 0x7FFF: Program ROM (32 KB)
  0x8000 - 0xFFFF: RAM (32 KB)
  0xFF00 - 0xFFFF: Stack (256 bytes, SP-relative to 0xFF00)

Usage:
  python emulator.py program.bin [--trace] [--step]
  python emulator.py program.asm [--trace] [--step]
"""

import sys
import os

# ---------------------------------------------------------------------------
# CPU State
# ---------------------------------------------------------------------------

class CPU:
    """Emulates the 8-bit breadboard CPU."""

    ROM_START = 0x0000
    RAM_START = 0x8000
    RAM_END   = 0xFFFF
    STACK_START = 0xFF00
    STACK_END   = 0xFFFF
    MEM_SIZE  = 0x10000  # 65536 bytes (16-bit address space)
    IP_RESET  = 0x0000   # IP starts at beginning of ROM

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset CPU to initial state."""
        self.a = 0       # Accumulator (8-bit)
        self.b = 0       # B register (8-bit)
        self.ip = self.IP_RESET  # Instruction pointer (12-bit)
        self.sp = 0xFF   # Stack pointer (8-bit, starts at top)
        self.flags_z = False  # Zero flag
        self.flags_c = False  # Carry flag
        self.flags_n = False  # Negative flag
        self.halted = False
        self.mem = bytearray(self.MEM_SIZE)
        self.output_buffer = []
        self.input_buffer = []
        self.cycle_count = 0
        self.instr_count = 0
        self.breakpoints = set()
        self.trace = False

    def load_program(self, data, base_addr=None):
        """Load program data into memory at base_addr (default: ROM_START)."""
        if base_addr is None:
            base_addr = self.ROM_START
        for i, byte in enumerate(data):
            if base_addr + i < self.MEM_SIZE:
                self.mem[base_addr + i] = byte

    def mem_read(self, addr):
        """Read a byte from memory."""
        addr &= 0xFFFF  # 16-bit address mask
        return self.mem[addr]

    def mem_write(self, addr, value):
        """Write a byte to memory (only RAM area)."""
        addr &= 0xFFFF
        value &= 0xFF
        if addr >= self.RAM_START:  # RAM + Stack area
            self.mem[addr] = value
        # Writes to ROM area are silently ignored

    def stack_push(self, value):
        """Push a value onto the stack."""
        addr = self.STACK_START | (self.sp & 0xFF)
        self.mem_write(addr, value & 0xFF)
        self.sp = (self.sp - 1) & 0xFF

    def stack_pop(self):
        """Pop a value from the stack."""
        self.sp = (self.sp + 1) & 0xFF
        addr = self.STACK_START | (self.sp & 0xFF)
        return self.mem_read(addr)

    def update_flags(self, result, carry=False):
        """Update flags based on ALU result."""
        result_8 = result & 0xFF
        self.flags_z = (result_8 == 0)
        self.flags_n = bool(result_8 & 0x80)
        self.flags_c = carry

    def fetch_byte(self):
        """Fetch the next byte from memory at IP, increment IP."""
        byte = self.mem_read(self.ip)
        self.ip = (self.ip + 1) & 0xFFFF
        return byte

    def fetch_word(self):
        """Fetch a 16-bit word from memory at IP (little endian), increment IP."""
        lo = self.fetch_byte()
        hi = self.fetch_byte()
        return (hi << 8) | lo

    def execute_one(self):
        """Execute one instruction. Returns False if halted."""
        if self.halted:
            return False

        start_ip = self.ip
        opcode = self.fetch_byte()

        if self.trace:
            self._trace_pre(start_ip, opcode)

        self._dispatch(opcode)
        self.instr_count += 1

        if self.trace:
            self._trace_post()

        return not self.halted

    def _dispatch(self, opcode):
        """Dispatch and execute an opcode."""
        # NOP
        if opcode == 0x00:
            pass

        # LDA imm
        elif opcode == 0x01:
            self.a = self.fetch_byte()

        # LDA [addr16]
        elif opcode == 0x02:
            addr = self.fetch_word()
            self.a = self.mem_read(addr)

        # STA [addr16]
        elif opcode == 0x03:
            addr = self.fetch_word()
            self.mem_write(addr, self.a)

        # LDB imm
        elif opcode == 0x04:
            self.b = self.fetch_byte()

        # LDB [addr16]
        elif opcode == 0x05:
            addr = self.fetch_word()
            self.b = self.mem_read(addr)

        # STB [addr16]
        elif opcode == 0x06:
            addr = self.fetch_word()
            self.mem_write(addr, self.b)

        # MOV A,B
        elif opcode == 0x07:
            self.a = self.b

        # MOV B,A
        elif opcode == 0x08:
            self.b = self.a

        # ALU operations
        elif opcode == 0x10:  # ADD
            r = self.a + self.b
            self.update_flags(r, carry=(r > 0xFF))
            self.a = r & 0xFF

        elif opcode == 0x11:  # SUB
            r = self.a - self.b
            self.update_flags(r, carry=(r < 0))
            self.a = r & 0xFF

        elif opcode == 0x12:  # AND
            self.a = self.a & self.b
            self.update_flags(self.a)

        elif opcode == 0x13:  # OR
            self.a = self.a | self.b
            self.update_flags(self.a)

        elif opcode == 0x14:  # XOR
            self.a = self.a ^ self.b
            self.update_flags(self.a)

        elif opcode == 0x15:  # NOT
            self.a = (~self.a) & 0xFF
            self.update_flags(self.a)

        elif opcode == 0x16:  # SHL
            carry = bool(self.a & 0x80)
            self.a = (self.a << 1) & 0xFF
            self.update_flags(self.a, carry=carry)

        elif opcode == 0x17:  # SHR
            carry = bool(self.a & 0x01)
            self.a = (self.a >> 1) & 0xFF
            self.update_flags(self.a, carry=carry)

        # ADI imm
        elif opcode == 0x18:
            imm = self.fetch_byte()
            r = self.a + imm
            self.update_flags(r, carry=(r > 0xFF))
            self.a = r & 0xFF

        # SBI imm
        elif opcode == 0x19:
            imm = self.fetch_byte()
            r = self.a - imm
            self.update_flags(r, carry=(r < 0))
            self.a = r & 0xFF

        # CMP
        elif opcode == 0x1A:
            r = self.a - self.b
            self.update_flags(r, carry=(r < 0))

        # CMI imm
        elif opcode == 0x1B:
            imm = self.fetch_byte()
            r = self.a - imm
            self.update_flags(r, carry=(r < 0))

        # PUSH A
        elif opcode == 0x20:
            self.stack_push(self.a)

        # POP A
        elif opcode == 0x21:
            self.a = self.stack_pop()

        # PUSH B
        elif opcode == 0x22:
            self.stack_push(self.b)

        # POP B
        elif opcode == 0x23:
            self.b = self.stack_pop()

        # JMP addr16 (0x30)
        elif opcode == 0x30:
            self.ip = self.fetch_word()

        # JZ addr16 (0x40)
        elif opcode == 0x40:
            addr = self.fetch_word()
            if self.flags_z:
                self.ip = addr

        # JNZ addr16 (0x50)
        elif opcode == 0x50:
            addr = self.fetch_word()
            if not self.flags_z:
                self.ip = addr

        # JC addr16 (0x60)
        elif opcode == 0x60:
            addr = self.fetch_word()
            if self.flags_c:
                self.ip = addr

        # JNC addr16 (0x70)
        elif opcode == 0x70:
            addr = self.fetch_word()
            if not self.flags_c:
                self.ip = addr

        # JN addr16 (0x80)
        elif opcode == 0x80:
            addr = self.fetch_word()
            if self.flags_n:
                self.ip = addr

        # CALL addr16 (0x90)
        elif opcode == 0x90:
            addr = self.fetch_word()
            # Push return address (current IP, which is past the operand)
            ret_addr = self.ip
            self.stack_push((ret_addr >> 8) & 0xFF)  # high byte
            self.stack_push(ret_addr & 0xFF)         # low byte
            self.ip = addr

        # RET (0xA0)
        elif opcode == 0xA0:
            lo = self.stack_pop()
            hi = self.stack_pop()
            self.ip = (hi << 8) | lo

        # IN (0xFD)
        elif opcode == 0xFD:
            if self.input_buffer:
                self.a = self.input_buffer.pop(0) & 0xFF
            else:
                # Interactive: read from stdin
                try:
                    line = input("IN> ")
                    self.a = int(line.strip(), 0) & 0xFF
                except (ValueError, EOFError):
                    self.a = 0

        # OUT (0xFE)
        elif opcode == 0xFE:
            self.output_buffer.append(self.a)
            if self.trace:
                print(f"  OUT: {self.a} (0x{self.a:02X})")

        # HLT (0xFF)
        elif opcode == 0xFF:
            self.halted = True

        else:
            # Unknown opcode: treat as NOP
            pass

    def _trace_pre(self, ip, opcode):
        """Print trace info before execution."""
        flags = f"{'Z' if self.flags_z else '.'}{'C' if self.flags_c else '.'}{'N' if self.flags_n else '.'}"
        print(f"[{self.instr_count:6d}] IP=0x{ip:04X} OP=0x{opcode:02X} "
              f"A=0x{self.a:02X} B=0x{self.b:02X} SP=0x{self.sp:02X} [{flags}]",
              end="")

    def _trace_post(self):
        """Print trace info after execution."""
        flags = f"{'Z' if self.flags_z else '.'}{'C' if self.flags_c else '.'}{'N' if self.flags_n else '.'}"
        print(f" -> A=0x{self.a:02X} B=0x{self.b:02X} SP=0x{self.sp:02X} "
              f"IP=0x{self.ip:04X} [{flags}]")

    def dump_state(self):
        """Print the full CPU state."""
        flags = f"{'Z' if self.flags_z else '.'}{'C' if self.flags_c else '.'}{'N' if self.flags_n else '.'}"
        print(f"\n=== CPU State ===")
        print(f"  A  = 0x{self.a:02X} ({self.a:3d})")
        print(f"  B  = 0x{self.b:02X} ({self.b:3d})")
        print(f"  IP = 0x{self.ip:04X}")
        print(f"  SP = 0x{self.sp:02X}")
        print(f"  Flags: [{flags}]")
        print(f"  Instructions executed: {self.instr_count}")
        print(f"  Halted: {self.halted}")
        if self.output_buffer:
            print(f"  Output: {self.output_buffer}")

    def dump_memory(self, start, length=16):
        """Hex dump a memory region."""
        print(f"\n=== Memory 0x{start:03X}-0x{start+length-1:03X} ===")
        for i in range(0, length, 16):
            addr = start + i
            hex_str = " ".join(f"{self.mem_read(addr + j):02X}" for j in range(min(16, length - i)))
            print(f"  0x{addr:03X}: {hex_str}")

    def run(self, max_instructions=1000000):
        """Run until halt or max instructions reached."""
        count = 0
        while self.execute_one():
            count += 1
            if count >= max_instructions:
                print(f"\nExecution limit reached ({max_instructions} instructions)")
                break
            if self.ip in self.breakpoints:
                print(f"\nBreakpoint hit at IP=0x{self.ip:03X}")
                break
        return count


# ---------------------------------------------------------------------------
# Program loading
# ---------------------------------------------------------------------------

def load_binary(filename):
    """Load a raw binary file."""
    with open(filename, "rb") as f:
        return f.read()


def run_interactive(cpu):
    """Run the CPU in interactive/step mode."""
    print("Interactive mode. Commands: s(tep), r(un), q(uit), d(ump), m(em) <addr>")
    while True:
        try:
            cmd = input("dbg> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd or cmd == "s":
            if not cpu.execute_one():
                print("CPU halted.")
                cpu.dump_state()
                break
            cpu.dump_state()

        elif cmd == "r":
            cpu.run()
            cpu.dump_state()

        elif cmd.startswith("m"):
            parts = cmd.split()
            addr = int(parts[1], 0) if len(parts) > 1 else 0
            length = int(parts[2], 0) if len(parts) > 2 else 32
            cpu.dump_memory(addr, length)

        elif cmd == "d":
            cpu.dump_state()

        elif cmd.startswith("b"):
            parts = cmd.split()
            if len(parts) > 1:
                bp = int(parts[1], 0)
                cpu.breakpoints.add(bp)
                print(f"Breakpoint set at 0x{bp:03X}")
            else:
                print(f"Breakpoints: {[f'0x{b:03X}' for b in sorted(cpu.breakpoints)]}")

        elif cmd == "o":
            print(f"Output: {cpu.output_buffer}")

        elif cmd == "q":
            break

        else:
            print("Unknown command. s=step, r=run, q=quit, d=dump, m=memory, b=breakpoint, o=output")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python emulator.py <program.bin|program.asm> [--trace] [--step]")
        print("  --trace  Print execution trace")
        print("  --step   Interactive step-by-step mode")
        sys.exit(1)

    filename = sys.argv[1]
    trace = "--trace" in sys.argv
    step_mode = "--step" in sys.argv

    # Check if it's an assembly file — assemble it first
    if filename.endswith(".asm"):
        try:
            from assembler import assemble_file
            program, _ = assemble_file(filename)
        except ImportError:
            print("Error: assembler.py not found. Please assemble the file first.")
            sys.exit(1)
    else:
        program = load_binary(filename)

    cpu = CPU()
    cpu.trace = trace
    cpu.load_program(program)

    print(f"Loaded {len(program)} bytes at 0x{cpu.ROM_START:04X}")
    print(f"CPU reset. IP=0x{cpu.ip:04X}")

    if step_mode:
        cpu.trace = True
        run_interactive(cpu)
    else:
        cpu.run()
        cpu.dump_state()
        if cpu.output_buffer:
            print(f"\nProgram output: {cpu.output_buffer}")


if __name__ == "__main__":
    main()
