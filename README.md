# Breadboard CPU

A minimalistic 8-bit breadboard CPU with microcode-based control, designed to be built on real breadboards using through-hole 74HC logic and GAL22V10 PLDs.

## Quick Start

```bash
# Assemble and run the Fibonacci example
python assembler.py examples/fibonacci.asm --listing
python emulator.py examples/fibonacci.asm

# Compile MiniC, assemble, and run
python compiler.py examples/fibonacci.mc -o examples/fib_compiled.asm
python emulator.py examples/fib_compiled.asm

# Generate microcode EEPROM binaries
python microcode.py

# Interactive debugger
python emulator.py examples/fibonacci.asm --step
```

## Toolchain

| Tool | Description |
|------|-------------|
| `microcode.py` | Generates microcode EEPROM binary images |
| `assembler.py` | Two-pass assembler (labels, directives, listing) |
| `compiler.py` | MiniC-to-assembly compiler |
| `emulator.py` | Instruction-level emulator with interactive debugger |

## Assembly Language

```asm
    LDA #42         ; A <- immediate
    LDA [0x10]      ; A <- RAM[0x10]
    STA [0x10]      ; RAM[0x10] <- A
    ADD             ; A <- A + B
    CMP             ; flags <- A - B
    JZ label        ; jump if zero
    CAL function    ; call subroutine
    OUT             ; output A
    HLT             ; halt
```

## MiniC Language

* **MiniC Compiler:** Compiles a C-like language to assembly. Includes variables, loops, conditionals, and functions with arguments and return values.

## Architecture Documentation

Detailed documentation is available in the `docs/` directory:
* [Architecture Overview](docs/architecture.md)
* [Instruction Set Architecture (ISA)](docs/isa.md)
* [Bill of Materials (BOM)](docs/bom.md)
* [Wiring Guide](docs/wiring.md) — Pin-by-pin connections

## Project Structure

```
microcode.py         # Microcode generator
emulator.py          # CPU emulator
assembler.py         # Assembler
compiler.py          # MiniC compiler
docs/                # Hardware documentation
examples/            # Example programs (.asm, .mc)
```