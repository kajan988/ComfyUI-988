"""
LM Studio 988 — local LLM/VLM text generation via LM Studio server.

Provides text generation using local LLM/VLM models via LM Studio server
SDK. Supports vision (multi-image), reasoning extraction (DeepSeek, Qwen,
QwQ, GLM, GPT-OSS), draft models for speculative decoding, and system
message templates.
"""
import json
import logging
import re
import copy
from typing import Optional, Tuple, List
import os
import time
from tempfile import NamedTemporaryFile
from pathlib import Path
import numpy as np
from PIL import Image

import lmstudio as lms

import comfy.model_management as model_management

from ._config_manager import ConfigManager
from ._model_fetcher import (
    get_model_display_choices,
    refresh_model_cache,
    resolve_model_id,
    initialize_model_cache,
    validate_model_identifier,
    get_last_fetch_error,
    get_last_fetch_success,
    get_cached_model_count,
    CUSTOM_MODEL_OPTION,
)

logger = logging.getLogger("988")

_config_manager = ConfigManager()
_config_manager.create_user_config_template()
_config_manager.ensure_default_config_exists()

_startup_server_url = _config_manager.get_server_url()
_startup_timeout = _config_manager.get_timeout()
_startup_excluded_patterns = _config_manager.get_excluded_patterns()
initialize_model_cache(_startup_server_url, _startup_timeout, excluded_patterns=_startup_excluded_patterns)

IMAGE_RESIZE_OPTIONS = [
    "No Resize",
    "Low (512px)",
    "Medium (768px)",
    "High (1024px)",
    "Ultra (1536px)",
]

RESIZE_DIMENSIONS = {
    "No Resize": None,
    "Low (512px)": 512,
    "Medium (768px)": 768,
    "High (1024px)": 1024,
    "Ultra (1536px)": 1536,
}

REASONING_MODE_OPTIONS = [
    "Auto-detect (recommended)",
    "Disabled",
    "Custom tags",
]

COMMON_REASONING_PATTERNS = [
    (r"<think>(.*?)</think>", "<think>", "</think>"),
    (r"<thinking>(.*?)</thinking>", "<thinking>", "</thinking>"),
    (r"<reasoning>(.*?)</reasoning>", "<reasoning>", "</reasoning>"),
    (r"<reason>(.*?)</reason>", "<reason>", "</reason>"),
]

GPT_OSS_ANALYSIS_PATTERN = r"<\|channel\|>analysis<\|message\|>(.*?)<\|end\|>"
GPT_OSS_FINAL_PATTERN = r"<\|channel\|>final<\|message\|>(.*?)$"

TEMPLATES_FILE = Path(__file__).parent.parent / "config" / "system_message_templates.json"

# Module-level cache for template choices to reduce file I/O and prevent
# combo list changes between prompt executions.
_template_cache_names: List[str] = ["OFF"]
_template_cache_map: dict = {"OFF": ""}
_template_cache_mtime: float = 0.0


def get_template_choices(force_reload: bool = False):
    """Load system message templates from the JSON file.

    Results are cached at module level to avoid unnecessary file I/O
    and to prevent the combo list from changing between executions
    (which can break ComfyUI's caching).

    Args:
        force_reload: If True, force re-read from file even if cached.

    Returns:
        Tuple of (list_of_names, dict_of_name_to_content).
        Always includes at least "OFF" with empty content.
    """
    global _template_cache_names, _template_cache_map, _template_cache_mtime

    try:
        current_mtime = TEMPLATES_FILE.stat().st_mtime
    except OSError:
        current_mtime = 0.0

    if not force_reload and current_mtime <= _template_cache_mtime:
        return list(_template_cache_names), dict(_template_cache_map)

    try:
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        names = []
        content_map = {}
        for t in data.get("templates", []):
            name = t.get("name", "UNNAMED")
            content = t.get("content", "")
            names.append(name)
            content_map[name] = content
        if not names:
            names = ["OFF"]
            content_map = {"OFF": ""}
        _template_cache_names = names
        _template_cache_map = content_map
        _template_cache_mtime = current_mtime
    except Exception as e:
        logger.warning(f"Failed to load system message templates: {e}")
        if not _template_cache_names:
            _template_cache_names = ["OFF"]
            _template_cache_map = {"OFF": ""}

    return list(_template_cache_names), dict(_template_cache_map)


