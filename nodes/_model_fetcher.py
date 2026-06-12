"""
Model fetcher for 988 LM Studio node.
Queries LM Studio server for available models via REST API.
Detects model capabilities (vision, tool use, reasoning) for emoji indicators.
"""
import re
import requests
import logging
from typing import List, Optional, Dict, Tuple, Any


logger = logging.getLogger("988")

_cached_models: List[str] = []
_cached_model_data: List[Dict[str, Any]] = []
_model_capabilities: Dict[str, Dict[str, bool]] = {}
_display_name_to_model_id: Dict[str, str] = {}
_last_fetch_error: Optional[str] = None
_last_fetch_success: bool = False

CUSTOM_MODEL_OPTION = "-- Custom (enter below) --"

CAP_VISION = "\U0001f441\ufe0f"
CAP_TOOL_USE = "\U0001f528"
CAP_REASONING = "\U0001f9e0"

REASONING_ARCHS = frozenset(["qwen35", "qwen35moe", "gemma4"])


def validate_model_identifier(model_id: str) -> Tuple[bool, Optional[str]]:
    if not model_id or not model_id.strip():
        return False, "Model identifier is empty"
    model_id = model_id.strip()
    if ".." in model_id:
        return False, "Model identifier contains invalid path traversal (..)"
    if len(model_id) > 256:
        return False, "Model identifier exceeds maximum length (256 characters)"
    if not re.match(r"^[\w\-.:@/]+$", model_id):
        return False, "Model identifier contains invalid characters (only alphanumeric, hyphens, underscores, dots, colons, @, and slashes allowed)"
    return True, None


def _is_excluded(model_id: str, excluded_patterns: List[str]) -> bool:
    if not excluded_patterns or not model_id:
        return False
    model_id_lower = model_id.lower()
    return any(pattern in model_id_lower for pattern in excluded_patterns)

def _detect_vision(model_entry: Dict[str, Any]) -> bool:
    if model_entry.get("type") == "vlm":
        return True
    model_id = model_entry.get("id", "")
    if "vision" in model_id.lower():
        return True
    return False


def _detect_tool_use(model_entry: Dict[str, Any]) -> bool:
    capabilities = model_entry.get("capabilities", [])
    if isinstance(capabilities, list) and "tool_use" in capabilities:
        return True
    arch = model_entry.get("arch", "")
    if "qwen3" in arch.lower():
        return True
    return False


def _detect_reasoning(model_entry: Dict[str, Any]) -> bool:
    arch = model_entry.get("arch", "")
    if arch in REASONING_ARCHS:
        return True
    model_id = model_entry.get("id", "").lower()
    if "r1" in model_id or "writer" in model_id:
        return True
    return False


def _build_capabilities_dict(model_entry: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "vision": _detect_vision(model_entry),
        "tool_use": _detect_tool_use(model_entry),
        "reasoning": _detect_reasoning(model_entry),
    }


def _get_capability_emoji(caps: Dict[str, bool]) -> str:
    parts = []
    if caps.get("vision"):
        parts.append(CAP_VISION)
    if caps.get("tool_use"):
        parts.append(CAP_TOOL_USE)
    if caps.get("reasoning"):
        parts.append(CAP_REASONING)
    return " ".join(parts)


def _build_display_name(model_id: str, caps: Dict[str, bool]) -> str:
    emoji_str = _get_capability_emoji(caps)
    if emoji_str:
        return f"{model_id}  {emoji_str}"
    return model_id


def _parse_v0_response(data: dict) -> List[Dict[str, Any]]:
    entries = []
    for entry in data.get("data", []):
        model_id = entry.get("id", "")
        if not model_id:
            continue
        is_valid, _ = validate_model_identifier(model_id)
        if is_valid:
            entries.append({
                "id": model_id,
                "arch": entry.get("arch", "") or "",
                "type": entry.get("type", "") or "",
                "capabilities": entry.get("capabilities", []) or [],
            })
    return entries


def _parse_v1_response(data: dict) -> List[Dict[str, Any]]:
    entries = []
    for entry in data.get("data", []):
        model_id = entry.get("id", "")
        if not model_id:
            continue
        is_valid, _ = validate_model_identifier(model_id)
        if is_valid:
            entries.append({
                "id": model_id,
                "arch": "",
                "type": "",
                "capabilities": [],
            })
    return entries

