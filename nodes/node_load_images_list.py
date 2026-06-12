"""Load Images 988 — load all images from a folder into a list."""
import os
import torch
import numpy as np
from PIL import Image, ImageOps


class LoadImages988:
    DESCRIPTION = "Load all supported image files from a directory into a batch tensor. Supports jpg, jpeg, png, webp."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    OUTPUT_IS_LIST = (True,)
    OUTPUT_TOOLTIPS = ("List of loaded image tensors",)
    FUNCTION = "load"
    CATEGORY = "\U0001f987988/Image"

    def load(self, directory):
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        exts = (".jpg", ".jpeg", ".png", ".webp")
        files = sorted(f for f in os.listdir(directory) if f.lower().endswith(exts))
        if not files:
            raise FileNotFoundError(f"No supported images in: {directory}")
        tensors = []
        for fname in files:
            path = os.path.join(directory, fname)
            try:
                img = ImageOps.exif_transpose(Image.open(path).convert("RGB"))
                arr = np.array(img).astype(np.float32) / 255.0
                tensors.append(torch.from_numpy(arr)[None,])
            except Exception as e:
                print(f"[988] LoadImages: skip {fname}: {e}")
        if not tensors:
            raise FileNotFoundError(f"No valid images loaded from: {directory}")
        batch = torch.cat(tensors, dim=0)
        return ([batch[i].unsqueeze(0) for i in range(batch.shape[0])],)


NODE_CLASS_MAPPINGS = {"LoadImages988": LoadImages988}
NODE_DISPLAY_NAME_MAPPINGS = {"LoadImages988": "Load Images into List 988"}