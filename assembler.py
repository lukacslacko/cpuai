#!/usr/bin/env python3
"""
Two-pass assembler for the breadboard CPU.

Syntax:
    label:          ; Define a label
    LDA #42         ; Load immediate (# prefix)
    LDA [0x1000]    ; Load from memory address ([] brackets)
    STA [0x1000]    ; Store to memory address
    ADD             ; A = A + B
    JMP label       ; Jump to label (16-bit)
    JZ label        ; Jump if zero
    .org 0x0000     ; Set origin address
    .db 0x42        ; Define byte
    .dw 0x1234      ; Define word (16-bit, big-endian)
    .equ NAME 42    ; Define constant

Usage:
    python assembler.py input.asm [-o output.bin] [--listing]
"""

import sys
import os
import re

# ---------------------------------------------------------------------------
# Instruction definitions
# ---------------------------------------------------------------------------

# Opcode table: mnemonic -> (base_opcode, operand_type)
# operand_type: None, 'imm', 'addr_mem', 'addr_jump'
OPCODES = {
    'NOP': (0x00, None),
    'LDA': None,  # Multiple variants, handled specially
    'STA': (0x03, 'addr_mem'),
    'LDB': None,  # Multiple variants
    'STB': (0x06, 'addr_mem'),
    'MVA': (0x07, None),  # MOV A,B
    'MVB': (0x08, None),  # MOV B,A
    'ADD': (0x10, None),
    'SUB': (0x11, None),
    'AND': (0x12, None),
    'OR':  (0x13, None),
    'XOR': (0x14, None),
    'NOT': (0x15, None),
    'SHL': (0x16, None),
    'SHR': (0x17, None),
    'ADI': (0x18, 'imm'),
    'SBI': (0x19, 'imm'),
    'CMP': (0x1A, None),
    'CMI': (0x1B, 'imm'),
    'PSA': (0x20, None),  # PUSH A
    'PPA': (0x21, None),  # POP A
    'PSB': (0x22, None),  # PUSH B
    'PPB': (0x23, None),  # POP B
    'JMP': (0x30, 'addr_jump'),
    'JZ':  (0x40, 'addr_jump'),
    'JNZ': (0x50, 'addr_jump'),
    'JC':  (0x60, 'addr_jump'),
    'JNC': (0x70, 'addr_jump'),
    'JN':  (0x80, 'addr_jump'),
    'CAL': (0x90, 'addr_jump'),
    'RET': (0xA0, None),
    'IN':  (0xFD, None),
    'OUT': (0xFE, None),
    'HLT': (0xFF, None),
}

# Aliases
ALIASES = {
    'PUSH': None,   # Handled specially
    'POP':  None,   # Handled specially
    'CALL': 'CAL',
    'MOV':  None,   # Handled specially
}

ROM_START = 0x0000


class AssemblerError(Exception):
    def __init__(self, message, line_num=None, line_text=None):
        self.line_num = line_num
        self.line_text = line_text
        if line_num is not None:
            super().__init__(f"Line {line_num}: {message}")
        else:
            super().__init__(message)


def parse_number(s):
    """Parse a number literal (decimal, hex, binary)."""
    s = s.strip()
    if s.startswith('0x') or s.startswith('0X'):
        return int(s, 16)
    elif s.startswith('0b') or s.startswith('0B'):
        return int(s, 2)
    elif s.startswith("'") and s.endswith("'") and len(s) == 3:
        return ord(s[1])
    else:
        return int(s)


def tokenize_line(line):
    """
    Parse an assembly line into components.
    Returns (label, mnemonic, operand, comment).
    """
    # Strip comments
    comment = None
    if ';' in line:
        idx = line.index(';')
        comment = line[idx + 1:].strip()
        line = line[:idx]

    line = line.strip()
    if not line:
        return None, None, None, comment

    # Check for label
    label = None
    if ':' in line:
        colon_idx = line.index(':')
        label = line[:colon_idx].strip()
        line = line[colon_idx + 1:].strip()

    if not line:
        return label, None, None, comment

    # Split mnemonic and operand
    parts = line.split(None, 1)
    mnemonic = parts[0].upper()
    operand = parts[1].strip() if len(parts) > 1 else None

    return label, mnemonic, operand, comment


