import { describe, it, expect } from "vitest";
import { IC28C64 } from "../../src/circuit/components/IC28C64.js";
import { IC28C256 } from "../../src/circuit/components/IC28C256.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

// ── helpers ──────────────────────────────────────────────────────────────────

function make28C64(romData?: Uint8Array): { ic: IC28C64; circuit: Circuit } {
  const ic = new IC28C64("rom", romData);
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function make28C256(romData?: Uint8Array): { ic: IC28C256; circuit: Circuit } {
  const ic = new IC28C256("rom", romData);
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function setAddr(a: (typeof IC28C64.prototype.a), addr: number): void {
  for (let i = 0; i < a.length; i++) {
    a[i]!.net!.drive("test:a", (addr >> i) & 1 ? NetState.HIGH : NetState.LOW);
  }
}

function readDataByte(d: (typeof IC28C64.prototype.d)): number {
  let byte = 0;
  for (let i = 0; i < 8; i++) {
    if (d[i]!.resolvedState === NetState.HIGH) byte |= 1 << i;
  }
  return byte;
}

// ── 28C64 (8KB EEPROM / ROM) ─────────────────────────────────────────────────

describe("IC28C64 (8KB EEPROM as ROM)", () => {
  it("has 28 pins in DIP order", () => {
    const { ic } = make28C64();
    expect(ic.pins.length).toBe(28);
    expect(ic.pins[0]!.name).toBe("NC");   // pin 1
    expect(ic.pins[13]!.name).toBe("GND"); // pin 14
    expect(ic.pins[19]!.name).toBe("!CE"); // pin 20
    expect(ic.pins[21]!.name).toBe("!OE"); // pin 22
    expect(ic.pins[25]!.name).toBe("NC");  // pin 26
    expect(ic.pins[26]!.name).toBe("!WE"); // pin 27
    expect(ic.pins[27]!.name).toBe("VCC"); // pin 28
  });

  it("outputs ROM data when enabled", () => {
    const rom = new Uint8Array(8192);
    rom[0] = 0xEA; rom[1] = 0x4C; rom[8191] = 0xFF;
    const { ic } = make28C64(rom);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);

    setAddr(ic.a, 0);    ic.evaluate(); expect(readDataByte(ic.d)).toBe(0xEA);
    setAddr(ic.a, 1);    ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x4C);
    setAddr(ic.a, 8191); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0xFF);
  });

  it("tri-states D bus when !CE=HIGH", () => {
    const rom = new Uint8Array(8192).fill(0xAA);
    const { ic } = make28C64(rom);

    ic.ce.net!.drive("test:ce", NetState.HIGH); // disabled
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("tri-states D bus when !OE=HIGH", () => {
    const rom = new Uint8Array(8192).fill(0xAA);
    const { ic } = make28C64(rom);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH); // output disabled
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("ignores write: !WE=LOW does not alter ROM data", () => {
    const rom = new Uint8Array(8192);
    rom[5] = 0x42;
    const { ic } = make28C64(rom);

    // Attempt write (should be silently ignored)
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH);
    ic.we.net!.drive("test:we", NetState.LOW); // write strobe
    // drive data pins externally
    for (let i = 0; i < 8; i++) ic.d[i]!.net!.drive("test:d", NetState.HIGH);
    setAddr(ic.a, 5); ic.evaluate();

    // Switch to read — data should still be 0x42
    for (let i = 0; i < 8; i++) ic.d[i]!.net!.unDrive("test:d");
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0x42);
  });

  it("defaults to 0x00 at uninitialised addresses", () => {
    const { ic } = make28C64();
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 200); ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0x00);
  });

  it("outputs all 8 bits correctly for 0xFF", () => {
    const rom = new Uint8Array(8192);
    rom[10] = 0xFF;
    const { ic } = make28C64(rom);
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 10); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.HIGH);
  });

  it("outputs all 8 bits correctly for 0x00", () => {
    const { ic } = make28C64();
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.LOW);
  });
});

// ── 28C256 (32KB EEPROM / ROM) ───────────────────────────────────────────────

describe("IC28C256 (32KB EEPROM as ROM)", () => {
  it("has 28 pins in DIP order", () => {
    const { ic } = make28C256();
    expect(ic.pins.length).toBe(28);
    expect(ic.pins[0]!.name).toBe("A14");  // pin 1
    expect(ic.pins[1]!.name).toBe("A12");  // pin 2
    expect(ic.pins[13]!.name).toBe("GND"); // pin 14
    expect(ic.pins[19]!.name).toBe("!CE"); // pin 20
    expect(ic.pins[21]!.name).toBe("!OE"); // pin 22
    expect(ic.pins[25]!.name).toBe("A13"); // pin 26
    expect(ic.pins[27]!.name).toBe("VCC"); // pin 28
  });

  it("a[] has 15 address pins A0-A14", () => {
    const { ic } = make28C256();
    expect(ic.a.length).toBe(15);
    expect(ic.a[0]!.name).toBe("A0");
    expect(ic.a[14]!.name).toBe("A14");
  });

  it("outputs ROM data at low address", () => {
    const rom = new Uint8Array(32768);
    rom[0] = 0x01; rom[1] = 0x02;
    const { ic } = make28C256(rom);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);

    setAddr(ic.a, 0); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x01);
    setAddr(ic.a, 1); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x02);
  });

  it("outputs ROM data at high address (A14=1)", () => {
    const rom = new Uint8Array(32768);
    rom[32767] = 0xAB;
    const { ic } = make28C256(rom);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);

    setAddr(ic.a, 32767); ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0xAB);
  });

  it("tri-states when not selected or output disabled", () => {
    const rom = new Uint8Array(32768).fill(0xFF);
    const { ic } = make28C256(rom);

    ic.ce.net!.drive("test:ce", NetState.HIGH); // disabled
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH); // OE off
    ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("ignores write: ROM data is unchanged after !WE pulse", () => {
    const rom = new Uint8Array(32768);
    rom[100] = 0x55;
    const { ic } = make28C256(rom);

    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH);
    ic.we.net!.drive("test:we", NetState.LOW);
    for (let i = 0; i < 8; i++) ic.d[i]!.net!.drive("test:d", NetState.HIGH);
    setAddr(ic.a, 100); ic.evaluate();

    for (let i = 0; i < 8; i++) ic.d[i]!.net!.unDrive("test:d");
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0x55);
  });
});
