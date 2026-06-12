"""Pipe IN 988 — bundle multiple signals of any type into a single PIPE."""

from ._type_helpers import ANY
from ._pipe_utils import PIPE, NUM_SLOTS, detect_type


class PipeIN988:
    DESCRIPTION = (
        "Merges up to 10 signals of any type into a single PIPE output. "
        "Inputs are kept in order — use Pipe OUT 988 to restore them."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {f"input_{i}": (ANY, {}) for i in range(NUM_SLOTS)},
        }

    RETURN_TYPES = (PIPE,)
    RETURN_NAMES = ("pipe",)
    OUTPUT_TOOLTIPS = ("Bundled pipe. Connect to Pipe OUT 988.",)
    FUNCTION = "merge"
    CATEGORY = "\U0001f987988/Utility"

    def merge(self, **kwargs):
        values = []
        types = []
        for i in range(NUM_SLOTS):
            val = kwargs.get(f"input_{i}")
            values.append(val)
            types.append(detect_type(val) if val is not None else None)
        return ({
            "values": values,
            "types": types,
            "count": sum(1 for v in values if v is not None),
        },)


NODE_CLASS_MAPPINGS = {"PipeIN988": PipeIN988}
NODE_DISPLAY_NAME_MAPPINGS = {"PipeIN988": "Pipe IN 988"}
