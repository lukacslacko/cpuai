import { Circuit } from "../circuit/Circuit.js";
import { Battery } from "../circuit/components/Battery.js";
import { Button } from "../circuit/components/Button.js";
import { Resistor } from "../circuit/components/Resistor.js";
import { LED } from "../circuit/components/LED.js";

/**
 * Canonical demo circuit: battery → button → resistor → LED → GND
 *
 * Topology:
 *   Battery.VCC → Button.a
 *   Button.b    → Resistor.a
 *   Resistor.b  → LED.anode
 *   LED.cathode → Battery.GND
 */
export function buildLedButtonCircuit(circuit: Circuit): {
  battery: Battery;
  button: Button;
  resistor: Resistor;
  led: LED;
} {
  const battery = new Battery();
  const button = new Button("SW1");
  const resistor = new Resistor("R1");
  const led = new LED("red");

  circuit.addComponent(battery);
  circuit.addComponent(button);
  circuit.addComponent(resistor);
  circuit.addComponent(led);

  // VCC rail
  circuit.connect(battery.vcc, button.a);

  // Signal path
  circuit.connect(button.b, resistor.a);
  circuit.connect(resistor.b, led.anode);

  // GND rail
  circuit.connect(led.cathode, battery.gnd);

  return { battery, button, resistor, led };
}
