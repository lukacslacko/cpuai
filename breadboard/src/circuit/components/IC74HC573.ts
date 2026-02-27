import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * 74HC573 - Octal Transparent D-Type Latch
 *
 * Pin layout (20-pin DIP):
 *  Pin  1: OE  - active-LOW output enable
 *  Pins 2-9: D0-D7 - data inputs
 *  Pin 10: GND
 *  Pins 11-18: Q0-Q7 - data outputs
 *  Pin 19: LE  - latch enable (HIGH=transparent, LOW=latched)
 *  Pin 20: VCC
 */
export class IC74HC573 extends Component {
  readonly oe: Pin;
  readonly d: Pin[];
  readonly q: Pin[];
  readonly le: Pin;
  readonly vcc: Pin;
  readonly gnd: Pin;

  private _latch: boolean[] = new Array(8).fill(false);
  private _prevLe = false;

  constructor(label?: string) {
    const oe = new Pin("OE", PinRole.INPUT);
    const d = Array.from({ length: 8 }, (_, i) => new Pin(`D${i}`, PinRole.INPUT));
    const q = Array.from({ length: 8 }, (_, i) => new Pin(`Q${i}`, PinRole.OUTPUT));
    const le = new Pin("LE", PinRole.INPUT);
    const vcc = new Pin("VCC", PinRole.POWER);
    const gnd = new Pin("GND", PinRole.POWER);

    // Pin order matches physical DIP-20:
    // 1=OE, 2=D0..9=D7, 10=GND, 11=Q0..18=Q7, 19=LE, 20=VCC
    super(label ?? "74HC573", [oe, ...d, gnd, ...q, le, vcc]);
    this.oe = oe;
    this.d = d;
    this.q = q;
    this.le = le;
    this.vcc = vcc;
    this.gnd = gnd;
  }

  evaluate(): void {
    const leHigh = this.le.logicLevel;
    const leRisingEdge = leHigh && !this._prevLe;
    const leFallingEdge = !leHigh && this._prevLe;

    // Transparent mode: latch tracks D inputs
    if (leHigh) {
      for (let i = 0; i < 8; i++) {
        this._latch[i] = this.d[i]!.logicLevel;
      }
    }

    // Latch on falling edge of LE (capture current D values)
    if (leFallingEdge) {
      for (let i = 0; i < 8; i++) {
        this._latch[i] = this.d[i]!.logicLevel;
      }
    }

    this._prevLe = leHigh;

    // OE active-LOW: tri-state outputs when OE=HIGH
    const oeActive = !this.oe.logicLevel; // OE pin is active-LOW

    if (!oeActive) {
      // Tri-state all Q outputs
      for (let i = 0; i < 8; i++) {
        this.q[i]!.unDrive(this.id + `:q${i}`);
      }
    } else {
      // Drive Q outputs from latch
      for (let i = 0; i < 8; i++) {
        this.q[i]!.drive(
          this.id + `:q${i}`,
          this._latch[i] ? NetState.HIGH : NetState.LOW
        );
      }
    }

    // Also suppress unused edge variables from TypeScript
    void leRisingEdge;
  }
}
