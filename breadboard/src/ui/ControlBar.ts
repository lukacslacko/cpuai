import { Emulator } from "../emulation/Emulator.js";

export class ControlBar {
  private readonly emulator: Emulator;
  private speedHz = 10;
  private readonly onSpeedChange: (hz: number) => void;

  constructor(emulator: Emulator, onSpeedChange: (hz: number) => void) {
    this.emulator = emulator;
    this.onSpeedChange = onSpeedChange;
    this._setup();
  }

  private _setup(): void {
    const btnStep = document.getElementById("btn-step") as HTMLButtonElement;
    const btnPlay = document.getElementById("btn-play") as HTMLButtonElement;
    const btnPause = document.getElementById("btn-pause") as HTMLButtonElement;
    const speedSlider = document.getElementById("speed-slider") as HTMLInputElement;
    const speedDisplay = document.getElementById("speed-display") as HTMLSpanElement;
    const tickCounter = document.getElementById("tick-counter") as HTMLSpanElement;

    btnStep.addEventListener("click", () => {
      if (!this.emulator.running) {
        this.emulator.step();
        tickCounter.textContent = `Tick: ${this.emulator.tickCount}`;
      }
    });

    btnPlay.addEventListener("click", () => {
      if (!this.emulator.running) {
        this.emulator.run(this.speedHz);
        btnPlay.disabled = true;
        btnPause.disabled = false;
        btnStep.disabled = true;
      }
    });

    btnPause.addEventListener("click", () => {
      this.emulator.pause();
      btnPlay.disabled = false;
      btnPause.disabled = true;
      btnStep.disabled = false;
      tickCounter.textContent = `Tick: ${this.emulator.tickCount}`;
    });

    speedSlider.addEventListener("input", () => {
      this.speedHz = parseInt(speedSlider.value, 10);
      speedDisplay.textContent = `${this.speedHz} Hz`;
      this.onSpeedChange(this.speedHz);
      if (this.emulator.running) {
        this.emulator.setSpeed(this.speedHz);
      }
    });

    // Update tick counter on each emulator tick
    this.emulator.onTick(() => {
      tickCounter.textContent = `Tick: ${this.emulator.tickCount}`;
    });
  }
}
