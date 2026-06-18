import { app } from "/scripts/app.js";

const DAC_V2 = "DaCAlgorithmV2988";

const IMAGE_SCALE_WIDGETS = ["min_scale_factor", "min_overlap", "tile_order"];
const TILECOUNT_WIDGETS = ["num_tiles"];

app.registerExtension({
    name: "988.DaCAlgorithmV2",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== DAC_V2) return;

        const origOnCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const res = origOnCreated?.apply(this, arguments);

            const algoWidget = this.widgets?.find(w => w.name === "algorithm");
            if (!algoWidget) return res;

            for (const w of this.widgets) {
                if (IMAGE_SCALE_WIDGETS.includes(w.name) || TILECOUNT_WIDGETS.includes(w.name)) {
                    w._origComputeSize = w.computeSize;
                }
            }

            const refresh = () => {
                const isImageScale = algoWidget.value === "Image Scale Factor";
                for (const w of this.widgets) {
                    const isImageW = IMAGE_SCALE_WIDGETS.includes(w.name);
                    const isTileCountW = TILECOUNT_WIDGETS.includes(w.name);
                    if (!isImageW && !isTileCountW) continue;

                    const shouldHide = (isImageW && !isImageScale) || (isTileCountW && isImageScale);

                    if (shouldHide) {
                        w.disabled = true;
                        w.computeSize = () => [0, -4];
                    } else {
                        w.disabled = false;
                        if (w._origComputeSize) {
                            w.computeSize = w._origComputeSize;
                        } else {
                            delete w.computeSize;
                        }
                    }
                }
                if (this.graph) this.graph.setDirtyCanvas(true, true);
            };

            algoWidget.callback = refresh;
            setTimeout(refresh, 0);

            return res;
        };
    },
});
