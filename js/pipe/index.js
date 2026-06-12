import { app } from "/scripts/app.js";

// ── Node IDs ──
const PIPE_IN = "PipeIN988";
const PIPE_OUT = "PipeOUT988";

// ── Slot limits ──
const MAX_SLOTS = 10;
const MIN_SLOTS = 2;

// ── Colour map (fallback when LGraphCanvas.link_type_colors lacks an entry) ──
const FALLBACK_COLORS = {
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

/** Resolve the colour for a type string: LiteGraph's built-in map first, then ours. */
function colorForType(type) {
    if (!type || type === "*") return null;
    const fromLG = LGraphCanvas?.link_type_colors?.[type];
    if (fromLG) return fromLG;
    return FALLBACK_COLORS[type] || null;
}

/**
 * Update a single slot (input or output) so its type + label reflect the
 * connected signal.  The socket colour is derived automatically from
 * LGraphCanvas.link_type_colors[slot.type] — we NEVER set slot.color.
 *
 *   typeName = concrete type string ("IMAGE", "MASK", …) or null/undefined/"*"
 */
function paintSlot(slot, typeName) {
    if (!slot) return;
    const isConcrete = typeName && typeName !== "*" && typeName !== "ANY";
    slot.type = isConcrete ? typeName : "*";
    const label = isConcrete ? typeName : "ANY";
    if (slot.label !== label) slot.label = label;
}

/** Colour the link wire so it matches the resolved type. */
function paintLink(graph, linkId, typeName) {
    if (!graph || linkId == null) return;
    const link = graph.links[linkId];
    if (!link) return;
    const c = colorForType(typeName);
    if (c) link.color = c;
}

// ──────────────────────────────────
//  Pipe IN 988  — autogrow + colour
// ──────────────────────────────────
app.registerExtension({
    name: "988.Pipe",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== PIPE_IN && nodeData.name !== PIPE_OUT) return;

        // ──────── Pipe IN ────────
        if (nodeData.name === PIPE_IN) {
            // Walk the link to find the actual type of the connected output.
            function readConnectedType(node, slot) {
                const inp = node.inputs[slot];
                if (!inp?.link) return null;
                const link = node.graph?.links[inp.link];
                if (!link) return null;
                const src = node.graph?.nodes.find(n => n.id === link.origin_id);
                if (src && src.outputs[link.origin_slot]) {
                    return src.outputs[link.origin_slot].type;
                }
                return link.type || "*";
            }

            // Ensure we always have (connected + 1) visible slots.
            function rebalanceSlots(node) {
                if (!node._graphLoaded) return;
                const connected = node.inputs.reduce((n, inp) => n + (inp.link ? 1 : 0), 0);
                const desired = Math.min(MAX_SLOTS, Math.max(MIN_SLOTS, connected + 1));

                while (node.inputs.length > desired) {
                    const idx = node.inputs.length - 1;
                    delete node._pipeTypes?.[idx];
                    node.removeInput(idx);
                }
                while (node.inputs.length < desired) {
                    const idx = node.inputs.length;
                    node.addInput(`input_${idx}`, "*");
                }
                for (let i = 0; i < node.inputs.length; i++) {
                    paintSlot(node.inputs[i], node._pipeTypes?.[i]);
                }
            }

            // ── onNodeCreated ──
            const origCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const res = origCreated?.apply(this, arguments);
                this._pipeTypes = {};
                this._graphLoaded = false;

                setTimeout(() => {
                    this._graphLoaded = true;
                    for (let i = 0; i < this.inputs.length; i++) {
                        const t = readConnectedType(this, i);
                        if (t) this._pipeTypes[i] = t;
                    }
                    rebalanceSlots(this);
                }, 0);
                return res;
            };

            // ── onConnectionsChange ──
            const origConn = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (inputType, slot, isConnected, link_info, outputSlot) {
                const res = origConn?.apply(this, arguments);

                if (inputType === 1 || inputType === true) {
                    if (!this._pipeTypes) this._pipeTypes = {};

                    if (isConnected && link_info) {
                        const t = readConnectedType(this, slot);
                        if (t) {
                            this._pipeTypes[slot] = t;
                            if (this._graphLoaded) paintLink(this.graph, link_info.id, t);
                        }
                    } else {
                        delete this._pipeTypes?.[slot];
                    }

                    paintSlot(this.inputs[slot], this._pipeTypes?.[slot]);

                    if (this._graphLoaded) rebalanceSlots(this);
                }
                return res;
            };
        }

        // ──────── Pipe OUT ────────
        if (nodeData.name === PIPE_OUT) {
            // Trace back through the pipe link to the Pipe IN node's _pipeTypes.
            function sourceTypes(node) {
                const inp = node.inputs[0];
                if (!inp?.link) return null;
                const link = node.graph?.links[inp.link];
                if (!link) return null;
                const src = node.graph?.nodes.find(n => n.id === link.origin_id);
                return src?._pipeTypes ?? null;
            }

            function syncOutputs(node) {
                const types = sourceTypes(node);
                for (let i = 0; i < node.outputs.length; i++) {
                    paintSlot(node.outputs[i], types?.[i]);
                }
            }

            const origCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const res = origCreated?.apply(this, arguments);
                setTimeout(() => syncOutputs(this), 0);
                return res;
            };

            const origConn = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (inputType, slot, isConnected, link_info, outputSlot) {
                const res = origConn?.apply(this, arguments);
                if ((inputType === 1 || inputType === true) && slot === 0) {
                    setTimeout(() => syncOutputs(this), 0);
                }
                return res;
            };
        }
    },
});
