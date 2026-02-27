import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * 74HC574 - Octal D-type Flip-Flop with 3-State Outputs (rising-edge triggered)
 *
 * Pin layout (20-pin DIP):
 *  Pin  1: OE  - active-LOW output enable
 *  Pins 2-9: D0-D7 - data inputs
 *  Pin 10: GND
 *  Pins 11-18: Q7-Q0 - data outputs (NOTE: reversed order vs 74HC573)
 *  Pin 19: CLK - clock input (captures D on rising edge)
 *  Pin 20: VCC
 *
 * Physical column alignment (DIP straddle):
 *   row e:  OE  D0  D1  D2  D3  D4  D5  D6  D7  GND
 *   row f:  VCC CLK Q0  Q1  Q2  Q3  Q4  Q5  Q6  Q7
 *
 * D0 is directly above CLK; D1 directly above Q0; etc.
 */
export class IC74HC574 extends Component {
  readonly oe: Pin;
  readonly d: Pin[];
  readonly q: Pin[];
  readonly clk: Pin;
  readonly vcc: Pin;
  readonly gnd: Pin;

  private _latch: boolean[] = new Array(8).fill(false);
  private _prevClk = false;

  constructor(label?: string) {
    const oe = new Pin("OE", PinRole.INPUT);
    const d = Array.from({ length: 8 }, (_, i) => new Pin(`D${i}`, PinRole.INPUT));
    const q = Array.from({ length: 8 }, (_, i) => new Pin(`Q${i}`, PinRole.OUTPUT));
    const clk = new Pin("CLK", PinRole.INPUT);
    const vcc = new Pin("VCC", PinRole.POWER);
    const gnd = new Pin("GND", PinRole.POWER);

    // Physical DIP-20 pin order:
    // 1=OE, 2=D0..9=D7, 10=GND, 11=Q7..18=Q0, 19=CLK, 20=VCC
    // Q outputs are physically reversed (Q7 at pin 11, Q0 at pin 18),
    // so reverse the array for the DIP layout while keeping this.q[0]=Q0 logically.
    super(label ?? "74HC574", [oe, ...d, gnd, ...q.slice().reverse(), clk, vcc]);
    this.oe = oe;
    this.d = d;
    this.q = q;
    this.clk = clk;
    this.vcc = vcc;
    this.gnd = gnd;
  }

  evaluate(): void {
    const clkHigh = this.clk.logicLevel;

    // Capture D inputs on the rising edge of CLK only.
    // _prevClk is updated immediately so subsequent evaluate() calls
    // within the same propagation step do not re-trigger the edge.
    if (clkHigh && !this._prevClk) {
      for (let i = 0; i < 8; i++) {
        this._latch[i] = this.d[i]!.logicLevel;
      }
    }
    this._prevClk = clkHigh;

    // OE active-LOW: drive Q outputs when OE=LOW, tri-state when OE=HIGH
    if (this.oe.logicLevel) {
      for (let i = 0; i < 8; i++) {
        this.q[i]!.unDrive(this.id + `:q${i}`);
      }
    } else {
      for (let i = 0; i < 8; i++) {
        this.q[i]!.drive(
          this.id + `:q${i}`,
          this._latch[i] ? NetState.HIGH : NetState.LOW
        );
      }
    }
  }
}
