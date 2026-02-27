import { AnyHole, HoleCoord } from "../breadboard/BreadboardModel.js";
import { HOLE_PITCH, TOP_ROWS } from "../breadboard/constants.js";

/** Pixel offsets for the breadboard origin (top-left of hole a1) */
export const BOARD_ORIGIN_X = 100;
export const BOARD_ORIGIN_Y = 80;

/** Gap between top and bottom halves (the center gap) in pixels */
export const CENTER_GAP = HOLE_PITCH * 2;

/** Power rail row offset from main grid */
export const RAIL_OFFSET = HOLE_PITCH * 1.5;

/** Y of the top edge of the PCB board rect — shared with BreadboardRenderer */
export const BOARD_TOP_Y = BOARD_ORIGIN_Y - RAIL_OFFSET * 2 - 10;

const ROW_ORDER: Record<string, number> = {
  a: 0,
  b: 1,
  c: 2,
  d: 3,
  e: 4,
  f: 5,
  g: 6,
  h: 7,
  i: 8,
  j: 9,
};

export function holeToWorld(hole: AnyHole): { x: number; y: number } {
  if (typeof hole === "string") {
    // Power rail symbolic coords — Y values must exactly match BreadboardRenderer rail hole positions
    // boardY = BOARD_TOP_Y = BOARD_ORIGIN_Y - RAIL_OFFSET*2 - 10
    // top pos rail: boardY + 8
    // top neg rail: boardY + 8 + HOLE_PITCH
    // botStripY    = BOARD_ORIGIN_Y + 10*HOLE_PITCH + CENTER_GAP + 8
    // bot neg rail: botStripY
    // bot pos rail: botStripY + HOLE_PITCH
    const x = BOARD_ORIGIN_X;
    const botStripY = BOARD_ORIGIN_Y + 10 * HOLE_PITCH + CENTER_GAP + 8;
    switch (hole) {
      case "rail:top:pos":
        return { x, y: BOARD_TOP_Y + 8 };
      case "rail:top:neg":
        return { x, y: BOARD_TOP_Y + 8 + HOLE_PITCH };
      case "rail:bot:neg":
        return { x, y: botStripY };
      case "rail:bot:pos":
        return { x, y: botStripY + HOLE_PITCH };
    }
  }

  const { row, col } = hole as HoleCoord;
  const rowIdx = ROW_ORDER[row] ?? 0;

  const x = BOARD_ORIGIN_X + (col - 1) * HOLE_PITCH;

  let y: number;
  if ((TOP_ROWS as readonly string[]).includes(row)) {
    // Top half: rows a(0)..e(4)
    y = BOARD_ORIGIN_Y + rowIdx * HOLE_PITCH;
  } else {
    // Bottom half: rows f(5)..j(9), with center gap
    y = BOARD_ORIGIN_Y + 5 * HOLE_PITCH + CENTER_GAP + (rowIdx - 5) * HOLE_PITCH;
  }

  return { x, y };
}
