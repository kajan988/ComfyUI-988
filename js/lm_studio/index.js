import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

/*
 * LM Studio 988 — Model Refresh Extension
 *
 * Intercepts the refresh_models toggle to fetch an updated model list from
 * the LM Studio server and update the dropdown widgets in-place.
 *
 * Compatibility:
 *   - Legacy LiteGraph frontend: full support via widget.options.values
 *   - Nodes 2.0 / Vue frontend: the server-side cache is always updated,
 *     so a browser refresh (F5) will pick up new models even if the
 *     in-place widget update does not propagate in a future Vue renderer.
 */

app.registerExtension({
    name: "988.LMStudio",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LMStudio988") return;

        const orig = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            orig?.apply(this, arguments);

            const node = this;
            const refreshWidget = node.widgets?.find(w => w.name === "refresh_models");
            if (!refreshWidget) return;

            const origCB = refreshWidget.callback;

            refreshWidget.callback = async function (value) {
                if (!value) {
                    if (origCB) origCB.call(this, value);
                    return;
                }

                // Refresh model dropdowns
                try {
                    const resp = await api.fetchApi("/988/lm_studio/refresh_models", { method: "POST" });
                    const data = await resp.json();
                    if (data.success && data.models) {
                        for (const name of ["model_selection", "draft_model_selection"]) {
                            const w = node.widgets?.find(ww => ww.name === name);
                            if (w && w.options) {
                                w.options.values = ["-- Custom (enter below) --", ...data.models];
                                if (!w.options.values.includes(w.value)) {
                                    w.value = w.options.values[0];
                                }
                            }
                        }
                    }
                } catch (e) { console.error("[988] Model refresh error:", e); }

                // Refresh template dropdown
                try {
                    const resp = await api.fetchApi("/988/lm_studio/refresh_templates", { method: "POST" });
                    const tmpl = await resp.json();
                    if (tmpl?.templates) {
                        const w = node.widgets?.find(ww => ww.name === "default_system_message");
                        if (w && w.options) {
                            const names = tmpl.templates.map(t => t.name);
                            w.options.values = names;
                            if (!names.includes(w.value)) {
                                w.value = names[0];
                            }
                        }
                    }
                } catch (e) { console.error("[988] Template refresh error:", e); }

                // Toggle back off (silent — no callback to avoid Vue/Node 2.0 re-render)
                const _cb = refreshWidget.callback;
                refreshWidget.callback = null;
                refreshWidget.value = false;
                refreshWidget.callback = _cb;

                if (origCB) origCB.call(this, false);
            };

            // Force initial value to false (silent)
            const _cb = refreshWidget.callback;
            refreshWidget.callback = null;
            refreshWidget.value = false;
            refreshWidget.callback = _cb;

            // Pre-populate dropdowns on node creation / page load.
            // After refreshing the server-side cache, update the combo options AND
            // restore the previously selected widget value by matching on the
            // normalized (emoji-stripped) model ID.  This prevents the widget's
            // internal index-based selection from drifting when the options array
            // is replaced — a common ComfyUI/LiteGraph combo pitfall that breaks
            // IS_CHANGED-based caching (see #1 below).
            (async () => {
                try {
                    const resp = await api.fetchApi("/988/lm_studio/refresh_models", { method: "POST" });
                    const data = await resp.json();
                    if (data.success && data.models) {
                        for (const name of ["model_selection", "draft_model_selection"]) {
                            const w = node.widgets?.find(ww => ww.name === name);
                            if (!w || !w.options) continue;

                            // ── #1 Preserve value across options replacement ──
                            // Strip 👁 and variation selector for canonical matching.
                            const stripEmoji = (s) => ("" + s)
                                .replace(/\uD83D\uDC41\uFE0F/g, "")
                                .replace(/\uFE0F/g, "")
                                .trim();

                            const prevValue = w.value;
                            const newValues = ["-- Custom (enter below) --", ...data.models];
                            w.options.values = newValues;

                            // Try canonical-ID match first, then exact match fallback.
                            const canonicalPrev = stripEmoji(prevValue);
                            let matchIdx = newValues.findIndex(
                                v => stripEmoji(v) === canonicalPrev
                            );
                            if (matchIdx === -1) {
                                matchIdx = newValues.indexOf(prevValue);
                            }
                            if (matchIdx >= 0) {
                                w.value = newValues[matchIdx];
                            }
                            // If no match found, leave the widget's default fallback.
                        }
                    }
                } catch (_) { /* first load may fail */ }
            })();
        };
    },
});
