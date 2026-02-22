# Breadboard CPU - Human Readable Hardware Dump

## U2 (74HC161)
*uIP Counter*

| Pin | Net Connection |
|---|---|
| ~CLR | `~RESET` |
| CLK | `~CLK` |
| A | `GND` |
| B | `GND` |
| C | `GND` |
| D | `GND` |
| ENP | `VCC` |
| ENT | `VCC` |
| ~LOAD | `~uIP_RST` |
| QA | `uIP_Q0` |
| QB | `uIP_Q1` |
| QC | `uIP_Q2` |
| QD | `uIP_Q3` |
| RCO | `UNCONNECTED` |

## U11 (74HC574)
*Flags Register*

| Pin | Net Connection |
|---|---|
| ~OE | `GND` |
| CLK | `FLAGS_CLK` |
| D0 | `ALU_Z` |
| D1 | `ALU_C` |
| D2 | `ALU_N` |
| D3 | `GND` |
| D4 | `GND` |
| D5 | `GND` |
| D6 | `GND` |
| D7 | `GND` |
| Q0 | `FLAGS_Q0` |
| Q1 | `FLAGS_Q1` |
| Q2 | `FLAGS_Q2` |
| Q3 | `FLAGS_Q3` |
| Q4 | `FLAGS_Q4` |
| Q5 | `FLAGS_Q5` |
| Q6 | `FLAGS_Q6` |
| Q7 | `FLAGS_Q7` |

## U9 (74HC574)
*Instruction Register*

