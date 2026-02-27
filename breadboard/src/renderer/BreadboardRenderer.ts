import {
  HOLE_PITCH,
  COL_MIN,
  COL_MAX,
  TOP_ROWS,
  BOT_ROWS,
} from "../breadboard/constants.js";
import {
  BOARD_ORIGIN_X,
  BOARD_ORIGIN_Y,
  CENTER_GAP,
  RAIL_OFFSET,
  BOARD_TOP_Y,
} from "../layout/holeToWorld.js";

const HOLE_RADIUS = 3.5;
const BOARD_COLOR = "#2d6a2d"; // PCB green
const HOLE_COLOR = "#111";
const RAIL_POS_COLOR = "#c62828"; // red
const RAIL_NEG_COLOR = "#212121"; // black
const RAIL_LINE_ALPHA = 0.3;

export class BreadboardRenderer {
  draw(ctx: CanvasRenderingContext2D): void {
    const cols = COL_MAX - COL_MIN + 1;
    const topRows = TOP_ROWS.length;
    const botRows = BOT_ROWS.length;

    // Total board dimensions
    const boardW = cols * HOLE_PITCH + 40;
    const boardH =
      (topRows + botRows) * HOLE_PITCH + CENTER_GAP + RAIL_OFFSET * 3 + 40;
    const boardX = BOARD_ORIGIN_X - 20;
    const boardY = BOARD_TOP_Y;

    // PCB background
    ctx.fillStyle = BOARD_COLOR;
    ctx.beginPath();
    ctx.roundRect(boardX, boardY, boardW, boardH, 8);
    ctx.fill();

    // Power rail strips (top)
    this._drawRailStrip(ctx, boardX, boardY + 8, boardW, "pos");
    this._drawRailStrip(ctx, boardX, boardY + 8 + HOLE_PITCH, boardW, "neg");

    // Power rail strips (bottom)
    const botStripY =
      BOARD_ORIGIN_Y + topRows * HOLE_PITCH + CENTER_GAP + botRows * HOLE_PITCH + 8;
    this._drawRailStrip(ctx, boardX, botStripY, boardW, "neg");
    this._drawRailStrip(ctx, boardX, botStripY + HOLE_PITCH, boardW, "pos");

    // Top rail holes
    this._drawRailHoles(ctx, boardY + 8, "pos");
    this._drawRailHoles(ctx, boardY + 8 + HOLE_PITCH, "neg");

    // Bottom rail holes
    this._drawRailHoles(ctx, botStripY, "neg");
    this._drawRailHoles(ctx, botStripY + HOLE_PITCH, "pos");

    // Main grid holes
    for (let col = COL_MIN; col <= COL_MAX; col++) {
      const x = BOARD_ORIGIN_X + (col - COL_MIN) * HOLE_PITCH;

      // Top half (rows a-e)
      for (let r = 0; r < topRows; r++) {
        const y = BOARD_ORIGIN_Y + r * HOLE_PITCH;
        this._drawHole(ctx, x, y);
      }

      // Center gap separator (visual only)
      if (col === COL_MIN) {
        const gapY = BOARD_ORIGIN_Y + topRows * HOLE_PITCH + CENTER_GAP / 2;
        ctx.strokeStyle = "rgba(0,0,0,0.2)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(boardX + 4, gapY);
        ctx.lineTo(boardX + boardW - 4, gapY);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Bottom half (rows f-j)
      for (let r = 0; r < botRows; r++) {
        const y =
          BOARD_ORIGIN_Y + topRows * HOLE_PITCH + CENTER_GAP + r * HOLE_PITCH;
        this._drawHole(ctx, x, y);
      }
    }

    // Column labels (every 5)
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "9px monospace";
    ctx.textAlign = "center";
    for (let col = COL_MIN; col <= COL_MAX; col += 5) {
      const x = BOARD_ORIGIN_X + (col - COL_MIN) * HOLE_PITCH;
      const y = BOARD_ORIGIN_Y - RAIL_OFFSET * 2 + 4;
      ctx.fillText(String(col), x, y);
    }

    // Row labels
    const allRows = [...TOP_ROWS, ...BOT_ROWS];
    const labelX = boardX + 4;
    ctx.textAlign = "left";
    ctx.font = "9px monospace";
    for (let r = 0; r < TOP_ROWS.length; r++) {
      const y = BOARD_ORIGIN_Y + r * HOLE_PITCH + 3;
      ctx.fillText(allRows[r]!, labelX, y);
    }
    for (let r = 0; r < BOT_ROWS.length; r++) {
      const y =
        BOARD_ORIGIN_Y + TOP_ROWS.length * HOLE_PITCH + CENTER_GAP + r * HOLE_PITCH + 3;
      ctx.fillText(allRows[TOP_ROWS.length + r]!, labelX, y);
    }
  }

  private _drawHole(ctx: CanvasRenderingContext2D, x: number, y: number): void {
    ctx.fillStyle = HOLE_COLOR;
    ctx.beginPath();
    ctx.arc(x, y, HOLE_RADIUS, 0, Math.PI * 2);
    ctx.fill();
  }

  private _drawRailStrip(
    ctx: CanvasRenderingContext2D,
    boardX: number,
    stripY: number,
    boardW: number,
    type: "pos" | "neg"
  ): void {
    ctx.fillStyle =
      type === "pos"
        ? `rgba(198,40,40,${RAIL_LINE_ALPHA})`
        : `rgba(33,33,33,${RAIL_LINE_ALPHA + 0.1})`;
    ctx.fillRect(boardX + 4, stripY - HOLE_PITCH / 2, boardW - 8, HOLE_PITCH);

    // Colored line
    ctx.strokeStyle = type === "pos" ? RAIL_POS_COLOR : RAIL_NEG_COLOR;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(boardX + 4, stripY);
    ctx.lineTo(boardX + boardW - 4, stripY);
    ctx.stroke();
  }

  private _drawRailHoles(
    ctx: CanvasRenderingContext2D,
    stripY: number,
    _type: "pos" | "neg"
  ): void {
    const cols = COL_MAX - COL_MIN + 1;
    for (let i = 0; i < cols; i++) {
      const x = BOARD_ORIGIN_X + i * HOLE_PITCH;
      this._drawHole(ctx, x, stripY);
    }
  }
}
