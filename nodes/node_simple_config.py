"""Simple Config 988 — pass through sampler settings as separate outputs."""
import comfy.samplers


class SimpleConfig988:
    DESCRIPTION = "Select a sampler and scheduler to pass their string values as individual outputs."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "steps": ("INT", {"default": 24, "min": 1, "max": 99}),
                "sampler": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
            },
        }

    RETURN_TYPES = ("INT", comfy.samplers.KSampler.SAMPLERS, comfy.samplers.KSampler.SCHEDULERS)
    RETURN_NAMES = ("steps", "sampler", "scheduler")
    OUTPUT_TOOLTIPS = ("Number of sampling steps", "Sampler name string", "Scheduler name string")
    FUNCTION = "run"
    CATEGORY = "\U0001f987988/Utility"

    def run(self, steps, sampler, scheduler):
        return (steps, sampler, scheduler)


NODE_CLASS_MAPPINGS = {"SimpleConfig988": SimpleConfig988}
NODE_DISPLAY_NAME_MAPPINGS = {"SimpleConfig988": "Simple Config 988"}