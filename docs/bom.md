# Bill of Materials

## ICs

| # | Part | Qty | Role | Notes |
|---|------|-----|------|-------|
| 1 | GAL22V10 | 2 | ALU (4 bits each) | Need GAL programmer |
| 2 | 28C256 (32KB EEPROM) | 3 | Microcode ROM | Addr: IR\|FLAGS\|uIP (24-bit total) |
| 3 | 28C256 (32KB EEPROM) | 1 | Program ROM | 32KB used (0x0000-0x7FFF) |
| 4 | 62256 (32KB SRAM) | 1 | RAM + Stack | 32KB used (0x8000-0xFFFF) |
| 5 | 74HC574 (8-bit register, tri-state) | 5 | A, B, IR, OUT, TMP |
| 6 | 74HC161 (4-bit sync counter) | 4 | IP (4x4=16 bits, cascaded) |
| 7 | 74HC161 (4-bit sync counter) | 1 | uIP (micro-step counter) |
| 8 | 74HC193 (4-bit up/down counter) | 2 | SP (8-bit stack pointer) |
| 9 | 74HC573 (8-bit transparent latch) | 2 | MAR low byte, MAR high byte |
| 10 | 74HC245 (8-bit bus transceiver) | 2 | Memory bus buffering |
| 11 | 74HC154 (4-to-16 decoder) | 2 | Bus source decode, bus dest decode |
| 12 | 74HC08 (quad AND) | 2 | Clock gating, signal combining |
| 13 | 74HC32 (quad OR) | 1 | Flag combining |
| 14 | 74HC04 (hex inverter) | 1 | Signal inversion |
| 15 | 74HC173 (4-bit register with enable) | 1 | FLAGS register (Z, C, N) |
| 16 | 555 Timer | 1 | Main clock (~100 kHz) |

## Passive Components

| Part | Qty | Notes |
|------|-----|-------|
| 0.1uF ceramic bypass caps | 25 | One per IC, VCC to GND |
| 10K resistor | 8 | Data bus pull-downs |
| 1K resistor | 30 | LED current limiters |
| 5mm LED | 30 | Debug: 8 bus + 12 IP + 3 flags + 8 output |
| Push button (momentary) | 2 | Manual clock, reset |
| SPDT toggle switch | 1 | Clock source: 555 vs manual |
| 1M pot + 2x capacitors | 1 set | 555 frequency adjust |

## Infrastructure

| Part | Qty | Notes |
|------|-----|-------|
| Full-size breadboard | 6-8 | 830 tie points each |
| 22AWG jumper wire kit | 1 | Pre-cut preferred |
| 5V power supply | 1 | 1-2A, regulated |
| Power bus strips | 4+ | Connect power across boards |

## Total IC Count: ~30

## Substitutions

- **74HC574 -> 74HC374**: Pin-compatible, either works
- **74HC161 -> 74HC163**: Sync clear vs async clear, minor difference
- **74HC193 -> pair of 74HC161**: Need separate up/down control
- **74HC573 -> 74HC574**: Use edge-triggered instead of transparent (adjust clock)
- **62256 -> 6264** (8KB SRAM): Sufficient, we only use 512 bytes
- **74HC173 -> 74HC175** (quad D): Need external output enable
