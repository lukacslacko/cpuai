import { describe, it, expect, beforeEach } from "vitest";
import { LED } from "../../src/circuit/components/LED.js";
import { Battery } from "../../src/circuit/components/Battery.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { Net } from "../../src/circuit/Net.js";
import { NetState } from "../../src/circuit/types.js";

describe("LED", () => {
  it("is lit when anode=HIGH and cathode=LOW", () => {
    const led = new LED("red");
    const circuit = new Circuit();
    circuit.addComponent(led);

    const anodeNet = circuit.connect(led.anode);
    const cathodeNet = circuit.connect(led.cathode);

    anodeNet.drive("src", NetState.HIGH);
    cathodeNet.drive("gnd", NetState.LOW);

    led.evaluate();
    expect(led.lit).toBe(true);
  });

  it("is dark when anode=LOW and cathode=HIGH (reversed)", () => {
    const led = new LED("red");
    const circuit = new Circuit();
    circuit.addComponent(led);

    const anodeNet = circuit.connect(led.anode);
    const cathodeNet = circuit.connect(led.cathode);

    anodeNet.drive("src", NetState.LOW);
    cathodeNet.drive("gnd", NetState.HIGH);

    led.evaluate();
    expect(led.lit).toBe(false);
  });

  it("is dark when both FLOAT", () => {
    const led = new LED("red");
    const circuit = new Circuit();
    circuit.addComponent(led);

    circuit.connect(led.anode);
    circuit.connect(led.cathode);

    led.evaluate();
    expect(led.lit).toBe(false);
  });

  it("is dark when anode=HIGH and cathode=HIGH", () => {
    const led = new LED("green");
    const circuit = new Circuit();
    circuit.addComponent(led);

    const anodeNet = circuit.connect(led.anode);
    const cathodeNet = circuit.connect(led.cathode);

    anodeNet.drive("src", NetState.HIGH);
    cathodeNet.drive("src2", NetState.HIGH);

    led.evaluate();
    expect(led.lit).toBe(false);
  });

  it("stores the LED color", () => {
    const led = new LED("blue");
    expect(led.color).toBe("blue");
  });
});

describe("LED in a battery circuit", () => {
  it("lights up when connected correctly", () => {
    const battery = new Battery();
    const led = new LED("red");
    const circuit = new Circuit();

    circuit.addComponent(battery);
    circuit.addComponent(led);

    circuit.connect(battery.vcc, led.anode);
    circuit.connect(battery.gnd, led.cathode);

    battery.evaluate();
    led.evaluate();

    expect(led.lit).toBe(true);
  });
});
