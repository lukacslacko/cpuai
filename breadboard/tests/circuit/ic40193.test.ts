import { describe, it, expect, beforeEach } from "vitest";
import { IC40193 } from "../../src/circuit/components/IC40193.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

function makeIC(): { ic: IC40193; circuit: Circuit } {
  const ic = new IC40193();
  const circuit = new Circuit();
  circuit.addComponent(ic);
  for (const pin of ic.pins) circuit.connect(pin);
  return { ic, circuit };
}

/** Drive UP high then low (one rising edge) */
function pulseUp(ic: IC40193): void {
  ic.up.net!.drive("test:up", NetState.HIGH);
  ic.evaluate();
  ic.up.net!.drive("test:up", NetState.LOW);
  ic.evaluate();
}

/** Drive DOWN high then low (one rising edge) */
function pulseDown(ic: IC40193): void {
  ic.down.net!.drive("test:down", NetState.HIGH);
  ic.evaluate();
  ic.down.net!.drive("test:down", NetState.LOW);
  ic.evaluate();
}

describe("IC40193", () => {
  it("has 16 pins in DIP order", () => {
    const { ic } = makeIC();
    expect(ic.pins.length).toBe(16);
    expect(ic.pins[0]!.name).toBe("B");    // pin 1
    expect(ic.pins[3]!.name).toBe("CLR"); // pin 4
    expect(ic.pins[7]!.name).toBe("GND"); // pin 8
    expect(ic.pins[8]!.name).toBe("QD");  // pin 9
    expect(ic.pins[15]!.name).toBe("VCC"); // pin 16
  });

  it("starts at count 0", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.evaluate();
    expect(ic.count).toBe(0);
  });

  it("increments on UP rising edge", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.evaluate();

    pulseUp(ic);
    expect(ic.count).toBe(1);

    pulseUp(ic);
    expect(ic.count).toBe(2);

    pulseUp(ic);
    expect(ic.count).toBe(3);
  });

  it("decrements on DOWN rising edge", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.down.net!.drive("test:down", NetState.LOW);

    // Set count to 5 via repeated UP pulses
    for (let i = 0; i < 5; i++) pulseUp(ic);
    expect(ic.count).toBe(5);

    pulseDown(ic);
    expect(ic.count).toBe(4);

    pulseDown(ic);
    expect(ic.count).toBe(3);
  });

  it("wraps around from 15 to 0 on UP", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    for (let i = 0; i < 15; i++) pulseUp(ic);
    expect(ic.count).toBe(15);

    pulseUp(ic);
    expect(ic.count).toBe(0);
  });

  it("wraps around from 0 to 15 on DOWN", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.evaluate();

    expect(ic.count).toBe(0);
    pulseDown(ic);
    expect(ic.count).toBe(15);
  });

  it("CLR resets count to 0 asynchronously", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    for (let i = 0; i < 7; i++) pulseUp(ic);
    expect(ic.count).toBe(7);

    ic.clr.net!.drive("test:clr", NetState.HIGH);
    ic.evaluate();
    expect(ic.count).toBe(0);

    // UP pulses do nothing while CLR is HIGH
    pulseUp(ic);
    ic.clr.net!.drive("test:clr", NetState.HIGH);
    ic.evaluate();
    expect(ic.count).toBe(0);
  });

  it("CLR takes priority over LOAD", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.a.net!.drive("test:a", NetState.HIGH);
    ic.b.net!.drive("test:b", NetState.HIGH);
    ic.c.net!.drive("test:c", NetState.HIGH);
    ic.d.net!.drive("test:d", NetState.HIGH);

    // Both CLR=HIGH and LOAD=LOW: CLR wins
    ic.clr.net!.drive("test:clr", NetState.HIGH);
    ic.load.net!.drive("test:load", NetState.LOW);
    ic.evaluate();
    expect(ic.count).toBe(0);
  });

  it("parallel LOAD loads ABCD into counter", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);

    // Load 0b1010 = 10
    ic.a.net!.drive("test:a", NetState.LOW);
    ic.b.net!.drive("test:b", NetState.HIGH);
    ic.c.net!.drive("test:c", NetState.LOW);
    ic.d.net!.drive("test:d", NetState.HIGH);
    ic.load.net!.drive("test:load", NetState.LOW); // active-LOW
    ic.evaluate();
    expect(ic.count).toBe(10); // 0b1010

    // Deactivate LOAD, count can proceed
    ic.load.net!.drive("test:load", NetState.HIGH);
    pulseUp(ic);
    expect(ic.count).toBe(11);
  });

  it("drives Q outputs matching count bits", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    // Count to 5 = 0b0101
    for (let i = 0; i < 5; i++) pulseUp(ic);

    expect(ic.qa.resolvedState).toBe(NetState.HIGH); // bit 0 = 1
    expect(ic.qb.resolvedState).toBe(NetState.LOW);  // bit 1 = 0
    expect(ic.qc.resolvedState).toBe(NetState.HIGH); // bit 2 = 1
    expect(ic.qd.resolvedState).toBe(NetState.LOW);  // bit 3 = 0
  });

  it("CO goes LOW when count=15 and UP is LOW", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    // Count to 15
    for (let i = 0; i < 15; i++) pulseUp(ic);
    expect(ic.count).toBe(15);

    // UP is LOW and count=15 → CO should be LOW (active)
    ic.evaluate();
    expect(ic.co.resolvedState).toBe(NetState.LOW);
  });

  it("CO is HIGH when count<15", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    for (let i = 0; i < 7; i++) pulseUp(ic);
    ic.evaluate();
    expect(ic.co.resolvedState).toBe(NetState.HIGH);
  });

  it("BO goes LOW when count=0 and DOWN is LOW", () => {
    const { ic } = makeIC();
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.evaluate();

    // count=0, DOWN=LOW → BO should be LOW (active)
    expect(ic.bo.resolvedState).toBe(NetState.LOW);
  });

  it("BO is HIGH when count>0", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);

    pulseUp(ic); // count = 1
    ic.evaluate();
    expect(ic.bo.resolvedState).toBe(NetState.HIGH);
  });

  it("does not double-count if UP stays HIGH across evaluate() calls", () => {
    const { ic } = makeIC();
    ic.down.net!.drive("test:down", NetState.LOW);
    ic.clr.net!.drive("test:clr", NetState.LOW);
    ic.load.net!.drive("test:load", NetState.HIGH);
    ic.up.net!.drive("test:up", NetState.LOW);
    ic.evaluate();

    // Rising edge
    ic.up.net!.drive("test:up", NetState.HIGH);
    ic.evaluate();
    expect(ic.count).toBe(1);

    // Still HIGH — no additional edge
    ic.evaluate();
    ic.evaluate();
    expect(ic.count).toBe(1);
  });
});
