import { Propagator } from "./Propagator.js";
import { ClockDriver } from "./ClockDriver.js";

export class Emulator {
  private readonly propagator: Propagator;
  private readonly clockDrivers: ClockDriver[];
  private _tickCount = 0;
  private _intervalId: ReturnType<typeof setInterval> | null = null;
  private _running = false;
  private _onTick: (() => void) | null = null;

  constructor(propagator: Propagator, clockDrivers: ClockDriver[] = []) {
    this.propagator = propagator;
    this.clockDrivers = clockDrivers;

    // Initial propagation to establish stable state
    this.propagator.propagate();
  }

  get tickCount(): number {
    return this._tickCount;
  }

  get running(): boolean {
    return this._running;
  }

  onTick(cb: () => void): void {
    this._onTick = cb;
  }

  /** Advance one half-clock cycle. */
  step(): void {
    for (const clk of this.clockDrivers) {
      clk.tick();
    }
    this.propagator.propagate();
    this._tickCount++;
    this._onTick?.();
  }

  /** Start running at the given frequency (full cycles per second). */
  run(speedHz: number): void {
    if (this._running) return;
    this._running = true;
    // step() = half-cycle, so interval = 500/speedHz ms per step
    const intervalMs = 500 / speedHz;
    this._intervalId = setInterval(() => this.step(), intervalMs);
  }

  pause(): void {
    if (!this._running) return;
    this._running = false;
    if (this._intervalId !== null) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  /** Re-configure running speed without stopping. */
  setSpeed(speedHz: number): void {
    if (this._running) {
      this.pause();
      this.run(speedHz);
    }
  }
}
