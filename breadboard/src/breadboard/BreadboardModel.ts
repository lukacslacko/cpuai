import { COL_MAX, COL_MIN, RowName, TOP_ROWS } from "./constants.js";

export type HoleCoord = {
  row: RowName;
  col: number;
};

/** Symbolic power rail hole coords */
export type PowerRailCoord =
  | "rail:top:pos"
  | "rail:top:neg"
  | "rail:bot:pos"
  | "rail:bot:neg";

export type AnyHole = HoleCoord | PowerRailCoord;

function isPowerRail(h: AnyHole): h is PowerRailCoord {
  return typeof h === "string";
}

export class BreadboardModel {
  /** Maps a hole to its electrical nodeId.
   *
   * Main grid: all 5 holes in the same column + half share one node.
   * Node id: `main:{col}:{top|bot}`
   *
   * Power rails: each continuous strip (broken at col 31/32 in reality,
   * but for simplicity we model them as single nodes).
   */
  nodeId(hole: AnyHole): string {
    if (isPowerRail(hole)) return hole;

    const { row, col } = hole;
    if (col < COL_MIN || col > COL_MAX) {
      throw new RangeError(`Column ${col} out of range [${COL_MIN}, ${COL_MAX}]`);
    }

    const half = (TOP_ROWS as readonly string[]).includes(row) ? "top" : "bot";
    return `main:${col}:${half}`;
  }

  /** Return all valid hole coordinates for the main grid */
  allHoles(): HoleCoord[] {
    const rows: RowName[] = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"];
    const holes: HoleCoord[] = [];
    for (const row of rows) {
      for (let col = COL_MIN; col <= COL_MAX; col++) {
        holes.push({ row, col });
      }
    }
    return holes;
  }
}
