import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
import { showTextOnNode } from "./show_text.mjs";

const TEXT_NODES = new Set(["RatioCalc988", "SequenceGen988", "DisplayUI988"]);

app.registerExtension({
    name: "988.Steudio",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (!TEXT_NODES.has(nodeData.name)) return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);
            showTextOnNode(this, message?.text, nodeData.name === "DisplayUI988");
        };

        const VALUES = Symbol();
        const configure = nodeType.prototype.configure;
        nodeType.prototype.configure = function () {
            this[VALUES] = arguments[0]?.widgets_values;
            return configure?.apply(this, arguments);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            onConfigure?.apply(this, arguments);
            const vals = this[VALUES];
            if (vals?.length) {
                requestAnimationFrame(() => showTextOnNode(this, vals[0], nodeData.name === "DisplayUI988"));
            }
        };
    },
});