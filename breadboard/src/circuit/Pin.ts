import { Net } from "./Net.js";
import { NetState, PinRole } from "./types.js";

export class Pin {
  readonly name: string;
  readonly role: PinRole;
  net: Net | null = null;

  constructor(name: string, role: PinRole = PinRole.BIDIRECTIONAL) {
    this.name = name;
    this.role = role;
  }

  get logicLevel(): boolean {
    return this.net?.logicLevel ?? false;
  }

  get resolvedState(): NetState {
    return this.net?.resolvedState ?? NetState.FLOAT;
  }

  resolvedStateExcluding(driverId: string): NetState {
    return this.net?.resolvedStateExcluding(driverId) ?? NetState.FLOAT;
  }

  drive(driverId: string, state: NetState.HIGH | NetState.LOW): void {
    this.net?.drive(driverId, state);
  }

  unDrive(driverId: string): void {
    this.net?.unDrive(driverId);
  }
}
