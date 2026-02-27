export class Camera {
  scale = 1.0;
  offsetX = 0;
  offsetY = 0;

  readonly minScale = 0.2;
  readonly maxScale = 5.0;

  worldToScreen(wx: number, wy: number): { x: number; y: number } {
    return {
      x: wx * this.scale + this.offsetX,
      y: wy * this.scale + this.offsetY,
    };
  }

  screenToWorld(sx: number, sy: number): { x: number; y: number } {
    return {
      x: (sx - this.offsetX) / this.scale,
      y: (sy - this.offsetY) / this.scale,
    };
  }

  /** Zoom around a screen-space pivot point */
  zoomAt(screenX: number, screenY: number, factor: number): void {
    const newScale = Math.max(
      this.minScale,
      Math.min(this.maxScale, this.scale * factor)
    );

    // Adjust offset so the pivot point stays fixed
    const worldX = (screenX - this.offsetX) / this.scale;
    const worldY = (screenY - this.offsetY) / this.scale;

    this.scale = newScale;
    this.offsetX = screenX - worldX * this.scale;
    this.offsetY = screenY - worldY * this.scale;
  }

  pan(dx: number, dy: number): void {
    this.offsetX += dx;
    this.offsetY += dy;
  }

  /** Center the camera on a world-space rectangle */
  fitToRect(
    canvasW: number,
    canvasH: number,
    worldW: number,
    worldH: number
  ): void {
    const scaleX = canvasW / (worldW + 200);
    const scaleY = canvasH / (worldH + 200);
    this.scale = Math.max(this.minScale, Math.min(this.maxScale, Math.min(scaleX, scaleY)));
    this.offsetX = (canvasW - worldW * this.scale) / 2;
    this.offsetY = (canvasH - worldH * this.scale) / 2;
  }
}
