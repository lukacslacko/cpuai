import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

/**
 * 28C64 — 8KB (64Kbit) EEPROM, used as ROM (write ignored)
 *
 * Pin layout (28-pin DIP):
 *  Pin  1: NC    (no connect; pulled LOW — leave unconnected)
 *  Pin  2: A12   Pin 15: D3
 *  Pin  3: A7    Pin 16: D4
 *  Pin  4: A6    Pin 17: D5
 *  Pin  5: A5    Pin 18: D6
 *  Pin  6: A4    Pin 19: D7
 *  Pin  7: A3    Pin 20: !CE  (active LOW chip enable)
 *  Pin  8: A2    Pin 21: A10
 *  Pin  9: A1    Pin 22: !OE  (active LOW output enable)
 *  Pin 10: A0    Pin 23: A11
 *  Pin 11: D0    Pin 24: A9
 *  Pin 12: D1    Pin 25: A8
 *  Pin 13: D2    Pin 26: NC   (no connect; pulled LOW — leave unconnected)
 *  Pin 14: GND   Pin 27: !WE  (ignored — read-only emulation)
 *                Pin 28: VCC
 *
 * Read:  !CE=L, !OE=L → drive D0-D7 from ROM data[addr]
 * Write: ignored
 * Idle:  D0-D7 tri-stated
 */
export class IC28C64 extends Component {
  readonly a: Pin[];   // a[0]=A0 .. a[12]=A12 (logical order)
  readonly d: Pin[];   // d[0]=D0 .. d[7]=D7
  readonly ce: Pin;    // !CE (active LOW)
  readonly oe: Pin;    // !OE (active LOW)
  readonly we: Pin;    // !WE (ignored)
  readonly nc1: Pin;   // NC  (pin 1)
  readonly nc26: Pin;  // NC  (pin 26)
  readonly vcc: Pin;
  readonly gnd: Pin;

  readonly data: Uint8Array;

  constructor(label?: string, romData?: Uint8Array) {
    const nc1 = new Pin("NC",  PinRole.INPUT);
    const a12 = new Pin("A12", PinRole.INPUT);
    const a7  = new Pin("A7",  PinRole.INPUT);
    const a6  = new Pin("A6",  PinRole.INPUT);
    const a5  = new Pin("A5",  PinRole.INPUT);
    const a4  = new Pin("A4",  PinRole.INPUT);
    const a3  = new Pin("A3",  PinRole.INPUT);
    const a2  = new Pin("A2",  PinRole.INPUT);
    const a1  = new Pin("A1",  PinRole.INPUT);
    const a0  = new Pin("A0",  PinRole.INPUT);
    const d0  = new Pin("D0",  PinRole.BIDIRECTIONAL);
    const d1  = new Pin("D1",  PinRole.BIDIRECTIONAL);
    const d2  = new Pin("D2",  PinRole.BIDIRECTIONAL);
    const gnd = new Pin("GND", PinRole.POWER);
    const d3  = new Pin("D3",  PinRole.BIDIRECTIONAL);
    const d4  = new Pin("D4",  PinRole.BIDIRECTIONAL);
    const d5  = new Pin("D5",  PinRole.BIDIRECTIONAL);
    const d6  = new Pin("D6",  PinRole.BIDIRECTIONAL);
    const d7  = new Pin("D7",  PinRole.BIDIRECTIONAL);
    const ce  = new Pin("!CE", PinRole.INPUT);
    const a10 = new Pin("A10", PinRole.INPUT);
    const oe  = new Pin("!OE", PinRole.INPUT);
    const a11 = new Pin("A11", PinRole.INPUT);
    const a9  = new Pin("A9",  PinRole.INPUT);
    const a8  = new Pin("A8",  PinRole.INPUT);
    const nc26 = new Pin("NC", PinRole.INPUT);
    const we  = new Pin("!WE", PinRole.INPUT);
    const vcc = new Pin("VCC", PinRole.POWER);

    // Physical DIP-28 order (pin 1 → pin 28)
    super(label ?? "28C64", [
      nc1, a12, a7, a6, a5, a4, a3, a2, a1, a0,
      d0, d1, d2, gnd,
      d3, d4, d5, d6, d7,
      ce, a10, oe, a11, a9, a8, nc26, we, vcc,
    ]);

    this.a = [a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12];
    this.d = [d0, d1, d2, d3, d4, d5, d6, d7];
    this.ce = ce; this.oe = oe; this.we = we;
    this.nc1 = nc1; this.nc26 = nc26;
    this.vcc = vcc; this.gnd = gnd;

    this.data = new Uint8Array(8192);
    if (romData) this.data.set(romData.subarray(0, 8192));
  }

  evaluate(): void {
    const chipEnabled  = !this.ce.logicLevel;
    const outputEnabled = chipEnabled && !this.oe.logicLevel;

    if (outputEnabled) {
      const byte = this.data[this._addr()] ?? 0;
      for (let i = 0; i < 8; i++) {
        this.d[i]!.drive(this.id + `:d${i}`, (byte >> i) & 1 ? NetState.HIGH : NetState.LOW);
      }
    } else {
      for (let i = 0; i < 8; i++) this.d[i]!.unDrive(this.id + `:d${i}`);
    }
  }

  private _addr(): number {
    let addr = 0;
    for (let i = 0; i < 13; i++) {
      if (this.a[i]!.logicLevel) addr |= 1 << i;
    }
    return addr;
  }
}
