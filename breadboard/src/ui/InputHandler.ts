import { Camera } from "../renderer/Camera.js";
import { ComponentPlacement } from "../layout/PlacementResult.js";
import { Button } from "../circuit/components/Button.js";
import { buttonBounds } from "../renderer/components/ButtonRenderer.js";

export class InputHandler {
  private isDragging = false;
  private lastX = 0;
  private lastY = 0;
  private placements: ComponentPlacement[] = [];
  private onButtonToggle: (() => void) | null = null;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly camera: Camera
  ) {
    this._setupListeners();
  }

  setPlacements(placements: ComponentPlacement[]): void {
    this.placements = placements;
  }

  onButtonToggled(cb: () => void): void {
    this.onButtonToggle = cb;
  }

  private _setupListeners(): void {
    const canvas = this.canvas;

    // Zoom
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 0.9;
      this.camera.zoomAt(e.offsetX, e.offsetY, factor);
    }, { passive: false });

    // Pan
    canvas.addEventListener("mousedown", (e) => {
      // Check if click is on a button
      const world = this.camera.screenToWorld(e.offsetX, e.offsetY);
      const clickedButton = this._findButtonAt(world.x, world.y);

      if (clickedButton) {
        clickedButton.pressed = !clickedButton.pressed;
        this.onButtonToggle?.();
        return;
      }

      this.isDragging = true;
      this.lastX = e.clientX;
      this.lastY = e.clientY;
      canvas.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastX;
      const dy = e.clientY - this.lastY;
      this.camera.pan(dx, dy);
      this.lastX = e.clientX;
      this.lastY = e.clientY;
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
      this.canvas.style.cursor = "grab";
    });

    // Touch support (basic)
    let lastTouchDist = 0;
    canvas.addEventListener("touchstart", (e) => {
      if (e.touches.length === 2) {
        const t0 = e.touches[0]!;
        const t1 = e.touches[1]!;
        lastTouchDist = Math.hypot(t1.clientX - t0.clientX, t1.clientY - t0.clientY);
      }
    });

    canvas.addEventListener("touchmove", (e) => {
      e.preventDefault();
      if (e.touches.length === 2) {
        const t0 = e.touches[0]!;
        const t1 = e.touches[1]!;
        const dist = Math.hypot(t1.clientX - t0.clientX, t1.clientY - t0.clientY);
        const factor = dist / lastTouchDist;
        const mx = (t0.clientX + t1.clientX) / 2;
        const my = (t0.clientY + t1.clientY) / 2;
        const rect = canvas.getBoundingClientRect();
        this.camera.zoomAt(mx - rect.left, my - rect.top, factor);
        lastTouchDist = dist;
      }
    }, { passive: false });
  }

  private _findButtonAt(worldX: number, worldY: number): Button | null {
    for (const p of this.placements) {
      if (p.componentType !== "button") continue;
      const bounds = buttonBounds(p);
      if (
        worldX >= bounds.x &&
        worldX <= bounds.x + bounds.w &&
        worldY >= bounds.y &&
        worldY <= bounds.y + bounds.h
      ) {
        return p.component as Button;
      }
    }
    return null;
  }
}
