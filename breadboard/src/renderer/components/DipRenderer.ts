import { ComponentPlacement } from "../../layout/PlacementResult.js";
import { holeToWorld } from "../../layout/holeToWorld.js";
import { HOLE_PITCH } from "../../breadboard/constants.js";

export function drawDip(ctx: CanvasRenderingContext2D, p: ComponentPlacement): void {
  const meta = p.meta as { startCol: number; halfPins: number; widthPx: number } | undefined;
  if (!meta) return;

  const { halfPins } = meta;
  const bodyW = halfPins * HOLE_PITCH - 4;
  const bodyH = 2 * HOLE_PITCH + 16;

  const topLeft = holeToWorld({ row: "e", col: meta.startCol });
  const x = topLeft.x - HOLE_PITCH / 2 + 2;
  const y = topLeft.y - 6;

  // DIP body
  ctx.fillStyle = "#1a1a1a";
  ctx.beginPath();
  ctx.roundRect(x, y, bodyW, bodyH, 3);
  ctx.fill();

  ctx.strokeStyle = "#444";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Notch (top center)
  ctx.fillStyle = "#2a2a2a";
  ctx.beginPath();
  ctx.arc(x + bodyW / 2, y, 5, 0, Math.PI);
  ctx.fill();

  // Part number label
  ctx.fillStyle = "#aaa";
  ctx.font = `bold ${Math.min(10, bodyW / (p.component.name.length * 0.7))}px monospace`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(p.component.name, x + bodyW / 2, y + bodyH / 2);

  // Pin lines + labels
  ctx.font = "7px monospace";
  ctx.fillStyle = "#888";

  for (const ph of p.pinHoles) {
    const holePos = holeToWorld(ph.hole);
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(holePos.x, holePos.y);

    // Draw toward the body
    const isTop = typeof ph.hole !== "string" && ph.hole.row === "e";
    const bodyEdgeY = isTop ? y + bodyH : y;
    ctx.lineTo(holePos.x, isTop ? holePos.y + 4 : holePos.y - 4);
    ctx.stroke();
    void bodyEdgeY;

    // Pin label
    ctx.fillStyle = "#ccc";
    ctx.textAlign = "center";
    ctx.textBaseline = isTop ? "bottom" : "top";
    const labelY = isTop ? holePos.y - 2 : holePos.y + 2;

    // Only show short labels (skip GND/VCC inside body)
    if (ph.pinName.length <= 3) {
      ctx.fillText(ph.pinName, holePos.x, labelY);
    }
  }
}
