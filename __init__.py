"""
ComfyUI-988 — collection of useful nodes for ComfyUI.
Licensed under GNU General Public License v3. See LICENSE.

Currently includes:
  - LM Studio 988           — text generation using local LLM/VLM models
  - LM Unload 988           — unload models from LM Studio and/or ComfyUI VRAM
  - DaC Algorithm 988        — optimal tile-based upscaling
  - Divide Image Select 988  — split image into tiles
  - Combine Tiles 988        — merge tiles back with blend masks
  - DAC Data Scale 988       — scale tile dimensions
  - Ratio Calculator 988     — detect aspect ratio from image
  - Ratio to Size 988        — convert ratio+MP to W/H
  - Seed Shifter 988         — batch seed generation with offset
  - Sequence Generator 988   — number sequences from expressions
  - Simple Config 988        — sampler config passthrough
  - Display UI 988           — show any value as text
  - Load Images into List 988 — batch load from folder
"""

from .nodes.node_lm_studio import NODE_CLASS_MAPPINGS as _MAPS_LM
from .nodes.node_lm_studio import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_LM
from .nodes.node_llm_unload import NODE_CLASS_MAPPINGS as _MAPS_UNLOAD
from .nodes.node_llm_unload import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_UNLOAD
from .nodes.node_dac_algorithm import NODE_CLASS_MAPPINGS as _MAPS_DAC
from .nodes.node_dac_algorithm import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_DAC
from .nodes.node_divide_image_select import NODE_CLASS_MAPPINGS as _MAPS_DIVIDE
from .nodes.node_divide_image_select import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_DIVIDE
from .nodes.node_combine_tiles import NODE_CLASS_MAPPINGS as _MAPS_COMBINE
from .nodes.node_combine_tiles import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_COMBINE
from .nodes.node_dac_data_scale import NODE_CLASS_MAPPINGS as _MAPS_DSCALE
from .nodes.node_dac_data_scale import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_DSCALE
from .nodes.node_ratio_calculator import NODE_CLASS_MAPPINGS as _MAPS_RCALC
from .nodes.node_ratio_calculator import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_RCALC
from .nodes.node_ratio_to_size import NODE_CLASS_MAPPINGS as _MAPS_RSIZE
from .nodes.node_ratio_to_size import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_RSIZE
from .nodes.node_seed_shifter import NODE_CLASS_MAPPINGS as _MAPS_SEED
from .nodes.node_seed_shifter import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_SEED
from .nodes.node_sequence_generator import NODE_CLASS_MAPPINGS as _MAPS_SEQ
from .nodes.node_sequence_generator import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_SEQ
from .nodes.node_simple_config import NODE_CLASS_MAPPINGS as _MAPS_CONFIG
from .nodes.node_simple_config import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_CONFIG
from .nodes.node_display_ui import NODE_CLASS_MAPPINGS as _MAPS_DISPLAY
from .nodes.node_display_ui import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_DISPLAY
from .nodes.node_load_images_list import NODE_CLASS_MAPPINGS as _MAPS_LOAD
from .nodes.node_load_images_list import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_LOAD

NODE_CLASS_MAPPINGS = {
    **_MAPS_LM, **_MAPS_UNLOAD,
    **_MAPS_DAC, **_MAPS_DIVIDE, **_MAPS_COMBINE, **_MAPS_DSCALE,
    **_MAPS_RCALC, **_MAPS_RSIZE,
    **_MAPS_SEED, **_MAPS_SEQ,
    **_MAPS_CONFIG, **_MAPS_DISPLAY, **_MAPS_LOAD,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **_NAMES_LM, **_NAMES_UNLOAD,
    **_NAMES_DAC, **_NAMES_DIVIDE, **_NAMES_COMBINE, **_NAMES_DSCALE,
    **_NAMES_RCALC, **_NAMES_RSIZE,
    **_NAMES_SEED, **_NAMES_SEQ,
    **_NAMES_CONFIG, **_NAMES_DISPLAY, **_NAMES_LOAD,
}

WEB_DIRECTORY = "./js"

# Register server API routes
from . import server_routes  # noqa: F401, E402

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# ── Startup banner (Pixaroma-style, red) ──────────────────────────
import os

def _display_988_banner(node_mappings):
    version = "?"
    try:
        import toml
        _p = os.path.join(os.path.dirname(__file__), 'pyproject.toml')
        with open(_p, "r", encoding="utf-8") as f:
            version = toml.load(f).get("project", {}).get("version", "?")
    except Exception:
        pass
    R = "\033[38;2;220;40;40m"
    B = "\033[1;97m"
    G = "\033[0;37m"
    X = "\033[0m"
    _BOX = "\u2501"
    bar = f"{R}{_BOX * 100}{X}"
    print(bar)
    print(f"  {B}9.8.8.NODES{X}  v{version}  |  {R}{len(node_mappings)} node(s){X} Loaded")
    _names = sorted(node_mappings.values())
    _line = ""
    for i, _n in enumerate(_names):
        _e = f"{_n}, " if i != len(_names) - 1 else _n
        if _line and len(_line) + len(_e) > 100:
            print("  " + G + _line.rstrip(", ") + X)
            _line = ""
        _line += _e
    if _line:
        print("  " + G + _line.rstrip(", ") + X)
    print(f"  {G}This is a notice, not an error. All {R}9.8.8.NODES{G} work in both Classic and Nodes 2.0 mode.{X}")
    print(bar)

_display_988_banner(NODE_DISPLAY_NAME_MAPPINGS)