| Pin | Net Connection |
|---|---|
| ~OE | `GND` |
| CLK | `IR_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `IR_Q0` |
| Q1 | `IR_Q1` |
| Q2 | `IR_Q2` |
| Q3 | `IR_Q3` |
| Q4 | `IR_Q4` |
| Q5 | `IR_Q5` |
| Q6 | `IR_Q6` |
| Q7 | `IR_Q7` |

## U3 (28C256)
*Microcode EEPROM A (bits 0-7)*

| Pin | Net Connection |
|---|---|
| ~CE | `GND` |
| ~OE | `GND` |
| ~WE | `VCC` |
| A0 | `uIP_Q0` |
| A1 | `uIP_Q1` |
| A2 | `uIP_Q2` |
| A3 | `uIP_Q3` |
| A4 | `FLAGS_Q0` |
| A5 | `FLAGS_Q1` |
| A6 | `FLAGS_Q2` |
| A7 | `IR_Q0` |
| A8 | `IR_Q1` |
| A9 | `IR_Q2` |
| A10 | `IR_Q3` |
| A11 | `IR_Q4` |
| A12 | `IR_Q5` |
| A13 | `IR_Q6` |
| A14 | `IR_Q7` |
| D0 | `UNCONNECTED` |
| D1 | `UNCONNECTED` |
| D2 | `UNCONNECTED` |
| D3 | `UNCONNECTED` |
| D4 | `UNCONNECTED` |
| D5 | `UNCONNECTED` |
| D6 | `UNCONNECTED` |
| D7 | `UNCONNECTED` |
| Q0 | `CTRL0` |
| Q1 | `CTRL1` |
| Q2 | `CTRL2` |
| Q3 | `CTRL3` |
| Q4 | `CTRL4` |
| Q5 | `CTRL5` |
| Q6 | `CTRL6` |
| Q7 | `CTRL7` |

## U4 (28C256)
*Microcode EEPROM B (bits 8-15)*

| Pin | Net Connection |
|---|---|
| ~CE | `GND` |
| ~OE | `GND` |
| ~WE | `VCC` |
| A0 | `uIP_Q0` |
| A1 | `uIP_Q1` |
| A2 | `uIP_Q2` |
| A3 | `uIP_Q3` |
| A4 | `FLAGS_Q0` |
| A5 | `FLAGS_Q1` |
| A6 | `FLAGS_Q2` |
| A7 | `IR_Q0` |
| A8 | `IR_Q1` |
| A9 | `IR_Q2` |
| A10 | `IR_Q3` |
| A11 | `IR_Q4` |
| A12 | `IR_Q5` |
| A13 | `IR_Q6` |
| A14 | `IR_Q7` |
| D0 | `UNCONNECTED` |
| D1 | `UNCONNECTED` |
| D2 | `UNCONNECTED` |
| D3 | `UNCONNECTED` |
| D4 | `UNCONNECTED` |
| D5 | `UNCONNECTED` |
| D6 | `UNCONNECTED` |
| D7 | `UNCONNECTED` |
| Q0 | `CTRL8` |
| Q1 | `CTRL9` |
| Q2 | `CTRL10` |
| Q3 | `CTRL11` |
| Q4 | `CTRL12` |
| Q5 | `CTRL13` |
| Q6 | `CTRL14` |
| Q7 | `CTRL15` |

## U_INV1 (74HC04)
*Inverters 1 (CLK, dest A-D, IR)*

| Pin | Net Connection |
|---|---|
| 1A | `CLK` |
| 2A | `~DST_A` |
| 3A | `~DST_B` |
| 4A | `~DST_C` |
| 5A | `~DST_D` |
| 6A | `~DST_IR` |
| 1Y | `~CLK` |
| 2Y | `A_CLK` |
| 3Y | `B_CLK` |
| 4Y | `C_CLK` |
| 5Y | `D_CLK` |
| 6Y | `IR_CLK` |

## U_INV2 (74HC04)
*Inverters 2 (dest H,L,OUT, A15, uIP_RST, HLT)*

| Pin | Net Connection |
|---|---|
| 1A | `~DST_H` |
| 2A | `~DST_L` |
| 3A | `~DST_OUT` |
| 4A | `ADDR15` |
| 5A | `CTRL15` |
| 6A | `~HLT` |
| 1Y | `H_CLK` |
| 2Y | `L_CLK` |
| 3Y | `OUT_CLK` |
| 4Y | `~A15` |
| 5Y | `~uIP_RST` |
| 6Y | `HLT_ACTIVE` |

## U5 (74HC154)
*Bus Source Decoder*

| Pin | Net Connection |
|---|---|
| A | `CTRL0` |
| B | `CTRL1` |
| C | `CTRL2` |
| D | `CTRL3` |
| ~G1 | `GND` |
| ~G2 | `GND` |
| ~Y0 | `UNCONNECTED` |
| ~Y1 | `~A_OE` |
| ~Y2 | `~B_OE` |
| ~Y3 | `~C_OE` |
| ~Y4 | `~D_OE` |
| ~Y5 | `~ALU_OE` |
| ~Y6 | `~MEM_OE` |
| ~Y7 | `~IPL_OE` |
| ~Y8 | `~IPH_OE` |
| ~Y9 | `~SP_OE` |
| ~Y10 | `UNCONNECTED` |
| ~Y11 | `UNCONNECTED` |
| ~Y12 | `UNCONNECTED` |
| ~Y13 | `UNCONNECTED` |
| ~Y14 | `UNCONNECTED` |
| ~Y15 | `UNCONNECTED` |

## U6 (74HC154)
*Bus Dest Decoder*

| Pin | Net Connection |
|---|---|
| A | `CTRL4` |
| B | `CTRL5` |
| C | `CTRL6` |
| D | `CTRL7` |
| ~G1 | `~CLK` |
| ~G2 | `GND` |
| ~Y0 | `UNCONNECTED` |
| ~Y1 | `~DST_A` |
| ~Y2 | `~DST_B` |
| ~Y3 | `~DST_C` |
| ~Y4 | `~DST_D` |
| ~Y5 | `~DST_IR` |
| ~Y6 | `UNCONNECTED` |
| ~Y7 | `~DST_H` |
| ~Y8 | `~DST_L` |
| ~Y9 | `UNCONNECTED` |
| ~Y10 | `UNCONNECTED` |
| ~Y11 | `UNCONNECTED` |
| ~Y12 | `~DST_OUT` |
| ~Y13 | `UNCONNECTED` |
| ~Y14 | `UNCONNECTED` |
| ~Y15 | `UNCONNECTED` |

## U6B (74HC154)
*Unclocked Dest Decoder*

| Pin | Net Connection |
|---|---|
| A | `CTRL4` |
| B | `CTRL5` |
| C | `CTRL6` |
| D | `CTRL7` |
| ~G1 | `GND` |
| ~G2 | `GND` |
| ~Y0 | `UNCONNECTED` |
| ~Y1 | `UNCONNECTED` |
| ~Y2 | `UNCONNECTED` |
| ~Y3 | `UNCONNECTED` |
| ~Y4 | `UNCONNECTED` |
| ~Y5 | `UNCONNECTED` |
| ~Y6 | `~MEM_WE` |
| ~Y7 | `UNCONNECTED` |
| ~Y8 | `UNCONNECTED` |
| ~Y9 | `~UC_IP_LO` |
| ~Y10 | `~UC_IP_HI` |
| ~Y11 | `~UC_SP` |
| ~Y12 | `UNCONNECTED` |
| ~Y13 | `~HLT` |
| ~Y14 | `UNCONNECTED` |
| ~Y15 | `UNCONNECTED` |

## U_A (74HC574)
*A Register*

| Pin | Net Connection |
|---|---|
| ~OE | `~A_OE` |
| CLK | `A_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

