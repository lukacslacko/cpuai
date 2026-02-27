import { Circuit } from "../circuit/Circuit.js";
import { NetState } from "../circuit/types.js";

const MAX_ITERATIONS = 100;

export class Propagator {
  private readonly circuit: Circuit;

  constructor(circuit: Circuit) {
    this.circuit = circuit;
  }

  /** Relaxation loop: evaluate all components until no net state changes. */
  propagate(): void {
    for (let iter = 0; iter < MAX_ITERATIONS; iter++) {
      // Snapshot current net states
      const before = this.circuit.nets.map((n) => n.resolvedState);

      // Evaluate all components
      for (const comp of this.circuit.components) {
        comp.evaluate();
      }

      // Check for stability
      const after = this.circuit.nets.map((n) => n.resolvedState);
      let stable = true;
      for (let i = 0; i < before.length; i++) {
        if (before[i] !== after[i]) {
          stable = false;
          break;
        }
      }

      if (stable) return;
    }

    console.warn(
      `Propagator: circuit did not stabilize after ${MAX_ITERATIONS} iterations`
    );
  }

  /** Snapshot all net states as a map from net id to NetState. */
  snapshot(): Map<string, NetState> {
    const map = new Map<string, NetState>();
    for (const net of this.circuit.nets) {
      map.set(net.id, net.resolvedState);
    }
    return map;
  }
}
