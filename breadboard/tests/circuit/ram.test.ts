import { describe, it, expect } from "vitest";
import { IC6264 } from "../../src/circuit/components/IC6264.js";
import { IC62256 } from "../../src/circuit/components/IC62256.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

// ── helpers ──────────────────────────────────────────────────────────────────

function make6264(): { ic: IC6264; circuit: Circuit } {
  const ic = new IC6264();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function make62256(): { ic: IC62256; circuit: Circuit } {
  const ic = new IC62256();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function setAddr(a: (typeof IC6264.prototype.a), addr: number): void {
  for (let i = 0; i < a.length; i++) {
    a[i]!.net!.drive("test:a", (addr >> i) & 1 ? NetState.HIGH : NetState.LOW);
  }
}

function setData(d: (typeof IC6264.prototype.d), byte: number): void {
  for (let i = 0; i < 8; i++) {
    d[i]!.net!.drive("test:d", (byte >> i) & 1 ? NetState.HIGH : NetState.LOW);
  }
}

function clearDataDrive(d: (typeof IC6264.prototype.d)): void {
  for (let i = 0; i < 8; i++) d[i]!.net!.unDrive("test:d");
}

function readDataByte(d: (typeof IC6264.prototype.d)): number {
  let byte = 0;
  for (let i = 0; i < 8; i++) {
    if (d[i]!.resolvedState === NetState.HIGH) byte |= 1 << i;
  }
  return byte;
}

// ── 6264 (8KB SRAM) ──────────────────────────────────────────────────────────

describe("IC6264 (8KB SRAM)", () => {
  it("has 28 pins in DIP order", () => {
    const { ic } = make6264();
    expect(ic.pins.length).toBe(28);
    expect(ic.pins[0]!.name).toBe("NC");
    expect(ic.pins[13]!.name).toBe("GND");
    expect(ic.pins[19]!.name).toBe("!CE");
    expect(ic.pins[21]!.name).toBe("!OE");
    expect(ic.pins[25]!.name).toBe("CE2");
    expect(ic.pins[26]!.name).toBe("!WE");
    expect(ic.pins[27]!.name).toBe("VCC");
  });

  it("tri-states D bus when not selected", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.HIGH); // disabled
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.we.net!.drive("test:we",   NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("tri-states D bus when CE2=LOW", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.LOW);  // disabled (active HIGH)
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.we.net!.drive("test:we",   NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("writes then reads back a byte", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.HIGH); // OE off during write
    ic.we.net!.drive("test:we",   NetState.LOW);  // write enabled
    setAddr(ic.a, 42);
    setData(ic.d, 0xA5);
    ic.evaluate(); // write 0xA5 to address 42

    // Switch to read mode
    clearDataDrive(ic.d);
    ic.we.net!.drive("test:we",   NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.evaluate();

    expect(readDataByte(ic.d)).toBe(0xA5);
  });

  it("D bus is tri-stated during write (outputs disabled)", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.we.net!.drive("test:we",   NetState.LOW);  // write mode
    setAddr(ic.a, 0);
    setData(ic.d, 0xFF);
    ic.evaluate();
    // Chip should not be driving D during write — check no chip drive
    // (external driver supplies the value, chip tri-states)
    // After writing, D resolves to what external driver supplies (0xFF)
    expect(readDataByte(ic.d)).toBe(0xFF); // external drive visible
  });

  it("reads all-zero from unwritten memory", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.we.net!.drive("test:we",   NetState.HIGH);
    setAddr(ic.a, 100); ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0x00);
  });

  it("writes to multiple addresses independently", () => {
    const { ic } = make6264();
    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.HIGH);
    ic.we.net!.drive("test:we",   NetState.LOW);

    setAddr(ic.a, 0);    setData(ic.d, 0x11); ic.evaluate();
    setAddr(ic.a, 1);    setData(ic.d, 0x22); ic.evaluate();
    setAddr(ic.a, 8191); setData(ic.d, 0xFF); ic.evaluate();

    clearDataDrive(ic.d);
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);

    setAddr(ic.a, 0);    ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x11);
    setAddr(ic.a, 1);    ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x22);
    setAddr(ic.a, 8191); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0xFF);
  });

  it("initialData constructor parameter pre-loads memory", () => {
    const init = new Uint8Array(8192);
    init[0] = 0xDE; init[1] = 0xAD;
    const ic = new IC6264("ram", init);
    const circuit = new Circuit();
    circuit.addComponent(ic);
    for (const pin of ic.pins) circuit.connect(pin);

    ic.ce.net!.drive("test:ce",   NetState.LOW);
    ic.ce2.net!.drive("test:ce2", NetState.HIGH);
    ic.oe.net!.drive("test:oe",   NetState.LOW);
    ic.we.net!.drive("test:we",   NetState.HIGH);

    setAddr(ic.a, 0); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0xDE);
    setAddr(ic.a, 1); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0xAD);
  });
});

