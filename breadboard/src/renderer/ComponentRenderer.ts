import { ComponentPlacement } from "../layout/PlacementResult.js";
import { drawDip } from "./components/DipRenderer.js";
import { drawLED } from "./components/LEDRenderer.js";
import { drawButton } from "./components/ButtonRenderer.js";
import { drawResistor } from "./components/ResistorRenderer.js";
import { drawBattery } from "./components/BatteryRenderer.js";

export class ComponentRenderer {
  draw(ctx: CanvasRenderingContext2D, placements: ComponentPlacement[]): void {
    for (const p of placements) {
      switch (p.componentType) {
        case "dip20":
          drawDip(ctx, p);
          break;
        case "led":
          drawLED(ctx, p);
          break;
        case "button":
          drawButton(ctx, p);
          break;
        case "resistor":
          drawResistor(ctx, p);
          break;
        case "battery":
          drawBattery(ctx, p);
          break;
        default:
          break;
      }
    }
  }
}
