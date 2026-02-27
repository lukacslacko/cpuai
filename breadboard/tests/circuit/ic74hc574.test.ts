import { describe, it, expect } from "vitest";
import { IC74HC574 } from "../../src/circuit/components/IC74HC574.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

function makeIC(): { ic: IC74HC574; circuit: Circuit } {
  const ic = new IC74HC574();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

describe("IC74HC574", () => {
  it("has 20 pins: OE, D0-D7, GND, Q7-Q0, CLK, VCC", () => {
    const { ic } = makeIC();
    expect(ic.pins.length).toBe(20);
    expect(ic.pins[0]!.name).toBe("OE");
    expect(ic.pins[9]!.name).toBe("GND");
    // Physical pin 11 = Q7 (reversed), pin 19 = CLK, pin 20 = VCC
    expect(ic.pins[10]!.name).toBe("Q7");
    expect(ic.pins[17]!.name).toBe("Q0");
    expect(ic.pins[18]!.name).toBe("CLK");
    expect(ic.pins[19]!.name).toBe("VCC");
  });

  it("captures D inputs on CLK rising edge", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.LOW);  // outputs enabled
    ic.clk.net!.drive("clk", NetState.LOW);

    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);

    ic.evaluate(); // CLK=LOW, no edge

    // Q should still be all LOW (initial latch state)
    expect(ic.q[0]!.resolvedState).toBe(NetState.LOW);

    // Rising edge
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();

    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);
    expect(ic.q[1]!.resolvedState).toBe(NetState.LOW);
  });

  it("does not re-capture on a second evaluate() with CLK still HIGH", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.LOW);
    ic.clk.net!.drive("clk", NetState.LOW);
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);

    // Rising edge — captures D0=HIGH
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();
    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);

    // Now change D0 to LOW while CLK stays HIGH
    ic.d[0]!.net!.drive("d0", NetState.LOW);
    ic.evaluate(); // CLK still HIGH, _prevClk=true → no new edge

    // Q0 should still be HIGH (latched from the rising edge)
    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);
  });

  it("captures new D values on the next rising edge after CLK returns LOW", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.LOW);
    ic.clk.net!.drive("clk", NetState.LOW);
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);

    // First rising edge — Q0=HIGH
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();
    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);

    // CLK goes LOW, change D0
    ic.clk.net!.drive("clk", NetState.LOW);
    ic.d[0]!.net!.drive("d0", NetState.LOW);
    ic.evaluate();

    // Second rising edge — Q0=LOW
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();
    expect(ic.q[0]!.resolvedState).toBe(NetState.LOW);
  });

  it("tri-states outputs when OE=HIGH", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.HIGH); // disabled
    ic.clk.net!.drive("clk", NetState.LOW);
    for (let i = 0; i < 8; i++) ic.d[i]!.net!.drive(`d${i}`, NetState.HIGH);

    // Rising edge with OE=HIGH
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();

    for (let i = 0; i < 8; i++) {
      expect(ic.q[i]!.resolvedState).toBe(NetState.FLOAT);
    }
  });

  it("drives outputs when OE transitions LOW after edge", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.HIGH); // starts disabled
    ic.clk.net!.drive("clk", NetState.LOW);
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);

    // Rising edge — latch captures D, but OE=HIGH so Q is tri-stated
    ic.clk.net!.drive("clk", NetState.HIGH);
    ic.evaluate();
    expect(ic.q[0]!.resolvedState).toBe(NetState.FLOAT);

    // Enable outputs
    ic.oe.net!.drive("oe", NetState.LOW);
    ic.evaluate();
    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);
    expect(ic.q[1]!.resolvedState).toBe(NetState.LOW);
  });

  it("Q0 is at physical pin position 18 (pinIndex 17), CLK at 19 (pinIndex 18)", () => {
    // Verifies the reversed Q-output physical layout
    const { ic } = makeIC();
    expect(ic.q[0]!.name).toBe("Q0");
    expect(ic.pins[17]!.name).toBe("Q0"); // physical pin 18
    expect(ic.pins[18]!.name).toBe("CLK"); // physical pin 19
    // D0 (pin 2) is directly above CLK (pin 19) in DIP layout
    expect(ic.pins[1]!.name).toBe("D0");  // physical pin 2
  });
});
