import { ComponentPlacement } from "../../layout/PlacementResult.js";
import { LED } from "../../circuit/components/LED.js";
import { holeToWorld } from "../../layout/holeToWorld.js";

const COLOR_MAP: Record<string, { body: string; glow: string }> = {
  red: { body: "#e53935", glow: "rgba(229,57,53,0.6)" },
  green: { body: "#43a047", glow: "rgba(67,160,71,0.6)" },
  yellow: { body: "#fdd835", glow: "rgba(253,216,53,0.6)" },
  blue: { body: "#1e88e5", glow: "rgba(30,136,229,0.6)" },
  white: { body: "#f5f5f5", glow: "rgba(245,245,245,0.6)" },
  orange: { body: "#fb8c00", glow: "rgba(251,140,0,0.6)" },
};

export function drawLED(ctx: CanvasRenderingContext2D, p: ComponentPlacement): void {
  const led = p.component as LED;
  const colors = COLOR_MAP[led.color] ?? COLOR_MAP["red"]!;

  const anodeHole = p.pinHoles[0];
  const cathodeHole = p.pinHoles[1];
  if (!anodeHole || !cathodeHole) return;

  const anodePos = holeToWorld(anodeHole.hole);
  const cathodePos = holeToWorld(cathodeHole.hole);

  const cx = (anodePos.x + cathodePos.x) / 2;
  const cy = (anodePos.y + cathodePos.y) / 2;
  const r = 7;

  // Glow effect when lit
  if (led.lit) {
    const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 3);
    grad.addColorStop(0, colors.glow);
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 3, 0, Math.PI * 2);
    ctx.fill();
  }

  // Body
  ctx.fillStyle = led.lit ? colors.body : darken(colors.body, 0.4);
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Pin leads
  ctx.strokeStyle = "#aaa";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(anodePos.x, anodePos.y);
  ctx.lineTo(cx - r, cy);
  ctx.moveTo(cathodePos.x, cathodePos.y);
  ctx.lineTo(cx + r, cy);
  ctx.stroke();

  // + marker on anode side
  ctx.fillStyle = "#ccc";
  ctx.font = "8px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("+", cx - r - 6, cy);
}

function darken(hex: string, factor: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${Math.round(r * factor)},${Math.round(g * factor)},${Math.round(b * factor)})`;
}
