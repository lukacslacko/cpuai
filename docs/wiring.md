# Wiring Guide

Pin-by-pin connections organized by module. All ICs use VCC=5V, GND=0V with 0.1uF bypass cap.

## Module 1: Clock

### 555 Timer (U1)
| Pin | Signal | Connects to |
|-----|--------|-------------|
| 3 | OUT | Clock switch center |

### Clock Switch
| Position | Signal |
|----------|--------|
| AUTO | 555 output |
| MANUAL | Push button (debounced) |
| OUT | CLK line (global) |

---

## Module 2: Micro-Sequencer

### uIP Counter - 74HC161 (U2)
| Pin | Signal | Connects to |
|-----|--------|-------------|
| 2 | CLK | Global CLK |
| 1 | ~CLR | uIP_RST (control bit 15, active-low via inverter) |
| 3-6 | Q0-Q3 | Microcode EEPROM A3-A0 |
| 7 | RCO | (unused) |
| 9 | ~LOAD | VCC (never parallel load) |
| 10 | ENT | VCC (always counting) |
| ENP | | VCC |
| D0-D3 | | GND (clear to 0) |

### Microcode EEPROM A - 28C256 (U3) - Low byte
| Pin | Signal | Connects to |
|-----|--------|-------------|
| A0-A3 | | uIP Q0-Q3 |
| A4-A6 | | FLAGS register Q0-Q2 (Z, C, N) |
| A7-A14 | | IR register Q0-Q7 |
| D0-D7 | | Control word bits 0-7 |
| ~CE | | GND (always enabled) |
| ~OE | | GND (always reading) |
| ~WE | | VCC (never writing in circuit) |

### Microcode EEPROM B - 28C256 (U4) - Middle byte
| Pin | Signal | Connects to |
|-----|--------|-------------|
| A0-A14 | | Same as EEPROM A |
| D0-D7 | | Control word bits 8-15 |
| ~CE, ~OE, ~WE | | Same as EEPROM A |

### Microcode EEPROM C - 28C256 (U4b) - High byte
| Pin | Signal | Connects to |
|-----|--------|-------------|
| A0-A14 | | Same as EEPROM A |
| D0-D7 | | Control word bits 16-23 |
| ~CE, ~OE, ~WE | | Same as EEPROM A |

---

## Module 3: Control Signal Decode

### Bus Source Decoder - 74HC138 (U5)
Decodes control bits 0-2 into 8 active-low outputs.
| Pin | Signal | Connects to |
|-----|--------|-------------|
| A,B,C | | Control bits 0, 1, 2 |
| ~G1 | | GND |
| G2A,G2B | | VCC via inverter (active when needed) |
| ~Y0 | n/a | SRC_NONE (not connected) |
| ~Y1 | ~A_OE | A register 74HC574 ~OE |
| ~Y2 | ~B_OE | B register 74HC574 ~OE |
| ~Y3 | ~ALU_OE | ALU output buffer ~OE |
| ~Y4 | ~MEM_OE | Memory ~OE |
| ~Y5 | ~IR_LO_OE | IR low nibble buffer ~OE |
| ~Y6 | ~IP_LO_OE | IP low byte buffer ~OE |
| ~Y7 | ~IP_HI_OE | IP high byte buffer ~OE |

### Bus Dest Decoder - 74HC154 (U6)
Decodes control bits 4-7 into 16 active-low outputs.
Clock these with the falling edge of CLK (invert CLK to get latch pulse).
| Pin | Signal | Connects to |
|-----|--------|-------------|
| A,B,C,D | | Control bits 4, 5, 6, 7 |
| ~Y0 | n/a | DST_NONE |
| ~Y1 | A_CLK | A register 74HC574 CLK (with AND gate) |
| ~Y2 | B_CLK | B register 74HC574 CLK |
| ~Y3 | IR_CLK | IR register 74HC574 CLK |
| ~Y4 | MAR_LO_LE | MAR low latch enable |
| ~Y5 | MAR_HI_LE | MAR high latch enable |
| ~Y6 | ~MEM_WE | RAM ~WE |
| ~Y7 | OUT_CLK | Output register CLK |
| ~Y8 | TMP_CLK | TMP register 74HC574 CLK |

---

## Module 4: Registers

### A Register - 74HC574 (U7)
| Pin | Signal | Connects to |
|-----|--------|-------------|
| D1-D8 | | Data bus D0-D7 |
| Q1-Q8 | | A bus (to ALU input A, and bus source mux) |
| CLK | | A_CLK from bus dest decoder |
| ~OE | | ~A_OE from bus source decoder |

### B Register - 74HC574 (U8)
Same structure as A, with B_CLK and ~B_OE.
Q outputs go to ALU input B.

### IR Register - 74HC574 (U9)
| Pin | Signal | Connects to |
|-----|--------|-------------|
| D1-D8 | | Data bus D0-D7 |
| Q1-Q8 | | Microcode EEPROM A7-A14 |
| Q1-Q4 | | Also: IR_LO buffer input (for jump addr high nibble) |
| CLK | | IR_CLK from bus dest decoder |
| ~OE | | VCC (always output to EEPROM address) |

### Output Register - 74HC574 (U10)
| Pin | Signal |
|-----|--------|
| D1-D8 | Data bus D0-D7 |
| Q1-Q8 | 8 LEDs (with 1K resistors) |
| CLK | OUT_CLK from bus dest decoder |
| ~OE | GND (always driving LEDs) |

