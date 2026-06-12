"""
Configuration manager for 988 LM Studio node.
Handles server settings with gitignore-protected user config.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List


logger = logging.getLogger("988")

DEFAULT_CONFIG: Dict[str, Any] = {
    "server_host": "127.0.0.1",
    "server_port": 1234,
    "timeout_seconds": 5,
    "excluded_model_patterns": ["embedding"],
}


class ConfigManager:
    """Manages LM Studio configuration with user override support."""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.default_config_path = self.config_dir / "default_config.json"
        self.user_config_path = self.config_dir / "user_config.json"

    def get_config(self) -> Dict[str, Any]:
        config = DEFAULT_CONFIG.copy()
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    for key in DEFAULT_CONFIG.keys():
                        if key in user_config:
                            config[key] = user_config[key]
                logger.debug(f"Loaded user config from {self.user_config_path}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in user_config.json: {e}. Using defaults.")
            except IOError as e:
                logger.warning(f"Could not read user_config.json: {e}. Using defaults.")
        return config

    def get_server_url(self) -> str:
        config = self.get_config()
        host = config.get("server_host", "127.0.0.1")
        port = config.get("server_port", 1234)
        return f"http://{host}:{port}"

    def get_timeout(self) -> float:
        config = self.get_config()
        return float(config.get("timeout_seconds", 5))

    def get_excluded_patterns(self) -> List[str]:
        config = self.get_config()
        val = config.get("excluded_model_patterns")
        result: List[str] = list(DEFAULT_CONFIG["excluded_model_patterns"])
        if isinstance(val, list):
            for p in val:
                if isinstance(p, str) and p not in result:
                    result.append(p)
        elif val is not None:
            logger.warning("excluded_model_patterns in user_config.json is not a list.")
        return result

    def create_user_config_template(self) -> None:
        if not self.user_config_path.exists():
            template = {
                "_comment": "988 LM Studio user configuration. This file is gitignored and survives updates.",
                "_instructions": "Modify values below to override defaults. Delete this file to reset.",
                "server_host": "127.0.0.1",
                "server_port": 1234,
                "timeout_seconds": 5,
                "excluded_model_patterns": ["embedding"],
            }
            try:
                with open(self.user_config_path, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=2)
                logger.info(f"Created user config template at {self.user_config_path}")
            except IOError as e:
                logger.warning(f"Could not create user_config.json template: {e}")

    def ensure_default_config_exists(self) -> None:
        if not self.default_config_path.exists():
            try:
                reference = {
                    "_comment": "Default configuration reference. Do not edit. Create user_config.json to override.",
                    **DEFAULT_CONFIG,
                }
                with open(self.default_config_path, "w", encoding="utf-8") as f:
                    json.dump(reference, f, indent=2)
            except IOError:
                pass
