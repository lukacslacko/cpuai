import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

export type LEDColor = "red" | "green" | "yellow" | "blue" | "white" | "orange";

export class LED extends Component {
  readonly anode: Pin;
  readonly cathode: Pin;
  readonly color: LEDColor;
  lit = false;

  constructor(color: LEDColor = "red") {
    const anode = new Pin("anode", PinRole.INPUT);
    const cathode = new Pin("cathode", PinRole.INPUT);
    super("LED", [anode, cathode]);
    this.anode = anode;
    this.cathode = cathode;
    this.color = color;
  }

  evaluate(): void {
    const anodeState = this.anode.resolvedState;
    const cathodeState = this.cathode.resolvedState;
    this.lit =
      anodeState === NetState.HIGH && cathodeState === NetState.LOW;
  }
}
