import { Net } from "../circuit/Net.js";
import { EdgeKind, NetState } from "../circuit/types.js";

export class ClockDriver {
  private readonly net: Net;
  private readonly driverId: string;
  private _high = false;
  private _ticks = 0;

  constructor(net: Net, driverId = "clock") {
    this.net = net;
    this.driverId = driverId;
    // Start LOW
    this.net.drive(this.driverId, NetState.LOW);
  }

  get ticks(): number {
    return this._ticks;
  }

  get isHigh(): boolean {
    return this._high;
  }

  /** Flip the clock level. Returns the edge that just occurred. */
  tick(): EdgeKind {
    this._high = !this._high;
    this._ticks++;
    this.net.drive(
      this.driverId,
      this._high ? NetState.HIGH : NetState.LOW
    );
    return this._high ? EdgeKind.RISING : EdgeKind.FALLING;
  }
}
