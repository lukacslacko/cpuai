import { describe, it, expect } from "vitest";
import { IC74137 } from "../../src/circuit/components/IC74137.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

function makeIC(): { ic: IC74137; circuit: Circuit } {
  const ic = new IC74137();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

function setAddr(ic: IC74137, addr: number): void {
  ic.a.net!.drive("test:a", addr & 1 ? NetState.HIGH : NetState.LOW);
  ic.b.net!.drive("test:b", addr & 2 ? NetState.HIGH : NetState.LOW);
  ic.c.net!.drive("test:c", addr & 4 ? NetState.HIGH : NetState.LOW);
}

function enable(ic: IC74137): void {
  ic.g1.net!.drive("test:g1", NetState.HIGH);
  ic.g2.net!.drive("test:g2", NetState.LOW);
}

describe("IC74137", () => {
  it("has 16 pins in DIP order", () => {
    const { ic } = makeIC();
    expect(ic.pins.length).toBe(16);
    expect(ic.pins[0]!.name).toBe("A");
    expect(ic.pins[3]!.name).toBe("!GL");
    expect(ic.pins[4]!.name).toBe("!G2");
    expect(ic.pins[5]!.name).toBe("G1");
    expect(ic.pins[6]!.name).toBe("Y7");
    expect(ic.pins[7]!.name).toBe("GND");
    expect(ic.pins[14]!.name).toBe("Y0");
    expect(ic.pins[15]!.name).toBe("VCC");
  });

  it("is transparent when !GL=LOW: outputs track address", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW); // transparent
    setAddr(ic, 3); ic.evaluate();
    expect(ic.y[3]!.resolvedState).toBe(NetState.LOW);
    for (let i = 0; i < 8; i++) {
      if (i !== 3) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
    }

    // Change address while still transparent
    setAddr(ic, 6); ic.evaluate();
    expect(ic.y[6]!.resolvedState).toBe(NetState.LOW);
    expect(ic.y[3]!.resolvedState).toBe(NetState.HIGH);
  });

  it("latches address on !GL rising edge (LOW→HIGH)", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW); // transparent
    setAddr(ic, 5); ic.evaluate();
    expect(ic.y[5]!.resolvedState).toBe(NetState.LOW);

    // Rising edge of !GL: latch addr=5
    ic.gl.net!.drive("test:gl", NetState.HIGH);
    ic.evaluate();
    expect(ic.y[5]!.resolvedState).toBe(NetState.LOW); // still 5

    // Change address — latched, so output should not change
    setAddr(ic, 2); ic.evaluate();
    expect(ic.y[5]!.resolvedState).toBe(NetState.LOW); // still 5
    expect(ic.y[2]!.resolvedState).toBe(NetState.HIGH);
  });

  it("holds latched value while !GL stays HIGH", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 4); ic.evaluate();

    ic.gl.net!.drive("test:gl", NetState.HIGH);
    ic.evaluate(); // latch addr=4

    // Multiple evaluates with GL=HIGH and changing address
    setAddr(ic, 0); ic.evaluate();
    setAddr(ic, 7); ic.evaluate();
    expect(ic.y[4]!.resolvedState).toBe(NetState.LOW);
    for (let i = 0; i < 8; i++) {
      if (i !== 4) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
    }
  });

  it("becomes transparent again when !GL returns LOW", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 1); ic.evaluate();

    // Latch addr=1
    ic.gl.net!.drive("test:gl", NetState.HIGH);
    ic.evaluate();

    // Return transparent
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 6); ic.evaluate();
    expect(ic.y[6]!.resolvedState).toBe(NetState.LOW);
    expect(ic.y[1]!.resolvedState).toBe(NetState.HIGH);
  });

  it("decodes all 8 addresses correctly in transparent mode", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW); // transparent

    for (let addr = 0; addr < 8; addr++) {
      setAddr(ic, addr); ic.evaluate();
      for (let i = 0; i < 8; i++) {
        const expected = i === addr ? NetState.LOW : NetState.HIGH;
        expect(ic.y[i]!.resolvedState).toBe(expected);
      }
    }
  });

  it("all outputs HIGH when disabled (G1=LOW)", () => {
    const { ic } = makeIC();
    ic.g1.net!.drive("test:g1", NetState.LOW);
    ic.g2.net!.drive("test:g2", NetState.LOW);
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 3); ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("all outputs HIGH when disabled (!G2=HIGH)", () => {
    const { ic } = makeIC();
    ic.g1.net!.drive("test:g1", NetState.HIGH);
    ic.g2.net!.drive("test:g2", NetState.HIGH); // disabled
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 3); ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);
  });

  it("latched address still decodes when enabled/disabled transitions", () => {
    const { ic } = makeIC();
    enable(ic);
    ic.gl.net!.drive("test:gl", NetState.LOW);
    setAddr(ic, 2); ic.evaluate();

    // Latch
    ic.gl.net!.drive("test:gl", NetState.HIGH);
    ic.evaluate();

    // Disable
    ic.g1.net!.drive("test:g1", NetState.LOW);
    ic.evaluate();
    for (let i = 0; i < 8; i++) expect(ic.y[i]!.resolvedState).toBe(NetState.HIGH);

    // Re-enable: should decode latched addr=2
    ic.g1.net!.drive("test:g1", NetState.HIGH);
    ic.evaluate();
    expect(ic.y[2]!.resolvedState).toBe(NetState.LOW);
  });
});
