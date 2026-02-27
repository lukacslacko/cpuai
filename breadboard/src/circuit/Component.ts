import { Pin } from "./Pin.js";
import { EdgeKind } from "./types.js";

let nextId = 0;

export abstract class Component {
  readonly id: string;
  readonly name: string;
  readonly pins: Pin[];

  constructor(name: string, pins: Pin[]) {
    this.id = `${name}_${nextId++}`;
    this.name = name;
    this.pins = pins;
  }

  /** Called every propagation iteration. Reads input pins, drives output nets. */
  abstract evaluate(): void;

  /** Called on clock transitions for sequential logic. Default: no-op. */
  onClockEdge(_edge: EdgeKind): void {}
}
