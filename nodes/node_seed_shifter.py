"""Seed Shifter 988 — generate reproducible batch seeds with offset."""


class SeedShifter988:
    DESCRIPTION = "Generate a batch of reproducible seeds from a base seed + offset. Each seed = base + offset + index."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
                "seed_shifter": ("INT", {"default": 0, "min": 0}),
                "batch": ("INT", {"default": 1, "min": 1}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seeds",)
    OUTPUT_IS_LIST = (True,)
    OUTPUT_TOOLTIPS = ("List of batch seeds",)
    FUNCTION = "shift"
    CATEGORY = "\U0001f987988/Number"

    def shift(self, seed, seed_shifter, batch):
        return ([seed + seed_shifter + i for i in range(batch)],)


NODE_CLASS_MAPPINGS = {"SeedShifter988": SeedShifter988}
NODE_DISPLAY_NAME_MAPPINGS = {"SeedShifter988": "Seed Shifter 988"}