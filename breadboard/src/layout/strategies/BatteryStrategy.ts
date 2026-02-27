import { PowerRailCoord } from "../../breadboard/BreadboardModel.js";
import { Component } from "../../circuit/Component.js";
import { ComponentPlacement, PinHole } from "../PlacementResult.js";
import { holeToWorld, BOARD_ORIGIN_X, BOARD_ORIGIN_Y, RAIL_OFFSET } from "../holeToWorld.js";

/** Map battery VCC/GND to symbolic power rail anchors. No holes consumed. */
export function placeBattery(
  component: Component
): { placement: ComponentPlacement; nextCol: number } {
  const vccHole: PowerRailCoord = "rail:top:pos";
  const gndHole: PowerRailCoord = "rail:top:neg";

  const pinHoles: PinHole[] = [
    { pinIndex: 0, pinName: component.pins[0]?.name ?? "VCC", hole: vccHole },
    { pinIndex: 1, pinName: component.pins[1]?.name ?? "GND", hole: gndHole },
  ];

  const posVcc = holeToWorld(vccHole);
  const posGnd = holeToWorld(gndHole);

  const placement: ComponentPlacement = {
    component,
    componentType: "battery",
    x: BOARD_ORIGIN_X - 60,
    y: (posVcc.y + posGnd.y) / 2,
    pinHoles,
  };

  void BOARD_ORIGIN_Y;
  void RAIL_OFFSET;

  return { placement, nextCol: 0 };
}
