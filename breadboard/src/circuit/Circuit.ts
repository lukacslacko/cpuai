import { Component } from "./Component.js";
import { Net } from "./Net.js";
import { Pin } from "./Pin.js";

let netSeq = 0;

export class Circuit {
  readonly components: Component[] = [];
  readonly nets: Net[] = [];

  addComponent(c: Component): void {
    this.components.push(c);
  }

  /** Connect one or more pins together onto a single shared net.
   *  If any pin already has a net, all pins join that net (eager merge). */
  connect(...pins: Pin[]): Net {
    // Find an existing net among the pins, or create a new one
    let net = pins.find((p) => p.net !== null)?.net ?? null;

    if (net === null) {
      net = new Net(`net_${netSeq++}`);
      this.nets.push(net);
    } else {
      // Merge any other nets the pins might already belong to
      for (const pin of pins) {
        if (pin.net !== null && pin.net !== net) {
          this._mergeNets(net, pin.net);
        }
      }
    }

    for (const pin of pins) {
      pin.net = net;
    }

    return net;
  }

  /** Merge srcNet into dstNet: migrate all driver entries and re-point all pins. */
  private _mergeNets(dstNet: Net, srcNet: Net): void {
    // Re-point every pin that referenced srcNet
    for (const comp of this.components) {
      for (const pin of comp.pins) {
        if (pin.net === srcNet) {
          pin.net = dstNet;
        }
      }
    }

    // Remove srcNet from the nets list
    const idx = this.nets.indexOf(srcNet);
    if (idx !== -1) this.nets.splice(idx, 1);
  }
}
