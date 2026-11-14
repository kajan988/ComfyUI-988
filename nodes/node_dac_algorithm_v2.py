"""DaC Algorithm 988 v2 — tile-based upscaling to a minimum scale factor."""
import math
import torch
import comfy.utils
from ._dac_shared import OVERLAP_DICT, TILE_ORDER_DICT, calculate_overlap

SCALING_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]


class DaCAlgorithmV2988:
    DESCRIPTION = "Upscale to a minimum scale factor while fitting the result to the tile grid using the selected overlap and tile order."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "tile_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "tile_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "min_scale_factor": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 64.0}),
                "min_overlap": (list(OVERLAP_DICT.keys()), {"default": "3%"}),
                "tile_order": (list(TILE_ORDER_DICT.keys()), {"default": "spiral"}),
                "scaling_method": (SCALING_METHODS, {"default": "lanczos"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "DAC_DATA", "STRING")
    RETURN_NAMES = ("image", "dac_data", "info")
    OUTPUT_TOOLTIPS = ("Upscaled image at optimal tiling dimensions", "Serialized tile data for downstream nodes", "Summary of all calculated parameters")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "\U0001f987988/Image"

    def _execute_image_scale(self, image, tile_width, tile_height, min_overlap, tile_order, scaling_method, min_scale_factor):
        overlap = OVERLAP_DICT.get(min_overlap, 0)
        tile_order_val = TILE_ORDER_DICT.get(tile_order, 0)
        _, height, width, _ = image.shape
        overlap_x = calculate_overlap(tile_width, overlap)
        overlap_y = calculate_overlap(tile_height, overlap)

        if width <= height:
            mf = math.ceil(min_scale_factor * width / tile_width)
            while True:
                uw = tile_width * mf
                gx = math.ceil(uw / tile_width)
                uw = (tile_width * gx) - (overlap_x * (gx - 1))
                ur = uw / width
                if ur >= min_scale_factor:
                    break
                mf += 1
            uh = int(height * ur)
            gy = math.ceil((uh - overlap_y) / (tile_height - overlap_y))
            overlap_y = round((tile_height * gy - uh) / (gy - 1)) if gy > 1 else 0
            if gx <= 1:
                overlap_x = 0
        else:
            mf = math.ceil(min_scale_factor * height / tile_height)
            while True:
                uh = tile_height * mf
                gy = math.ceil(uh / tile_height)
                uh = (tile_height * gy) - (overlap_y * (gy - 1))
                ur = uh / height
                if ur >= min_scale_factor:
                    break
                mf += 1
            uw = int(width * ur)
            gx = math.ceil((uw - overlap_x) / (tile_width - overlap_x))
            overlap_x = round((tile_width * gx - uw) / (gx - 1)) if gx > 1 else 0
            if gy <= 1:
                overlap_y = 0

        effective_upscale = round(uw / width, 2)
        dac_data = {
            "upscaled_width": uw, "upscaled_height": uh,
            "tile_width": tile_width, "tile_height": tile_height,
            "overlap_x": overlap_x, "overlap_y": overlap_y,
            "grid_x": gx, "grid_y": gy,
            "tile_order": tile_order_val,
        }

        samples = image.movedim(-1, 1)
        uw = max(1, round(samples.shape[3] * uh / samples.shape[2])) if uw == 0 else uw
        uh = max(1, round(samples.shape[2] * uw / samples.shape[3])) if uh == 0 else uh
        result = comfy.utils.common_upscale(samples, uw, uh, scaling_method, crop=0).movedim(1, -1)

        lines = [
            "DaC Algorithm v2 — Image Scale Factor",
            f"Original image: {width}x{height} ({(width * height) / 1_000_000:.2f} MP)",
            f"Upscaled image: {uw}x{uh} ({(uw * uh) / 1_000_000:.2f} MP)",
            f"Tile size: {tile_width}x{tile_height}",
            f"Grid: {gx}x{gy} ({gx * gy} tiles)",
            f"Overlap: {overlap_x}x{overlap_y}",
            f"Scale: {effective_upscale}x",
            f"Method: {scaling_method}",
        ]
        info = "\n".join(lines)
        return (result, dac_data, info)

    def execute(self, image, tile_width, tile_height, min_scale_factor, min_overlap, tile_order, scaling_method):
        if isinstance(min_scale_factor, list):
            min_scale_factor = min_scale_factor[0]
        return self._execute_image_scale(
            image, tile_width, tile_height, min_overlap, tile_order, scaling_method,
            min_scale_factor
        )


NODE_CLASS_MAPPINGS = {"DaCAlgorithmV2988": DaCAlgorithmV2988}
NODE_DISPLAY_NAME_MAPPINGS = {"DaCAlgorithmV2988": "DaC Algorithm 988 v2"}
