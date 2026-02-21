#!/usr/bin/env python3
"""
Structural Hardware Emulator for the Breadboard CPU.
Simulates individual 74HC series chips, memory, and GALs.
Also generates wiring documentation and Bill of Materials automatically.
"""

import sys

class Net:
    def __init__(self, name, pull=None):
        self.name = name
        self.pull = pull
        self.state = pull if pull is not None else 0
        self.next_state = self.state
        self.drivers = []

    def eval(self):
        val = None
        for d in self.drivers:
            v = d()
            if v is not None and v != 'Z':
                if val is not None and val != v:
                    pass # Bus contention
                val = v
        self.next_state = val if val is not None else (self.pull if self.pull is not None else 0)

    def apply(self):
        changed = self.state != self.next_state
        self.state = self.next_state
        return changed

class System:
    def __init__(self):
        self.nets = {}
        self.chips = []
        self.wiring_log = []

    def net(self, name, pull=None):
        if name not in self.nets:
            self.nets[name] = Net(name, pull)
        return self.nets[name]

    def bus(self, name, width, pull=None):
        return [self.net(f"{name}{i}", pull) for i in range(width)]

    def add(self, chip):
        self.chips.append(chip)
        return chip

    def wire(self, chip, pin_name, net):
        if pin_name not in chip.inputs and pin_name not in chip.outputs:
            raise ValueError(f"Pin {pin_name} not found on {chip.ref} ({chip.part_name})")
        chip.connections[pin_name] = net
        self.wiring_log.append((chip, pin_name, net.name))
        if pin_name in chip.outputs:
            net.drivers.append(lambda: chip.out_states.get(pin_name, 'Z'))

    def load_rom(self, data):
        self.rom_chip.load(data)
        
    def load_microcode(self, mc_a, mc_b, mc_c):
        self.mc_a.load(mc_a)
        self.mc_b.load(mc_b)
        self.mc_c.load(mc_c)

    def eval_combinational(self):
        for _ in range(30):
            for chip in self.chips:
                chip.eval()
            changed = False
            for net in self.nets.values():
                net.eval()
                if net.apply():
                    changed = True
            if not changed:
                return
        print("WARNING: Combinational loop detected!")

    def tick(self):
        if not hasattr(self, 'clk_val'):
            self.clk_val = 0
            self.net("CLK").drivers.append(lambda: self.clk_val)

        # Rising edge
        self.clk_val = 1
        self.eval_combinational()
        for chip in self.chips:
            chip.tick()
        self.eval_combinational()

        # Falling edge
        self.clk_val = 0
        self.eval_combinational()
        for chip in self.chips:
            chip.tick()
        self.eval_combinational()
        
        self.eval_combinational()

    def get_bus_val(self, bus):
        v = 0
        for i, n in enumerate(bus):
            if n.state == 1:
                v |= (1 << i)
        return v

    def emit_human_readable(self, filename):
        with open(filename, 'w') as f:
            f.write("# Breadboard CPU - Human Readable Hardware Dump\n\n")
            for chip in self.chips:
                f.write(f"## {chip.ref} ({chip.part_name})\n")
                f.write(f"*{chip.desc}*\n\n")
                
                # Sort pins systematically (inputs then outputs)
                all_pins = chip.inputs + chip.outputs
                
                f.write("| Pin | Net Connection |\n")
                f.write("|---|---|\n")
                for pin in all_pins:
                    net = chip.connections.get(pin)
                    net_name = net.name if net else "UNCONNECTED"
                    f.write(f"| {pin} | `{net_name}` |\n")
                
                f.write("\n")
        print(f"Generated {filename}")

class Chip:
    part_name = "Generic"
    def __init__(self, ref, inputs, outputs, desc=""):
        self.ref = ref
        self.desc = desc
        self.inputs = inputs
        self.outputs = outputs
        self.connections = {}
        self.out_states = {p: 'Z' for p in outputs}

    def read(self, pin_name):
        net = self.connections.get(pin_name)
        return net.state if net else 0

    def write(self, pin_name, val):
        self.out_states[pin_name] = val

    def eval(self): pass
    def tick(self): pass

class IC_74HC574(Chip):
    part_name = "74HC574"
    def __init__(self, ref, desc="8-bit Register"):
        super().__init__(ref, ['~OE', 'CLK'] + [f'D{i}' for i in range(8)], [f'Q{i}' for i in range(8)], desc)
        self.val = 0
        self.prev_clk = 0

    def eval(self):
        if self.read('~OE') == 0:
            for i in range(8): self.write(f'Q{i}', (self.val >> i) & 1)
        else:
            for i in range(8): self.write(f'Q{i}', 'Z')

    def tick(self):
        clk = self.read('CLK')
        if clk == 1 and self.prev_clk == 0:
            v = 0
            for i in range(8):
                if self.read(f'D{i}') == 1: v |= (1 << i)
            self.val = v
        self.prev_clk = clk

