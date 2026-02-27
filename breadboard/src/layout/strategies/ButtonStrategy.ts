import { HoleCoord } from "../../breadboard/BreadboardModel.js";
import { Component } from "../../circuit/Component.js";
import { ComponentPlacement, PinHole } from "../PlacementResult.js";
import { holeToWorld } from "../holeToWorld.js";

/** Place a button straddling the center gap: pin a → row e, pin b → row f, same column. */
export function placeButton(
  component: Component,
  startCol: number
): { placement: ComponentPlacement; nextCol: number } {
  const holeA: HoleCoord = { row: "e", col: startCol };
  const holeB: HoleCoord = { row: "f", col: startCol };

  const pinHoles: PinHole[] = [
    { pinIndex: 0, pinName: component.pins[0]?.name ?? "a", hole: holeA },
    { pinIndex: 1, pinName: component.pins[1]?.name ?? "b", hole: holeB },
  ];

  const posA = holeToWorld(holeA);
  const posB = holeToWorld(holeB);

  const placement: ComponentPlacement = {
    component,
    componentType: "button",
    x: (posA.x + posB.x) / 2,
    y: (posA.y + posB.y) / 2,
    pinHoles,
  };

  return { placement, nextCol: startCol + 2 };
}
