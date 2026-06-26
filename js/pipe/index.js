import { app } from "/scripts/app.js";

// ── Node IDs ──
const PIPE_IN = "PipeIN988";
const PIPE_OUT = "PipeOUT988";
const PIPE_TYPE = "PIPE988";

// ── Slot limits ──
const MAX_SLOTS = 10;
const MIN_SLOTS = 1;
const PIPE_SLOT = 0;

// ── Colour map (fallback when LGraphCanvas.link_type_colors lacks an entry) ──
const FALLBACK_COLORS = {
    PIPE988:         [0.659, 0.478, 0.831],
    IMAGE:          [0.247, 0.494, 0.871],
    MASK:           [0.694, 0.831, 0.184],
    LATENT:         [0.831, 0.153, 0.486],
    MODEL:          [0.592, 0.463, 0.227],
    CONDITIONING:   [0.063, 0.722, 0.722],
    CLIP:           [0.914, 0.811, 0.231],
    CLIP_VISION:    [0.914, 0.811, 0.231],
    VAE:            [0.600, 0.337, 0.666],
    CONTROL_NET:    [0.831, 0.153, 0.153],
    STRING:         [0.592, 0.592, 0.592],
    INT:            [0.500, 0.500, 0.500],
    FLOAT:          [0.500, 0.500, 0.500],
    BOOLEAN:        [0.800, 0.500, 0.100],
    AUDIO:          [0.300, 0.600, 0.800],
    SIGMAS:         [0.500, 0.200, 0.700],
    UPSCALE_MODEL:  [0.400, 0.600, 0.300],
    STYLE_MODEL:    [0.300, 0.500, 0.700],
};

// ── Helpers ──

function colorForType(type) {
    if (!type || type === "*") return null;
    const fromLG = LGraphCanvas?.link_type_colors?.[type];
    if (fromLG) return fromLG;
    return FALLBACK_COLORS[type] || null;
}

function paintSlot(slot, typeName, sourceName) {
    if (!slot) return;
    const isPipe = slot.type === PIPE_TYPE;
    if (isPipe) return;
    const isConcrete = typeName && typeName !== "*" && typeName !== "ANY";
    slot.type = isConcrete ? typeName : "*";
    const label = isConcrete ? (sourceName || typeName) : "ANY";
    if (slot.label !== label) {
        slot.label = label;
        slot.name = label;
    }
}

function paintLink(graph, linkId, typeName) {
    if (!graph || linkId == null) return;
    const link = graph.links[linkId];
    if (!link) return;
    const c = colorForType(typeName);
    if (c) link.color = c;
}

