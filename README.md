# ComfyUI-988

Collection of useful ComfyUI nodes.

## 🦇 988 Kajan nodes

### Responsibilities

This project contains code adapted from:

| Original project | Author | Licence | Adapted files |
|-------------------|-------|----------|-------------------|
| [EA_LMStudio](https://github.com/EnragedAntelope/EA_LMStudio) | EnragedAntelope | MIT | `node_lm_studio.py`, `node_llm_unload.py`, `_model_fetcher.py`, `_config_manager.py` |
| [ComfyUI_Steudio](https://github.com/Steudio/ComfyUI_Steudio) | Steudio | GPL v3 | `node_dac_algorithm_v2.py`, `node_divide_image_select.py`, `node_combine_tiles_v2.py`, `node_dac_data_scale.py` |
| [ComfyUI-Photopea](https://github.com/coolzilj/ComfyUI-Photopea) | coolzilj | MIT | `js/photopea/` |

| Node | Subcategory | Description |
|------|-------------|-------------|
| **LM Studio 988** | 🦇988/LM Studio | Text generation using local LLM/VLM models via LM Studio server. Supports vision (multi-image), reasoning extraction (DeepSeek, Qwen, QwQ, GLM, GPT-OSS), draft models for speculative decoding, and system message templates. |
| **LM Unload 988** | 🦇988/LM Studio | OPTIONAL Passthrough node that unloads LLM models from LM Studio and/or clears ComfyUI VRAM. |
| **DaC Algorithm 988 v2** | 🦇988/Image | Calculate optimal upscale dimensions for a minimum scale factor while maintaining tile overlap constraints. |
| **Divide Image Select 988** | 🦇988/Image | Divide the upscaled image into tiles using coordinates from DaC Algorithm. `tile=0` returns all tiles, `tile=N` returns a single tile. |
| **Combine Tiles 988 v2** | 🦇988/Image | Combine processed tiles back into a single image using Gaussian-blurred overlap masks for seamless blending. |
| **DAC Data Scale 988** | 🦇988/Image | Scale all DAC_DATA dimensions (width, height, tile, overlap) by a multiplier. Grid and tile order are preserved unchanged. |

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/your-username/ComfyUI-988.git
cd ComfyUI-988
pip install -r requirements.txt
```

## Structure

```
ComfyUI-988/
├── __init__.py              # Aggregates all node mappings
├── server_routes.py         # Server API routes
├── nodes/                   # Python node implementations
│   ├── node_lm_studio.py    #   LM Studio 988
│   ├── node_llm_unload.py   #   LM Unload 988
│   ├── node_dac_algorithm_v2.py     #   DaC Algorithm 988 v2
│   ├── node_divide_image_select.py #   Divide Image Select 988
│   ├── node_combine_tiles_v2.py    #   Combine Tiles 988 v2
│   ├── node_dac_data_scale.py      #   DAC Data Scale 988
│   ├── _config_manager.py   #   Configuration management
│   ├── _model_fetcher.py    #   LM Studio model cache
│   └── _dac_shared.py       #   DaC shared helpers
├── js/                      # Frontend extensions
│   ├── lm_studio/
│   │   ├── index.js         #   Extension entry point
│   │   ├── model_refresh.mjs
│   │   └── templates.mjs
│   └── photopea/
│       └── index.js         #   Photopea integration
├── config/                  # Configuration files
│   ├── default_config.json
│   ├── system_message_templates.json
│   └── user_config.json     # Gitignored — local overrides
├── workflows/               # Example workflows
│   ├── DaC_Upscale.json
│   └── DaC_Upscale.jpg
├── requirements.txt
├── pyproject.toml
└── .gitignore
```