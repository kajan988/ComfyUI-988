"""Pipe OUT 988 — split a PIPE back into individual signals."""

from ._type_helpers import ANY
from ._pipe_utils import PIPE, NUM_SLOTS


class PipeOUT988:
    DESCRIPTION = (
        "Unpacks a PIPE from Pipe IN 988 back into individual signals. "
        "Outputs appear in the same order and with the same types as the "
        "original inputs to the IN node."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pipe": (PIPE, {}),
            }
        }

    RETURN_TYPES = tuple(ANY for _ in range(NUM_SLOTS))
    RETURN_NAMES = tuple("ANY" for _ in range(NUM_SLOTS))
    OUTPUT_TOOLTIPS = tuple(
        f"Signal {i} — type detected from Pipe IN input" for i in range(NUM_SLOTS)
    )
    FUNCTION = "unpack"
    CATEGORY = "\U0001f987988/Utility"

    def unpack(self, pipe):
        if pipe is None:
            return tuple(None for _ in range(NUM_SLOTS))
        values = pipe.get("values", [])
        padded = values + [None] * (NUM_SLOTS - len(values))
        return tuple(padded[:NUM_SLOTS])


NODE_CLASS_MAPPINGS = {"PipeOUT988": PipeOUT988}
NODE_DISPLAY_NAME_MAPPINGS = {"PipeOUT988": "Pipe OUT 988"}
