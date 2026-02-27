import { Camera } from "./Camera.js";
import { BreadboardRenderer } from "./BreadboardRenderer.js";
import { WireRenderer } from "./WireRenderer.js";
import { ComponentRenderer } from "./ComponentRenderer.js";
import { LayoutResult } from "../layout/PlacementResult.js";

export class Renderer {
  private readonly camera: Camera;
  private readonly boardRenderer: BreadboardRenderer;
  private readonly wireRenderer: WireRenderer;
  private readonly componentRenderer: ComponentRenderer;
  private _layout: LayoutResult | null = null;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    camera: Camera
  ) {
    this.camera = camera;
    this.boardRenderer = new BreadboardRenderer();
    this.wireRenderer = new WireRenderer();
    this.componentRenderer = new ComponentRenderer();
  }

  setLayout(layout: LayoutResult): void {
    this._layout = layout;
  }

  render(): void {
    const canvas = this.canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Resize canvas to match display size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }

    // Clear
    ctx.clearRect(0, 0, rect.width, rect.height);
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Apply camera transform
    ctx.save();
    ctx.translate(this.camera.offsetX, this.camera.offsetY);
    ctx.scale(this.camera.scale, this.camera.scale);

    // Draw breadboard background
    this.boardRenderer.draw(ctx);

    if (this._layout) {
      // Draw jump wires
      this.wireRenderer.draw(ctx, this._layout.wires);

      // Draw components
      this.componentRenderer.draw(ctx, this._layout.placements);
    }

    ctx.restore();
  }
}
