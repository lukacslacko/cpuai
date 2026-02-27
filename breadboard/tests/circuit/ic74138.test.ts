import { describe, it, expect } from "vitest";
import { IC74138 } from "../../src/circuit/components/IC74138.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

function makeIC(): { ic: IC74138; circuit: Circuit } {
  const ic = new IC74138();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function setAddr(ic: IC74138, addr: number): void {
  ic.a.net!.drive("test:a", addr & 1 ? NetState.HIGH : NetState.LOW);
  ic.b.net!.drive("test:b", addr & 2 ? NetState.HIGH : NetState.LOW);
  ic.c.net!.drive("test:c", addr & 4 ? NetState.HIGH : NetState.LOW);
}

function enable(ic: IC74138): void {
  ic.g1.net!.drive("test:g1",   NetState.HIGH);
  ic.g2a.net!.drive("test:g2a", NetState.LOW);
  ic.g2b.net!.drive("test:g2b", NetState.LOW);
}

function disable(ic: IC74138): void {
  ic.g1.net!.drive("test:g1",   NetState.LOW);
}

describe("IC74138", () => {
  it("has 16 pins in DIP order", () => {
    const { ic } = makeIC();
    expect(ic.pins.length).toBe(16);
    expect(ic.pins[0]!.name).toBe("A");
    expect(ic.pins[3]!.name).toBe("G2A");
    expect(ic.pins[4]!.name).toBe("G2B");
    expect(ic.pins[5]!.name).toBe("G1");
    expect(ic.pins[6]!.name).toBe("Y7");
    expect(ic.pins[7]!.name).toBe("GND");
    expect(ic.pins[14]!.name).toBe("Y0");
    expect(ic.pins[15]!.name).toBe("VCC");
  });

  it("selects Y0 when addr=0 and enabled", () => {
    const { ic } = makeIC();
    enable(ic); setAddr(ic, 0); ic.evaluate();
    expect(ic.y[0]!.resolvedState).toBe(NetState.LOW);
    for (let i = 1; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("selects Y7 when addr=7 and enabled", () => {
    const { ic } = makeIC();
    enable(ic); setAddr(ic, 7); ic.evaluate();
    expect(ic.y[7]!.resolvedState).toBe(NetState.LOW);
    for (let i = 0; i < 7; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("decodes all 8 addresses correctly", () => {
    const { ic } = makeIC();
    enable(ic);
    for (let addr = 0; addr < 8; addr++) {
      setAddr(ic, addr); ic.evaluate();
      for (let i = 0; i < 8; i++) {
        const expected = i === addr ? NetState.LOW : NetState.HIGH;
        expect(ic.y[i]!.resolvedState).toBe(expected);
      }
    }
  });

  it("all outputs HIGH when G1=LOW (disabled)", () => {
    const { ic } = makeIC();
    enable(ic); setAddr(ic, 3); ic.evaluate();
    disable(ic); ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("all outputs HIGH when G2A=HIGH (disabled)", () => {
    const { ic } = makeIC();
    ic.g1.net!.drive("test:g1",   NetState.HIGH);
    ic.g2a.net!.drive("test:g2a", NetState.HIGH); // disabled
    ic.g2b.net!.drive("test:g2b", NetState.LOW);
    setAddr(ic, 5); ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("all outputs HIGH when G2B=HIGH (disabled)", () => {
    const { ic } = makeIC();
    ic.g1.net!.drive("test:g1",   NetState.HIGH);
    ic.g2a.net!.drive("test:g2a", NetState.LOW);
    ic.g2b.net!.drive("test:g2b", NetState.HIGH); // disabled
    setAddr(ic, 5); ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("y array is indexed logically (y[0]=Y0 at pin 15)", () => {
    const { ic } = makeIC();
    expect(ic.y[0]!.name).toBe("Y0");
    expect(ic.y[7]!.name).toBe("Y7");
    expect(ic.pins[14]!.name).toBe("Y0"); // physical pin 15
    expect(ic.pins[6]!.name).toBe("Y7");  // physical pin 7
  });
});
