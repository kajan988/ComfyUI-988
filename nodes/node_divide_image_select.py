"""Divide Image Select 988 — split upscaled image into tiles based on DaC data."""
import torch
from ._dac_shared import create_tile_coordinates


class DivideImageSelect988:
    DESCRIPTION = "Divide the upscaled image into tiles using coordinates from DaC Algorithm. tile=0 returns all tiles, tile=N returns a single tile."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "dac_data": ("DAC_DATA",),
                "tile": ("INT", {"default": 0, "min": 0, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("tiles", "matrix")
    OUTPUT_IS_LIST = (True, False)
    OUTPUT_TOOLTIPS = ("List of image tiles; tile=0 returns all tiles", "Visual tile matrix string")
    FUNCTION = "execute"
    CATEGORY = "\U0001f987988/Image"

    def execute(self, image, dac_data, tile):
        _, img_h, img_w, _ = image.shape
        tw = dac_data["tile_width"]
        th = dac_data["tile_height"]
        ox = dac_data["overlap_x"]
        oy = dac_data["overlap_y"]
        gx = dac_data["grid_x"]
        gy = dac_data["grid_y"]
        to = dac_data["tile_order"]

        coords, matrix = create_tile_coordinates(img_w, img_h, tw, th, ox, oy, gx, gy, to)

        tiles = []
        for cx, cy in coords:
            tiles.append(image[:, cy:cy + th, cx:cx + tw, :])

        if tile == 0:
            result = torch.cat(tiles, dim=0)
        else:
            result = tiles[tile - 1]

        matrix_ui = "DaC Matrix:\n" + "\n".join(" ".join(row) for row in matrix)
        return ([result[i].unsqueeze(0) for i in range(result.shape[0])], matrix_ui)


NODE_CLASS_MAPPINGS = {"DivideImageSelect988": DivideImageSelect988}
NODE_DISPLAY_NAME_MAPPINGS = {"DivideImageSelect988": "Divide Image Select 988"}