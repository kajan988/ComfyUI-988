"""
Model fetcher for 988 LM Studio node.
Queries LM Studio server for available models — tries /api/v0/models for
vision capability detection, falls back to /v1/models.
Only the eye emoji (👁️) is used to mark vision-capable (VLM) models.
"""
import re
import requests
import logging
from typing import List, Optional, Dict, Tuple, Any


logger = logging.getLogger("988")

_cached_models: List[str] = []               # plain model IDs
_cached_model_data: List[Dict[str, Any]] = [] # raw entries from v0 (if available)
_model_vision: Dict[str, bool] = {}          # model_id → is_vision
_last_fetch_error: Optional[str] = None
_last_fetch_success: bool = False

CUSTOM_MODEL_OPTION = "-- Custom (enter below) --"
CAP_VISION = "\U0001f441\ufe0f"  # 👁


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


def _has_vision(endpoint: str, timeout: float) -> Optional[Dict[str, bool]]:
    """Try /api/v0/models and return {model_id: vision_flag} if successful.
    Detects VLM purely from the `type` field (``type == \"vlm\"``) — no name-based heuristics."""
    try:
        resp = requests.get(endpoint, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        result: Dict[str, bool] = {}
        for entry in data.get("data", []):
            mid = entry.get("id", "")
            if not mid or not validate_model_identifier(mid)[0]:
                continue
            # VLM detection: only the v0 endpoint's type field
            is_vlm = entry.get("type") == "vlm"
            result[mid] = is_vlm
        return result if result else None
    except Exception:
        return None


def _parse_v1_models(endpoint: str, timeout: float) -> List[str]:
    """Fetch models via /v1/models endpoint."""
    resp = requests.get(endpoint, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    models: List[str] = []
    for entry in data.get("data", []):
        mid = entry.get("id", "")
        if mid and validate_model_identifier(mid)[0]:
            models.append(mid)
    return models


def fetch_models_from_server(
    server_url: str,
    timeout: float = 5.0,
    excluded_patterns: Optional[List[str]] = None,
) -> Tuple[List[str], Dict[str, bool], Optional[str]]:
    """
    Fetch models from LM Studio. Tries /api/v0/models first for vision data,
    falls back to /v1/models if v0 is unavailable.

    Returns:
        (model_ids, vision_map, error_message)
    """
    if excluded_patterns is None:
        excluded_patterns = ["embedding"]

    base = server_url.rstrip("/")
    v0_url = f"{base}/api/v0/models"
    v1_url = f"{base}/v1/models"

    # Try v0 (with capabilities)
    vision_map = _has_vision(v0_url, timeout)
    models: List[str] = []

    if vision_map is not None:
        # v0 succeeded — get model IDs from the vision map keys
        models = list(vision_map.keys())
        logger.info(f"988: Fetched {len(models)} models from {v0_url} (with vision data)")
    else:
        # v0 failed — fallback to v1 (no capability data)
        try:
            models = _parse_v1_models(v1_url, timeout)
            vision_map = {m: False for m in models}
            logger.info(f"988: Fetched {len(models)} models from {v1_url} (basic, no vision data)")
        except requests.exceptions.ConnectionError:
            err = f"Cannot connect to LM Studio at {server_url}. Ensure LM Studio is running with server enabled."
            logger.warning(f"988: {err}")
            return [], {}, err
        except requests.exceptions.Timeout:
            err = f"Connection to LM Studio timed out ({timeout}s). Server may be busy or unreachable."
            logger.warning(f"988: {err}")
            return [], {}, err
        except requests.exceptions.HTTPError as e:
            err = f"LM Studio returned HTTP error: {e.response.status_code}"
            logger.warning(f"988: {err}")
            return [], {}, err
        except Exception as e:
            err = f"Unexpected error fetching models: {type(e).__name__}: {str(e)}"
            logger.error(f"988: {err}")
            return [], {}, err

    # Filter excluded patterns
    filtered_models: List[str] = []
    filtered_vision: Dict[str, bool] = {}
    for mid in models:
        if _is_excluded(mid, excluded_patterns):
            continue
        filtered_models.append(mid)
        filtered_vision[mid] = vision_map.get(mid, False)

    filtered_models.sort(key=str.lower)
    return filtered_models, filtered_vision, None


def _build_display_name(model_id: str, is_vision: bool) -> str:
    """Build display name: model_id + 👁️ if vision-capable."""
    if is_vision:
        return f"{model_id}  {CAP_VISION}"
    return model_id


def refresh_model_cache(
    server_url: str,
    timeout: float = 5.0,
    excluded_patterns: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    global _cached_models, _cached_model_data, _model_vision
    global _last_fetch_error, _last_fetch_success

    models, vision_map, error = fetch_models_from_server(server_url, timeout, excluded_patterns)

    if error:
        _last_fetch_error = error
        _last_fetch_success = False
        return False, error

    _cached_models = models
    _model_vision = vision_map
    _last_fetch_error = None
    _last_fetch_success = True

    count = len(models)
    if count:
        return True, f"Successfully loaded {count} models from LM Studio"
    else:
        return True, "Connected to LM Studio but no models found (embedding models are excluded)"


def initialize_model_cache(server_url: str, timeout: float = 5.0, excluded_patterns=None) -> None:
    success, message = refresh_model_cache(server_url, timeout, excluded_patterns=excluded_patterns)
    if not success:
        logger.warning(f"988 startup: {message}")


def get_model_choices() -> List[str]:
    """Return display names (plain ID or ID + 👁️)."""
    choices = [CUSTOM_MODEL_OPTION]
    for mid in _cached_models:
        choices.append(_build_display_name(mid, _model_vision.get(mid, False)))
    return choices


def resolve_model_id(display_name: str) -> str:
    """Strip the 👁️ emoji from a display name to get the plain model ID."""
    if not display_name or display_name == CUSTOM_MODEL_OPTION:
        return display_name
    # Remove CAP_VISION and variation selector
    cleaned = display_name.replace(CAP_VISION, "").replace("\ufe0f", "")
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else display_name


def get_last_fetch_error() -> Optional[str]:
    return _last_fetch_error


def get_last_fetch_success() -> bool:
    return _last_fetch_success


def get_cached_model_count() -> int:
    return len(_cached_models)
