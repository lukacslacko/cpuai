import { describe, it, expect, beforeEach } from "vitest";
import { Button } from "../../src/circuit/components/Button.js";
import { Circuit } from "../../src/circuit/Circuit.js";
import { NetState } from "../../src/circuit/types.js";

describe("Button", () => {
  let button: Button;
  let circuit: Circuit;

  beforeEach(() => {
    button = new Button();
    circuit = new Circuit();
    circuit.addComponent(button);
  });

  it("does not pass-through when open (not pressed)", () => {
    const netA = circuit.connect(button.a);
    circuit.connect(button.b);

    netA.drive("src", NetState.HIGH);
    button.evaluate();

    // b should remain FLOAT since button is open
    expect(button.b.resolvedState).toBe(NetState.FLOAT);
  });

  it("passes HIGH from a to b when pressed", () => {
    const netA = circuit.connect(button.a);
    circuit.connect(button.b);

    netA.drive("src", NetState.HIGH);
    button.pressed = true;
    button.evaluate();

    expect(button.b.resolvedState).toBe(NetState.HIGH);
  });

  it("passes LOW from a to b when pressed", () => {
    const netA = circuit.connect(button.a);
    circuit.connect(button.b);

    netA.drive("src", NetState.LOW);
    button.pressed = true;
    button.evaluate();

    expect(button.b.resolvedState).toBe(NetState.LOW);
  });

  it("passes signal bidirectionally (b → a) when pressed", () => {
    circuit.connect(button.a);
    const netB = circuit.connect(button.b);

    netB.drive("src", NetState.HIGH);
    button.pressed = true;
    button.evaluate();

    expect(button.a.resolvedState).toBe(NetState.HIGH);
  });

  it("releases drive when button opens", () => {
    const netA = circuit.connect(button.a);
    circuit.connect(button.b);

    netA.drive("src", NetState.HIGH);

    button.pressed = true;
    button.evaluate();
    expect(button.b.resolvedState).toBe(NetState.HIGH);

    button.pressed = false;
    button.evaluate();
    expect(button.b.resolvedState).toBe(NetState.FLOAT);
  });

  it("starts unpressed by default", () => {
    expect(button.pressed).toBe(false);
  });
});
