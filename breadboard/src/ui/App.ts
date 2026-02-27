import { Circuit } from "../circuit/Circuit.js";
import { Propagator } from "../emulation/Propagator.js";
import { Emulator } from "../emulation/Emulator.js";
import { Layouter } from "../layout/Layouter.js";
import { Camera } from "../renderer/Camera.js";
import { Renderer } from "../renderer/Renderer.js";
import { ControlBar } from "./ControlBar.js";
import { InputHandler } from "./InputHandler.js";
import { buildLedButtonCircuit } from "../examples/ledButton.js";
import { BOARD_ORIGIN_X, BOARD_ORIGIN_Y } from "../layout/holeToWorld.js";
import { HOLE_PITCH, COL_MAX } from "../breadboard/constants.js";
import { CENTER_GAP } from "../layout/holeToWorld.js";

export class App {
  private readonly canvas: HTMLCanvasElement;
  private readonly camera: Camera;
  private readonly renderer: Renderer;
  private readonly emulator: Emulator;
  private readonly inputHandler: InputHandler;
  private _animFrameId: number | null = null;

  constructor() {
    this.canvas = document.getElementById("main-canvas") as HTMLCanvasElement;

    // Build circuit
    const circuit = new Circuit();
    buildLedButtonCircuit(circuit);

    // Layout
    const layouter = new Layouter();
    const layout = layouter.layout(circuit);

    // Emulation
    const propagator = new Propagator(circuit);
    this.emulator = new Emulator(propagator);

    // Rendering
    this.camera = new Camera();
    this.renderer = new Renderer(this.canvas, this.camera);
    this.renderer.setLayout(layout);

    // Fit camera to breadboard
    const boardW = COL_MAX * HOLE_PITCH + BOARD_ORIGIN_X + 40;
    const boardH =
      BOARD_ORIGIN_Y + 10 * HOLE_PITCH + CENTER_GAP + 80;
    const rect = this.canvas.getBoundingClientRect();
    this.camera.fitToRect(rect.width || 800, rect.height || 600, boardW, boardH);

    // Input
    this.inputHandler = new InputHandler(this.canvas, this.camera);
    this.inputHandler.setPlacements(layout.placements);
    this.inputHandler.onButtonToggled(() => {
      // Re-propagate after button toggle
      propagator.propagate();
    });

    // Control bar
    const _controlBar = new ControlBar(this.emulator, (_hz) => {});

    // Start render loop
    this._loop();
  }

  private _loop(): void {
    this.renderer.render();
    this._animFrameId = requestAnimationFrame(() => this._loop());
  }

  destroy(): void {
    if (this._animFrameId !== null) {
      cancelAnimationFrame(this._animFrameId);
    }
    this.emulator.pause();
  }
}