class LMStudio988:
    """
    LM Studio integration node for ComfyUI.
    Queries local LM Studio server for text generation with LLM/VLM models.

    Note: model.respond() automatically applies the model's chat template.
    """

    CATEGORY = "\U0001f987988/LM Studio"
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("response", "reasoning", "troubleshooting")
    OUTPUT_NODE = True
    FUNCTION = "generate"

    DESCRIPTION = (
        "LM Studio 988 — a node for integrating with LM Studio's local LLM/VLM capabilities."
    )

    @classmethod
    def INPUT_TYPES(cls):
        model_choices = get_model_display_choices()
        default_model = model_choices[0] if model_choices else CUSTOM_MODEL_OPTION
        template_names, _ = get_template_choices()

        return {
            "required": {
                "system_message": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful assistant.",
                    "tooltip": "System prompt that defines the LLM's role and behavior.",
                }),
                "default_system_message": (template_names, {
                    "default": "OFF",
                    "tooltip": "Select a predefined system message template to append after your custom system message.",
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "The user prompt to send to the LLM.",
                }),
                "model_selection": (model_choices, {
                    "default": default_model,
                    "tooltip": "Select a model from LM Studio. Select 'Custom' to manually enter a model identifier.",
                }),
                "custom_model_name": ("STRING", {
                    "default": "",
                    "tooltip": "Manual model identifier. Only used when 'Custom' is selected above.",
                }),
                "max_tokens": ("INT", {
                    "default": 1024, "min": 1, "max": 131072, "step": 1,
                    "tooltip": "Maximum OUTPUT tokens for the response.",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05,
                    "tooltip": "Controls randomness. Lower = focused, Higher = creative.",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "tooltip": "Seed for reproducibility.",
                }),
            },
            "optional": {
                "image_resize": (IMAGE_RESIZE_OPTIONS, {
                    "default": "Medium (768px)",
                    "tooltip": "Resize images before processing. Smaller = faster inference.",
                }),
                "image1": ("IMAGE", {
                    "tooltip": "First image input for vision models (VLMs).",
                }),
                "image2": ("IMAGE", {
                    "tooltip": "Second image input for multi-image VLMs.",
                }),
                "image3": ("IMAGE", {
                    "tooltip": "Third image input for multi-image VLMs.",
                }),
                "image4": ("IMAGE", {
                    "tooltip": "Fourth image input for multi-image VLMs.",
                }),
                "draft_model_selection": (model_choices, {
                    "default": default_model,
                    "tooltip": "Optional draft model for speculative decoding.",
                }),
                "custom_draft_model": ("STRING", {
                    "default": "",
                    "tooltip": "Manual draft model identifier. Leave empty to disable.",
                }),
                "top_p": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Nucleus sampling threshold. 1.0 = disabled.",
                }),
                "top_k": ("INT", {
                    "default": 0, "min": 0, "max": 500, "step": 1,
                    "tooltip": "Top-K sampling. 0 = disabled. Recommended: 20-40 for thinking models.",
                }),
                "repeat_penalty": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05,
                    "tooltip": "Penalizes repeated tokens. 1.0 = disabled.",
                }),
                "reasoning_mode": (REASONING_MODE_OPTIONS, {
                    "default": "Auto-detect (recommended)",
                    "tooltip": "How to extract reasoning/thinking from model output.",
                }),
                "custom_open_tag": ("STRING", {
                    "default": "<think>",
                    "tooltip": "Custom opening tag for reasoning extraction.",
                }),
                "custom_close_tag": ("STRING", {
                    "default": "</think>",
                    "tooltip": "Custom closing tag for reasoning extraction.",
                }),
                "unload_all_models": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Unloads ComfyUI models (SD, VAE, etc.) from VRAM.",
                }),
                "empty_cuda_cache": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Clears the CUDA cache.",
                }),
                "refresh_models": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Toggle ON to re-fetch the model list from LM Studio.",
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs) -> str:
        # When refresh_models is toggled ON, return a truly unique value
        # so the node ALWAYS re-executes (not a constant string).
        if kwargs.get("refresh_models", False):
            return f"__refresh__{time.time()}"

        exclude = {"refresh_models", "image1", "image2", "image3", "image4"}
        try:
            fingerprint = {}
            for k, v in kwargs.items():
                if k in exclude:
                    continue
                # Defensively handle non-serializable types via str()
                try:
                    json.dumps(v)
                    fingerprint[k] = v
                except (TypeError, ValueError):
                    fingerprint[k] = str(v)

            return json.dumps(fingerprint, sort_keys=True)
        except Exception as e:
            # If fingerprinting itself fails, log it and return a unique
            # value so the node re-executes (safe fallback).
            logger.error(f"IS_CHANGED fingerprint failed: {type(e).__name__}: {e}")
            logger.debug(f"IS_CHANGED kwargs: {kwargs}")
            return f"__fallback__{time.time()}_{id(kwargs)}"

    def _resolve_model_identifier(
        self, selection: str, custom_name: str, field_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        if selection == CUSTOM_MODEL_OPTION:
            if not custom_name or not custom_name.strip():
                return None, None
            model_id = custom_name.strip()
        else:
            model_id = resolve_model_id(selection)
        is_valid, error = validate_model_identifier(model_id)
        if not is_valid:
            return None, f"Invalid {field_name}: {error}"
        return model_id, None

    def _resize_image(self, pil_image: Image.Image, max_dimension: Optional[int]) -> Image.Image:
        if max_dimension is None:
            return pil_image
        width, height = pil_image.size
        max_current = max(width, height)
        if max_current <= max_dimension:
            return pil_image
        scale = max_dimension / max_current
        new_width = int(width * scale)
        new_height = int(height * scale)
        return pil_image.resize((new_width, new_height), Image.LANCZOS)

    def _convert_image_to_pil(self, image_tensor, resize_option: str = "No Resize") -> Optional[Image.Image]:
        try:
            if image_tensor is None:
                return None
            if len(image_tensor.shape) == 4:
                img_array = image_tensor[0].cpu().numpy()
            else:
                img_array = image_tensor.cpu().numpy()
            img_array = (img_array * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_array)
            max_dim = RESIZE_DIMENSIONS.get(resize_option)
            if max_dim is not None:
                pil_image = self._resize_image(pil_image, max_dim)
            return pil_image
        except Exception as e:
            logger.error(f"Failed to convert image: {e}")
            return None

    def _extract_reasoning_auto(self, text: str) -> Tuple[str, str, Optional[str]]:
        analysis_match = re.search(GPT_OSS_ANALYSIS_PATTERN, text, re.DOTALL)
        if analysis_match:
            reasoning = analysis_match.group(1).strip()
            final_match = re.search(GPT_OSS_FINAL_PATTERN, text, re.DOTALL)
            if final_match:
                response = final_match.group(1).strip()
            else:
                response = re.sub(GPT_OSS_ANALYSIS_PATTERN, "", text, flags=re.DOTALL)
                response = re.sub(r"<\|start\|>assistant", "", response)
                response = re.sub(r"<\|channel\|>final<\|message\|>", "", response)
                response = re.sub(r"<\|end\|>", "", response)
                response = response.strip()
            return response, reasoning, "<|channel|>analysis"

        for pattern, open_tag, close_tag in COMMON_REASONING_PATTERNS:
            matches = list(re.finditer(pattern, text, re.DOTALL))
            if matches:
                reasoning_parts = [m.group(1) for m in matches]
                clean_text = re.sub(pattern, "", text, flags=re.DOTALL)
                return clean_text.strip(), "\n---\n".join(reasoning_parts).strip(), open_tag

        for _, open_tag, close_tag in COMMON_REASONING_PATTERNS:
            if close_tag in text and open_tag not in text:
                parts = text.split(close_tag, 1)
                if len(parts) == 2:
                    reasoning = parts[0].strip()
                    response = parts[1].strip()
                    if reasoning and response:
                        return response, reasoning, f"{close_tag} (missing open tag)"

        return text, "", None

    def _extract_reasoning_custom(self, text: str, open_tag: str, close_tag: str) -> Tuple[str, str]:
        if not open_tag or open_tag not in text:
            return text, ""
        reasoning_parts = []
        response_text = text
        while open_tag in response_text:
            start_idx = response_text.find(open_tag)
            end_idx = response_text.find(close_tag, start_idx + len(open_tag))
            if end_idx == -1:
                reasoning_parts.append(response_text[start_idx + len(open_tag):])
                response_text = response_text[:start_idx]
                break
            reasoning_content = response_text[start_idx + len(open_tag):end_idx]
            reasoning_parts.append(reasoning_content)
            response_text = response_text[:start_idx] + response_text[end_idx + len(close_tag):]
        return response_text.strip(), "\n---\n".join(reasoning_parts).strip()

    def generate(
        self,
        system_message: str,
        default_system_message: str,
        prompt: str,
        model_selection: str,
        custom_model_name: str,
        max_tokens: int,
        temperature: float,
        seed: int,
        image_resize: str = "Medium (768px)",
        image1=None, image2=None, image3=None, image4=None,
        draft_model_selection: str = CUSTOM_MODEL_OPTION,
        custom_draft_model: str = "",
        top_p: float = 1.0, top_k: int = 0, repeat_penalty: float = 1.0,
        reasoning_mode: str = "Auto-detect (recommended)",
        custom_open_tag: str = "<think>", custom_close_tag: str = "</think>",
        unload_all_models: bool = False, empty_cuda_cache: bool = False,
        refresh_models: bool = False,
    ) -> Tuple[str, str, str]:
        troubleshooting_lines = []

        config = _config_manager.get_config()
        server_url = _config_manager.get_server_url()
        timeout = _config_manager.get_timeout()
        excluded_patterns = config.get("excluded_model_patterns", [])

        troubleshooting_lines.append(f"[INFO] Server: {server_url}")
        troubleshooting_lines.append(f"[INFO] Cached models: {get_cached_model_count()}")

        if refresh_models:
            success, message = refresh_model_cache(server_url, timeout, excluded_patterns=excluded_patterns)
            if success:
                troubleshooting_lines.append(f"[INFO] Model refresh: {message}")
            else:
                troubleshooting_lines.append(f"[WARNING] Model refresh failed: {message}")

        last_error = get_last_fetch_error()
        if last_error and not get_last_fetch_success():
            troubleshooting_lines.append(f"[WARNING] Startup model fetch: {last_error}")

        model_identifier, error = self._resolve_model_identifier(model_selection, custom_model_name, "model")
        if error:
            troubleshooting_lines.append(f"[ERROR] {error}")
            return "", "", "\n".join(troubleshooting_lines)
        if not model_identifier:
            error_msg = "No model selected. Choose a model from dropdown or enter a custom model name."
            troubleshooting_lines.append(f"[ERROR] {error_msg}")
            return "", "", "\n".join(troubleshooting_lines)
        troubleshooting_lines.append(f"[INFO] Model: {model_identifier}")

        draft_model, error = self._resolve_model_identifier(draft_model_selection, custom_draft_model, "draft model")
        if error:
            troubleshooting_lines.append(f"[WARNING] Draft model error: {error}")
            draft_model = None
        elif draft_model:
            troubleshooting_lines.append(f"[INFO] Draft model: {draft_model}")

        if unload_all_models:
            troubleshooting_lines.append("[INFO] Unloading ComfyUI models...")
            model_management.unload_all_models()
        if empty_cuda_cache:
            troubleshooting_lines.append("[INFO] Clearing CUDA cache...")
            model_management.soft_empty_cache()

        image_inputs = [image1, image2, image3, image4]
        pil_images: List[Image.Image] = []
        for idx, img_tensor in enumerate(image_inputs, start=1):
            if img_tensor is not None:
                pil_img = self._convert_image_to_pil(img_tensor, image_resize)
                if pil_img:
                    pil_images.append(pil_img)
                    if image_resize != "No Resize":
                        troubleshooting_lines.append(f"[INFO] Image {idx}: {pil_img.size[0]}x{pil_img.size[1]} (resized)")
                    else:
                        troubleshooting_lines.append(f"[INFO] Image {idx}: {pil_img.size[0]}x{pil_img.size[1]}")
                else:
                    troubleshooting_lines.append(f"[WARNING] Failed to process image {idx}")
        if pil_images:
            troubleshooting_lines.append(f"[INFO] Total images for VLM: {len(pil_images)}")

        try:
            troubleshooting_lines.append("[INFO] Connecting to LM Studio...")
            host = config.get("server_host", "127.0.0.1")
            port = config.get("server_port", 1234)
            server_address = f"{host}:{port}"

            with lms.Client(server_address) as client:
                model = client.llm.model(model_identifier)
                troubleshooting_lines.append(f"[INFO] Model loaded: {model_identifier}")

                _, template_content_map = get_template_choices()
                template_content = template_content_map.get(default_system_message, "")
                if template_content:
                    effective_system = f"{system_message}\n\n{template_content}"
                else:
                    effective_system = system_message

                chat = lms.Chat(effective_system)

                if pil_images:
                    image_handles = []
                    temp_paths = []
                    try:
                        for pil_img in pil_images:
                            with NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
                                pil_img.save(temp, format="JPEG", quality=95)
                                temp.flush()
                                temp_paths.append(temp.name)
                                image_handle = client.files.prepare_image(temp.name)
                                image_handles.append(image_handle)
                        chat.add_user_message(prompt, images=image_handles)
                    finally:
                        for path in temp_paths:
                            try:
                                os.unlink(path)
                            except OSError:
                                pass
                else:
                    chat.add_user_message(prompt)

                gen_config = {
                    "temperature": temperature,
                    "maxTokens": max_tokens,
                    "contextOverflowPolicy": "truncateMiddle",
                }
                if top_p < 1.0:
                    gen_config["topPSampling"] = top_p
                if top_k > 0:
                    gen_config["topKSampling"] = top_k
                if repeat_penalty != 1.0:
                    gen_config["repeatPenalty"] = repeat_penalty
                if draft_model:
                    gen_config["draftModel"] = draft_model

                troubleshooting_lines.append(f"[INFO] Config: maxTokens={max_tokens}, temp={temperature}, seed={seed}")
                if top_k > 0:
                    troubleshooting_lines.append(f"[INFO] Sampling: top_k={top_k}, top_p={top_p}")
                troubleshooting_lines.append("[INFO] Generating...")

                start_time = time.time()
                response = model.respond(chat, config=gen_config)
                response_text = str(response)
                troubleshooting_lines.append("[INFO] Generation complete")
                troubleshooting_lines.append(f"[INFO] Raw response length: {len(response_text)} chars")

                tokens_per_sec = getattr(response.stats, 'tokens_per_second', 0.0)
                input_tokens = getattr(response.stats, 'prompt_tokens_count', 0)
                output_tokens = getattr(response.stats, 'predicted_tokens_count', 0)
                time_to_first_token = getattr(response.stats, 'time_to_first_token_sec', None)
                stop_reason = getattr(response.stats, 'stop_reason', 'unknown')
                elapsed = time.time() - start_time

                troubleshooting_lines.append(f"[INFO] Tokens per second: {tokens_per_sec:.2f}")
                troubleshooting_lines.append(f"[INFO] Input tokens: {input_tokens}")
                troubleshooting_lines.append(f"[INFO] Output tokens: {output_tokens}")
                if time_to_first_token is not None:
                    troubleshooting_lines.append(f"[INFO] Time to first token: {time_to_first_token:.3f}s")
                troubleshooting_lines.append(f"[INFO] Stop reason: {stop_reason}")
                troubleshooting_lines.append(f"[INFO] Total time: {elapsed:.2f}s")

                final_response = response_text
                reasoning = ""
                if reasoning_mode == "Auto-detect (recommended)":
                    final_response, reasoning, detected_pattern = self._extract_reasoning_auto(response_text)
                    if detected_pattern:
                        troubleshooting_lines.append(f"[INFO] Auto-detected reasoning format: {detected_pattern}")
                    else:
                        troubleshooting_lines.append("[INFO] No reasoning tags detected")
                elif reasoning_mode == "Custom tags":
                    final_response, reasoning = self._extract_reasoning_custom(response_text, custom_open_tag, custom_close_tag)

                if reasoning:
                    troubleshooting_lines.append(f"[INFO] Extracted reasoning: {len(reasoning)} chars")
                    troubleshooting_lines.append(f"[INFO] Clean response: {len(final_response)} chars")

                return final_response, reasoning, "\n".join(troubleshooting_lines)

        except Exception as e:
            error_msg = f"Generation failed: {type(e).__name__}: {e}"
            troubleshooting_lines.append(f"[ERROR] {error_msg}")
            error_str = str(e).lower()
            if "connection" in error_str or "refused" in error_str:
                troubleshooting_lines.append("[HINT] Ensure LM Studio is running with server enabled")
            elif "context" in error_str or "length" in error_str or "2048" in error_str:
                troubleshooting_lines.append("[HINT] Context length exceeded. In LM Studio, increase the model's context length setting")
            elif "not found" in error_str or "model" in error_str:
                troubleshooting_lines.append("[HINT] Check model identifier matches LM Studio exactly")
            elif "image" in error_str or "vision" in error_str or "multi" in error_str:
                troubleshooting_lines.append("[HINT] This model may not support images or multiple image inputs.")
            logger.exception("LM Studio 988 generation error")
            return "", "", "\n".join(troubleshooting_lines)


NODE_CLASS_MAPPINGS = {"LMStudio988": LMStudio988}
NODE_DISPLAY_NAME_MAPPINGS = {"LMStudio988": "LM Studio 988"}