class IC_74HC161(Chip):
    part_name = "74HC161"
    def __init__(self, ref, desc="4-bit Counter"):
        super().__init__(ref, ['~CLR', 'CLK', 'A', 'B', 'C', 'D', 'ENP', 'ENT', '~LOAD'], ['QA', 'QB', 'QC', 'QD', 'RCO'], desc)
        self.val = 0
        self.prev_clk = 0

    def eval(self):
        if self.read('~CLR') == 0: self.val = 0
        for i, p in enumerate(['QA', 'QB', 'QC', 'QD']): self.write(p, (self.val >> i) & 1)
        self.write('RCO', 1 if (self.val == 15 and self.read('ENT') == 1) else 0)

    def tick(self):
        clk = self.read('CLK')
        if clk == 1 and self.prev_clk == 0:
            if self.read('~CLR') != 0:
                if self.read('~LOAD') == 0:
                    v = 0
                    for i, p in enumerate(['A', 'B', 'C', 'D']):
                        if self.read(p) == 1: v |= (1 << i)
                    self.val = v
                elif self.read('ENP') == 1 and self.read('ENT') == 1:
                    self.val = (self.val + 1) & 0x0F
        self.prev_clk = clk

class IC_74HC193(Chip):
    part_name = "74HC193"
    def __init__(self, ref, desc="4-bit Up/Down Counter"):
        super().__init__(ref, ['CLR', 'UP', 'DOWN', 'A', 'B', 'C', 'D', '~LOAD'], ['QA', 'QB', 'QC', 'QD', '~CO', '~BO'], desc)
        self.val = 0
        self.prev_up = 0
        self.prev_dn = 0

    def eval(self):
        if self.read('CLR') == 1: self.val = 0
        for i, p in enumerate(['QA', 'QB', 'QC', 'QD']): self.write(p, (self.val >> i) & 1)
        self.write('~CO', 0 if (self.val == 15 and self.read('UP') == 0) else 1)
        self.write('~BO', 0 if (self.val == 0 and self.read('DOWN') == 0) else 1)

    def tick(self):
        up = self.read('UP')
        dn = self.read('DOWN')
        if self.read('CLR') == 0:
            if self.read('~LOAD') == 0:
                v = 0
                for i, p in enumerate(['A', 'B', 'C', 'D']):
                    if self.read(p) == 1: v |= (1 << i)
                self.val = v
            else:
                if up == 1 and self.prev_up == 0 and dn == 1:
                    self.val = (self.val + 1) & 0x0F
                if dn == 1 and self.prev_dn == 0 and up == 1:
                    self.val = (self.val - 1) & 0x0F
        self.prev_up = up
        self.prev_dn = dn

class IC_74HC245(Chip):
    part_name = "74HC245"
    def __init__(self, ref, desc="8-bit Transceiver"):
        super().__init__(ref, ['DIR', '~OE'] + [f'A{i}' for i in range(8)] + [f'B{i}' for i in range(8)], 
                              [f'A{i}_OUT' for i in range(8)] + [f'B{i}_OUT' for i in range(8)], desc)
    def eval(self):
        if self.read('~OE') == 0:
            if self.read('DIR') == 1:
                for i in range(8):
                    self.write(f'A{i}_OUT', 'Z')
                    self.write(f'B{i}_OUT', self.read(f'A{i}'))
            else:
                for i in range(8):
                    self.write(f'B{i}_OUT', 'Z')
                    self.write(f'A{i}_OUT', self.read(f'B{i}'))
        else:
            for i in range(8):
                self.write(f'A{i}_OUT', 'Z')
                self.write(f'B{i}_OUT', 'Z')

