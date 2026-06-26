"""Pipe OUT 988 — split a PIPE back into individual signals.

Second output onward is a PIPE pass-through for chaining (LP-style).
Outputs 0–9 preserve index order for backward compatibility.
"""

from ._type_helpers import ANY
from ._pipe_utils import PIPE, NUM_SLOTS


class PipeOUT988:
    DESCRIPTION = (
        "Unpacks a PIPE from Pipe IN 988 back into individual signals. "
        "Outputs 0–9 carry the individual signals. "
        "Last output is the pipe pass-through — connect it to the next "
        "Pipe IN to chain pipes."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipe": (PIPE, {}),
            }
        }

    RETURN_TYPES = tuple(ANY for _ in range(NUM_SLOTS)) + (PIPE,)
    RETURN_NAMES = tuple("ANY" for _ in range(NUM_SLOTS)) + ("pipe",)
    OUTPUT_TOOLTIPS = tuple(
        f"Signal {i} — type detected from Pipe IN input" for i in range(NUM_SLOTS)
    ) + ("Pipe pass-through.",)
    FUNCTION = "unpack"
    CATEGORY = "\U0001f987988/Utility"

    def unpack(self, pipe):
        if pipe is None:
            return tuple(None for _ in range(NUM_SLOTS)) + (None,)
        values = pipe.get("values", [])
        padded = values + [None] * (NUM_SLOTS - len(values))
        return tuple(padded[:NUM_SLOTS]) + (pipe,)


NODE_CLASS_MAPPINGS = {"PipeOUT988": PipeOUT988}
NODE_DISPLAY_NAME_MAPPINGS = {"PipeOUT988": "Pipe OUT 988"}