## U_B (74HC574)
*B Register*

| Pin | Net Connection |
|---|---|
| ~OE | `~B_OE` |
| CLK | `B_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

## U_C (74HC574)
*C Register*

| Pin | Net Connection |
|---|---|
| ~OE | `~C_OE` |
| CLK | `C_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

## U_D (74HC574)
*D Register*

| Pin | Net Connection |
|---|---|
| ~OE | `~D_OE` |
| CLK | `D_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

## U_H (74HC574)
*H Register (ADDR[15:8])*

| Pin | Net Connection |
|---|---|
| ~OE | `GND` |
| CLK | `H_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `ADDR8` |
| Q1 | `ADDR9` |
| Q2 | `ADDR10` |
| Q3 | `ADDR11` |
| Q4 | `ADDR12` |
| Q5 | `ADDR13` |
| Q6 | `ADDR14` |
| Q7 | `ADDR15` |

## U_L (74HC574)
*L Register (ADDR[7:0])*

| Pin | Net Connection |
|---|---|
| ~OE | `GND` |
| CLK | `L_CLK` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `ADDR0` |
| Q1 | `ADDR1` |
| Q2 | `ADDR2` |
| Q3 | `ADDR3` |
| Q4 | `ADDR4` |
| Q5 | `ADDR5` |
| Q6 | `ADDR6` |
| Q7 | `ADDR7` |

## U_IP0 (74HC161)
*4-bit Counter*

| Pin | Net Connection |
|---|---|
| ~CLR | `~RESET` |
| CLK | `CLK` |
| A | `DATA0` |
| B | `DATA1` |
| C | `DATA2` |
| D | `DATA3` |
| ENP | `CTRL12` |
| ENT | `CTRL12` |
| ~LOAD | `~UC_IP_LO` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| RCO | `IP0_RCO` |

## U_IP1 (74HC161)
*4-bit Counter*

| Pin | Net Connection |
|---|---|
| ~CLR | `~RESET` |
| CLK | `CLK` |
| A | `DATA4` |
| B | `DATA5` |
| C | `DATA6` |
| D | `DATA7` |
| ENP | `CTRL12` |
| ENT | `IP0_RCO` |
| ~LOAD | `~UC_IP_LO` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| RCO | `IP1_RCO` |

## U_IP2 (74HC161)
*4-bit Counter*

