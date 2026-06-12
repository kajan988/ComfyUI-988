"""Ratio to Size 988 — convert aspect ratio + megapixel target to optimal W/H divisible by 64."""
import math
from ._image_ratios import RATIO


class RatioToSize988:
    DESCRIPTION = "Pick an aspect ratio and target megapixel count to get optimal width and height (multiples of 64) within a precision tolerance."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ratio": (list(RATIO.keys()),),
                "megapixel": ("FLOAT", {"default": 1.05, "min": 0.10, "max": 3.00, "step": 0.01}),
                "precision": ("FLOAT", {"default": 0.30, "min": 0.00, "max": 1.00, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "info")
    OUTPUT_TOOLTIPS = ("Optimal width (multiple of 64)", "Optimal height (multiple of 64)", "Summary of selected parameters")
    FUNCTION = "calc"
    CATEGORY = "\U0001f987988/Image"

    def calc(self, ratio, megapixel, precision):
        aw, ah = RATIO.get(ratio, (1, 1))
        total = int(megapixel * 1_000_000)
        w = int((total * (aw / ah)) ** 0.5)
        h = int(w * (ah / aw))
        while True:
            w = (w // 64) * 64
            h = (h // 64) * 64
            if abs((w / h) - (aw / ah)) <= precision:
                break
            if w > 64 and h > 64:
                if (w / h) > (aw / ah):
                    w -= 64
                else:
                    h -= 64
            else:
                break
        info = f"Ratio: {ratio}\nWidth: {w}\nHeight: {h}\nMegapixel: {w * h:,}"
        return (w, h, info)


NODE_CLASS_MAPPINGS = {"RatioToSize988": RatioToSize988}
NODE_DISPLAY_NAME_MAPPINGS = {"RatioToSize988": "Ratio to Size 988"}