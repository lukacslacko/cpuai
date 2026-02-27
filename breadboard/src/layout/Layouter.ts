import { Circuit } from "../circuit/Circuit.js";
import { Component } from "../circuit/Component.js";
import { Battery } from "../circuit/components/Battery.js";
import { LED } from "../circuit/components/LED.js";
import { Resistor } from "../circuit/components/Resistor.js";
import { Button } from "../circuit/components/Button.js";
import { IC74HC573 } from "../circuit/components/IC74HC573.js";
import { IC74HC574 } from "../circuit/components/IC74HC574.js";
import { ComponentPlacement, LayoutResult } from "./PlacementResult.js";
import { placeBattery } from "./strategies/BatteryStrategy.js";
import { placeButton } from "./strategies/ButtonStrategy.js";
import { placeDip20 } from "./strategies/DipStrategy.js";
import { placeTwoPin } from "./strategies/TwoPinStrategy.js";
import { WireRouter } from "./WireRouter.js";

export class Layouter {
  private readonly router: WireRouter;

  constructor() {
    this.router = new WireRouter();
  }

  layout(circuit: Circuit): LayoutResult {
    const placements: ComponentPlacement[] = [];
    let col = 3; // Start at column 3 to leave margin

    for (const comp of circuit.components) {
      const result = this._placeComponent(comp, col);
      if (result) {
        placements.push(result.placement);
        if (result.nextCol > col) col = result.nextCol;
      }
    }

    const wires = this.router.route(circuit, placements);

    return {
      placements,
      wires,
      columnsUsed: col,
    };
  }

  private _placeComponent(
    comp: Component,
    col: number
  ): { placement: ComponentPlacement; nextCol: number } | null {
    if (comp instanceof Battery) {
      return placeBattery(comp);
    }

    if (comp instanceof LED) {
      return placeTwoPin(comp, col, "led");
    }

    if (comp instanceof Resistor) {
      return placeTwoPin(comp, col, "resistor");
    }

    if (comp instanceof Button) {
      return placeButton(comp, col);
    }

    if (comp instanceof IC74HC573 || comp instanceof IC74HC574) {
      return placeDip20(comp, col);
    }

    console.warn(`Layouter: unknown component type for ${comp.name}`);
    return null;
  }
}
