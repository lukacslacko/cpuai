import { HoleCoord } from "../../breadboard/BreadboardModel.js";
import { Component } from "../../circuit/Component.js";
import { ComponentPlacement, ComponentType, PinHole } from "../PlacementResult.js";
import { holeToWorld } from "../holeToWorld.js";

/** Place a 2-pin component (LED, Resistor) in row c at two consecutive columns. */
export function placeTwoPin(
  component: Component,
  startCol: number,
  componentType: ComponentType
): { placement: ComponentPlacement; nextCol: number } {
  const holeA: HoleCoord = { row: "c", col: startCol };
  const holeB: HoleCoord = { row: "c", col: startCol + 1 };

  const pinHoles: PinHole[] = [
    { pinIndex: 0, pinName: component.pins[0]?.name ?? "a", hole: holeA },
    { pinIndex: 1, pinName: component.pins[1]?.name ?? "b", hole: holeB },
  ];

  const posA = holeToWorld(holeA);
  const posB = holeToWorld(holeB);

  const placement: ComponentPlacement = {
    component,
    componentType,
    x: (posA.x + posB.x) / 2,
    y: (posA.y + posB.y) / 2,
    pinHoles,
  };

  return { placement, nextCol: startCol + 3 };
}
