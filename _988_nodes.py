"""
ComfyUI-988 — collection of useful nodes for ComfyUI.
mxToolkit-style single-file entry point.
Licensed under GNU General Public License v3. See LICENSE.

Exports NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS for ComfyUI loader.
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
from .nodes.node_pipe_merge import NODE_CLASS_MAPPINGS as _MAPS_PIPE_IN
from .nodes.node_pipe_merge import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_PIPE_IN
from .nodes.node_pipe_unpack import NODE_CLASS_MAPPINGS as _MAPS_PIPE_OUT
from .nodes.node_pipe_unpack import NODE_DISPLAY_NAME_MAPPINGS as _NAMES_PIPE_OUT

NODE_CLASS_MAPPINGS = {
    **_MAPS_LM, **_MAPS_UNLOAD,
    **_MAPS_DAC, **_MAPS_DIVIDE, **_MAPS_COMBINE, **_MAPS_DSCALE,
    **_MAPS_RCALC, **_MAPS_RSIZE,
    **_MAPS_SEED, **_MAPS_SEQ,
    **_MAPS_CONFIG, **_MAPS_DISPLAY, **_MAPS_LOAD,
    **_MAPS_PIPE_IN, **_MAPS_PIPE_OUT,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **_NAMES_LM, **_NAMES_UNLOAD,
    **_NAMES_DAC, **_NAMES_DIVIDE, **_NAMES_COMBINE, **_NAMES_DSCALE,
    **_NAMES_RCALC, **_NAMES_RSIZE,
    **_NAMES_SEED, **_NAMES_SEQ,
    **_NAMES_CONFIG, **_NAMES_DISPLAY, **_NAMES_LOAD,
    **_NAMES_PIPE_IN, **_NAMES_PIPE_OUT,
}
