import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * CD40193 / 74HC193 — 4-Bit Synchronous Up/Down Binary Counter
 *
 * Pin layout (16-pin DIP):
 *  Pin  1: B    - data input (bit 1)
 *  Pin  2: QB   - output bit 1
 *  Pin  3: QA   - output bit 0 (LSB)
 *  Pin  4: CLR  - clear (async, active HIGH → resets to 0000)
 *  Pin  5: DOWN - count-down clock (rising edge)
 *  Pin  6: UP   - count-up clock (rising edge)
 *  Pin  7: QC   - output bit 2
 *  Pin  8: GND
 *  Pin  9: QD   - output bit 3 (MSB)
 *  Pin 10: BO   - borrow output (active LOW; LOW when count=0 and DOWN is LOW)
 *  Pin 11: CO   - carry output (active LOW; LOW when count=15 and UP is LOW)
 *  Pin 12: LOAD - parallel load (async, active LOW → loads A/B/C/D)
 *  Pin 13: D    - data input (bit 3, MSB)
 *  Pin 14: C    - data input (bit 2)
 *  Pin 15: A    - data input (bit 0, LSB)
 *  Pin 16: VCC
 *
 * Physical DIP column alignment:
 *  row e: B   QB  QA  CLR DOWN UP  QC  GND
 *  row f: VCC A   C   D   LOAD CO  BO  QD
 *  (each column N pairs pin N with pin 17-N across the gap)
 */
export class IC40193 extends Component {
  readonly a: Pin;    // data input A (LSB)
  readonly b: Pin;    // data input B
  readonly c: Pin;    // data input C
  readonly d: Pin;    // data input D (MSB)
  readonly qa: Pin;   // output QA (LSB)
  readonly qb: Pin;   // output QB
  readonly qc: Pin;   // output QC
  readonly qd: Pin;   // output QD (MSB)
  readonly up: Pin;   // count-up clock
  readonly down: Pin; // count-down clock
  readonly clr: Pin;  // clear (async, active HIGH)
  readonly load: Pin; // parallel load (async, active LOW)
  readonly co: Pin;   // carry output (active LOW)
  readonly bo: Pin;   // borrow output (active LOW)
  readonly vcc: Pin;
  readonly gnd: Pin;

  private _count = 0;
  private _prevUp = false;
  private _prevDown = false;

  constructor(label?: string) {
    // Pins created in physical DIP-16 order (pin 1 → pin 16):
    const b    = new Pin("B",    PinRole.INPUT);
    const qb   = new Pin("QB",   PinRole.OUTPUT);
    const qa   = new Pin("QA",   PinRole.OUTPUT);
    const clr  = new Pin("CLR",  PinRole.INPUT);
    const down = new Pin("DOWN", PinRole.INPUT);
    const up   = new Pin("UP",   PinRole.INPUT);
    const qc   = new Pin("QC",   PinRole.OUTPUT);
    const gnd  = new Pin("GND",  PinRole.POWER);
    const qd   = new Pin("QD",   PinRole.OUTPUT);
    const bo   = new Pin("BO",   PinRole.OUTPUT);
    const co   = new Pin("CO",   PinRole.OUTPUT);
    const load = new Pin("LOAD", PinRole.INPUT);
    const d    = new Pin("D",    PinRole.INPUT);
    const c    = new Pin("C",    PinRole.INPUT);
    const a    = new Pin("A",    PinRole.INPUT);
    const vcc  = new Pin("VCC",  PinRole.POWER);

    super(label ?? "40193", [b, qb, qa, clr, down, up, qc, gnd, qd, bo, co, load, d, c, a, vcc]);

    this.a = a; this.b = b; this.c = c; this.d = d;
    this.qa = qa; this.qb = qb; this.qc = qc; this.qd = qd;
    this.up = up; this.down = down;
    this.clr = clr; this.load = load;
    this.co = co; this.bo = bo;
    this.vcc = vcc; this.gnd = gnd;
  }

  evaluate(): void {
    const upHigh   = this.up.logicLevel;
    const downHigh = this.down.logicLevel;
    const clrHigh  = this.clr.logicLevel;
    const loadLow  = !this.load.logicLevel; // active-LOW

    // Priority 1: async clear
    if (clrHigh) {
      this._count = 0;
    }
    // Priority 2: async parallel load
    else if (loadLow) {
      const a = this.a.logicLevel ? 1 : 0;
      const b = this.b.logicLevel ? 1 : 0;
      const c = this.c.logicLevel ? 1 : 0;
      const d = this.d.logicLevel ? 1 : 0;
      this._count = (d << 3) | (c << 2) | (b << 1) | a;
    }
    // Priority 3: edge-triggered count (only when CLR=LOW and LOAD=HIGH)
    else {
      if (upHigh && !this._prevUp) {
        this._count = (this._count + 1) & 0xf;
      }
      if (downHigh && !this._prevDown) {
        this._count = (this._count - 1 + 16) & 0xf;
      }
    }

    this._prevUp   = upHigh;
    this._prevDown = downHigh;

    // Drive Q outputs
    const drv = (bit: number, id: string, pin: Pin) =>
      pin.drive(this.id + id, bit ? NetState.HIGH : NetState.LOW);

    drv((this._count >> 0) & 1, ":qa", this.qa);
    drv((this._count >> 1) & 1, ":qb", this.qb);
    drv((this._count >> 2) & 1, ":qc", this.qc);
    drv((this._count >> 3) & 1, ":qd", this.qd);

    // CO: active-LOW; pulses LOW when count=15 and UP clock is LOW
    this.co.drive(
      this.id + ":co",
      this._count === 15 && !upHigh ? NetState.LOW : NetState.HIGH
    );

    // BO: active-LOW; pulses LOW when count=0 and DOWN clock is LOW
    this.bo.drive(
      this.id + ":bo",
      this._count === 0 && !downHigh ? NetState.LOW : NetState.HIGH
    );
  }

  get count(): number {
    return this._count;
  }
}