// ──────────────────────────────────
//  Pipe IN 988  — autogrow inputs + colour + single pipe output
// ──────────────────────────────────
app.registerExtension({
    name: "988.Pipe",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== PIPE_IN && nodeData.name !== PIPE_OUT) return;

        // ──────── Pipe IN ────────
        if (nodeData.name === PIPE_IN) {
            function readConnectedSource(node, slot) {
                const inp = node.inputs[slot];
                if (!inp?.link) return null;
                const link = node.graph?.links[inp.link];
                if (!link) return null;
                const src = node.graph?.nodes.find(n => n.id === link.origin_id);
                if (src && src.outputs[link.origin_slot]) {
                    const out = src.outputs[link.origin_slot];
                    const type = out.type === PIPE_TYPE ? PIPE_TYPE : out.type;
                    const name = out.label || out.name || type;
                    return { type, name };
                }
                return { type: link.type || "*", name: link.type || "*" };
            }

            function addPipeSlot(node) {
                if (!node.inputs.some(i => i.name === "pipe")) {
                    node.addInput("pipe", PIPE_TYPE);
                }
            }

            function ensurePipeOutput(node) {
                if (!node.outputs.some(o => o.name === "pipe")) {
                    node.addOutput("pipe", PIPE_TYPE);
                }
            }

            function rebalanceSlots(node) {
                if (!node._graphLoaded) return;

                addPipeSlot(node);
                ensurePipeOutput(node);

                let connected = 0;
                for (let i = PIPE_SLOT + 1; i < node.inputs.length; i++) {
                    if (node.inputs[i].link) connected++;
                }
                const desired = Math.min(MAX_SLOTS, Math.max(MIN_SLOTS, connected + 1));

                while (node.inputs.length - (PIPE_SLOT + 1) > desired) {
                    const idx = node.inputs.length - 1;
                    const si = idx - (PIPE_SLOT + 1);
                    delete node._pipeTypes?.[si];
                    delete node._pipeNames?.[si];
                    node.removeInput(idx);
                }
                while (node.inputs.length - (PIPE_SLOT + 1) < desired) {
                    const si = node.inputs.length - (PIPE_SLOT + 1);
                    node.addInput(`input_${si}`, "*");
                }
                for (let i = PIPE_SLOT + 1; i < node.inputs.length; i++) {
                    const si = i - (PIPE_SLOT + 1);
                    paintSlot(node.inputs[i], node._pipeTypes?.[si], node._pipeNames?.[si]);
                }

                node.size = node.computeSize();
            }

            const origCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const res = origCreated?.apply(this, arguments);
                this._pipeTypes = {};
                this._pipeNames = {};
                this._graphLoaded = false;

                while (this.inputs.length > PIPE_SLOT) {
                    this.removeInput(this.inputs.length - 1);
                }
                while (this.outputs.length > PIPE_SLOT) {
                    this.removeOutput(this.outputs.length - 1);
                }
                addPipeSlot(this);
                ensurePipeOutput(this);

                setTimeout(() => {
                    this._graphLoaded = true;
                    for (let i = PIPE_SLOT + 1; i < this.inputs.length; i++) {
                        const src = readConnectedSource(this, i);
                        if (src && src.type !== PIPE_TYPE) {
                            const si = i - (PIPE_SLOT + 1);
                            this._pipeTypes[si] = src.type;
                            this._pipeNames[si] = src.name;
                        }
                    }
                    rebalanceSlots(this);
                }, 0);
                return res;
            };

            const origConn = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (inputType, slot, isConnected, link_info, outputSlot) {
                const res = origConn?.apply(this, arguments);

                if (inputType === 1 || inputType === true) {
                    if (!this._pipeTypes) this._pipeTypes = {};
                    if (!this._pipeNames) this._pipeNames = {};

                    if (slot === PIPE_SLOT) {
                        if (!this._graphLoaded) return res;
                        setTimeout(() => {
                            if (isConnected) {
                                const link = this.graph?.links[link_info?.id];
                                if (link) {
                                    const c = colorForType(PIPE_TYPE);
                                    if (c) link.color = c;
                                }
                            }
                            rebalanceSlots(this);
                        }, 0);
                        return res;
                    }

                    const si = slot - (PIPE_SLOT + 1);

                    if (isConnected && link_info) {
                        const src = readConnectedSource(this, slot);
                        if (src) {
                            this._pipeTypes[si] = src.type;
                            this._pipeNames[si] = src.name;
                            if (this._graphLoaded) paintLink(this.graph, link_info.id, src.type);
                        }
                    } else {
                        delete this._pipeTypes?.[si];
                        delete this._pipeNames?.[si];
                        const isLastSignal = slot === this.inputs.length - 1;
                        if (!isLastSignal && this.inputs[slot] && !this.inputs[slot].link) {
                            this.removeInput(slot);
                            const compactedTypes = {};
                            const compactedNames = {};
                            for (const k in this._pipeTypes) {
                                const nk = Number(k);
                                if (nk < si) {
                                    compactedTypes[nk] = this._pipeTypes[nk];
                                } else {
                                    compactedTypes[nk - 1] = this._pipeTypes[nk];
                                }
                            }
                            for (const k in this._pipeNames) {
                                const nk = Number(k);
                                if (nk < si) {
                                    compactedNames[nk] = this._pipeNames[nk];
                                } else {
                                    compactedNames[nk - 1] = this._pipeNames[nk];
                                }
                            }
                            this._pipeTypes = compactedTypes;
                            this._pipeNames = compactedNames;
                        }
                    }

                    if (this.inputs[slot]) {
                        paintSlot(this.inputs[slot], this._pipeTypes?.[si], this._pipeNames?.[si]);
                    }

                    if (this._graphLoaded) rebalanceSlots(this);
                }
                return res;
            };
        }

        // ──────── Pipe OUT ────────
        if (nodeData.name === PIPE_OUT) {
            // Pipe passthrough sits at the LAST slot (index MAX_SLOTS) so signal
            // output indices 0..MAX_SLOTS-1 never shift — backward compatible.
            // All MAX_SLOTS signals are always shown (no autogrow) to keep indices
            // stable across saves/loads.
            const PIPE_OUT_SLOT = MAX_SLOTS;

            function traceSourcePipe(node) {
                let current = node;
                for (let depth = 0; depth < 20; depth++) {
                    const inp = current.inputs[PIPE_SLOT];
                    if (!inp?.link) return null;
                    const link = current.graph?.links[inp.link];
                    if (!link) return null;
                    const src = current.graph?.nodes.find(n => n.id === link.origin_id);
                    if (!src) return null;
                    if (src._pipeTypes) return src;
                    if (link.type === PIPE_TYPE) {
                        current = src;
                        continue;
                    }
                    return null;
                }
                return null;
            }

            function setOutputLabel(out, typeName, sourceName) {
                if (!out) return;
                const isConcrete = typeName && typeName !== "*" && typeName !== "ANY" && typeName !== PIPE_TYPE;
                out.type = isConcrete ? typeName : "*";
                const label = isConcrete ? (sourceName || typeName) : "ANY";
                if (out.label !== label) {
                    out.label = label;
                    out.name = label;
                }
            }

            function syncOutputs(node) {
                const src = traceSourcePipe(node);
                const types = src?._pipeTypes ?? null;
                const names = src?._pipeNames ?? null;

                // Ensure all signal slots 0..MAX_SLOTS-1 exist
                while (node.outputs.length < PIPE_OUT_SLOT) {
                    node.addOutput("ANY", "*");
                }
                // Ensure pipe passthrough at the last slot
                while (node.outputs.length <= PIPE_OUT_SLOT) {
                    node.addOutput("ANY", "*");
                }

                // Paint signal outputs 0..MAX_SLOTS-1
                for (let i = 0; i < MAX_SLOTS; i++) {
                    setOutputLabel(node.outputs[i], types?.[i], names?.[i]);
                }

                // Paint pipe passthrough at the last slot
                const pipeOut = node.outputs[PIPE_OUT_SLOT];
                pipeOut.type = PIPE_TYPE;
                if (pipeOut.label !== "pipe") {
                    pipeOut.label = "pipe";
                    pipeOut.name = "pipe";
                }

                node.size = node.computeSize();
            }

            const origCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const res = origCreated?.apply(this, arguments);

                if (!this.widgets) this.widgets = [];
                if (!this.widgets.some(w => w.name === "\u21BB")) {
                    this.addWidget("button", "\u21BB", null, () => {
                        syncOutputs(this);
                    });
                }

                syncOutputs(this);
                return res;
            };

            const origMenu = nodeType.prototype.getExtraMenuOptions;
            nodeType.prototype.getExtraMenuOptions = function (_, options) {
                origMenu?.apply(this, arguments);
                options.unshift({
                    content: "\u21BB Refresh outputs",
                    callback: () => {
                        syncOutputs(this);
                        this.graph?.setDirtyCanvas(true, true);
                    },
                });
            };

            const origConn = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (inputType, slot, isConnected, link_info, outputSlot) {
                const res = origConn?.apply(this, arguments);
                if ((inputType === 1 || inputType === true) && slot === PIPE_SLOT) {
                    if (isConnected && link_info) {
                        const c = colorForType(PIPE_TYPE);
                        if (c) {
                            const link = this.graph?.links[link_info.id];
                            if (link) link.color = c;
                        }
                    }
                    syncOutputs(this);
                }
                return res;
            };
        }
    },
});
