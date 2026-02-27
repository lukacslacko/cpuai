import { Circuit } from "../circuit/Circuit.js";
import { Battery } from "../circuit/components/Battery.js";
import { Button } from "../circuit/components/Button.js";
import { Resistor } from "../circuit/components/Resistor.js";
import { LED, LEDColor } from "../circuit/components/LED.js";
import { IC40193 } from "../circuit/components/IC40193.js";

const LED_COLORS: LEDColor[] = ["green", "yellow", "orange", "red"];

/**
 * Counter demo circuit: CD40193 4-bit up/down counter → 4 LEDs
 *
 * - UP button:   a → VCC, b → UP pin   (rising edge increments counter)
 * - DOWN button: a → VCC, b → DOWN pin (rising edge decrements counter)
 * - CLR button:  a → VCC, b → CLR pin  (active HIGH async reset to 0)
 * - LOAD: tied to VCC (active-LOW, so HIGH = disabled, no parallel load)
 * - A/B/C/D: tied to GND (load value = 0, not used while LOAD=HIGH)
 * - QA–QD → 330Ω resistor → LED → GND (QA=LSB, QD=MSB)
 * - CO (active-LOW carry out): not connected
 * - BO (active-LOW borrow out): not connected
 *
 * Layout order (left to right):
 *   battery | UP button | DOWN button | CLR button | 40193 | resistors 0-3 | LEDs 0-3
 */
export function buildLatchDemoCircuit(circuit: Circuit): {
  battery: Battery;
  ic: IC40193;
  upButton: Button;
  downButton: Button;
  clrButton: Button;
  resistors: Resistor[];
  leds: LED[];
} {
  const battery = new Battery();
  const ic = new IC40193("40193");
  const upButton = new Button("UP");
  const downButton = new Button("DOWN");
  const clrButton = new Button("CLR");
  const resistors = Array.from({ length: 4 }, (_, i) => new Resistor(`R${i}`));
  const leds = LED_COLORS.map((c) => new LED(c));

  // Registration order controls layout order (left to right)
  circuit.addComponent(battery);
  circuit.addComponent(upButton);
  circuit.addComponent(downButton);
  circuit.addComponent(clrButton);
  circuit.addComponent(ic);
  for (const r of resistors) circuit.addComponent(r);
  for (const l of leds) circuit.addComponent(l);

  // Power rails
  circuit.connect(battery.vcc, ic.vcc);
  circuit.connect(battery.gnd, ic.gnd);

  // LOAD tied HIGH (active-LOW → disabled, counter runs freely)
  circuit.connect(battery.vcc, ic.load);

  // Data inputs tied LOW (load value = 0; irrelevant while LOAD=HIGH)
  circuit.connect(battery.gnd, ic.a, ic.b, ic.c, ic.d);

  // UP button: a → VCC, b → UP pin
  circuit.connect(battery.vcc, upButton.a);
  circuit.connect(upButton.b, ic.up);

  // DOWN button: a → VCC, b → DOWN pin
  circuit.connect(battery.vcc, downButton.a);
  circuit.connect(downButton.b, ic.down);

  // CLR button: a → VCC, b → CLR pin (active HIGH)
  circuit.connect(battery.vcc, clrButton.a);
  circuit.connect(clrButton.b, ic.clr);

  // QA–QD outputs: Q → resistor → LED anode; LED cathode → GND
  const outputs = [ic.qa, ic.qb, ic.qc, ic.qd];
  for (let i = 0; i < 4; i++) {
    circuit.connect(outputs[i]!, resistors[i]!.a);
    circuit.connect(resistors[i]!.b, leds[i]!.anode);
    circuit.connect(leds[i]!.cathode, battery.gnd);
  }

  return { battery, ic, upButton, downButton, clrButton, resistors, leds };
}
