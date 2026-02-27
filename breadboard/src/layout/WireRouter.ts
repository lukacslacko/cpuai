import { BreadboardModel, AnyHole } from "../breadboard/BreadboardModel.js";
import { Circuit } from "../circuit/Circuit.js";
import { Net } from "../circuit/Net.js";
import { ComponentPlacement, WirePlacement } from "./PlacementResult.js";

const NET_COLORS: Record<string, string> = {
  vcc: "#e53935",
  gnd: "#212121",
};

const PALETTE = [
  "#ff9800",
  "#ffeb3b",
  "#4caf50",
  "#2196f3",
  "#9c27b0",
  "#ffffff",
  "#ff5722",
  "#00bcd4",
];

export class WireRouter {
  private readonly bbModel: BreadboardModel;

  constructor() {
    this.bbModel = new BreadboardModel();
  }

  route(
    circuit: Circuit,
    placements: ComponentPlacement[]
  ): WirePlacement[] {
    // Build map: net → list of (hole) that are placed for each pin
    const netHoles = new Map<Net, AnyHole[]>();

    for (const p of placements) {
      for (const ph of p.pinHoles) {
        const pin = p.component.pins[ph.pinIndex];
        if (!pin?.net) continue;

        const holes = netHoles.get(pin.net) ?? [];
        holes.push(ph.hole);
        netHoles.set(pin.net, holes);
      }
    }

    // Assign colors to nets
    const netColor = new Map<Net, string>();
    let paletteIdx = 0;
    for (const net of circuit.nets) {
      const lowerName = net.id.toLowerCase();
      if (lowerName.includes("vcc") || lowerName.includes("pos")) {
        netColor.set(net, NET_COLORS.vcc!);
      } else if (lowerName.includes("gnd") || lowerName.includes("neg")) {
        netColor.set(net, NET_COLORS.gnd!);
      } else {
        // Check pin names
        const holes = netHoles.get(net);
        const anyVcc = holes?.some(
          (h) => typeof h === "string" && h.includes("pos")
        );
        const anyGnd = holes?.some(
          (h) => typeof h === "string" && h.includes("neg")
        );
        if (anyVcc) {
          netColor.set(net, NET_COLORS.vcc!);
        } else if (anyGnd) {
          netColor.set(net, NET_COLORS.gnd!);
        } else {
          netColor.set(net, PALETTE[paletteIdx % PALETTE.length]!);
          paletteIdx++;
        }
      }
    }

    // Build wires: for each net, group holes by nodeId.
    // If >1 distinct nodeId, add jump wires between group representatives.
    const wires: WirePlacement[] = [];

    for (const [net, holes] of netHoles) {
      const color = netColor.get(net) ?? "#ffffff";

      // Group holes by nodeId
      const groups = new Map<string, AnyHole[]>();
      for (const hole of holes) {
        const nodeId = this.bbModel.nodeId(hole);
        const g = groups.get(nodeId) ?? [];
        g.push(hole);
        groups.set(nodeId, g);
      }

      if (groups.size <= 1) continue; // All already connected

      // Take one representative per group and wire them linearly
      const reps: AnyHole[] = [];
      for (const g of groups.values()) {
        reps.push(g[0]!);
      }

      for (let i = 0; i < reps.length - 1; i++) {
        wires.push({
          net,
          fromHole: reps[i]!,
          toHole: reps[i + 1]!,
          color,
        });
      }
    }

    return wires;
  }
}
