import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { refreshModelList } from "./model_refresh.mjs";
import { refreshTemplateDropdown } from "./templates.mjs";

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

    async nodeCreated(node) {
        if (node.comfyClass !== "LMStudio988") return;

        const refreshWidget = node.widgets?.find(w => w.name === "refresh_models");
        if (!refreshWidget) return;

        // Refresh models and templates on node creation (page load / node add)
        (async () => {
            try {
                const modelData = await refreshModelList(api);
                if (modelData.success && modelData.models) {
                    const choices = ["-- Custom (enter below) --", ...modelData.models];
                    for (const widgetName of ["model_selection", "draft_model_selection"]) {
                        const w = node.widgets?.find(ww => ww.name === widgetName);
                        if (w && w.options) {
                            w.options.values = choices;
                            if (!choices.includes(w.value)) {
                                w.value = choices[0];
                            }
                        }
                    }
                }
            } catch (err) {
                // Silently fail on first load
            }
        })();

        (async () => {
            try {
                const data = await refreshTemplateDropdown(api);
                if (data?.templates) {
                    const w = node.widgets?.find(ww => ww.name === "default_system_message");
                    if (w && w.options) {
                        const names = data.templates.map(t => t.name);
                        w.options.values = names;
                        if (!names.includes(w.value)) {
                            w.value = names[0];
                        }
                    }
                }
            } catch (err) {
                // Silently fail on first load
            }
        })();

        const originalCallback = refreshWidget.callback;

        refreshWidget.callback = async function (value) {
            if (!value) {
                if (originalCallback) originalCallback.call(this, value);
                return;
            }

            try {
                const data = await refreshModelList(api);
                if (data.success && data.models) {
                    const choices = ["-- Custom (enter below) --", ...data.models];

                    for (const widgetName of ["model_selection", "draft_model_selection"]) {
                        const w = node.widgets?.find(ww => ww.name === widgetName);
                        if (w && w.options) {
                            w.options.values = choices;
                            if (!choices.includes(w.value)) {
                                w.value = choices[0];
                            }
                        }
                    }

                    console.log(`[988] Refreshed models: ${data.models.length} found`);
                } else {
                    console.warn(`[988] Model refresh failed: ${data.message || "unknown error"}`);
                }
            } catch (err) {
                console.error("[988] Failed to refresh models:", err);
            }

            // Also refresh template dropdown
            try {
                const tmplData = await refreshTemplateDropdown(api);
                if (tmplData?.templates) {
                    const tmplWidget = node.widgets?.find(w => w.name === "default_system_message");
                    if (tmplWidget && tmplWidget.options) {
                        const tmplNames = tmplData.templates.map(t => t.name);
                        tmplWidget.options.values = tmplNames;
                        if (!tmplNames.includes(tmplWidget.value)) {
                            tmplWidget.value = tmplNames[0];
                        }
                    }
                    console.log(`[988] Refreshed templates: ${tmplData.templates.length} loaded`);
                }
            } catch (err) {
                console.error("[988] Failed to refresh templates:", err);
            }

            // Toggle back off so it acts like a one-shot button
            refreshWidget.value = false;

            if (originalCallback) originalCallback.call(this, false);
        };
    },
});