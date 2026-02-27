import { describe, it, expect, beforeEach } from "vitest";
import { IC74HC573 } from "../../src/circuit/components/IC74HC573.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

function makeIC(): { ic: IC74HC573; circuit: Circuit } {
  const ic = new IC74HC573();
  const circuit = new Circuit();
  circuit.addComponent(ic);

  // Connect all pins to fresh nets
  for (const pin of ic.pins) {
    circuit.connect(pin);
  }

  return { ic, circuit };
}

describe("IC74HC573", () => {
  it("is transparent when LE=HIGH, OE=LOW: Q tracks D", () => {
    const { ic } = makeIC();

    // OE=LOW (active), LE=HIGH (transparent)
    ic.oe.net!.drive("oe", NetState.LOW);
    ic.le.net!.drive("le", NetState.HIGH);

    // Drive D0=HIGH, D1=LOW, others=LOW
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) {
      ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);
    }

    ic.evaluate();

    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);
    expect(ic.q[1]!.resolvedState).toBe(NetState.LOW);
  });

  it("latches on LE falling edge", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.LOW);
    ic.le.net!.drive("le", NetState.HIGH);

    // Set D0=HIGH while transparent
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) {
      ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);
    }
    ic.evaluate();

    // Transition to LE=LOW (falling edge)
    ic.le.net!.drive("le", NetState.LOW);
    ic.evaluate();

    // Confirm latch captured HIGH
    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);

    // Change D0, verify Q doesn't change
    ic.d[0]!.net!.drive("d0", NetState.LOW);
    ic.evaluate();

    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH); // still latched
  });

  it("tri-states outputs when OE=HIGH", () => {
    const { ic } = makeIC();

    // OE=HIGH (disabled), LE=LOW (latched with all LOW defaults)
    ic.oe.net!.drive("oe", NetState.HIGH);
    ic.le.net!.drive("le", NetState.LOW);

    for (let i = 0; i < 8; i++) {
      ic.d[i]!.net!.drive(`d${i}`, NetState.HIGH);
    }

    ic.evaluate();

    // All Q should be FLOAT
    for (let i = 0; i < 8; i++) {
      expect(ic.q[i]!.resolvedState).toBe(NetState.FLOAT);
    }
  });

  it("outputs become active when OE transitions LOW", () => {
    const { ic } = makeIC();

    ic.oe.net!.drive("oe", NetState.HIGH);
    ic.le.net!.drive("le", NetState.HIGH);

    // Set D values while transparent
    ic.d[0]!.net!.drive("d0", NetState.HIGH);
    for (let i = 1; i < 8; i++) {
      ic.d[i]!.net!.drive(`d${i}`, NetState.LOW);
    }
    ic.evaluate(); // outputs tri-stated because OE=HIGH

    // Enable OE
    ic.oe.net!.drive("oe", NetState.LOW);
    ic.evaluate();

    expect(ic.q[0]!.resolvedState).toBe(NetState.HIGH);
    expect(ic.q[1]!.resolvedState).toBe(NetState.LOW);
  });

  it("has 20 pins in the correct order", () => {
    const { ic } = makeIC();
    expect(ic.pins.length).toBe(20);
    expect(ic.pins[0]!.name).toBe("OE");
    expect(ic.pins[9]!.name).toBe("GND");
    expect(ic.pins[18]!.name).toBe("LE");
    expect(ic.pins[19]!.name).toBe("VCC");
  });
});
