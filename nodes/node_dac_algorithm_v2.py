"""DaC Algorithm 988 v2 — dual-mode tile-based upscaling with dynamic widget visibility."""
import math
import torch
import comfy.utils
from ._dac_shared import OVERLAP_DICT, TILE_ORDER_DICT, calculate_overlap

SCALING_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]
ALGORITHM_MODES = ["Image Scale Factor", "TileCount"]


class DaCAlgorithmV2988:
    DESCRIPTION = "Image Scale Factor: upscale to min scale factor. TileCount: specify tile size and total tile count, algorithm auto-calculates grid and overlap to match input aspect ratio."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "tile_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "tile_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "algorithm": (ALGORITHM_MODES, {"default": "Image Scale Factor"}),
                "min_scale_factor": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 64.0}),
                "min_overlap": (list(OVERLAP_DICT.keys()), {"default": "3%"}),
                "tile_order": (list(TILE_ORDER_DICT.keys()), {"default": "spiral"}),
                "scaling_method": (SCALING_METHODS, {"default": "lanczos"}),
                "num_tiles": ("INT", {"default": 4, "min": 1, "max": 1024}),
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
        min_scale_factor = max(min_scale_factor, 1.0)

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

        info = (
            f"DaC Algorithm v2 — Image Scale Factor\n"
            f"Original image: {width}x{height}\n"
            f"Upscaled image: {uw}x{uh}\n"
            f"Tile size: {tile_width}x{tile_height}\n"
            f"Grid: {gx}x{gy} ({gx * gy} tiles)\n"
            f"Overlap: {overlap_x}x{overlap_y}\n"
            f"Scale: {effective_upscale}x\n"
            f"Method: {scaling_method}"
        )
        return (result, dac_data, info)

    def _execute_tile_count(self, image, tile_width, tile_height, num_tiles, scaling_method):
        _, height, width, _ = image.shape
        input_aspect = width / height
        tile_order_val = TILE_ORDER_DICT.get("linear", 0)

        best = None  # (gx, gy, overlap_x, overlap_y, out_w, out_h, error)

        for n in range(num_tiles, min(num_tiles * 4, 2048) + 1):
            factor = n
            for gx in range(1, factor + 1):
                gy = (factor + gx - 1) // gx
                if gx * gy < n:
                    continue

                or_val = self._calc_overlap_ratio(gx, gy, tile_width, tile_height, input_aspect)
                if or_val is None or or_val < 0.02 or or_val > 0.50:
                    continue

                ox = calculate_overlap(tile_width, or_val)
                oy = calculate_overlap(tile_height, or_val)

                out_w = int(tile_width * gx - ox * (gx - 1))
                out_h = int(tile_height * gy - oy * (gy - 1))
                if out_w <= 0 or out_h <= 0:
                    continue

                out_aspect = out_w / out_h
                error = abs(out_aspect - input_aspect) / input_aspect

                if best is None or error < best[6]:
                    best = (gx, gy, ox, oy, out_w, out_h, error)
                    if error < 0.0001:
                        break
            if best is not None and best[6] < 0.0001:
                break

        if best is None:
            gx = max(1, round(math.sqrt(num_tiles * input_aspect * tile_height / tile_width)))
            gy = max(1, (num_tiles + gx - 1) // gx)

            or_val = 0.08
            ox = calculate_overlap(tile_width, or_val)
            oy = calculate_overlap(tile_height, or_val)
            out_w = int(tile_width * gx - ox * (gx - 1))
            out_h = int(tile_height * gy - oy * (gy - 1))

            best = (gx, gy, ox, oy, out_w, out_h, 0.0)

        gx, gy, ox, oy, out_w, out_h, _ = best

        dac_data = {
            "upscaled_width": out_w, "upscaled_height": out_h,
            "tile_width": tile_width, "tile_height": tile_height,
            "overlap_x": ox, "overlap_y": oy,
            "grid_x": gx, "grid_y": gy,
            "tile_order": tile_order_val,
        }

        samples = image.movedim(-1, 1)
        result = comfy.utils.common_upscale(samples, out_w, out_h, scaling_method, crop=0).movedim(1, -1)

        info = (
            f"DaC Algorithm v2 — TileCount ({num_tiles} tiles)\n"
            f"Original image: {width}x{height}\n"
            f"Output image: {out_w}x{out_h}\n"
            f"Tile size: {tile_width}x{tile_height}\n"
            f"Grid: {gx}x{gy} ({gx * gy} tiles, {gx * gy - num_tiles} extra)\n"
            f"Overlap: {ox}x{oy}\n"
            f"Method: {scaling_method}"
        )
        return (result, dac_data, info)

    @staticmethod
    def _calc_overlap_ratio(gx, gy, tw, th, input_aspect):
        A = input_aspect * th / tw
        denom = gx - A * gy + A - 1
        if abs(denom) < 1e-12:
            if abs(gx - A * gy) < 1e-10:
                return 0.10
            return None
        return (gx - A * gy) / denom

    def execute(self, image, tile_width, tile_height, algorithm, min_scale_factor, min_overlap, tile_order, scaling_method, num_tiles):
        if isinstance(algorithm, list):
            algorithm = algorithm[0]

        if algorithm == "TileCount":
            if isinstance(num_tiles, list):
                num_tiles = num_tiles[0]
            return self._execute_tile_count(image, tile_width, tile_height, num_tiles, scaling_method)

        if isinstance(min_scale_factor, list):
            min_scale_factor = min_scale_factor[0]
        return self._execute_image_scale(
            image, tile_width, tile_height, min_overlap, tile_order, scaling_method,
            min_scale_factor
        )


NODE_CLASS_MAPPINGS = {"DaCAlgorithmV2988": DaCAlgorithmV2988}
NODE_DISPLAY_NAME_MAPPINGS = {"DaCAlgorithmV2988": "DaC Algorithm 988 v2"}
