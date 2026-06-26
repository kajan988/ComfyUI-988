"""Pipe IN 988 — bundle multiple signals of any type into a single PIPE.

First input/output is always a PIPE pass-through (like LP-style).
An incoming pipe provides defaults for all slots; individual inputs override.
"""

from ._type_helpers import ANY
from ._pipe_utils import PIPE, NUM_SLOTS, detect_type


class PipeIN988:
    DESCRIPTION = (
        "Merges up to 10 signals of any type into a single PIPE output. "
        "First input is a pipe pass-through — an incoming pipe provides defaults "
        "for all slots; individual inputs override them. "
        "Use Pipe OUT 988 to unpack."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "pipe": (PIPE,),
                **{f"input_{i}": (ANY, {"defaultInput": True}) for i in range(NUM_SLOTS)},
            },
        }

    RETURN_TYPES = (PIPE,)
    RETURN_NAMES = ("pipe",)
    OUTPUT_TOOLTIPS = ("Pipe pass-through — contains all bundled signals.",)
    FUNCTION = "merge"
    CATEGORY = "\U0001f987988/Utility"

    def merge(self, pipe=None, **kwargs):
        new_values = [None] * NUM_SLOTS
        new_types = [None] * NUM_SLOTS

        if pipe is not None:
            existing = pipe.get("values", [])
            for i in range(min(len(existing), NUM_SLOTS)):
                new_values[i] = existing[i]
            existing_types = pipe.get("types", [])
            for i in range(min(len(existing_types), NUM_SLOTS)):
                new_types[i] = existing_types[i]

        for i in range(NUM_SLOTS):
            val = kwargs.get(f"input_{i}")
            if val is not None:
                new_values[i] = val
                new_types[i] = detect_type(val)

        result_pipe = {
            "values": new_values,
            "types": new_types,
            "count": sum(1 for v in new_values if v is not None),
        }

        return (result_pipe,)


NODE_CLASS_MAPPINGS = {"PipeIN988": PipeIN988}
NODE_DISPLAY_NAME_MAPPINGS = {"PipeIN988": "Pipe IN 988"}