// ── 62256 (32KB SRAM) ────────────────────────────────────────────────────────

describe("IC62256 (32KB SRAM)", () => {
  it("has 28 pins in DIP order", () => {
    const { ic } = make62256();
    expect(ic.pins.length).toBe(28);
    expect(ic.pins[0]!.name).toBe("A14");
    expect(ic.pins[13]!.name).toBe("GND");
    expect(ic.pins[19]!.name).toBe("!CE");
    expect(ic.pins[21]!.name).toBe("!OE");
    expect(ic.pins[26]!.name).toBe("!WE");
    expect(ic.pins[27]!.name).toBe("VCC");
  });

  it("a[] has 15 address pins", () => {
    const { ic } = make62256();
    expect(ic.a.length).toBe(15);
    expect(ic.a[0]!.name).toBe("A0");
    expect(ic.a[14]!.name).toBe("A14");
  });

  it("writes then reads back at address 0", () => {
    const { ic } = make62256();
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH);
    ic.we.net!.drive("test:we", NetState.LOW);
    setAddr(ic.a, 0);
    setData(ic.d, 0xBE);
    ic.evaluate();

    clearDataDrive(ic.d);
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0xBE);
  });

  it("writes and reads at high address (A14=1, addr=32767)", () => {
    const { ic } = make62256();
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH);
    ic.we.net!.drive("test:we", NetState.LOW);
    setAddr(ic.a, 32767);
    setData(ic.d, 0x7F);
    ic.evaluate();

    clearDataDrive(ic.d);
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.evaluate();
    expect(readDataByte(ic.d)).toBe(0x7F);
  });

  it("tri-states D bus when !CE=HIGH", () => {
    const { ic } = make62256();
    ic.ce.net!.drive("test:ce", NetState.HIGH); // disabled
    ic.oe.net!.drive("test:oe", NetState.LOW);
    ic.we.net!.drive("test:we", NetState.HIGH);
    setAddr(ic.a, 0); ic.evaluate();
    for (const d of ic.d) expect(d.resolvedState).toBe(NetState.FLOAT);
  });

  it("different addresses store independent data", () => {
    const { ic } = make62256();
    ic.ce.net!.drive("test:ce", NetState.LOW);
    ic.oe.net!.drive("test:oe", NetState.HIGH);
    ic.we.net!.drive("test:we", NetState.LOW);

    setAddr(ic.a, 0x0000); setData(ic.d, 0x11); ic.evaluate();
    setAddr(ic.a, 0x4000); setData(ic.d, 0x22); ic.evaluate();
    setAddr(ic.a, 0x7FFF); setData(ic.d, 0x33); ic.evaluate();

    clearDataDrive(ic.d);
    ic.we.net!.drive("test:we", NetState.HIGH);
    ic.oe.net!.drive("test:oe", NetState.LOW);

    setAddr(ic.a, 0x0000); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x11);
    setAddr(ic.a, 0x4000); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x22);
    setAddr(ic.a, 0x7FFF); ic.evaluate(); expect(readDataByte(ic.d)).toBe(0x33);
  });
});
