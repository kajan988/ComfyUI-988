"""
Server API routes for 988 nodes.
Registered as side-effect import in __init__.py.
"""
from aiohttp import web
from server import PromptServer

from .nodes._model_fetcher import refresh_model_cache, get_model_choices, CUSTOM_MODEL_OPTION
from .nodes._config_manager import ConfigManager


@PromptServer.instance.routes.post("/988/lm_studio/refresh_models")
async def refresh_models_route(request):
    """API endpoint to refresh model list from LM Studio server."""
    config_manager = ConfigManager()
    server_url = config_manager.get_server_url()
    timeout = config_manager.get_timeout()
    excluded_patterns = config_manager.get_excluded_patterns()

    print(f"[988] refresh_models_route called — server={server_url}, timeout={timeout}")

    success, message = refresh_model_cache(server_url, timeout, excluded_patterns=excluded_patterns)
    models = get_model_choices()[1:]  # skip CUSTOM_MODEL_OPTION

    print(f"[988] refresh_models_route result — success={success}, message='{message}', models={len(models)}")

    return web.json_response({
        "success": success,
        "message": message,
        "models": models,
    })


@PromptServer.instance.routes.post("/988/lm_studio/refresh_templates")
async def refresh_templates_route(request):
    """API endpoint to get current system message templates."""
    from .nodes.node_lm_studio import get_template_choices
    names, content_map = get_template_choices()
    templates = [{"name": n, "content": content_map[n]} for n in names]
    return web.json_response({
        "success": True,
        "templates": templates,
    })
