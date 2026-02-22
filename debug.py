import hardware
import microcode
import subprocess, sys

microcode.generate_microcode()

# Compile fibonacci.mc -> fibonacci_hl.asm
result = subprocess.run(
    [r'C:\Users\lukac\AppData\Local\Programs\Python\Python312\python.exe',
     'compiler.py', 'examples/fibonacci.mc', '-o', 'examples/fibonacci_hl.asm'],
    stdout=subprocess.PIPE, text=True, cwd=r'c:\Users\lukac\Documents\git\cpuai'
)
print("=== COMPILER ===")
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.returncode != 0:
    sys.exit(1)

# Assemble
result = subprocess.run(
    [r'C:\Users\lukac\AppData\Local\Programs\Python\Python312\python.exe',
     'assembler.py', 'examples/fibonacci_hl.asm', '-o', 'examples/fibonacci_hl.bin', '--listing'],
    stdout=subprocess.PIPE, text=True, cwd=r'c:\Users\lukac\Documents\git\cpuai'
)
print("=== ASSEMBLER ===")
print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
if result.returncode != 0:
    sys.exit(1)

with open('examples/fibonacci_hl.bin', 'rb') as f:
    prog = f.read()
with open('microcode_a.bin', 'rb') as f: mc_a = f.read()
with open('microcode_b.bin', 'rb') as f: mc_b = f.read()
with open('microcode_c.bin', 'rb') as f: mc_c = f.read()

cpu = hardware.build_cpu()
cpu.load_rom(prog)
cpu.load_microcode(mc_a, mc_b, mc_c)
hardware.run_sim(cpu, max_cycles=50000)
