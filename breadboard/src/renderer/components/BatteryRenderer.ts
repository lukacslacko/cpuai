import { ComponentPlacement } from "../../layout/PlacementResult.js";
import { BOARD_TOP_Y } from "../../layout/holeToWorld.js";
import { HOLE_PITCH, TOP_ROWS } from "../../breadboard/constants.js";

export function drawBattery(ctx: CanvasRenderingContext2D, p: ComponentPlacement): void {
  const cx = p.x;
  const cy = p.y;

  const bodyW = 30;
  const bodyH = 50;

  // Battery body
  ctx.fillStyle = "#444";
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.roundRect(cx - bodyW / 2, cy - bodyH / 2, bodyW, bodyH, 4);
  ctx.fill();
  ctx.stroke();

  // Positive terminal (top)
  ctx.fillStyle = "#e53935";
  ctx.fillRect(cx - 5, cy - bodyH / 2 - 4, 10, 5);
  ctx.fillStyle = "#fff";
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("+", cx, cy - bodyH / 2 - 2);

  // Negative terminal (bottom)
  ctx.fillStyle = "#212121";
  ctx.fillRect(cx - 5, cy + bodyH / 2, 10, 5);
  ctx.fillStyle = "#fff";
  ctx.fillText("−", cx, cy + bodyH / 2 + 2);

  // "9V" label
  ctx.fillStyle = "#ccc";
  ctx.font = "9px monospace";
  ctx.fillText("9V", cx, cy);

  // VCC wire to top rail (matches holeToWorld "rail:top:pos" = BOARD_TOP_Y + 8)
  const vccRailY = BOARD_TOP_Y + 8;
  ctx.strokeStyle = "#e53935";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy - bodyH / 2 - 4);
  ctx.lineTo(cx, vccRailY);
  ctx.stroke();

  // GND wire to second rail (matches holeToWorld "rail:top:neg" = BOARD_TOP_Y + 8 + HOLE_PITCH)
  const gndRailY = BOARD_TOP_Y + 8 + HOLE_PITCH;
  void TOP_ROWS;
  ctx.strokeStyle = "#212121";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx, cy + bodyH / 2 + 4);
  ctx.lineTo(cx, gndRailY);
  ctx.stroke();
}
