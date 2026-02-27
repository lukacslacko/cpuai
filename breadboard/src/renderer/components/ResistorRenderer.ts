import { ComponentPlacement } from "../../layout/PlacementResult.js";
import { holeToWorld } from "../../layout/holeToWorld.js";

// Standard color band colors for a 1kΩ resistor (brown-black-red-gold)
const BANDS = ["#8b4513", "#111", "#e53935", "#ffd700"];

export function drawResistor(ctx: CanvasRenderingContext2D, p: ComponentPlacement): void {
  const pinA = p.pinHoles[0];
  const pinB = p.pinHoles[1];
  if (!pinA || !pinB) return;

  const posA = holeToWorld(pinA.hole);
  const posB = holeToWorld(pinB.hole);

  const bodyW = 18;
  const bodyH = 8;
  const cx = (posA.x + posB.x) / 2;
  const cy = (posA.y + posB.y) / 2;

  // Lead wires
  ctx.strokeStyle = "#aaa";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(posA.x, posA.y);
  ctx.lineTo(cx - bodyW / 2, cy);
  ctx.moveTo(posB.x, posB.y);
  ctx.lineTo(cx + bodyW / 2, cy);
  ctx.stroke();

  // Body
  ctx.fillStyle = "#d4b483"; // tan
  ctx.strokeStyle = "#8a7050";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(cx - bodyW / 2, cy - bodyH / 2, bodyW, bodyH, 2);
  ctx.fill();
  ctx.stroke();

  // Color bands
  const bandSpacing = bodyW / (BANDS.length + 1);
  for (let i = 0; i < BANDS.length; i++) {
    const bx = cx - bodyW / 2 + bandSpacing * (i + 1);
    ctx.fillStyle = BANDS[i]!;
    ctx.fillRect(bx - 1, cy - bodyH / 2 + 1, 2, bodyH - 2);
  }
}
