"""DAC Data Scale 988 — scale all DAC_DATA dimensions by a multiplier, preserving grid and order."""


class DacDataScale988:
    DESCRIPTION = "Scale all DAC_DATA dimensions (width, height, tile, overlap) by a multiplier. Grid and tile order are preserved unchanged."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dac_data": ("DAC_DATA",),
                "multiplier": ("FLOAT", {"default": 1.0, "min": 0.25, "max": 16.0, "step": 0.25}),
            },
        }

    RETURN_TYPES = ("DAC_DATA", "STRING")
    RETURN_NAMES = ("dac_data", "info")
    OUTPUT_TOOLTIPS = ("Scaled DAC_DATA for downstream nodes", "Summary of changes")
    FUNCTION = "scale"
    CATEGORY = "\U0001f987988/Image"

    def scale(self, dac_data, multiplier):
        preserve = {"grid_x", "grid_y", "tile_order"}
        scaled = {}
        for k, v in dac_data.items():
            if k in preserve:
                scaled[k] = v
            elif isinstance(v, (int, float)):
                scaled[k] = int(round(v * multiplier))
            else:
                scaled[k] = v

        info = (
            f"DAC Data Scaled: {multiplier}x\n"
            f"Upscaled: {dac_data['upscaled_width']}x{dac_data['upscaled_height']} -> {scaled['upscaled_width']}x{scaled['upscaled_height']}\n"
            f"Tiles: {dac_data['tile_width']}x{dac_data['tile_height']} -> {scaled['tile_width']}x{scaled['tile_height']}\n"
            f"Overlap: {dac_data['overlap_x']}x{dac_data['overlap_y']} -> {scaled['overlap_x']}x{scaled['overlap_y']}\n"
            f"Grid: {dac_data['grid_x']}x{dac_data['grid_y']} (unchanged)"
        )
        return (scaled, info)


NODE_CLASS_MAPPINGS = {"DacDataScale988": DacDataScale988}
NODE_DISPLAY_NAME_MAPPINGS = {"DacDataScale988": "DAC Data Scale 988"}