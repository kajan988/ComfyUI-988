"""Pipe OUT 988 — split a PIPE back into individual signals.

First output is a PIPE pass-through for chaining (LP-style).
Outputs 1–10 carry the individual signals.
"""

from ._type_helpers import ANY
from ._pipe_utils import PIPE, NUM_SLOTS


class PipeOUT988:
    DESCRIPTION = (
        "Unpacks a PIPE from Pipe IN 988 back into individual signals. "
        "First output is the pipe pass-through — connect it to the next "
        "Pipe IN to chain pipes. Remaining outputs carry the individual signals."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipe": (PIPE, {}),
            }
        }

    RETURN_TYPES = (PIPE,) + tuple(ANY for _ in range(NUM_SLOTS))
    RETURN_NAMES = ("pipe",) + tuple("ANY" for _ in range(NUM_SLOTS))
    OUTPUT_TOOLTIPS = ("Pipe pass-through.",) + tuple(
        f"Signal {i} — type detected from Pipe IN input" for i in range(NUM_SLOTS)
    )
    FUNCTION = "unpack"
    CATEGORY = "\U0001f987988/Utility"

    def unpack(self, pipe):
        if pipe is None:
            return (None,) + tuple(None for _ in range(NUM_SLOTS))
        values = pipe.get("values", [])
        padded = values + [None] * (NUM_SLOTS - len(values))
        return (pipe,) + tuple(padded[:NUM_SLOTS])


NODE_CLASS_MAPPINGS = {"PipeOUT988": PipeOUT988}
NODE_DISPLAY_NAME_MAPPINGS = {"PipeOUT988": "Pipe OUT 988"}
