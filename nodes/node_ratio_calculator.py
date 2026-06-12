"""Ratio Calculator 988 — find closest aspect ratio from an image."""
import math
from ._type_helpers import ANY
from ._image_ratios import RATIO


class RatioCalc988:
    DESCRIPTION = "Analyse an image and return its closest matching aspect ratio label (e.g. 16:9)."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = (ANY,)
    RETURN_NAMES = ("ratio",)
    OUTPUT_TOOLTIPS = ("Closest aspect-ratio label string",)
    OUTPUT_NODE = True
    FUNCTION = "calc"
    CATEGORY = "\U0001f987988/Image"

    def calc(self, image):
        _, height, width, _ = image.shape
        gcd = math.gcd(width, height)
        sw = width // gcd
        sh = height // gcd
        closest = None
        min_diff = float("inf")
        for name, (rw, rh) in RATIO.items():
            diff = abs(sw / sh - rw / rh)
            if diff < min_diff:
                min_diff = diff
                closest = name
        return {"ui": {"text": closest}, "result": (closest,)}


NODE_CLASS_MAPPINGS = {"RatioCalc988": RatioCalc988}
NODE_DISPLAY_NAME_MAPPINGS = {"RatioCalc988": "Ratio Calculator 988"}