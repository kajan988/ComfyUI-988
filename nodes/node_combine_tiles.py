"""Combine Tiles 988 — merge processed tiles back into a single image with blend masks."""
import torch
from ._dac_shared import create_tile_coordinates, blend_tile_mask


class CombineTiles988:
    DESCRIPTION = "Combine processed tiles back into a single image using Gaussian-blurred overlap masks for seamless blending."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "dac_data": ("DAC_DATA",),
            },
            "input_is_list": True,
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "matrix")
    OUTPUT_TOOLTIPS = ("Combined full-resolution image", "Visual tile matrix string")
    FUNCTION = "execute"
    CATEGORY = "\U0001f987988/Image"

    def execute(self, images, dac_data):
        if isinstance(dac_data, list):
            dac_data = dac_data[0]

        out = [images[i] for i in range(len(images))]
        images_t = torch.stack(out).squeeze(1)

        uw = dac_data["upscaled_width"]
        uh = dac_data["upscaled_height"]
        ox = dac_data["overlap_x"]
        oy = dac_data["overlap_y"]
        gx = dac_data["grid_x"]
        gy = dac_data["grid_y"]
        to = dac_data["tile_order"]
        tw = images_t.shape[2]
        th = images_t.shape[1]

        coords, matrix = create_tile_coordinates(uw, uh, tw, th, ox, oy, gx, gy, to)

        output = torch.zeros((1, uh, uw, 3), dtype=images_t.dtype)
        for idx, (cx, cy) in enumerate(coords):
            tile = images_t[idx]
            mask = blend_tile_mask(cx, cy, tw, th, uw, uh, ox, oy)
            output[:, cy:cy + th, cx:cx + tw, :] *= (1 - mask)
            output[:, cy:cy + th, cx:cx + tw, :] += tile * mask

        matrix_ui = "DaC Matrix:\n" + "\n".join(" ".join(row) for row in matrix)
        return (output, matrix_ui)


NODE_CLASS_MAPPINGS = {"CombineTiles988": CombineTiles988}
NODE_DISPLAY_NAME_MAPPINGS = {"CombineTiles988": "Combine Tiles 988"}