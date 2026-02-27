import { HoleCoord } from "../../breadboard/BreadboardModel.js";
import { Component } from "../../circuit/Component.js";
import { ComponentPlacement, PinHole } from "../PlacementResult.js";
import { HOLE_PITCH } from "../../breadboard/constants.js";
import { holeToWorld } from "../holeToWorld.js";

/** Place a 20-pin DIP straddling the center gap.
 *  Pins 1-10 → row e (top half), columns N..N+9 (pin 1 at left)
 *  Pins 11-20 → row f (bot half), columns N+9..N   (mirrored)
 */
export function placeDip20(
  component: Component,
  startCol: number
): { placement: ComponentPlacement; nextCol: number } {
  const PIN_COUNT = 20;
  const halfPins = PIN_COUNT / 2; // 10
  const pinHoles: PinHole[] = [];

  for (let i = 0; i < halfPins; i++) {
    // Pins 0-9 (physical pins 1-10) → row e
    const col = startCol + i;
    const hole: HoleCoord = { row: "e", col };
    pinHoles.push({ pinIndex: i, pinName: component.pins[i]?.name ?? `p${i}`, hole });
  }

  for (let i = 0; i < halfPins; i++) {
    // Pins 10-19 (physical pins 11-20) → row f, mirrored
    const col = startCol + halfPins - 1 - i;
    const hole: HoleCoord = { row: "f", col };
    pinHoles.push({
      pinIndex: halfPins + i,
      pinName: component.pins[halfPins + i]?.name ?? `p${halfPins + i}`,
      hole,
    });
  }

  // Visual center: midpoint between first and last pin columns, between rows e and f
  const centerCol = startCol + (halfPins - 1) / 2;
  const topHole = holeToWorld({ row: "e", col: centerCol });
  const botHole = holeToWorld({ row: "f", col: centerCol });
  const x = topHole.x;
  const y = (topHole.y + botHole.y) / 2;

  const placement: ComponentPlacement = {
    component,
    componentType: "dip20",
    x,
    y,
    pinHoles,
    meta: { startCol, halfPins, widthPx: halfPins * HOLE_PITCH },
  };

  return { placement, nextCol: startCol + halfPins + 2 };
}
