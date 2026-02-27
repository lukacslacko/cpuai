import { AnyHole } from "../breadboard/BreadboardModel.js";
import { Component } from "../circuit/Component.js";
import { Net } from "../circuit/Net.js";

export type ComponentType =
  | "battery"
  | "led"
  | "resistor"
  | "button"
  | "dip20"
  | "unknown";

export interface PinHole {
  pinIndex: number;
  pinName: string;
  hole: AnyHole;
}

export interface ComponentPlacement {
  component: Component;
  componentType: ComponentType;
  /** World pixel position of the component's visual center (for rendering) */
  x: number;
  y: number;
  /** Which hole each pin is placed at */
  pinHoles: PinHole[];
  /** Extra metadata per component type */
  meta?: Record<string, unknown>;
}

export interface WirePlacement {
  net: Net;
  /** Start hole (grid hole coord) */
  fromHole: AnyHole;
  /** End hole (grid hole coord) */
  toHole: AnyHole;
  /** Palette color for this net */
  color: string;
}

export interface LayoutResult {
  placements: ComponentPlacement[];
  wires: WirePlacement[];
  /** Total width used (in holes) */
  columnsUsed: number;
}
