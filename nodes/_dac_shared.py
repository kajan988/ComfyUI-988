"""
Shared helpers for Divide and Conquer suite.
Tile coordinate calculation, overlap math, constants.
"""
import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import torch

OVERLAP_DICT = {
    "None": 0,
    "1/64 Tile": 0.015625,
    "1/32 Tile": 0.03125,
    "1/16 Tile": 0.0625,
    "1/8 Tile": 0.125,
    "1/4 Tile": 0.25,
    "1/2 Tile": 0.5,
}

TILE_ORDER_DICT = {"linear": 0, "spiral": 1}

SCALING_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]


def calculate_overlap(tile_size, overlap_fraction):
    return int(overlap_fraction * tile_size)


def create_tile_coordinates(image_width, image_height, tile_width, tile_height, overlap_x, overlap_y, grid_x, grid_y, tile_order):
    tiles = []
    num_columns = grid_x
    num_rows = grid_y

    for row in range(grid_y):
        y = row * (tile_height - overlap_y)
        if row == grid_y - 1 and grid_y > 1:
            y = image_height - tile_height
        for col in range(grid_x):
            x = col * (tile_width - overlap_x)
            if col == grid_x - 1 and grid_x > 1:
                x = image_width - tile_width
            tiles.append((x, y))

    if tile_order == 1:
        spiral_tiles = []
        visited = set()
        sx, sy = num_columns // 2, num_rows // 2
        dx, dy = 1, 0
        layer = 1
        while len(spiral_tiles) < len(tiles):
            for _ in range(2):
                for _ in range(layer):
                    if 0 <= sx < num_columns and 0 <= sy < num_rows and (sx, sy) not in visited:
                        index = sy * num_columns + sx
                        if index < len(tiles):
                            spiral_tiles.append(tiles[index])
                            visited.add((sx, sy))
                    sx += dx
                    sy += dy
                dx, dy = -dy, dx
            layer += 1
        spiral_tiles.reverse()
        tiles = spiral_tiles

    matrix = [["" for _ in range(num_columns)] for _ in range(num_rows)]
    for i, (x, y) in enumerate(tiles):
        row = y // (tile_height - overlap_y) if (tile_height - overlap_y) > 0 else 0
        col = x // (tile_width - overlap_x) if (tile_width - overlap_x) > 0 else 0
        matrix[row][col] = f"{i + 1} ({x},{y})"

    return tiles, matrix


def blend_tile_mask(tile_x, tile_y, tile_w, tile_h, img_w, img_h, overlap_x, overlap_y, overlap_factor=4):
    f_ox = overlap_x // overlap_factor
    f_oy = overlap_y // overlap_factor
    blend_x = int(math.sqrt(overlap_x))
    blend_y = int(math.sqrt(overlap_y))
    mask = Image.new("L", (tile_w, tile_h), 0)
    draw = ImageDraw.Draw(mask)

    at_top = tile_y == 0
    at_bottom = tile_y >= img_h - tile_h
    at_left = tile_x == 0
    at_right = tile_x >= img_w - tile_w
    fills_tall = img_h == tile_h
    fills_wide = img_w == tile_w

    if at_top and at_left and not fills_tall and not fills_wide:
        draw.rectangle([0, 0, tile_w - f_ox, tile_h - f_oy], fill=255)
    elif at_top and at_right and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, 0, tile_w, tile_h - f_oy], fill=255)
    elif at_bottom and at_left and not fills_tall and not fills_wide:
        draw.rectangle([0, f_oy, tile_w - f_ox, tile_h], fill=255)
    elif at_bottom and at_right and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, f_oy, tile_w, tile_h], fill=255)
    elif at_top and at_left and fills_tall:
        draw.rectangle([0, 0, tile_w - f_ox, tile_h], fill=255)
    elif at_top and at_right and fills_tall:
        draw.rectangle([f_ox, 0, tile_w, tile_h], fill=255)
    elif at_top and at_left and fills_wide:
        draw.rectangle([0, 0, tile_w, tile_h - f_oy], fill=255)
    elif at_bottom and at_left and fills_wide:
        draw.rectangle([0, f_oy, tile_w, tile_h], fill=255)
    elif not at_left and not at_right and at_top and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, 0, tile_w - f_ox, tile_h - f_oy], fill=255)
    elif not at_left and not at_right and at_bottom and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, f_oy, tile_w - f_ox, tile_h], fill=255)
    elif at_left and not at_top and not at_bottom and not fills_tall and not fills_wide:
        draw.rectangle([0, f_oy, tile_w - f_ox, tile_h - f_oy], fill=255)
    elif at_right and not at_top and not at_bottom and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, f_oy, tile_w, tile_h - f_oy], fill=255)
    elif not at_left and not at_right and at_top and fills_tall and not fills_wide:
        draw.rectangle([f_ox, 0, tile_w - f_ox, tile_h], fill=255)
    elif at_left and not at_top and not at_bottom and not fills_tall and fills_wide:
        draw.rectangle([0, f_oy, tile_w, tile_h - f_oy], fill=255)
    elif not at_left and not at_right and not at_top and not at_bottom and not fills_tall and not fills_wide:
        draw.rectangle([f_ox, f_oy, tile_w - f_ox, tile_h - f_oy], fill=255)

    radius = (blend_x, blend_y)
    if overlap_x <= 64 or overlap_y <= 64:
        mask = mask.filter(ImageFilter.BoxBlur(radius=radius))
    else:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=radius))

    mask_np = np.array(mask) / 255.0
    return torch.tensor(mask_np, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)