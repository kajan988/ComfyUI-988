"""
LM Unload 988 — passthrough mini-node that triggers unloading of all models
from LM Studio and optionally clears ComfyUI VRAM / CUDA cache.
Accepts any input type and passes it through unchanged.
"""
import logging
import lmstudio as lms
import comfy.model_management as model_management
from ._config_manager import ConfigManager

logger = logging.getLogger("988")
_config_manager = ConfigManager()


class LMUnload988:
    CATEGORY = "\U0001f987988/LM Studio"
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output",)
    OUTPUT_NODE = True
    FUNCTION = "process"

    DESCRIPTION = (
        "LM Unload 988 — a passthrough node that unloads LLM models from "
        "LM Studio and/or clears ComfyUI VRAM. Wire any input through it; "
        "the value passes through unchanged while the unloading happens as "
        "a side effect. Useful at the end of a workflow or before switching "
        "models to free GPU memory."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "trigger": ("*", {
                    "tooltip": "Any input value — passes through unchanged.",
                }),
                "unload_llm": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Unload all LLM models from LM Studio.",
                }),
                "unload_all_models": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Unloads all ComfyUI models from VRAM.",
                }),
                "empty_cuda_cache": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Clears the CUDA cache.",
                }),
            },
        }

    def process(self, trigger, unload_llm=True, unload_all_models=True, empty_cuda_cache=False):
        config = _config_manager.get_config()
        host = config.get("server_host", "127.0.0.1")
        port = config.get("server_port", 1234)
        server_address = f"{host}:{port}"

        if unload_llm:
            try:
                with lms.Client(server_address) as client:
                    loaded_models = client.list_loaded_models()
                    for model_handle in loaded_models:
                        try:
                            model_handle.unload()
                        except Exception as e:
                            logger.warning(f"Failed to unload model: {e}")
            except Exception as e:
                logger.warning(f"Failed to connect to LM Studio for unload: {e}")

        if unload_all_models:
            try:
                model_management.unload_all_models()
            except Exception as e:
                logger.warning(f"Failed to unload ComfyUI models: {e}")
        if empty_cuda_cache:
            try:
                model_management.soft_empty_cache()
            except Exception as e:
                logger.warning(f"Failed to clear CUDA cache: {e}")

        return (trigger,)


NODE_CLASS_MAPPINGS = {"LMUnload988": LMUnload988}
NODE_DISPLAY_NAME_MAPPINGS = {"LMUnload988": "LM Unload 988"}
