/** Distance between hole centers in pixels */
export const HOLE_PITCH = 20;

/** Number of main-grid columns (1-based) */
export const COL_MIN = 1;
export const COL_MAX = 90;
export const COL_COUNT = COL_MAX - COL_MIN + 1;

/** Row names for the two halves of the main grid */
export const TOP_ROWS = ["a", "b", "c", "d", "e"] as const;
export const BOT_ROWS = ["f", "g", "h", "i", "j"] as const;
export type TopRow = (typeof TOP_ROWS)[number];
export type BotRow = (typeof BOT_ROWS)[number];
export type RowName = TopRow | BotRow;

/** How many holes per column strip (5 in each half) */
export const ROWS_PER_STRIP = 5;

/** Power rail layout constants */
export const POWER_RAIL_ROWS = 2; // positive (+) and negative (-)
