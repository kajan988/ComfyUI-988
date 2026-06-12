import { ComfyWidgets } from "../../../scripts/widgets.js";
import { app } from "../../../scripts/app.js";

/**
 * Shared helper to render text output on a node body widget.
 * Used by RatioCalc988, SequenceGen988, DisplayUI988.
 */
export function showTextOnNode(node, text, isDisplayUI) {
    if (!text) return;
    if (node.widgets) {
        const hasConverted = +!!node.inputs?.[0]?.widget;
        for (let i = hasConverted; i < node.widgets.length; i++) {
            node.widgets[i].onRemove?.();
        }
        node.widgets.length = hasConverted;
    }

    const widget = ComfyWidgets["STRING"](
        node, "text_box", ["STRING", { multiline: true }], app
    ).widget;

    widget.inputEl.readOnly = true;
    widget.inputEl.style.opacity = 0.6;

    if (isDisplayUI) {
        widget.value = Array.isArray(text)
            ? text.map(line => line + "\\n").join("\\n")
            : text;
    } else {
        widget.value = Array.isArray(text) ? text.join("") : text;
    }
}