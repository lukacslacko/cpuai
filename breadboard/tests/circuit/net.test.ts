import { describe, it, expect, beforeEach } from "vitest";
import { Net } from "../../src/circuit/Net.js";
import { NetState } from "../../src/circuit/types.js";

describe("Net resolution", () => {
  let net: Net;

  beforeEach(() => {
    net = new Net("test");
  });

  it("resolves FLOAT when no drivers", () => {
    expect(net.resolvedState).toBe(NetState.FLOAT);
    expect(net.logicLevel).toBe(false);
  });

  it("resolves HIGH when driven HIGH", () => {
    net.drive("a", NetState.HIGH);
    expect(net.resolvedState).toBe(NetState.HIGH);
    expect(net.logicLevel).toBe(true);
  });

  it("resolves LOW when driven LOW", () => {
    net.drive("a", NetState.LOW);
    expect(net.resolvedState).toBe(NetState.LOW);
    expect(net.logicLevel).toBe(false);
  });

  it("resolves CONFLICT when driven both HIGH and LOW", () => {
    net.drive("a", NetState.HIGH);
    net.drive("b", NetState.LOW);
    expect(net.resolvedState).toBe(NetState.CONFLICT);
  });

  it("resolves HIGH when multiple HIGH drivers", () => {
    net.drive("a", NetState.HIGH);
    net.drive("b", NetState.HIGH);
    expect(net.resolvedState).toBe(NetState.HIGH);
  });

  it("returns to FLOAT after unDrive", () => {
    net.drive("a", NetState.HIGH);
    net.unDrive("a");
    expect(net.resolvedState).toBe(NetState.FLOAT);
  });

  it("resolves remaining driver after one unDrives", () => {
    net.drive("a", NetState.HIGH);
    net.drive("b", NetState.LOW);
    expect(net.resolvedState).toBe(NetState.CONFLICT);
    net.unDrive("b");
    expect(net.resolvedState).toBe(NetState.HIGH);
  });

  it("unDrive of non-existent driver is a no-op", () => {
    net.drive("a", NetState.HIGH);
    net.unDrive("nonexistent");
    expect(net.resolvedState).toBe(NetState.HIGH);
  });
});
