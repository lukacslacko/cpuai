import hardware

cpu = hardware.build_cpu()
with open('examples/multiply.bin', 'rb') as f: prog = f.read()
for i, b in enumerate(prog): cpu.ram_chip.mem[i] = b

print('Resetting CPU...')
cpu.reset_val = 1
cpu.net('~RESET').drivers.append(lambda: cpu.reset_val)
cpu.reset_val = 0
cpu.tick()
cpu.reset_val = 1
cpu.eval_combinational()

print('Tracing execution...')
for cycle in range(2000):
   uip = sum((cpu.net(f"uIP_Q{i}").state << i) for i in range(4))
   if uip == 0:
      ip_vals = [i.val for i in cpu.ip]
      ip = (ip_vals[3] << 12) | (ip_vals[2] << 8) | (ip_vals[1] << 4) | ip_vals[0]
      cw = hex(cpu.get_bus_val([cpu.net(f'CTRL{i}') for i in range(24)]))
      print(f'cyc={cycle:04d} IP={ip:04X} SP={cpu.sp[0].val | (cpu.sp[1].val << 4):02X} A={cpu.reg_a.val:02X} B={cpu.reg_b.val:02X} C={cpu.reg_c.val:02X} D={cpu.reg_d.val:02X}')
   
   cpu.tick()
   if cpu.hlt_net.state == 1:
      print("HALT")
      break
