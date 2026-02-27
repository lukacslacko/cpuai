import { NetState } from "./types.js";

export class Net {
  readonly id: string;
  private drivers = new Map<string, NetState.HIGH | NetState.LOW>();

  constructor(id: string) {
    this.id = id;
  }

  drive(driverId: string, state: NetState.HIGH | NetState.LOW): void {
    this.drivers.set(driverId, state);
  }

  unDrive(driverId: string): void {
    this.drivers.delete(driverId);
  }

  get resolvedState(): NetState {
    return this._resolve(this.drivers);
  }

  /** Net state as seen from outside a specific driver (ignores that driver's contribution). */
  resolvedStateExcluding(driverId: string): NetState {
    if (!this.drivers.has(driverId)) return this.resolvedState;
    const temp = new Map(this.drivers);
    temp.delete(driverId);
    return this._resolve(temp);
  }

  private _resolve(drivers: Map<string, NetState.HIGH | NetState.LOW>): NetState {
    if (drivers.size === 0) return NetState.FLOAT;
    let hasHigh = false;
    let hasLow = false;
    for (const state of drivers.values()) {
      if (state === NetState.HIGH) hasHigh = true;
      else hasLow = true;
    }
    if (hasHigh && hasLow) return NetState.CONFLICT;
    if (hasHigh) return NetState.HIGH;
    return NetState.LOW;
  }

  /** FLOAT defaults to false (LOW) for component inputs */
  get logicLevel(): boolean {
    return this.resolvedState === NetState.HIGH;
  }
}
