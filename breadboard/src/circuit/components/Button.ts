import { Component } from "../Component.js";
import { Pin } from "../Pin.js";
import { NetState, PinRole } from "../types.js";

export class Button extends Component {
  readonly a: Pin;
  readonly b: Pin;
  pressed = false;

  constructor(label?: string) {
    const a = new Pin("a", PinRole.BIDIRECTIONAL);
    const b = new Pin("b", PinRole.BIDIRECTIONAL);
    super(label ?? "Button", [a, b]);
    this.a = a;
    this.b = b;
  }

  evaluate(): void {
    if (!this.pressed) {
      this.a.unDrive(this.id + ":ab");
      this.b.unDrive(this.id + ":ba");
      return;
    }

    // Check each side excluding our own propagated drive to avoid oscillation
    const aExt = this.a.resolvedStateExcluding(this.id + ":ab");
    const bExt = this.b.resolvedStateExcluding(this.id + ":ba");

    const aDriven = aExt === NetState.HIGH || aExt === NetState.LOW;
    const bDriven = bExt === NetState.HIGH || bExt === NetState.LOW;

    if (aDriven) {
      this.b.drive(this.id + ":ba", aExt as NetState.HIGH | NetState.LOW);
    } else {
      this.b.unDrive(this.id + ":ba");
    }

    if (bDriven) {
      this.a.drive(this.id + ":ab", bExt as NetState.HIGH | NetState.LOW);
    } else {
      this.a.unDrive(this.id + ":ab");
    }
  }
}