| Pin | Net Connection |
|---|---|
| ~CLR | `~RESET` |
| CLK | `CLK` |
| A | `DATA0` |
| B | `DATA1` |
| C | `DATA2` |
| D | `DATA3` |
| ENP | `CTRL12` |
| ENT | `IP1_RCO` |
| ~LOAD | `~UC_IP_HI` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| RCO | `IP2_RCO` |

## U_IP3 (74HC161)
*4-bit Counter*

| Pin | Net Connection |
|---|---|
| ~CLR | `~RESET` |
| CLK | `CLK` |
| A | `DATA4` |
| B | `DATA5` |
| C | `DATA6` |
| D | `DATA7` |
| ENP | `CTRL12` |
| ENT | `IP2_RCO` |
| ~LOAD | `~UC_IP_HI` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| RCO | `UNCONNECTED` |

## U_IPL_DATA (74HC245)
*IPL to Data Bus*

| Pin | Net Connection |
|---|---|
| DIR | `VCC` |
| ~OE | `~IPL_OE` |
| A0 | `IP_Q0` |
| A1 | `IP_Q1` |
| A2 | `IP_Q2` |
| A3 | `IP_Q3` |
| A4 | `IP_Q4` |
| A5 | `IP_Q5` |
| A6 | `IP_Q6` |
| A7 | `IP_Q7` |
| B0 | `DATA0` |
| B1 | `DATA1` |
| B2 | `DATA2` |
| B3 | `DATA3` |
| B4 | `DATA4` |
| B5 | `DATA5` |
| B6 | `DATA6` |
| B7 | `DATA7` |
| A0_OUT | `IP_Q0` |
| A1_OUT | `IP_Q1` |
| A2_OUT | `IP_Q2` |
| A3_OUT | `IP_Q3` |
| A4_OUT | `IP_Q4` |
| A5_OUT | `IP_Q5` |
| A6_OUT | `IP_Q6` |
| A7_OUT | `IP_Q7` |
| B0_OUT | `DATA0` |
| B1_OUT | `DATA1` |
| B2_OUT | `DATA2` |
| B3_OUT | `DATA3` |
| B4_OUT | `DATA4` |
| B5_OUT | `DATA5` |
| B6_OUT | `DATA6` |
| B7_OUT | `DATA7` |

## U_IPH_DATA (74HC245)
*IPH to Data Bus*

| Pin | Net Connection |
|---|---|
| DIR | `VCC` |
| ~OE | `~IPH_OE` |
| A0 | `IP_Q8` |
| A1 | `IP_Q9` |
| A2 | `IP_Q10` |
| A3 | `IP_Q11` |
| A4 | `IP_Q12` |
| A5 | `IP_Q13` |
| A6 | `IP_Q14` |
| A7 | `IP_Q15` |
| B0 | `DATA0` |
| B1 | `DATA1` |
| B2 | `DATA2` |
| B3 | `DATA3` |
| B4 | `DATA4` |
| B5 | `DATA5` |
| B6 | `DATA6` |
| B7 | `DATA7` |
| A0_OUT | `IP_Q8` |
| A1_OUT | `IP_Q9` |
| A2_OUT | `IP_Q10` |
| A3_OUT | `IP_Q11` |
| A4_OUT | `IP_Q12` |
| A5_OUT | `IP_Q13` |
| A6_OUT | `IP_Q14` |
| A7_OUT | `IP_Q15` |
| B0_OUT | `DATA0` |
| B1_OUT | `DATA1` |
| B2_OUT | `DATA2` |
| B3_OUT | `DATA3` |
| B4_OUT | `DATA4` |
| B5_OUT | `DATA5` |
| B6_OUT | `DATA6` |
| B7_OUT | `DATA7` |

## U_SP0 (74HC193)
*4-bit Up/Down Counter*

