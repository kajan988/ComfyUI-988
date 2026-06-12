"""Display UI 988 — show any value as text in the node body."""
from ._type_helpers import ANY


class DisplayUI988:
    DESCRIPTION = "Display any input value as a read-only text box on the node. Accepts strings, numbers, or any wire type."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"value": (ANY, {})}}

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "show"
    CATEGORY = "\U0001f987988/Utility"

    def show(self, value):
        if isinstance(value, str):
            text = value
        elif isinstance(value, (int, float, bool)):
            text = str(value)
        else:
            text = str(value)
        return {"ui": {"text": [text]}}


NODE_CLASS_MAPPINGS = {"DisplayUI988": DisplayUI988}
NODE_DISPLAY_NAME_MAPPINGS = {"DisplayUI988": "Display UI 988"}