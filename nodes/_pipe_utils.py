"""Pipe/Bus type definition and type detection for 988 nodes."""

import torch

PIPE = "PIPE988"
NUM_SLOTS = 10


def detect_type(val):
    if val is None:
        return "ANY"
    class_name = type(val).__name__
    type_map = {
        "ModelPatcher": "MODEL",
        "CLIP": "CLIP",
        "VAE": "VAE",
        "ControlNet": "CONTROL_NET",
        "ClipVisionModel": "CLIP_VISION",
        "StyleModel": "STYLE_MODEL",
        "UpscaleModel": "UPSCALE_MODEL",
    }
    if class_name in type_map:
        return type_map[class_name]
    if isinstance(val, torch.Tensor):
        d = val.dim()
        if d == 4:
            return "IMAGE"
        if d in (2, 3):
            return "MASK"
        if d == 1:
            return "SIGMAS"
        return "ANY"
    if isinstance(val, dict):
        if "samples" in val:
            return "LATENT"
        if "waveform" in val:
            return "AUDIO"
        return "ANY"
    if isinstance(val, list):
        if val and isinstance(val[0], tuple):
            return "CONDITIONING"
        return "ANY"
    if isinstance(val, str):
        return "STRING"
    if isinstance(val, bool):
        return "BOOLEAN"
    if isinstance(val, int):
        return "INT"
    if isinstance(val, float):
        return "FLOAT"
    return "ANY"


def make_pipe(*values):
    values_list = list(values) + [None] * (NUM_SLOTS - len(values))
    values_list = values_list[:NUM_SLOTS]
    types = []
    for v in values_list:
        types.append(detect_type(v) if v is not None else None)
    return {
        "values": values_list,
        "types": types,
        "count": sum(1 for v in values_list if v is not None),
    }