| Pin | Net Connection |
|---|---|
| CLR | `GND` |
| UP | `SP_UP_NAND` |
| DOWN | `SP_DN_NAND` |
| A | `DATA0` |
| B | `DATA1` |
| C | `DATA2` |
| D | `DATA3` |
| ~LOAD | `~UC_SP` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| ~CO | `SP0_CO` |
| ~BO | `SP0_BO` |

## U_SP1 (74HC193)
*4-bit Up/Down Counter*

| Pin | Net Connection |
|---|---|
| CLR | `GND` |
| UP | `SP0_CO` |
| DOWN | `SP0_BO` |
| A | `DATA4` |
| B | `DATA5` |
| C | `DATA6` |
| D | `DATA7` |
| ~LOAD | `~UC_SP` |
| QA | `UNCONNECTED` |
| QB | `UNCONNECTED` |
| QC | `UNCONNECTED` |
| QD | `UNCONNECTED` |
| ~CO | `UNCONNECTED` |
| ~BO | `UNCONNECTED` |

## U_NAND_SP (74HC00)
*Quad NAND*

| Pin | Net Connection |
|---|---|
| 1A | `CTRL13` |
| 1B | `CLK` |
| 2A | `CTRL14` |
| 2B | `CLK` |
| 3A | `UNCONNECTED` |
| 3B | `UNCONNECTED` |
| 4A | `UNCONNECTED` |
| 4B | `UNCONNECTED` |
| 1Y | `SP_UP_NAND` |
| 2Y | `SP_DN_NAND` |
| 3Y | `UNCONNECTED` |
| 4Y | `UNCONNECTED` |

## U_SP_ADD_LO (74HC283)
*SP+IR Adder Low*

| Pin | Net Connection |
|---|---|
| A1 | `SP_Q0` |
| A2 | `SP_Q1` |
| A3 | `SP_Q2` |
| A4 | `SP_Q3` |
| B1 | `IR_Q0` |
| B2 | `IR_Q1` |
| B3 | `IR_Q2` |
| B4 | `IR_Q3` |
| C0 | `GND` |
| S1 | `UNCONNECTED` |
| S2 | `UNCONNECTED` |
| S3 | `UNCONNECTED` |
| S4 | `UNCONNECTED` |
| C4 | `SP_ADD_CARRY` |

## U_SP_ADD_HI (74HC283)
*SP+IR Adder High*

| Pin | Net Connection |
|---|---|
| A1 | `SP_Q4` |
| A2 | `SP_Q5` |
| A3 | `SP_Q6` |
| A4 | `SP_Q7` |
| B1 | `GND` |
| B2 | `GND` |
| B3 | `GND` |
| B4 | `GND` |
| C0 | `SP_ADD_CARRY` |
| S1 | `UNCONNECTED` |
| S2 | `UNCONNECTED` |
| S3 | `UNCONNECTED` |
| S4 | `UNCONNECTED` |
| C4 | `UNCONNECTED` |

## U_SP_DATA (74HC245)
*SP+offset to Data Bus*

| Pin | Net Connection |
|---|---|
| DIR | `VCC` |
| ~OE | `~SP_OE` |
| A0 | `SP_SUM0` |
| A1 | `SP_SUM1` |
| A2 | `SP_SUM2` |
| A3 | `SP_SUM3` |
| A4 | `SP_SUM4` |
| A5 | `SP_SUM5` |
| A6 | `SP_SUM6` |
| A7 | `SP_SUM7` |
| B0 | `DATA0` |
| B1 | `DATA1` |
| B2 | `DATA2` |
| B3 | `DATA3` |
| B4 | `DATA4` |
| B5 | `DATA5` |
| B6 | `DATA6` |
| B7 | `DATA7` |
| A0_OUT | `SP_SUM0` |
| A1_OUT | `SP_SUM1` |
| A2_OUT | `SP_SUM2` |
| A3_OUT | `SP_SUM3` |
| A4_OUT | `SP_SUM4` |
| A5_OUT | `SP_SUM5` |
| A6_OUT | `SP_SUM6` |
| A7_OUT | `SP_SUM7` |
| B0_OUT | `DATA0` |
| B1_OUT | `DATA1` |
| B2_OUT | `DATA2` |
| B3_OUT | `DATA3` |
| B4_OUT | `DATA4` |
| B5_OUT | `DATA5` |
| B6_OUT | `DATA6` |
| B7_OUT | `DATA7` |

