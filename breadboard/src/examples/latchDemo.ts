import { Circuit } from "../circuit/Circuit.js";
import { Battery } from "../circuit/components/Battery.js";
import { Button } from "../circuit/components/Button.js";
import { Resistor } from "../circuit/components/Resistor.js";
import { LED, LEDColor } from "../circuit/components/LED.js";
import { IC74HC573 } from "../circuit/components/IC74HC573.js";

const LED_COLORS: LEDColor[] = [
  "red", "orange", "yellow", "green",
  "blue", "blue", "white", "red",
];

/**
 * Latch demo circuit: 8 input buttons → 74HC573 → 8 LEDs
 *
 * - D0–D7: each driven by a button (unpressed=LOW, pressed=HIGH)
 * - OE: tied to GND → always active (OE is active-LOW)
 * - LE button: unpressed=LOW (latched), pressed=HIGH (transparent)
 * - Q0–Q7 → 330Ω resistor → LED → GND
 *
 * Layout order (left to right):
 *   battery | D buttons 0-7 | 74HC573 | LE button | resistors 0-7 | LEDs 0-7
 */
export function buildLatchDemoCircuit(circuit: Circuit): {
  battery: Battery;
  ic: IC74HC573;
  leButton: Button;
  dButtons: Button[];
  resistors: Resistor[];
  leds: LED[];
} {
  const battery = new Battery();
  const ic = new IC74HC573("74HC573");
  const leButton = new Button("LE");
  const dButtons = Array.from({ length: 8 }, (_, i) => new Button(`D${i}`));
  const resistors = Array.from({ length: 8 }, (_, i) => new Resistor(`R${i}`));
  const leds = LED_COLORS.map((c) => new LED(c));

  // Registration order controls layout order (left to right)
  circuit.addComponent(battery);
  for (const b of dButtons) circuit.addComponent(b);
  circuit.addComponent(ic);
  circuit.addComponent(leButton);
  for (const r of resistors) circuit.addComponent(r);
  for (const l of leds) circuit.addComponent(l);

  // Power rails
  circuit.connect(battery.vcc, ic.vcc);
  // OE tied to GND so outputs are always enabled (OE is active-LOW)
  circuit.connect(battery.gnd, ic.gnd, ic.oe);

  // LE button: a → VCC, b → LE
  // Unpressed: LE=FLOAT→LOW → latched mode
  // Pressed:   LE=HIGH       → transparent mode
  circuit.connect(battery.vcc, leButton.a);
  circuit.connect(leButton.b, ic.le);

  // D input buttons: a → VCC, b → D pin
  // Unpressed: D=FLOAT→LOW; Pressed: D=HIGH
  for (let i = 0; i < 8; i++) {
    circuit.connect(battery.vcc, dButtons[i]!.a);
    circuit.connect(dButtons[i]!.b, ic.d[i]!);
  }

  // Q outputs: Q → resistor → LED anode; LED cathode → GND
  for (let i = 0; i < 8; i++) {
    circuit.connect(ic.q[i]!, resistors[i]!.a);
    circuit.connect(resistors[i]!.b, leds[i]!.anode);
    circuit.connect(leds[i]!.cathode, battery.gnd);
  }

  return { battery, ic, leButton, dButtons, resistors, leds };
}
