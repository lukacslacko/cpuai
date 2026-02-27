import { describe, it, expect } from "vitest";
import { Circuit } from "../../src/circuit/Circuit.js";
import { Battery } from "../../src/circuit/components/Battery.js";
import { Button } from "../../src/circuit/components/Button.js";
import { Resistor } from "../../src/circuit/components/Resistor.js";
import { LED } from "../../src/circuit/components/LED.js";
import { IC74HC573 } from "../../src/circuit/components/IC74HC573.js";
import { Layouter } from "../../src/layout/Layouter.js";
import { buildLedButtonCircuit } from "../../src/examples/ledButton.js";
import { COL_MIN, COL_MAX } from "../../src/breadboard/constants.js";
import { HoleCoord } from "../../src/breadboard/BreadboardModel.js";

function isMainHole(hole: unknown): hole is HoleCoord {
  return typeof hole === "object" && hole !== null && "row" in hole && "col" in hole;
}

describe("Layouter - no hole collisions", () => {
  it("places led-button circuit with no collisions", () => {
    const circuit = new Circuit();
    buildLedButtonCircuit(circuit);

    const layouter = new Layouter();
    const result = layouter.layout(circuit);

    // Collect all main-grid holes
    const usedHoles = new Set<string>();
    for (const p of result.placements) {
      for (const ph of p.pinHoles) {
        if (isMainHole(ph.hole)) {
          const key = `${ph.hole.row}:${ph.hole.col}`;
          expect(usedHoles.has(key), `Duplicate hole ${key}`).toBe(false);
          usedHoles.add(key);
        }
      }
    }
  });

  it("DIP-20 straddles center gap: pins 1-10 on row e, pins 11-20 on row f", () => {
    const circuit = new Circuit();
    const ic = new IC74HC573();
    circuit.addComponent(ic);
    // Connect all pins to fresh nets
    for (const pin of ic.pins) circuit.connect(pin);

    const layouter = new Layouter();
    const result = layouter.layout(circuit);

    const icPlacement = result.placements.find((p) => p.componentType === "dip20");
    expect(icPlacement).toBeDefined();

    if (!icPlacement) return;

    // First 10 pins should be in row e
    for (let i = 0; i < 10; i++) {
      const ph = icPlacement.pinHoles[i];
      expect(ph).toBeDefined();
      if (ph && isMainHole(ph.hole)) {
        expect(ph.hole.row).toBe("e");
      }
    }

    // Next 10 pins should be in row f
    for (let i = 10; i < 20; i++) {
      const ph = icPlacement.pinHoles[i];
      expect(ph).toBeDefined();
      if (ph && isMainHole(ph.hole)) {
        expect(ph.hole.row).toBe("f");
      }
    }
  });

  it("all main-grid holes are within column bounds [1, 63]", () => {
    const circuit = new Circuit();
    const battery = new Battery();
    const button = new Button();
    const resistor = new Resistor();
    const led = new LED("red");
    const ic = new IC74HC573();

    circuit.addComponent(battery);
    circuit.addComponent(button);
    circuit.addComponent(resistor);
    circuit.addComponent(led);
    circuit.addComponent(ic);

    for (const pin of [...battery.pins, ...button.pins, ...resistor.pins, ...led.pins, ...ic.pins]) {
      circuit.connect(pin);
    }

    const layouter = new Layouter();
    const result = layouter.layout(circuit);

    for (const p of result.placements) {
      for (const ph of p.pinHoles) {
        if (isMainHole(ph.hole)) {
          expect(ph.hole.col).toBeGreaterThanOrEqual(COL_MIN);
          expect(ph.hole.col).toBeLessThanOrEqual(COL_MAX);
        }
      }
    }
  });

  it("button straddles center gap: pin a on row e, pin b on row f", () => {
    const circuit = new Circuit();
    const button = new Button();
    circuit.addComponent(button);
    circuit.connect(button.a);
    circuit.connect(button.b);

    const layouter = new Layouter();
    const result = layouter.layout(circuit);

    const btnPlacement = result.placements.find((p) => p.componentType === "button");
    expect(btnPlacement).toBeDefined();

    if (!btnPlacement) return;

    const pinA = btnPlacement.pinHoles[0];
    const pinB = btnPlacement.pinHoles[1];

    expect(pinA).toBeDefined();
    expect(pinB).toBeDefined();

    if (pinA && isMainHole(pinA.hole)) expect(pinA.hole.row).toBe("e");
    if (pinB && isMainHole(pinB.hole)) expect(pinB.hole.row).toBe("f");
  });
});
