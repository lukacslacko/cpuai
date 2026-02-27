import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * 74138 / 74HC138 — 3-to-8 Line Decoder / Demultiplexer
 *
 * Pin layout (16-pin DIP):
 *  Pin  1: A    - address input bit 0 (LSB)
 *  Pin  2: B    - address input bit 1
 *  Pin  3: C    - address input bit 2 (MSB)
 *  Pin  4: G2A  - enable (active LOW)
 *  Pin  5: G2B  - enable (active LOW)
 *  Pin  6: G1   - enable (active HIGH)
 *  Pin  7: Y7   - output 7 (active LOW)
 *  Pin  8: GND
 *  Pin  9: Y6   - output 6 (active LOW)
 *  Pin 10: Y5   - output 5 (active LOW)
 *  Pin 11: Y4   - output 4 (active LOW)
 *  Pin 12: Y3   - output 3 (active LOW)
 *  Pin 13: Y2   - output 2 (active LOW)
 *  Pin 14: Y1   - output 1 (active LOW)
 *  Pin 15: Y0   - output 0 (active LOW)
 *  Pin 16: VCC
 *
 * Enable: G1=HIGH AND G2A=LOW AND G2B=LOW
 * When enabled: Y[addr]=LOW, all others HIGH (addr = C:B:A)
 * When disabled: all outputs HIGH
 */
export class IC74138 extends Component {
  readonly a: Pin;   // address bit 0
  readonly b: Pin;   // address bit 1
  readonly c: Pin;   // address bit 2
  readonly g1: Pin;  // enable (active HIGH)
  readonly g2a: Pin; // enable (active LOW)
  readonly g2b: Pin; // enable (active LOW)
  readonly y: Pin[]; // outputs y[0]..y[7] (active LOW)
  readonly vcc: Pin;
  readonly gnd: Pin;

  constructor(label?: string) {
    const a   = new Pin("A",   PinRole.INPUT);
    const b   = new Pin("B",   PinRole.INPUT);
    const c   = new Pin("C",   PinRole.INPUT);
    const g2a = new Pin("G2A", PinRole.INPUT);
    const g2b = new Pin("G2B", PinRole.INPUT);
    const g1  = new Pin("G1",  PinRole.INPUT);
    const y7  = new Pin("Y7",  PinRole.OUTPUT);
    const gnd = new Pin("GND", PinRole.POWER);
    const y6  = new Pin("Y6",  PinRole.OUTPUT);
    const y5  = new Pin("Y5",  PinRole.OUTPUT);
    const y4  = new Pin("Y4",  PinRole.OUTPUT);
    const y3  = new Pin("Y3",  PinRole.OUTPUT);
    const y2  = new Pin("Y2",  PinRole.OUTPUT);
    const y1  = new Pin("Y1",  PinRole.OUTPUT);
    const y0  = new Pin("Y0",  PinRole.OUTPUT);
    const vcc = new Pin("VCC", PinRole.POWER);

    // Physical DIP order: pin 1 → 16
    super(label ?? "74138", [a, b, c, g2a, g2b, g1, y7, gnd, y6, y5, y4, y3, y2, y1, y0, vcc]);

    this.a = a; this.b = b; this.c = c;
    this.g1 = g1; this.g2a = g2a; this.g2b = g2b;
    this.y = [y0, y1, y2, y3, y4, y5, y6, y7];
    this.vcc = vcc; this.gnd = gnd;
  }

  evaluate(): void {
    const enabled =
      this.g1.logicLevel &&
      !this.g2a.logicLevel &&
      !this.g2b.logicLevel;

    const addr =
      (this.a.logicLevel ? 1 : 0) |
      (this.b.logicLevel ? 2 : 0) |
      (this.c.logicLevel ? 4 : 0);

    for (let i = 0; i < 8; i++) {
      // Active-LOW: selected output is LOW, all others HIGH
      const state = (enabled && i === addr) ? NetState.LOW : NetState.HIGH;
      this.y[i]!.drive(this.id + `:y${i}`, state);
    }
  }
}
