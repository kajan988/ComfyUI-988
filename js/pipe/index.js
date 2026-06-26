import { app } from "/scripts/app.js";

// ── Node IDs ──
const PIPE_IN = "PipeIN988";
const PIPE_OUT = "PipeOUT988";
const PIPE_TYPE = "PIPE988";

// ── Slot limits ──
const MAX_SLOTS = 10;
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

// ──────────────────────────────────
//  Pipe IN/OUT 988
// ──────────────────────────────────
app.registerExtension({
    name: "988.Pipe",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== PIPE_IN && nodeData.name !== PIPE_OUT) return;

        // ──────── Pipe IN — stable sockets, dynamic labels ────────
        // All 11 inputs (pipe + 10 signals) are declared in INPUT_TYPES and
        // always exist.  No add/remove of sockets — only type/label/colour
        // is updated dynamically when connections change.
        if (nodeData.name === PIPE_IN) {
            function readConnectedSource(node, slot) {
                const inp = node.inputs[slot];
                if (!inp?.link) return null;
                const link = node.graph?.links[inp.link];
                if (!link) return null;
                const src = node.graph?.nodes.find(n => n.id === link.origin_id);
                if (src && src.outputs[link.origin_slot]) {
                    const out = src.outputs[link.origin_slot];
                    return {
                        type: out.type === PIPE_TYPE ? PIPE_TYPE : out.type,
                        name: out.label || out.name || out.type,
                    };
                }
                return { type: link.type || "*", name: link.type || "*" };
            }

            function applySlotLabel(node, slot) {
                const inp = node.inputs?.[slot];
                if (!inp || inp.name === "pipe") return;
                const si = slot - 1; // signal index (slot 0 is pipe)
                if (!inp.link) {
                    inp.type = "*";
                    if (inp.label !== "ANY") { inp.label = "ANY"; inp.name = "ANY"; }
                    if (node._pipeTypes) delete node._pipeTypes[si];
                    if (node._pipeNames) delete node._pipeNames[si];
                    return;
                }
                const src = readConnectedSource(node, slot);
                const typeName = src?.type;
                const sourceName = src?.name;
                if (node._pipeTypes) node._pipeTypes[si] = typeName || "*";
                if (node._pipeNames) node._pipeNames[si] = sourceName || typeName || "*";
                const isConcrete = typeName && typeName !== "*" && typeName !== "ANY";
                inp.type = isConcrete ? typeName : "*";
                const label = isConcrete ? (sourceName || typeName) : "ANY";
                if (inp.label !== label) { inp.label = label; inp.name = label; }
                if (isConcrete) {
                    const link = node.graph?.links[inp.link];
                    const c = colorForType(typeName);
                    if (c && link) link.color = c;
                }
            }

            function applyAllLabels(node) {
                for (let i = 0; i < node.inputs.length; i++) {
                    if (node.inputs[i]?.name !== "pipe") applySlotLabel(node, i);
                }
            }

            const origCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const res = origCreated?.apply(this, arguments);
                this._pipeTypes = {};
                this._pipeNames = {};
                // Defer so graph links are restored before we trace them
                setTimeout(() => applyAllLabels(this), 0);
                return res;
            };

            const origConn = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (inputType, slot, isConnected, link_info, outputSlot) {
                const res = origConn?.apply(this, arguments);
                if ((inputType === 1 || inputType === true)) {
                    applySlotLabel(this, slot);
                }
                return res;
            };
        }

        // ──────── Pipe OUT ────────
        if (nodeData.name === PIPE_OUT) {
            // Layout: output 0 = pipe passthrough, outputs 1..MAX_SLOTS = signals.
            // All outputs are always visible (no autogrow) for stable indices.
            const PIPE_OUT_SLOT = 0;
            const SIGNAL_START = 1;

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

                // Ensure all 1 + MAX_SLOTS outputs exist
                const totalDesired = 1 + MAX_SLOTS;
                while (node.outputs.length < totalDesired) {
                    node.addOutput("ANY", "*");
                }

                // Output 0: pipe passthrough
                const pipeOut = node.outputs[PIPE_OUT_SLOT];
                pipeOut.type = PIPE_TYPE;
                if (pipeOut.label !== "pipe") {
                    pipeOut.label = "pipe";
                    pipeOut.name = "pipe";
                }

                // Outputs 1..MAX_SLOTS: signals
                for (let i = 0; i < MAX_SLOTS; i++) {
                    const slot = node.outputs[SIGNAL_START + i];
                    setOutputLabel(slot, types?.[i], names?.[i]);
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
