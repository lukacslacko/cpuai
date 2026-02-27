import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

export class Battery extends Component {
  readonly vcc: Pin;
  readonly gnd: Pin;

  constructor() {
    const vcc = new Pin("VCC", PinRole.POWER);
    const gnd = new Pin("GND", PinRole.POWER);
    super("Battery", [vcc, gnd]);
    this.vcc = vcc;
    this.gnd = gnd;
  }

  evaluate(): void {
    this.vcc.drive(this.id + ":vcc", NetState.HIGH);
    this.gnd.drive(this.id + ":gnd", NetState.LOW);
  }
}
