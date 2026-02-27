import { ComponentPlacement } from "../../layout/PlacementResult.js";
import { Button } from "../../circuit/components/Button.js";
import { holeToWorld } from "../../layout/holeToWorld.js";
import { CENTER_GAP, BOARD_ORIGIN_Y } from "../../layout/holeToWorld.js";
import { HOLE_PITCH, TOP_ROWS } from "../../breadboard/constants.js";

export function drawButton(ctx: CanvasRenderingContext2D, p: ComponentPlacement): void {
  const button = p.component as Button;

  const pinA = p.pinHoles[0];
  const pinB = p.pinHoles[1];
  if (!pinA || !pinB) return;

  const posA = holeToWorld(pinA.hole);
  const posB = holeToWorld(pinB.hole);

  const cx = (posA.x + posB.x) / 2;
  // Center is in the gap
  const gapCenter =
    BOARD_ORIGIN_Y + TOP_ROWS.length * HOLE_PITCH + CENTER_GAP / 2;
  void gapCenter;

  const capW = 14;
  const capH = 10;
  const bodyW = 10;
  const bodyH = (posB.y - posA.y) + 4;

  // Body (plastic mount)
  ctx.fillStyle = "#555";
  ctx.beginPath();
  ctx.roundRect(cx - bodyW / 2, posA.y - 2, bodyW, bodyH, 2);
  ctx.fill();

  // Tactile cap
  const capY = button.pressed
    ? (posA.y + posB.y) / 2 - capH / 2 + 2
    : (posA.y + posB.y) / 2 - capH / 2;

  ctx.fillStyle = button.pressed ? "#888" : "#bbb";
  ctx.strokeStyle = "#444";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.roundRect(cx - capW / 2, capY, capW, capH, 3);
  ctx.fill();
  ctx.stroke();

  // Lead wires
  ctx.strokeStyle = "#aaa";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(posA.x, posA.y);
  ctx.lineTo(posA.x, posA.y + 4);
  ctx.moveTo(posB.x, posB.y);
  ctx.lineTo(posB.x, posB.y - 4);
  ctx.stroke();

  // Label
  ctx.fillStyle = "#aaa";
  ctx.font = "8px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText(button.pressed ? "ON" : "OFF", cx, posB.y + 4);
}

/** Returns hit-test bounds for click detection */
export function buttonBounds(p: ComponentPlacement): {
  x: number;
  y: number;
  w: number;
  h: number;
} {
  const pinA = p.pinHoles[0];
  const pinB = p.pinHoles[1];
  if (!pinA || !pinB) return { x: 0, y: 0, w: 0, h: 0 };

  const posA = holeToWorld(pinA.hole);
  const posB = holeToWorld(pinB.hole);

  return {
    x: p.x - 10,
    y: posA.y - 4,
    w: 20,
    h: posB.y - posA.y + 8,
  };
}
