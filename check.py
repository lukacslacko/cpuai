import hardware

cpu = hardware.build_cpu()
print('Testing destination 1 (A)')
cpu.net('CTRL4').next_state = 1
cpu.net('CTRL5').next_state = 0
cpu.net('CTRL6').next_state = 0
cpu.net('CTRL7').next_state = 0

# Set these up first
for n in ['CTRL4','CTRL5','CTRL6','CTRL7']: 
    cpu.net(n).apply()

# Make CLK=0
cpu.net('CLK').next_state = 0
cpu.net('CLK').apply()
cpu.eval_combinational()

print('~CLK=1 (CLK=0) -> A_CLK=', cpu.net('A_CLK').state, ' IR_CLK=', cpu.net('IR_CLK').state, '~DST_A=', cpu.net('~DST_A').state, '~DST_IR=', cpu.net('~DST_IR').state)

# Make CLK=1
cpu.net('CLK').next_state = 1
cpu.net('CLK').apply()
cpu.eval_combinational()

print('~CLK=0 (CLK=1) -> A_CLK=', cpu.net('A_CLK').state, ' IR_CLK=', cpu.net('IR_CLK').state, '~DST_A=', cpu.net('~DST_A').state, '~DST_IR=', cpu.net('~DST_IR').state)

