"""DaC Algorithm 988 — optimal tile-based upscaling with overlap control."""
import math
import torch
import comfy.utils
from comfy import model_management
from ._dac_shared import OVERLAP_DICT, TILE_ORDER_DICT, SCALING_METHODS, calculate_overlap


class DaCAlgorithm988:
    DESCRIPTION = "Calculate optimal upscale dimensions while maintaining minimum tile overlap and scale factor constraints. Optionally upscale with a model before tiling."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "tile_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "tile_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "min_overlap": (list(OVERLAP_DICT.keys()), {"default": "1/32 Tile"}),
                "min_scale_factor": ("FLOAT", {"default": 3.0, "min": 1.0, "max": 8.0}),
                "tile_order": (list(TILE_ORDER_DICT.keys()), {"default": "spiral"}),
                "scaling_method": (SCALING_METHODS, {"default": "lanczos"}),
            },
            "optional": {
                "upscale_model": ("UPSCALE_MODEL",),
                "use_upscale_with_model": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "DAC_DATA", "STRING")
    RETURN_NAMES = ("image", "dac_data", "info")
    OUTPUT_TOOLTIPS = ("Upscaled image at optimal tiling dimensions", "Serialized tile data for downstream nodes", "Summary of all calculated parameters")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "\U0001f987988/Image"

    def execute(self, image, tile_width, tile_height, min_overlap, min_scale_factor, tile_order, scaling_method, upscale_model=None, use_upscale_with_model=True):
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

        if use_upscale_with_model and upscale_model:
            device = model_management.get_torch_device()
            mem = model_management.module_size(upscale_model.model)
            mem += (512 * 512 * 3) * image.element_size() * max(upscale_model.scale, 1.0) * 384.0
            mem += image.nelement() * image.element_size()
            model_management.free_memory(mem, device)
            upscale_model.to(device)
            in_img = image.movedim(-1, -3).to(device)
            tile = 512
            oom = True
            while oom:
                try:
                    steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=32)
                    pbar = comfy.utils.ProgressBar(steps)
                    s = comfy.utils.tiled_scale(in_img, lambda a: upscale_model(a), tile_x=tile, tile_y=tile, overlap=32, upscale_amount=upscale_model.scale, pbar=pbar)
                    oom = False
                except model_management.OOM_EXCEPTION as e:
                    tile //= 2
                    if tile < 128:
                        raise e
            upscale_model.to("cpu")
            samples = torch.clamp(s.movedim(-3, -1), min=0, max=1.0).movedim(-1, 1)
        else:
            samples = image.movedim(-1, 1)

        uw = max(1, round(samples.shape[3] * uh / samples.shape[2])) if uw == 0 else uw
        uh = max(1, round(samples.shape[2] * uw / samples.shape[3])) if uh == 0 else uh
        result = comfy.utils.common_upscale(samples, uw, uh, scaling_method, crop=0).movedim(1, -1)

        info = (
            f"DaC Algorithm:\nOriginal: {width}x{height}\n"
            f"Upscaled: {uw}x{uh}\n"
            f"Grid: {gx}x{gy} ({gx * gy} tiles)\n"
            f"Overlap: {overlap_x}x{overlap_y}\n"
            f"Scale: {effective_upscale}x"
        )
        return (result, dac_data, info)


NODE_CLASS_MAPPINGS = {"DaCAlgorithm988": DaCAlgorithm988}
NODE_DISPLAY_NAME_MAPPINGS = {"DaCAlgorithm988": "DaC Algorithm 988"}