class IC_74HC283(Chip):
    part_name = "74HC283"
    def __init__(self, ref, desc="4-bit Adder"):
        super().__init__(ref, ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C0'], ['S1', 'S2', 'S3', 'S4', 'C4'], desc)
    def eval(self):
        a = sum((self.read(f'A{i+1}') << i) for i in range(4))
        b = sum((self.read(f'B{i+1}') << i) for i in range(4))
        res = a + b + self.read('C0')
        for i in range(4): self.write(f'S{i+1}', (res >> i) & 1)
        self.write('C4', (res >> 4) & 1)

class IC_74HC138(Chip):
    part_name = "74HC138"
    def __init__(self, ref, desc="3-to-8 Decoder"):
        super().__init__(ref, ['A', 'B', 'C', '~G2A', '~G2B', 'G1'], [f'~Y{i}' for i in range(8)], desc)
    def eval(self):
        en = (self.read('G1') == 1) and (self.read('~G2A') == 0) and (self.read('~G2B') == 0)
        idx = (self.read('C') << 2) | (self.read('B') << 1) | self.read('A')
        for i in range(8): self.write(f'~Y{i}', 0 if (en and i == idx) else 1)

class IC_74HC154(Chip):
    part_name = "74HC154"
    def __init__(self, ref, desc="4-to-16 Decoder"):
        super().__init__(ref, ['A', 'B', 'C', 'D', '~G1', '~G2'], [f'~Y{i}' for i in range(16)], desc)
    def eval(self):
        en = (self.read('~G1') == 0) and (self.read('~G2') == 0)
        idx = (self.read('D') << 3) | (self.read('C') << 2) | (self.read('B') << 1) | self.read('A')
        for i in range(16): self.write(f'~Y{i}', 0 if (en and i == idx) else 1)

class IC_74HC04(Chip):
    part_name = "74HC04"
    def __init__(self, ref, desc="Hex Inverter"):
        super().__init__(ref, [f'{i}A' for i in range(1, 7)], [f'{i}Y' for i in range(1, 7)], desc)
    def eval(self):
        for i in range(1, 7): self.write(f'{i}Y', 1 - self.read(f'{i}A'))

class IC_74HC08(Chip):
    part_name = "74HC08"
    def __init__(self, ref, desc="Quad AND"):
        super().__init__(ref, ['1A','1B','2A','2B','3A','3B','4A','4B'], ['1Y','2Y','3Y','4Y'], desc)
    def eval(self):
        for i in range(1, 5): self.write(f'{i}Y', self.read(f'{i}A') & self.read(f'{i}B'))

class IC_74HC32(Chip):
    part_name = "74HC32"
    def __init__(self, ref, desc="Quad OR"):
        super().__init__(ref, ['1A','1B','2A','2B','3A','3B','4A','4B'], ['1Y','2Y','3Y','4Y'], desc)
    def eval(self):
        for i in range(1, 5): self.write(f'{i}Y', self.read(f'{i}A') | self.read(f'{i}B'))

class IC_28C256(Chip):
    part_name = "28C256"
    def __init__(self, ref, desc="32KB EEPROM"):
        super().__init__(ref, ['~CE', '~OE', '~WE'] + [f'A{i}' for i in range(15)] + [f'D{i}' for i in range(8)], [f'Q{i}' for i in range(8)], desc)
        self.mem = bytearray(32768)
    def load(self, data):
        for i, b in enumerate(data):
            if i < len(self.mem): self.mem[i] = b
    def eval(self):
        ce, oe, we = self.read('~CE'), self.read('~OE'), self.read('~WE')
        addr = sum((self.read(f'A{i}') << i) for i in range(15))
        if ce == 0 and we == 0:
            val = sum((self.read(f'D{i}') << i) for i in range(8))
            self.mem[addr] = val
        if ce == 0 and oe == 0 and we == 1:
            val = self.mem[addr]
            for i in range(8): self.write(f'Q{i}', (val >> i) & 1)
        else:
            for i in range(8): self.write(f'Q{i}', 'Z')

class IC_62256(IC_28C256):
    part_name = "62256"
    def __init__(self, ref, desc="32KB SRAM"): super().__init__(ref, desc)

class GAL_ALU(Chip):
    part_name = "GAL22V10"
    def __init__(self, ref, desc="ALU PLD"):
        super().__init__(ref, 
            ['A0','A1','A2','A3','A4','A5','A6','A7', 'B0','B1','B2','B3','B4','B5','B6','B7', 'OP0','OP1','OP2', '~OE'], 
            ['Q0','Q1','Q2','Q3','Q4','Q5','Q6','Q7','Z','C','N'], desc)
    def eval(self):
        a = sum((self.read(f'A{i}') << i) for i in range(8))
        b = sum((self.read(f'B{i}') << i) for i in range(8))
        op = sum((self.read(f'OP{i}') << i) for i in range(3))
        res, carry = 0, 0
        if op == 0: res = a + b; carry = 1 if res > 255 else 0
        elif op == 1: res = a - b; carry = 1 if res < 0 else 0
        elif op == 2: res = a & b
        elif op == 3: res = a | b
        elif op == 4: res = a ^ b
        elif op == 5: res = ~a & 0xFF
        elif op == 6: carry = (a >> 7) & 1; res = (a << 1) & 0xFF
        elif op == 7: carry = a & 1; res = (a >> 1) & 0xFF
        res &= 0xFF
        self.write('Z', 1 if res == 0 else 0)
        self.write('C', carry)
        self.write('N', (res >> 7) & 1)
        if self.read('~OE') == 0:
            for i in range(8): self.write(f'Q{i}', (res >> i) & 1)
        else:
            for i in range(8): self.write(f'Q{i}', 'Z')

# --- CPU Builder ---

def build_cpu():
    sys = System()
    
    # Global Nets
    sys.net("CLK", pull=0)
    sys.net("~RESET", pull=1)
    
    # Create dedicated VCC and GND nets that are strictly tied
    sys.net("GND", pull=0).drivers.append(lambda: 0)
    sys.net("VCC", pull=1).drivers.append(lambda: 1)
    
    data_bus = sys.bus("DATA", 8, pull=0)
    addr_bus = sys.bus("ADDR", 16, pull=0)
    
    # Micro-Sequencer
    uip = sys.add(IC_74HC161("U2", "uIP Counter"))
    sys.wire(uip, "CLK", sys.net("~CLK")) # Clock on falling edge to avoid IR/ROM race condition
    sys.wire(uip, "~CLR", sys.net("~uIP_CLR"))
    sys.wire(uip, "ENT", sys.net("VCC"))
    sys.wire(uip, "ENP", sys.net("VCC"))
    sys.wire(uip, "~LOAD", sys.net("VCC"))
    for i in ['A', 'B', 'C', 'D']: sys.wire(uip, i, sys.net("GND"))
        
    flags_reg = sys.add(IC_74HC574("U11", "Flags Register"))
    sys.wire(flags_reg, "CLK", sys.net("FLAGS_CLK"))
    sys.wire(flags_reg, "~OE", sys.net("GND"))
    sys.wire(flags_reg, "D0", sys.net("ALU_Z"))
    sys.wire(flags_reg, "D1", sys.net("ALU_C"))
    sys.wire(flags_reg, "D2", sys.net("ALU_N"))
    for i in range(3, 8): sys.wire(flags_reg, f"D{i}", sys.net("GND"))
        
    ir = sys.add(IC_74HC574("U9", "Instruction Register"))
    sys.wire(ir, "CLK", sys.net("IR_CLK"))
    sys.wire(ir, "~OE", sys.net("GND"))
    for i in range(8): sys.wire(ir, f"D{i}", data_bus[i])
        
    mc_a = sys.add(IC_28C256("U3", "Microcode EEPROM A"))
    mc_b = sys.add(IC_28C256("U4", "Microcode EEPROM B"))
    mc_c = sys.add(IC_28C256("U4b", "Microcode EEPROM C"))
    for mc in [mc_a, mc_b, mc_c]:
        sys.wire(mc, "~CE", sys.net("GND"))
        sys.wire(mc, "~OE", sys.net("GND"))
        sys.wire(mc, "~WE", sys.net("VCC"))
        for i in range(4): sys.wire(mc, f"A{i}", sys.net(f"uIP_Q{i}"))
        for i in range(3): sys.wire(mc, f"A{i+4}", sys.net(f"FLAGS_Q{i}"))
        for i in range(8): sys.wire(mc, f"A{i+7}", sys.net(f"IR_Q{i}"))
            
    for i, p in enumerate(['QA', 'QB', 'QC', 'QD']): sys.wire(uip, p, sys.net(f"uIP_Q{i}"))
    for i in range(8): sys.wire(ir, f"Q{i}", sys.net(f"IR_Q{i}"))
    for i in range(8): sys.wire(flags_reg, f"Q{i}", sys.net(f"FLAGS_Q{i}"))
        
    for i in range(8):
        sys.wire(mc_a, f"Q{i}", sys.net(f"CTRL{i}"))
        sys.wire(mc_b, f"Q{i}", sys.net(f"CTRL{i+8}"))
        sys.wire(mc_c, f"Q{i}", sys.net(f"CTRL{i+16}"))
        
    # Control Decode
    src_dec = sys.add(IC_74HC154("U5", "Bus Source Decoder"))
    sys.wire(src_dec, "~G1", sys.net("GND"))
    sys.wire(src_dec, "~G2", sys.net("GND"))
    sys.wire(src_dec, "A", sys.net("CTRL0"))
    sys.wire(src_dec, "B", sys.net("CTRL1"))
    sys.wire(src_dec, "C", sys.net("CTRL2"))
    sys.wire(src_dec, "D", sys.net("CTRL3"))
    
    inv1 = sys.add(IC_74HC04("UINV1", "Clock Inverter"))
    sys.wire(inv1, "1A", sys.net("CLK"))
    sys.wire(inv1, "1Y", sys.net("~CLK"))
    
    dst_dec = sys.add(IC_74HC154("U6", "Bus Dest Decoder"))
    sys.wire(dst_dec, "~G1", sys.net("~CLK"))
    sys.wire(dst_dec, "~G2", sys.net("GND"))
    sys.wire(dst_dec, "A", sys.net("CTRL4"))
    sys.wire(dst_dec, "B", sys.net("CTRL5"))
    sys.wire(dst_dec, "C", sys.net("CTRL6"))
    sys.wire(dst_dec, "D", sys.net("CTRL7"))
    
    def wire_dst(y_num, name):
        sys.wire(dst_dec, f"~Y{y_num}", sys.net(f"~DST_{name}"))
        inv = sys.add(IC_74HC04(f"UINV_{name}"))
        sys.wire(inv, "1A", sys.net(f"~DST_{name}"))
        sys.wire(inv, "1Y", sys.net(f"{name}_CLK"))

    # Dest map: 1:A, 2:B, 3:C, 4:D, 5:IR, 6:MEM, 7:IP_LO, 8:IP_HI, 9:SP, 10:OUT
    wire_dst(1, "A")
    wire_dst(2, "B")
    wire_dst(3, "C")
    wire_dst(4, "D")
    wire_dst(5, "IR")
    sys.wire(dst_dec, "~Y6", sys.net("~MEM_WE"))  # Level sensitive
    wire_dst(10, "OUT")
    
    dst_dec_uc = sys.add(IC_74HC154("U6B", "Unclocked Dest Decoder"))
    sys.wire(dst_dec_uc, "~G1", sys.net("GND"))
    sys.wire(dst_dec_uc, "~G2", sys.net("GND"))
    sys.wire(dst_dec_uc, "A", sys.net("CTRL4"))
    sys.wire(dst_dec_uc, "B", sys.net("CTRL5"))
    sys.wire(dst_dec_uc, "C", sys.net("CTRL6"))
    sys.wire(dst_dec_uc, "D", sys.net("CTRL7"))
    sys.wire(dst_dec_uc, "~Y7", sys.net("~UC_IP_LO"))
    sys.wire(dst_dec_uc, "~Y8", sys.net("~UC_IP_HI"))
    sys.wire(dst_dec_uc, "~Y9", sys.net("~UC_SP"))
    
    # Source map
    sys.wire(src_dec, "~Y1", sys.net("~A_OE"))
    sys.wire(src_dec, "~Y2", sys.net("~B_OE"))
    sys.wire(src_dec, "~Y3", sys.net("~C_OE"))
    sys.wire(src_dec, "~Y4", sys.net("~D_OE"))
    sys.wire(src_dec, "~Y5", sys.net("~ALU_OE"))
    sys.wire(src_dec, "~Y6", sys.net("~MEM_OE"))
    sys.wire(src_dec, "~Y7", sys.net("~IP_LO_OE"))
    sys.wire(src_dec, "~Y8", sys.net("~IP_HI_OE"))
    sys.wire(src_dec, "~Y9", sys.net("~SP_OE"))
    
    # Main Registers
    def add_reg(name, oe_net_name):
        reg = sys.add(IC_74HC574(f"U_{name}", f"{name} Register"))
        sys.wire(reg, "CLK", sys.net(f"{name}_CLK"))
        sys.wire(reg, "~OE", sys.net(oe_net_name))
        for i in range(8):
            sys.wire(reg, f"D{i}", data_bus[i])
            sys.wire(reg, f"Q{i}", data_bus[i])
            sys.net(f"{name}_Q{i}").drivers.append(lambda idx=i: (reg.val >> idx) & 1)
        return reg

    sys.reg_a = add_reg("A", "~A_OE")
    sys.reg_b = add_reg("B", "~B_OE")
    sys.reg_c = add_reg("C", "~C_OE")
    sys.reg_d = add_reg("D", "~D_OE")
    
    # ADDR Source Decode (Bits 8-9) -> 0: IP, 1: CD, 2: SP_IDX
    addr_dec = sys.add(IC_74HC138("U_ADDR_DEC", "ADDR Source Decode"))
    sys.wire(addr_dec, "A", sys.net("CTRL8"))
    sys.wire(addr_dec, "B", sys.net("CTRL9"))
    sys.wire(addr_dec, "C", sys.net("GND"))
    sys.wire(addr_dec, "~G2A", sys.net("GND"))
    sys.wire(addr_dec, "~G2B", sys.net("GND"))
    sys.wire(addr_dec, "G1", sys.net("VCC"))
    sys.wire(addr_dec, "~Y0", sys.net("~IP_ADDR_OE"))
    sys.wire(addr_dec, "~Y1", sys.net("~CD_ADDR_OE"))
    sys.wire(addr_dec, "~Y2", sys.net("~SP_ADDR_OE"))
    
    # CD -> ADDR_BUS buffers
    cd_buf_lo = sys.add(IC_74HC245("U_CD_BUF_LO", "C to ADDR_LO"))
    cd_buf_hi = sys.add(IC_74HC245("U_CD_BUF_HI", "D to ADDR_HI"))
    sys.wire(cd_buf_lo, "DIR", sys.net("VCC"))
    sys.wire(cd_buf_hi, "DIR", sys.net("VCC"))
    sys.wire(cd_buf_lo, "~OE", sys.net("~CD_ADDR_OE"))
    sys.wire(cd_buf_hi, "~OE", sys.net("~CD_ADDR_OE"))
    for i in range(8):
        sys.wire(cd_buf_lo, f"A{i}", sys.net(f"C_Q{i}"))
        sys.wire(cd_buf_lo, f"A{i}_OUT", sys.net(f"C_Q{i}")) # fake internally
        sys.wire(cd_buf_lo, f"B{i}", addr_bus[i])
        sys.wire(cd_buf_lo, f"B{i}_OUT", addr_bus[i])
        
        sys.wire(cd_buf_hi, f"A{i}", sys.net(f"D_Q{i}"))
        sys.wire(cd_buf_hi, f"A{i}_OUT", sys.net(f"D_Q{i}"))
        sys.wire(cd_buf_hi, f"B{i}", addr_bus[i+8])
        sys.wire(cd_buf_hi, f"B{i}_OUT", addr_bus[i+8])
        
    # IP
    ip = [sys.add(IC_74HC161(f"U_IP{i}")) for i in range(4)]
    sys.ip = ip
    sys.wire(ip[0], "ENT", sys.net("CTRL14"))
    sys.wire(ip[0], "ENP", sys.net("CTRL14"))
    for i in range(3):
        sys.wire(ip[i+1], "ENT", sys.net(f"IP{i}_RCO"))
        sys.wire(ip[i+1], "ENP", sys.net("CTRL14"))
        sys.wire(ip[i], "RCO", sys.net(f"IP{i}_RCO"))
    
    for i in range(4):
        sys.wire(ip[i], "CLK", sys.net("CLK"))
        sys.wire(ip[i], "~CLR", sys.net("~RESET"))
        sys.wire(ip[i], "~LOAD", sys.net("~UC_IP_LO" if i < 2 else "~UC_IP_HI"))
        for j, p in enumerate(['A', 'B', 'C', 'D']):
            sys.wire(ip[i], p, data_bus[j + (0 if i%2==0 else 4)])
        for j, p in enumerate(['QA', 'QB', 'QC', 'QD']):
            sys.net(f"IP_Q{i*4+j}").drivers.append(lambda idx=i, jdx=j: (ip[idx].val >> jdx) & 1)
            
    ip_addr_lo = sys.add(IC_74HC245("U_IP_ADDR_LO"))
    ip_addr_hi = sys.add(IC_74HC245("U_IP_ADDR_HI"))
    sys.wire(ip_addr_lo, "~OE", sys.net("~IP_ADDR_OE"))
    sys.wire(ip_addr_hi, "~OE", sys.net("~IP_ADDR_OE"))
    sys.wire(ip_addr_lo, "DIR", sys.net("VCC"))
    sys.wire(ip_addr_hi, "DIR", sys.net("VCC"))
    for i in range(8):
        sys.wire(ip_addr_lo, f"A{i}", sys.net(f"IP_Q{i}"))
        sys.wire(ip_addr_lo, f"A{i}_OUT", sys.net(f"IP_Q{i}"))
        sys.wire(ip_addr_lo, f"B{i}", addr_bus[i])
        sys.wire(ip_addr_lo, f"B{i}_OUT", addr_bus[i])
        
        sys.wire(ip_addr_hi, f"A{i}", sys.net(f"IP_Q{i+8}"))
        sys.wire(ip_addr_hi, f"A{i}_OUT", sys.net(f"IP_Q{i+8}"))
        sys.wire(ip_addr_hi, f"B{i}", addr_bus[i+8])
        sys.wire(ip_addr_hi, f"B{i}_OUT", addr_bus[i+8])
        
    ip_data_lo = sys.add(IC_74HC245("U_IP_DATA_LO"))
    ip_data_hi = sys.add(IC_74HC245("U_IP_DATA_HI"))
    sys.wire(ip_data_lo, "~OE", sys.net("~IP_LO_OE"))
    sys.wire(ip_data_hi, "~OE", sys.net("~IP_HI_OE"))
    sys.wire(ip_data_lo, "DIR", sys.net("VCC"))
    sys.wire(ip_data_hi, "DIR", sys.net("VCC"))
    for i in range(8):
        sys.wire(ip_data_lo, f"A{i}", sys.net(f"IP_Q{i}"))
        sys.wire(ip_data_lo, f"A{i}_OUT", sys.net(f"IP_Q{i}"))
        sys.wire(ip_data_lo, f"B{i}", data_bus[i])
        sys.wire(ip_data_lo, f"B{i}_OUT", data_bus[i])
        
        sys.wire(ip_data_hi, f"A{i}", sys.net(f"IP_Q{i+8}"))
        sys.wire(ip_data_hi, f"A{i}_OUT", sys.net(f"IP_Q{i+8}"))
        sys.wire(ip_data_hi, f"B{i}", data_bus[i])
        sys.wire(ip_data_hi, f"B{i}_OUT", data_bus[i])

    # SP Tracker (193 cascades)
    sp0 = sys.add(IC_74HC193("U_SP0"))
    sp1 = sys.add(IC_74HC193("U_SP1"))
    sys.sp = [sp0, sp1]
    
    # Needs to default to HIGH and pulse LOW then HIGH. We can use NAND!
    class IC_74HC00(Chip):
        part_name = "74HC00"
        def __init__(self, ref, desc="Quad NAND"):
            super().__init__(ref, ['1A','1B','2A','2B','3A','3B','4A','4B'], ['1Y','2Y','3Y','4Y'], desc)
        def eval(self):
            for i in range(1, 5): self.write(f'{i}Y', 1 - (self.read(f'{i}A') & self.read(f'{i}B')))

    nand_sp = sys.add(IC_74HC00("U_NAND_SP"))
    sys.wire(nand_sp, "1A", sys.net("CTRL15")) # SP_INC
    sys.wire(nand_sp, "1B", sys.net("CLK"))    # Pulse LOW on CLK=1, rise on CLK=0
    sys.wire(nand_sp, "1Y", sys.net("SP_UP_NAND"))
    
    sys.wire(nand_sp, "2A", sys.net("CTRL16")) # SP_DEC
    sys.wire(nand_sp, "2B", sys.net("CLK"))
    sys.wire(nand_sp, "2Y", sys.net("SP_DN_NAND"))
    
    # We want SP_UP and SP_DN to default HIGH. Wait, the NAND generates exactly this!
    sys.wire(sp0, "UP", sys.net("SP_UP_NAND"))
    sys.wire(sp0, "DOWN", sys.net("SP_DN_NAND"))
    sys.wire(sp0, "~CO", sys.net("SP0_CO"))
    sys.wire(sp0, "~BO", sys.net("SP0_BO"))
    
    # 193 cascade is direct: ~CO to UP, ~BO to DOWN
    sys.wire(sp1, "UP", sys.net("SP0_CO"))
    sys.wire(sp1, "DOWN", sys.net("SP0_BO"))
    
    for sp in [sp0, sp1]:
        sys.wire(sp, "CLR", sys.net("GND"))
        sys.wire(sp, "~LOAD", sys.net("~UC_SP"))

    for i, p in enumerate(['A', 'B', 'C', 'D']):
        sys.wire(sp0, p, data_bus[i])
        sys.wire(sp1, p, data_bus[i+4])
        
    for i, p in enumerate(['QA', 'QB', 'QC', 'QD']):
        sys.net(f"SP_Q{i}").drivers.append(lambda idx=i: (sp0.val >> idx) & 1)
        sys.net(f"SP_Q{i+4}").drivers.append(lambda idx=i: (sp1.val >> idx) & 1)
        
    sp_data = sys.add(IC_74HC245("U_SP_DATA"))
    sys.wire(sp_data, "~OE", sys.net("~SP_OE"))
    sys.wire(sp_data, "DIR", sys.net("VCC"))
    for i in range(8):
        sys.wire(sp_data, f"A{i}", sys.net(f"SP_Q{i}"))
        sys.wire(sp_data, f"A{i}_OUT", sys.net(f"SP_Q{i}"))
        sys.wire(sp_data, f"B{i}", data_bus[i])
        sys.wire(sp_data, f"B{i}_OUT", data_bus[i])
        
    add1 = sys.add(IC_74HC283("U_ADD1"))
    add2 = sys.add(IC_74HC283("U_ADD2"))
    sys.wire(add1, "C0", sys.net("GND"))
    sys.wire(add1, "C4", sys.net("ADD1_C4"))
    sys.wire(add2, "C0", sys.net("ADD1_C4"))
    
    for i in range(4):
        sys.wire(add1, f"A{i+1}", sys.net(f"SP_Q{i}"))
        sys.wire(add1, f"B{i+1}", sys.net(f"IR_Q{i}"))
        sys.wire(add2, f"A{i+1}", sys.net(f"SP_Q{i+4}"))
        sys.wire(add2, f"B{i+1}", sys.net("GND"))
        
    sp_addr_lo = sys.add(IC_74HC245("U_SP_ADDR_LO"))
    sp_addr_hi = sys.add(IC_74HC245("U_SP_ADDR_HI"))
    sys.wire(sp_addr_lo, "~OE", sys.net("~SP_ADDR_OE"))
    sys.wire(sp_addr_lo, "DIR", sys.net("VCC"))
    sys.wire(sp_addr_hi, "~OE", sys.net("~SP_ADDR_OE"))
    sys.wire(sp_addr_hi, "DIR", sys.net("VCC"))
    for i in range(4):
        sys.wire(sp_addr_lo, f"A{i}", sys.net(f"U_ADD1.S{i+1}"))
        sys.net(f"U_ADD1.S{i+1}").drivers.append(lambda idx=i: add1.out_states[f'S{idx+1}'])
        sys.wire(sp_addr_lo, f"A{i}_OUT", sys.net(f"U_ADD1.S{i+1}"))
        sys.wire(sp_addr_lo, f"B{i}", addr_bus[i])
        sys.wire(sp_addr_lo, f"B{i}_OUT", addr_bus[i])
        
        sys.wire(sp_addr_lo, f"A{i+4}", sys.net(f"U_ADD2.S{i+1}"))
        sys.net(f"U_ADD2.S{i+1}").drivers.append(lambda idx=i: add2.out_states[f'S{idx+1}'])
        sys.wire(sp_addr_lo, f"A{i+4}_OUT", sys.net(f"U_ADD2.S{i+1}"))
        sys.wire(sp_addr_lo, f"B{i+4}", addr_bus[i+4])
        sys.wire(sp_addr_lo, f"B{i+4}_OUT", addr_bus[i+4])
        
        sys.wire(sp_addr_hi, f"A{i}", sys.net("VCC"))
        sys.wire(sp_addr_hi, f"A{i}_OUT", sys.net("VCC"))
        sys.wire(sp_addr_hi, f"B{i}", addr_bus[i+8])
        sys.wire(sp_addr_hi, f"B{i}_OUT", addr_bus[i+8])
        sys.wire(sp_addr_hi, f"A{i+4}", sys.net("VCC"))
        sys.wire(sp_addr_hi, f"A{i+4}_OUT", sys.net("VCC"))
        sys.wire(sp_addr_hi, f"B{i+4}", addr_bus[i+12])
        sys.wire(sp_addr_hi, f"B{i+4}_OUT", addr_bus[i+12])

    alu = sys.add(GAL_ALU("U_ALU"))
    sys.wire(alu, "~OE", sys.net("~ALU_OE"))
    for i in range(8):
        sys.wire(alu, f"A{i}", sys.net(f"A_Q{i}"))
        sys.wire(alu, f"B{i}", sys.net(f"B_Q{i}"))
        sys.wire(alu, f"Q{i}", data_bus[i])
        
    sys.wire(alu, "OP0", sys.net("CTRL10"))
    sys.wire(alu, "OP1", sys.net("CTRL11"))
    sys.wire(alu, "OP2", sys.net("CTRL12"))
    
    and_flg = sys.add(IC_74HC08("U_AND_FLG"))
    sys.wire(and_flg, "4A", sys.net("CTRL13"))
    sys.wire(and_flg, "4B", sys.net("CLK"))
    sys.wire(and_flg, "4Y", sys.net("FLAGS_CLK"))
    
    # Combine ~RESET and ~uIP_RST to clear uIP
    sys.wire(and_flg, "1A", sys.net("~RESET"))
    sys.wire(and_flg, "1B", sys.net("~uIP_RST"))
    sys.wire(and_flg, "1Y", sys.net("~uIP_CLR"))
    
    sys.wire(alu, "Z", sys.net("ALU_Z"))
    sys.wire(alu, "C", sys.net("ALU_C"))
    sys.wire(alu, "N", sys.net("ALU_N"))
    sys.net("ALU_Z").drivers.append(lambda: alu.out_states.get('Z', 0))
    sys.net("ALU_C").drivers.append(lambda: alu.out_states.get('C', 0))
    sys.net("ALU_N").drivers.append(lambda: alu.out_states.get('N', 0))
    
    rom = sys.add(IC_28C256("U_ROM"))
    ram = sys.add(IC_62256("U_RAM"))
    
    inv_a15 = sys.add(IC_74HC04("U_INV_A15"))
    sys.wire(inv_a15, "4A", addr_bus[15])
    sys.wire(inv_a15, "4Y", sys.net("~A15"))
    
    # ROM is mapped to 0x0000-0x7FFF (A15 = 0)
    # So ROM ~CE is tied to A15 directly.
    sys.wire(rom, "~CE", addr_bus[15])
    
    # RAM is mapped to 0x8000-0xFFFF (A15 = 1)
    # So RAM ~CE is tied to ~A15.
    sys.wire(ram, "~CE", sys.net("~A15"))
    
    sys.wire(rom, "~OE", sys.net("~MEM_OE"))
    sys.wire(ram, "~OE", sys.net("~MEM_OE"))
    sys.wire(rom, "~WE", sys.net("VCC"))
    sys.wire(ram, "~WE", sys.net("~MEM_WE"))
    
    for mem in [rom, ram]:
        for i in range(15): sys.wire(mem, f"A{i}", addr_bus[i])
        for i in range(8):
            sys.wire(mem, f"D{i}", data_bus[i])
            sys.wire(mem, f"Q{i}", data_bus[i])
            
    inv_rst = sys.add(IC_74HC04("U_INV_RST"))
    sys.wire(inv_rst, "5A", sys.net("CTRL17"))
    sys.wire(inv_rst, "5Y", sys.net("~uIP_RST"))
    
    # HLT Logic - CTRL18
    # Not purely hardware, handled by sim
    sys.hlt_net = sys.net("CTRL18")

    sys.rom_chip = rom
    sys.ram_chip = ram
    sys.mc_a = mc_a
    sys.mc_b = mc_b
    sys.mc_c = mc_c
    sys.ir = ir
    
    return sys

def dump_state(sys_obj):
    A = sys_obj.reg_a.val
    B = sys_obj.reg_b.val
    C = sys_obj.reg_c.val
    D = sys_obj.reg_d.val
    ip_vals = [i.val for i in sys_obj.ip]
    IP = (ip_vals[3] << 12) | (ip_vals[2] << 8) | (ip_vals[1] << 4) | ip_vals[0]
    SP = (sys_obj.sp[1].val << 4) | sys_obj.sp[0].val
    
    freg = sys_obj.chips[1] # U11
    flags = f"{'Z' if freg.val & 1 else '.'}{'C' if freg.val & 2 else '.'}{'N' if freg.val & 4 else '.'}"
    
    ctrl = 0
    for i in range(24):
        if sys_obj.net(f"CTRL{i}").state: ctrl |= (1 << i)

    ds = ctrl & 0x0F
    dd = (ctrl >> 4) & 0x0F
    
    print(f"IP={IP:04X} SP={SP:02X} A={A:02X} B={B:02X} C={C:02X} D={D:02X} [{flags}] CW={ctrl:06X}")

def emit_wiring(sys):
    with open("docs/wiring.md", "w") as f:
        f.write("# Auto-generated Wiring Guide\n\n")
        
        # Group by chip
        for chip in sys.chips:
            f.write(f"## {chip.ref} ({chip.part_name}) - {chip.desc}\n")
            f.write("| Pin Name | Connects to Net |\n")
            f.write("|---|---|\n")
            for pin in chip.inputs + chip.outputs:
                if pin in chip.connections:
                    f.write(f"| {pin} | {chip.connections[pin].name} |\n")
            f.write("\n")
            
def emit_bom(sys):
    with open("docs/bom.md", "w") as f:
        f.write("# Auto-generated Bill of Materials\n\n")
        f.write("| Part | Quantity |\n")
        f.write("|---|---|\n")
        
        counts = {}
        for chip in sys.chips:
            counts[chip.part_name] = counts.get(chip.part_name, 0) + 1
            
        for part, qty in sorted(counts.items()):
            f.write(f"| {part} | {qty} |\n")

def run_sim(sys_obj, max_cycles=5000):
    print("Resetting CPU...")
    if not hasattr(sys_obj, 'reset_val'):
        sys_obj.reset_val = 1
        sys_obj.net("~RESET").drivers.append(lambda: sys_obj.reset_val)
        
    sys_obj.reset_val = 0
    sys_obj.tick()
    sys_obj.reset_val = 1

    
    print("Running...")
    cycles = 0
    while cycles < max_cycles:
        # Check HLT before tick
        if sys_obj.hlt_net.state == 1:
            print(f"Halted after {cycles} clock cycles.")
            dump_state(sys_obj)
            return
            
        sys_obj.tick()
        cycles += 1
            
        # Optional: Print trace on instruction boundary (uIP == 0)
        uip_val = sum((sys_obj.net(f"uIP_Q{i}").state << i) for i in range(4))
        if uip_val == 0: dump_state(sys_obj)
        
    print(f"\n--- TIMEOUT: Reached {max_cycles} cycles without HALT ---")
    dump_state(sys_obj)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "emit":
        cpu = build_cpu()
        emit_wiring(cpu)
        emit_bom(cpu)
        cpu.emit_human_readable("docs/hardware_dump.md")
        print("Generated structural docs.")
    elif len(sys.argv) > 1:
        # Load binary
        with open(sys.argv[1], "rb") as f:
            prog = f.read()
            
        with open("microcode_a.bin", "rb") as f: mc_a = f.read()
        with open("microcode_b.bin", "rb") as f: mc_b = f.read()
        with open("microcode_c.bin", "rb") as f: mc_c = f.read()
            
        cpu = build_cpu()
        cpu.load_rom(prog)
        cpu.load_microcode(mc_a, mc_b, mc_c)
        run_sim(cpu)
    else:
        print("Usage: python hardware.py emit")
        print("       python hardware.py program.bin")