### FLAGS Register - 74HC173 (U11)
| Pin | Signal | Connects to |
|-----|--------|-------------|
| D0 | Z_in | ALU zero flag output |
| D1 | C_in | ALU carry flag output |
| D2 | N_in | ALU negative flag output |
| Q0-Q2 | | Microcode EEPROM A4-A6 |
| CLK | | FLAGS_IN (control bit 9) AND CLK |
| ~OE | | GND (always output to EEPROM) |

---

## Module 5: IP (Instruction Pointer)

Three cascaded 74HC161 counters (12-bit).

### IP Low - 74HC161 (U12) - bits 0-3
| Pin | Signal |
|-----|--------|
| CLK | IP_INC (control bit 10) AND CLK |
| ~CLR | Global ~RESET |
| D0-D3 | MAR output bits 0-3 (for IP_LOAD) |
| ~LOAD | IP_LOAD (control bit 11, active-low) |
| Q0-Q3 | IP bus [3:0], MAR input |
| RCO | IP Mid ENT |

### IP Mid-Low - 74HC161 (U13) - bits 4-7
Same structure, cascaded from IP Low.

### IP Mid-High - 74HC161 (U14) - bits 8-11
Same structure, cascaded from IP Mid-Low.

### IP High - 74HC161 (U14b) - bits 12-15
Same structure, cascaded from IP Mid-High.

---

## Module 6: MAR (Memory Address Register)

### MAR Low - 74HC573 (U15) - bits 0-7
| Pin | Signal |
|-----|--------|
| D0-D7 | Data bus D0-D7 |
| Q0-Q7 | Address bus A0-A7 |
| LE | MAR_LO_LE from dest decoder |
| ~OE | GND (always driving address bus) |

### MAR High - 74HC573 (U16) - bits 8-15
| Pin | Signal |
|-----|--------|
| D0-D7 | Data bus D0-D7 |
| Q0-Q7 | Address bus A8-A15 |
| LE | MAR_HI_LE from dest decoder |
| ~OE | GND |

---

## Module 7: SP (Stack Pointer)

### SP Low - 74HC193 (U17) - bits 0-3
| Pin | Signal |
|-----|--------|
| UP | SP_INC (control bit 12) AND CLK |
| DOWN | SP_DEC (control bit 13) AND CLK |
| ~CLR | Global ~RESET (resets to 0xFF via preset) |
| Q0-Q3 | SP output bits [3:0] |
| ~BO | SP High DOWN (cascade borrow) |
| ~CO | SP High UP (cascade carry) |

### SP High - 74HC193 (U18) - bits 4-7
Cascaded from SP Low.

### SP-to-MAR Logic
When SP_TO_MAR (control bit 16) is active:
- MAR Low latch gets SP value (SP drives data bus)
- MAR High latch gets 0xFF (hardwired for stack at 0xFF00)

Note: SP_TO_MAR uses a separate buffer (74HC245) to put SP on the data bus,
and hardwires MAR_HI to 0xFF via a latch or direct connection.

---

## Module 8: ALU

### GAL22V10 Low (U19) - bits 0-3
| Pin | Signal |
|-----|--------|
| I0-I3 | A register bits 0-3 |
| I4-I7 | B register bits 0-3 |
| I8-I10 | ALU_OP (control bits 6-8) |
| I11 | Carry-in (GND for low nibble, or from prev) |
| O0-O3 | Result bits 0-3 |
| O4 | Carry out -> GAL High carry in |
| O5 | Partial zero detect |

### GAL22V10 High (U20) - bits 4-7
Same structure, carry-in from Low carry-out.
Generates final Z, C, N flags.

### ALU Output Buffer - 74HC245 (U21)
| Pin | Signal |
|-----|--------|
| A0-A7 | ALU result bits 0-7 |
| B0-B7 | Data bus D0-D7 |
| DIR | HIGH (A->B, ALU to bus) |
| ~OE | ~ALU_OE from bus source decoder |

---

## Module 9: Memory

| Pin | Signal |
|-----|--------|
| A0-A14 | Address bus A0-A14 |
| D0-D7 | Data bus D0-D7 |
| ~CE | Address decode: active when A15=0 (addr < 0x8000) |
| ~OE | ~MEM_OE from bus source decoder |
| ~WE | VCC (read-only in circuit) |

### RAM - 62256 (U23)
| Pin | Signal |
|-----|--------|
| A0-A14 | Address bus A0-A14 |
| D0-D7 | Data bus D0-D7 |
| ~CE | Address decode: active when A15=1 (addr >= 0x8000) |
| ~OE | ~MEM_OE from bus source decoder |
| ~WE | ~MEM_WE from bus dest decoder |

---

## Module 10: Data Bus Pull-downs

8x 10K resistors from each data bus line to GND.
Ensures bus reads as 0x00 when no source is active.

---

## Address Decoding Logic

Simple decode using address bit A15:
- ROM: `~A15` — addresses 0x0000-0x7FFF
- RAM: `A15` — addresses 0x8000-0xFFFF

Use one 74HC04 inverter for ~CE signals.

---

## Reset Circuit

Push button with RC debounce:
- Drives ~CLR on all counters (IP, uIP, SP)
- IP resets to 0x0000
- SP resets to 0xFF
- uIP resets to 0
