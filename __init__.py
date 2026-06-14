"""
ComfyUI-988 — collection of useful nodes for ComfyUI.
Licensed under GNU General Public License v3. See LICENSE.
"""

from ._988_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

from . import server_routes  # noqa: F401, E402

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# ── Startup banner (red) ──────────────────────────
import os

def _display_988_banner(node_mappings):
    version = "?"
    try:
        import toml
        _p = os.path.join(os.path.dirname(__file__), 'pyproject.toml')
        with open(_p, "r", encoding="utf-8") as f:
            version = toml.load(f).get("project", {}).get("version", "?")
    except Exception:
        pass
    R = "\033[38;2;220;40;40m"
    B = "\033[1;97m"
    G = "\033[0;37m"
    X = "\033[0m"
    _BOX = "\u2501"
    bar = f"{R}{_BOX * 100}{X}"
    print(bar)
    print(f"  {B}9.8.8.NODES{X}  v{version}  |  {R}{len(node_mappings)} node(s){X} Loaded")
    _names = sorted(node_mappings.values())
    _line = ""
    for i, _n in enumerate(_names):
        _e = f"{_n}, " if i != len(_names) - 1 else _n
        if _line and len(_line) + len(_e) > 100:
            print("  " + G + _line.rstrip(", ") + X)
            _line = ""
        _line += _e
    if _line:
        print("  " + G + _line.rstrip(", ") + X)
    print(f"  {G}This is a notice, not an error. All {R}9.8.8.NODES{G} work in both Classic and Nodes 2.0 mode.{X}")
    print(bar)

_display_988_banner(NODE_DISPLAY_NAME_MAPPINGS)