## U_ALU (GAL22V10)
*ALU PLD*

| Pin | Net Connection |
|---|---|
| A0 | `A_Q0` |
| A1 | `A_Q1` |
| A2 | `A_Q2` |
| A3 | `A_Q3` |
| A4 | `A_Q4` |
| A5 | `A_Q5` |
| A6 | `A_Q6` |
| A7 | `A_Q7` |
| B0 | `B_Q0` |
| B1 | `B_Q1` |
| B2 | `B_Q2` |
| B3 | `B_Q3` |
| B4 | `B_Q4` |
| B5 | `B_Q5` |
| B6 | `B_Q6` |
| B7 | `B_Q7` |
| OP0 | `CTRL8` |
| OP1 | `CTRL9` |
| OP2 | `CTRL10` |
| ~OE | `~ALU_OE` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |
| Z | `ALU_Z` |
| C | `ALU_C` |
| N | `ALU_N` |

## U_AND_FLG (74HC08)
*Quad AND*

| Pin | Net Connection |
|---|---|
| 1A | `UNCONNECTED` |
| 1B | `UNCONNECTED` |
| 2A | `UNCONNECTED` |
| 2B | `UNCONNECTED` |
| 3A | `UNCONNECTED` |
| 3B | `UNCONNECTED` |
| 4A | `CTRL11` |
| 4B | `CLK` |
| 1Y | `UNCONNECTED` |
| 2Y | `UNCONNECTED` |
| 3Y | `UNCONNECTED` |
| 4Y | `FLAGS_CLK` |

## U_ROM (28C256)
*32KB EEPROM*

| Pin | Net Connection |
|---|---|
| ~CE | `ADDR15` |
| ~OE | `~MEM_OE` |
| ~WE | `VCC` |
| A0 | `ADDR0` |
| A1 | `ADDR1` |
| A2 | `ADDR2` |
| A3 | `ADDR3` |
| A4 | `ADDR4` |
| A5 | `ADDR5` |
| A6 | `ADDR6` |
| A7 | `ADDR7` |
| A8 | `ADDR8` |
| A9 | `ADDR9` |
| A10 | `ADDR10` |
| A11 | `ADDR11` |
| A12 | `ADDR12` |
| A13 | `ADDR13` |
| A14 | `ADDR14` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

## U_RAM (62256)
*32KB SRAM*

| Pin | Net Connection |
|---|---|
| ~CE | `~A15` |
| ~OE | `~MEM_OE` |
| ~WE | `~MEM_WE` |
| A0 | `ADDR0` |
| A1 | `ADDR1` |
| A2 | `ADDR2` |
| A3 | `ADDR3` |
| A4 | `ADDR4` |
| A5 | `ADDR5` |
| A6 | `ADDR6` |
| A7 | `ADDR7` |
| A8 | `ADDR8` |
| A9 | `ADDR9` |
| A10 | `ADDR10` |
| A11 | `ADDR11` |
| A12 | `ADDR12` |
| A13 | `ADDR13` |
| A14 | `ADDR14` |
| D0 | `DATA0` |
| D1 | `DATA1` |
| D2 | `DATA2` |
| D3 | `DATA3` |
| D4 | `DATA4` |
| D5 | `DATA5` |
| D6 | `DATA6` |
| D7 | `DATA7` |
| Q0 | `DATA0` |
| Q1 | `DATA1` |
| Q2 | `DATA2` |
| Q3 | `DATA3` |
| Q4 | `DATA4` |
| Q5 | `DATA5` |
| Q6 | `DATA6` |
| Q7 | `DATA7` |

