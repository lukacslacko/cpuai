import { HoleCoord } from "../../breadboard/BreadboardModel.js";
import { Component } from "../../circuit/Component.js";
import { ComponentPlacement, PinHole } from "../PlacementResult.js";
import { HOLE_PITCH } from "../../breadboard/constants.js";
import { holeToWorld } from "../holeToWorld.js";

/**
 * Place an N-pin DIP straddling the center gap.
 *  Pins 1..(N/2)   → row e (top half), columns startCol .. startCol+(N/2-1)
 *  Pins (N/2+1)..N → row f (bot half), columns startCol+(N/2-1)..startCol (mirrored)
 *
 * Works for any even pin count (16, 20, ...).
 */
export function placeDip(
  component: Component,
  startCol: number,
  pinCount = 20
): { placement: ComponentPlacement; nextCol: number } {
  const halfPins = pinCount / 2;
  const pinHoles: PinHole[] = [];

  for (let i = 0; i < halfPins; i++) {
    const col = startCol + i;
    const hole: HoleCoord = { row: "e", col };
    pinHoles.push({ pinIndex: i, pinName: component.pins[i]?.name ?? `p${i}`, hole });
  }

  for (let i = 0; i < halfPins; i++) {
    const col = startCol + halfPins - 1 - i;
    const hole: HoleCoord = { row: "f", col };
    pinHoles.push({
      pinIndex: halfPins + i,
      pinName: component.pins[halfPins + i]?.name ?? `p${halfPins + i}`,
      hole,
    });
  }

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

/** Convenience alias kept for callers that pass an explicit 20-pin DIP. */
export function placeDip20(
  component: Component,
  startCol: number
): { placement: ComponentPlacement; nextCol: number } {
  return placeDip(component, startCol, 20);
}
