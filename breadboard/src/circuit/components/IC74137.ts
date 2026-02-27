import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * 74137 / 74HC137 — 3-to-8 Line Decoder / Demultiplexer with Address Latch
 *
 * Pin layout (16-pin DIP):
 *  Pin  1: A    - address input bit 0 (LSB)
 *  Pin  2: B    - address input bit 1
 *  Pin  3: C    - address input bit 2 (MSB)
 *  Pin  4: !GL  - latch enable (active LOW = transparent; rising edge latches)
 *  Pin  5: !G2  - enable (active LOW)
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
 * Latch: !GL=LOW → transparent (address passes through)
 *        !GL rising edge (LOW→HIGH) → address latched
 * Enable: G1=HIGH AND !G2=LOW → enabled
 * When enabled: Y[addr]=LOW, all others HIGH (addr = C:B:A)
 * When disabled: all outputs HIGH
 */
export class IC74137 extends Component {
  readonly a: Pin;   // address bit 0
  readonly b: Pin;   // address bit 1
  readonly c: Pin;   // address bit 2
  readonly gl: Pin;  // latch enable (active LOW; pin labelled !GL)
  readonly g2: Pin;  // enable (active LOW; pin labelled !G2)
  readonly g1: Pin;  // enable (active HIGH)
  readonly y: Pin[]; // outputs y[0]..y[7] (active LOW)
  readonly vcc: Pin;
  readonly gnd: Pin;

  private _latchedAddr = 0;
  private _prevGl = false; // previous logic level of !GL (false = LOW)

  constructor(label?: string) {
    const a   = new Pin("A",   PinRole.INPUT);
    const b   = new Pin("B",   PinRole.INPUT);
    const c   = new Pin("C",   PinRole.INPUT);
    const gl  = new Pin("!GL", PinRole.INPUT);
    const g2  = new Pin("!G2", PinRole.INPUT);
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
    super(label ?? "74137", [a, b, c, gl, g2, g1, y7, gnd, y6, y5, y4, y3, y2, y1, y0, vcc]);

    this.a = a; this.b = b; this.c = c;
    this.gl = gl; this.g2 = g2; this.g1 = g1;
    this.y = [y0, y1, y2, y3, y4, y5, y6, y7];
    this.vcc = vcc; this.gnd = gnd;
  }

  evaluate(): void {
    const glHigh = this.gl.logicLevel; // !GL pin HIGH = latch mode

    if (!glHigh) {
      // !GL=LOW → transparent: latch tracks current address
      this._latchedAddr =
        (this.a.logicLevel ? 1 : 0) |
        (this.b.logicLevel ? 2 : 0) |
        (this.c.logicLevel ? 4 : 0);
    } else if (!this._prevGl) {
      // Rising edge of !GL (LOW→HIGH): latch the current address
      this._latchedAddr =
        (this.a.logicLevel ? 1 : 0) |
        (this.b.logicLevel ? 2 : 0) |
        (this.c.logicLevel ? 4 : 0);
    }
    // else !GL stays HIGH: hold latched address

    this._prevGl = glHigh;

    const enabled = this.g1.logicLevel && !this.g2.logicLevel;

    for (let i = 0; i < 8; i++) {
      const state = (enabled && i === this._latchedAddr) ? NetState.LOW : NetState.HIGH;
      this.y[i]!.drive(this.id + `:y${i}`, state);
    }
  }
}
