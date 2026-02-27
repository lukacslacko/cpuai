import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

export class Resistor extends Component {
  readonly a: Pin;
  readonly b: Pin;

  constructor(label?: string) {
    const a = new Pin("a", PinRole.BIDIRECTIONAL);
    const b = new Pin("b", PinRole.BIDIRECTIONAL);
    super(label ?? "Resistor", [a, b]);
    this.a = a;
    this.b = b;
  }

  evaluate(): void {
    // Check the state of each side EXCLUDING our own drives on that side,
    // so we don't oscillate by reading back our own output.
    const aExt = this.a.resolvedStateExcluding(this.id + ":ba");
    const bExt = this.b.resolvedStateExcluding(this.id + ":ab");

    const aDriven = aExt === NetState.HIGH || aExt === NetState.LOW;
    const bDriven = bExt === NetState.HIGH || bExt === NetState.LOW;

    if (aDriven && !bDriven) {
      // Propagate a → b
      this.b.drive(this.id + ":ab", aExt as NetState.HIGH | NetState.LOW);
      this.a.unDrive(this.id + ":ba");
    } else if (bDriven && !aDriven) {
      // Propagate b → a
      this.a.drive(this.id + ":ba", bExt as NetState.HIGH | NetState.LOW);
      this.b.unDrive(this.id + ":ab");
    } else {
      // Both driven or neither — release our drives
      this.a.unDrive(this.id + ":ba");
      this.b.unDrive(this.id + ":ab");
    }
  }
}