def fetch_model_data_from_server(
    server_url: str,
    timeout: float = 5.0,
    excluded_patterns: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if excluded_patterns is None:
        excluded_patterns = ["embedding"]
    base = server_url.rstrip("/")
    tried_v0 = False
    entries: List[Dict[str, Any]] = []

    try:
        v0_url = f"{base}/api/v0/models"
        resp = requests.get(v0_url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        entries = _parse_v0_response(data)
        tried_v0 = True
        logger.info("988: Fetched %d models from %s (with capabilities)", len(entries), v0_url)
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except Exception:
        pass

    if not tried_v0:
        try:
            v1_url = f"{base}/v1/models"
            resp = requests.get(v1_url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            entries = _parse_v1_response(data)
            logger.info("988: Fetched %d models from %s (basic, no capabilities)", len(entries), v1_url)
        except requests.exceptions.ConnectionError:
            error = f"Cannot connect to LM Studio at {server_url}. Ensure LM Studio is running with server enabled."
            logger.warning("988: %s", error)
            return [], error
        except requests.exceptions.Timeout:
            error = f"Connection to LM Studio timed out ({timeout}s). Server may be busy or unreachable."
            logger.warning("988: %s", error)
            return [], error
        except requests.exceptions.HTTPError as e:
            error = f"LM Studio returned HTTP error: {e.response.status_code}"
            logger.warning("988: %s", error)
            return [], error
        except Exception as e:
            error = f"Unexpected error fetching models: {type(e).__name__}: {str(e)}"
            logger.error("988: %s", error)
            return [], error

    filtered = [e for e in entries if not _is_excluded(e["id"], excluded_patterns)]
    filtered.sort(key=lambda e: e["id"].lower())
    return filtered, None


def refresh_model_cache(
    server_url: str,
    timeout: float = 5.0,
    excluded_patterns: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    global _cached_models, _cached_model_data, _model_capabilities
    global _display_name_to_model_id, _last_fetch_error, _last_fetch_success

    entries, error = fetch_model_data_from_server(server_url, timeout, excluded_patterns)
    if error:
        _last_fetch_error = error
        _last_fetch_success = False
        return False, error

    _cached_model_data = entries
    _cached_models = [e["id"] for e in entries]
    _model_capabilities = {e["id"]: _build_capabilities_dict(e) for e in entries}

    mapping: Dict[str, str] = {}
    for e in entries:
        caps = _model_capabilities[e["id"]]
        display_name = _build_display_name(e["id"], caps)
        mapping[display_name] = e["id"]
    _display_name_to_model_id = mapping

    _last_fetch_error = None
    _last_fetch_success = True

    count = len(_cached_models)
    if count:
        return True, f"Successfully loaded {count} models from LM Studio"
    else:
        return True, "Connected to LM Studio but no models found (embedding models are excluded)"


def initialize_model_cache(server_url: str, timeout: float = 5.0, excluded_patterns=None) -> None:
    success, message = refresh_model_cache(server_url, timeout, excluded_patterns=excluded_patterns)
    if not success:
        logger.warning("988 startup: %s", message)


def get_model_choices() -> List[str]:
    choices = [CUSTOM_MODEL_OPTION]
    choices.extend(_cached_models)
    return choices


def get_model_display_choices() -> List[str]:
    global _display_name_to_model_id
    choices = [CUSTOM_MODEL_OPTION]
    mapping: Dict[str, str] = {}
    for model_id in _cached_models:
        caps = _model_capabilities.get(model_id, {})
        display_name = _build_display_name(model_id, caps)
        mapping[display_name] = model_id
        choices.append(display_name)
    _display_name_to_model_id = mapping
    return choices


def resolve_model_id(display_name: str) -> str:
    if not display_name or display_name == CUSTOM_MODEL_OPTION:
        return display_name
    if display_name in _display_name_to_model_id:
        return _display_name_to_model_id[display_name]
    has_emoji = any(e in display_name for e in (CAP_VISION, CAP_TOOL_USE, CAP_REASONING))
    if not has_emoji:
        return display_name
    cleaned = display_name
    for e in (CAP_VISION, CAP_TOOL_USE, CAP_REASONING):
        cleaned = cleaned.replace(e, "")
    cleaned = cleaned.replace("\ufe0f", "")
    cleaned = " ".join(cleaned.split())
    return cleaned


def get_models_with_capabilities() -> List[Dict[str, Any]]:
    return [
        {"id": mid, "vision": caps.get("vision", False), "tool_use": caps.get("tool_use", False), "reasoning": caps.get("reasoning", False)}
        for mid, caps in _model_capabilities.items()
    ]


def get_last_fetch_error() -> Optional[str]:
    return _last_fetch_error


def get_last_fetch_success() -> bool:
    return _last_fetch_success


def get_cached_model_count() -> int:
    return len(_cached_models)
