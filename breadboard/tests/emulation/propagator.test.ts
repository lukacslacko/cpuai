import { describe, it, expect } from "vitest";
import { Circuit } from "../../src/circuit/Circuit.js";
import { Battery } from "../../src/circuit/components/Battery.js";
import { Resistor } from "../../src/circuit/components/Resistor.js";
import { LED } from "../../src/circuit/components/LED.js";
import { Button } from "../../src/circuit/components/Button.js";
import { Propagator } from "../../src/emulation/Propagator.js";
import { NetState } from "../../src/circuit/types.js";

describe("Propagator - battery → resistor → LED → GND", () => {
  it("LED is lit after propagate()", () => {
    const circuit = new Circuit();
    const battery = new Battery();
    const resistor = new Resistor();
    const led = new LED("red");

    circuit.addComponent(battery);
    circuit.addComponent(resistor);
    circuit.addComponent(led);

    circuit.connect(battery.vcc, resistor.a);
    circuit.connect(resistor.b, led.anode);
    circuit.connect(led.cathode, battery.gnd);

    const propagator = new Propagator(circuit);
    propagator.propagate();

    expect(led.lit).toBe(true);
  });

  it("LED is dark before propagate (no drivers active)", () => {
    const circuit = new Circuit();
    const battery = new Battery();
    const led = new LED("red");

    circuit.addComponent(battery);
    circuit.addComponent(led);

    // Deliberately NOT calling connect yet — pins unconnected
    circuit.connect(battery.vcc);
    circuit.connect(battery.gnd);
    circuit.connect(led.anode);
    circuit.connect(led.cathode);

    // Without connecting, LED anode is FLOAT → not lit
    led.evaluate();
    expect(led.lit).toBe(false);
  });

  it("LED goes dark when resistor net is disconnected", () => {
    const circuit = new Circuit();
    const battery = new Battery();
    const resistor = new Resistor();
    const led = new LED("red");

    circuit.addComponent(battery);
    circuit.addComponent(resistor);
    circuit.addComponent(led);

    circuit.connect(battery.vcc, resistor.a);
    circuit.connect(resistor.b, led.anode);
    circuit.connect(led.cathode, battery.gnd);

    const propagator = new Propagator(circuit);
    propagator.propagate();
    expect(led.lit).toBe(true);

    // Break the circuit: undrive resistor's contribution
    // by releasing the net driver (simulating disconnect)
    resistor.b.net?.drive("manual_break", NetState.FLOAT as unknown as NetState.LOW);
    led.evaluate();
    // After forcing float, LED should go dark (anode won't be HIGH)
    // Actually let's just verify the propagation path: removing battery drives
    battery.vcc.net!.unDrive(battery["id"] + ":vcc");
    propagator.propagate();
    expect(led.lit).toBe(false);
  });

  it("button gates LED: open = dark, pressed = lit", () => {
    const circuit = new Circuit();
    const battery = new Battery();
    const button = new Button();
    const led = new LED("red");

    circuit.addComponent(battery);
    circuit.addComponent(button);
    circuit.addComponent(led);

    circuit.connect(battery.vcc, button.a);
    circuit.connect(button.b, led.anode);
    circuit.connect(led.cathode, battery.gnd);

    const propagator = new Propagator(circuit);
    propagator.propagate();
    expect(led.lit).toBe(false); // button open

    button.pressed = true;
    propagator.propagate();
    expect(led.lit).toBe(true); // button closed
  });
});
