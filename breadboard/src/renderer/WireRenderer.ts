import { WirePlacement } from "../layout/PlacementResult.js";
import { holeToWorld } from "../layout/holeToWorld.js";

export class WireRenderer {
  draw(ctx: CanvasRenderingContext2D, wires: WirePlacement[]): void {
    // Group wires by net to stagger arc heights
    const netWireIndex = new Map<string, number>();

    for (const wire of wires) {
      const netId = wire.net.id;
      const idx = netWireIndex.get(netId) ?? 0;

      const from = holeToWorld(wire.fromHole);
      const to = holeToWorld(wire.toHole);

      this._drawArcWire(ctx, from.x, from.y, to.x, to.y, wire.color, idx);

      netWireIndex.set(netId, idx + 1);
    }
  }

  private _drawArcWire(
    ctx: CanvasRenderingContext2D,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color: string,
    index: number
  ): void {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dist = Math.sqrt(dx * dx + dy * dy);

    // Arc height: min(dist*0.3 + index*5, 60)
    const arcH = Math.min(dist * 0.3 + index * 5, 60);

    // Midpoint
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;

    // Perpendicular direction (normalized)
    const len = dist || 1;
    const perpX = -dy / len;
    const perpY = dx / len;

    // Control point
    const cx = mx + perpX * arcH;
    const cy = my + perpY * arcH;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo(cx, cy, x2, y2);
    ctx.stroke();

    // Draw dots at endpoints
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x1, y1, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x2, y2, 3, 0, Math.PI * 2);
    ctx.fill();
  }
}
