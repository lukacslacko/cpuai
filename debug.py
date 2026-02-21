with open('examples/multiply.bin', 'rb') as f:
    prog = f.read()

for i in range(0, len(prog), 16):
    chunk = prog[i:i+16]
    hex_str = ' '.join(f'{b:02X}' for b in chunk)
    print(f'{i:04X}: {hex_str}')