class Assembler:
    """Two-pass assembler for the breadboard CPU."""

    def __init__(self):
        self.labels = {}
        self.constants = {}
        self.origin = ROM_START
        self.output = bytearray()
        self.listing = []
        self.current_addr = ROM_START
        self.errors = []

    def resolve_value(self, s, line_num=None):
        """Resolve a value: number literal, label, or constant."""
        s = s.strip()

        # Check for constant
        if s.upper() in self.constants:
            return self.constants[s.upper()]

        # Check for label
        if s in self.labels:
            return self.labels[s]

        # Check for expression: label + offset or label - offset
        m = re.match(r'(\w+)\s*([+-])\s*(\w+)', s)
        if m:
            base = self.resolve_value(m.group(1), line_num)
            offset = self.resolve_value(m.group(3), line_num)
            if m.group(2) == '+':
                return base + offset
            else:
                return base - offset

        # Try parsing as number
        try:
            return parse_number(s)
        except ValueError:
            raise AssemblerError(f"Undefined symbol: {s}", line_num)

    def _parse_operand(self, mnemonic, operand, line_num, pass_num):
        """
        Parse operand for a mnemonic.
        Returns (opcode_byte, operand_bytes_list).
        """
        # Handle LDA variants
        if mnemonic == 'LDA':
            if operand is None:
                raise AssemblerError("LDA requires an operand", line_num)
            if operand.startswith('#'):
                # LDA #imm
                val = self.resolve_value(operand[1:], line_num) if pass_num == 2 else 0
                return 0x01, [val & 0xFF]
            elif operand.startswith('[') and operand.endswith(']'):
                # LDA [addr16]
                val = self.resolve_value(operand[1:-1], line_num) if pass_num == 2 else 0
                return 0x02, [val & 0xFF, (val >> 8) & 0xFF]
            else:
                raise AssemblerError(f"Invalid LDA operand: {operand}", line_num)

        # Handle LDB variants
        if mnemonic == 'LDB':
            if operand is None:
                raise AssemblerError("LDB requires an operand", line_num)
            if operand.startswith('#'):
                val = self.resolve_value(operand[1:], line_num) if pass_num == 2 else 0
                return 0x04, [val & 0xFF]
            elif operand.startswith('[') and operand.endswith(']'):
                val = self.resolve_value(operand[1:-1], line_num) if pass_num == 2 else 0
                return 0x05, [val & 0xFF, (val >> 8) & 0xFF]
            else:
                raise AssemblerError(f"Invalid LDB operand: {operand}", line_num)

        # Handle PUSH/POP aliases
        if mnemonic == 'PUSH':
            if operand and operand.upper() == 'A':
                return 0x20, []
            elif operand and operand.upper() == 'B':
                return 0x22, []
            else:
                raise AssemblerError("PUSH requires A or B", line_num)

        if mnemonic == 'POP':
            if operand and operand.upper() == 'A':
                return 0x21, []
            elif operand and operand.upper() == 'B':
                return 0x23, []
            else:
                raise AssemblerError("POP requires A or B", line_num)

        # Handle MOV alias
        if mnemonic == 'MOV':
            if operand:
                parts = [p.strip().upper() for p in operand.split(',')]
                if parts == ['A', 'B']:
                    return 0x07, []
                elif parts == ['B', 'A']:
                    return 0x08, []
            raise AssemblerError("MOV requires A,B or B,A", line_num)

        # Look up in opcode table
        if mnemonic == 'CALL':
            mnemonic = 'CAL'

        entry = OPCODES.get(mnemonic)
        if entry is None:
            raise AssemblerError(f"Unknown instruction: {mnemonic}", line_num)

        base_opcode, op_type = entry

        if op_type is None:
            # No operand
            return base_opcode, []

        elif op_type == 'imm':
            if operand is None:
                raise AssemblerError(f"{mnemonic} requires an immediate operand", line_num)
            op = operand.lstrip('#')
            val = self.resolve_value(op, line_num) if pass_num == 2 else 0
            return base_opcode, [val & 0xFF]

        elif op_type == 'addr_mem':
            if operand is None:
                raise AssemblerError(f"{mnemonic} requires a 16-bit memory address", line_num)
            op = operand
            if op.startswith('[') and op.endswith(']'):
                op = op[1:-1]
            val = self.resolve_value(op, line_num) if pass_num == 2 else 0
            return base_opcode, [val & 0xFF, (val >> 8) & 0xFF]

        elif op_type == 'addr_jump':
            if operand is None:
                raise AssemblerError(f"{mnemonic} requires a 16-bit address/label", line_num)
            val = self.resolve_value(operand, line_num) if pass_num == 2 else 0
            return base_opcode, [val & 0xFF, (val >> 8) & 0xFF]

        else:
            raise AssemblerError(f"Internal error: unknown operand type {op_type}", line_num)

    def _process_directive(self, mnemonic, operand, line_num, pass_num):
        """
        Process an assembler directive.
        Returns number of bytes emitted, or -1 for directives that don't emit.
        """
        if mnemonic == '.ORG':
            val = self.resolve_value(operand, line_num) if operand else 0
            self.current_addr = val
            return -1

        elif mnemonic == '.EQU':
            parts = operand.split(None, 1)
            if len(parts) != 2:
                raise AssemblerError(".equ requires NAME VALUE", line_num)
            name = parts[0].upper()
            val = self.resolve_value(parts[1], line_num) if pass_num == 2 else 0
            if pass_num == 1:
                try:
                    val = parse_number(parts[1])
                except ValueError:
                    val = 0
            self.constants[name] = val
            return -1

        elif mnemonic == '.DB':
            # Define bytes: .db 0x42, 0x43, "hello"
            bytes_out = []
            for part in self._split_data(operand):
                part = part.strip()
                if part.startswith('"') and part.endswith('"'):
                    for ch in part[1:-1]:
                        bytes_out.append(ord(ch))
                else:
                    val = self.resolve_value(part, line_num) if pass_num == 2 else 0
                    bytes_out.append(val & 0xFF)
            if pass_num == 2:
                for b in bytes_out:
                    self._emit(b)
            return len(bytes_out)

        elif mnemonic == '.DW':
            # Define words (16-bit, big-endian)
            words = [p.strip() for p in operand.split(',')]
            count = 0
            for w in words:
                val = self.resolve_value(w, line_num) if pass_num == 2 else 0
                if pass_num == 2:
                    self._emit((val >> 8) & 0xFF)
                    self._emit(val & 0xFF)
                count += 2
            return count

        elif mnemonic == '.DS':
            # Define space (reserve bytes)
            val = self.resolve_value(operand, line_num) if operand else 1
            if pass_num == 2:
                for _ in range(val):
                    self._emit(0)
            return val

        return None  # Not a directive

    def _split_data(self, s):
        """Split .db data handling quoted strings."""
        parts = []
        current = ""
        in_string = False
        for ch in s:
            if ch == '"':
                in_string = not in_string
                current += ch
            elif ch == ',' and not in_string:
                parts.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            parts.append(current.strip())
        return parts

    def _emit(self, byte):
        """Emit a byte at the current address."""
        # Extend output array if needed
        offset = self.current_addr - self.origin
        while len(self.output) <= offset:
            self.output.append(0)
        self.output[offset] = byte & 0xFF
        self.current_addr += 1

    def assemble(self, source, filename="<input>"):
        """
        Assemble source code.
        Returns (binary_data, listing).
        """
        lines = source.split('\n')

        # Pass 1: collect labels and calculate addresses
        self.current_addr = self.origin
        for line_num, line in enumerate(lines, 1):
            try:
                label, mnemonic, operand, comment = tokenize_line(line)

                if label:
                    self.labels[label] = self.current_addr

                if mnemonic is None:
                    continue

                if mnemonic.startswith('.'):
                    result = self._process_directive(mnemonic, operand, line_num, pass_num=1)
                    if result is not None and result >= 0:
                        self.current_addr += result
                    continue

                # Instruction: calculate size
                opc, operand_bytes = self._parse_operand(mnemonic, operand, line_num, pass_num=1)
                self.current_addr += 1 + len(operand_bytes)

            except AssemblerError as e:
                self.errors.append(str(e))

        if self.errors:
            return None, self.errors

        # Pass 2: emit code
        self.current_addr = self.origin
        self.output = bytearray()

        for line_num, line in enumerate(lines, 1):
            try:
                label, mnemonic, operand, comment = tokenize_line(line)

                if mnemonic is None:
                    continue

                if mnemonic.startswith('.'):
                    self._process_directive(mnemonic, operand, line_num, pass_num=2)
                    continue

                addr = self.current_addr
                opc, operand_bytes = self._parse_operand(mnemonic, operand, line_num, pass_num=2)
                self._emit(opc)
                for b in operand_bytes:
                    self._emit(b)

                # Add listing entry
                all_bytes = [opc] + operand_bytes
                hex_str = " ".join(f"{b:02X}" for b in all_bytes)
                self.listing.append(f"0x{addr:04X}: {hex_str:12s}  {line.strip()}")

            except AssemblerError as e:
                self.errors.append(str(e))

        if self.errors:
            return None, self.errors

        return bytes(self.output), self.listing


def assemble_file(filename):
    """Assemble a file and return (binary, listing)."""
    with open(filename, 'r') as f:
        source = f.read()

    asm = Assembler()
    result, listing = asm.assemble(source, filename)

    if result is None:
        print(f"Assembler errors:")
        for err in listing:
            print(f"  {err}")
        sys.exit(1)

    return result, listing


def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py input.asm [-o output.bin] [--listing]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    show_listing = "--listing" in sys.argv

    # Parse -o option
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".bin"

    result, listing = assemble_file(input_file)

    with open(output_file, "wb") as f:
        f.write(result)

    print(f"Assembled {input_file} -> {output_file} ({len(result)} bytes)")

    if show_listing:
        print("\nListing:")
        for entry in listing:
            print(f"  {entry}")

    # Also print labels
    asm = Assembler()
    with open(input_file, 'r') as f:
        asm.assemble(f.read())
    if asm.labels:
        print(f"\nLabels:")
        for name, addr in sorted(asm.labels.items(), key=lambda x: x[1]):
            print(f"  {name:20s} = 0x{addr:04X}")


if __name__ == "__main__":
    main()
