# ComfyUI-988

Collection of useful ComfyUI nodes.

## 🦇 988

Este proyecto está bajo **GNU General Public License v3**. Ver [LICENSE](LICENSE).

### Attribuciones

Este proyecto contiene código adaptado de:

| Proyecto original | Autor | Licencia | Archivos adaptados |
|-------------------|-------|----------|-------------------|
| [EA_LMStudio](https://github.com/EnragedAntelope/EA_LMStudio) | EnragedAntelope | MIT | `node_lm_studio.py`, `node_llm_unload.py`, `_model_fetcher.py`, `_config_manager.py` |
| [ComfyUI_Steudio](https://github.com/Steudio/ComfyUI_Steudio) | Steudio | GPL v3 | `node_dac_algorithm.py`, `node_divide_image_select.py`, `node_combine_tiles.py`, `node_dac_data_scale.py`, `node_display_ui.py`, `js/steudio/` |

| Node | Subcategory | Description |
|------|-------------|-------------|
| **LM Studio 988** | 🦇988/LM Studio | Text generation using local LLM/VLM models via LM Studio server. Supports vision (multi-image), reasoning extraction (DeepSeek, Qwen, QwQ, GLM, GPT-OSS), draft models for speculative decoding, and system message templates. |
| **LM Unload 988** | 🦇988/LM Studio | Passthrough node that unloads LLM models from LM Studio and/or clears ComfyUI VRAM. |
| **DaC Algorithm 988** | 🦇988/Image | Calculate optimal upscale dimensions while maintaining minimum tile overlap and scale factor constraints. Optionally upscale with a model before tiling. |
| **Divide Image Select 988** | 🦇988/Image | Divide the upscaled image into tiles using coordinates from DaC Algorithm. `tile=0` returns all tiles, `tile=N` returns a single tile. |
| **Combine Tiles 988** | 🦇988/Image | Combine processed tiles back into a single image using Gaussian-blurred overlap masks for seamless blending. |
| **DAC Data Scale 988** | 🦇988/Image | Scale all DAC_DATA dimensions (width, height, tile, overlap) by a multiplier. Grid and tile order are preserved unchanged. |
| **Ratio Calculator 988** | 🦇988/Image | Analyse an image and return its closest matching aspect ratio label (e.g. 16:9). |
| **Ratio to Size 988** | 🦇988/Image | Pick an aspect ratio and target megapixel count to get optimal width and height (multiples of 64) within a precision tolerance. |
| **Load Images into List 988** | 🦇988/Image | Load all supported image files from a directory into a batch tensor. Supports jpg, jpeg, png, webp. |
| **Seed Shifter 988** | 🦇988/Number | Generate a batch of reproducible seeds from a base seed + offset. Each seed = base + offset + index. |
| **Sequence Generator 988** | 🦇988/Number | Generate a sequence of numbers. Syntax: `x...y+z` (step), `x...y#z` (evenly spaced), `x,y,z` (literal list). |
| **Simple Config 988** | 🦇988/Utility | Select a sampler and scheduler to pass their string values as individual outputs. |
| **Display UI 988** | 🦇988/Utility | Display any input value as a read-only text box on the node. Accepts strings, numbers, or any wire type. |
| **Pipe IN 988** | 🦇988/Utility | Bundle up to 10 signals of any type into a single PIPE. Autogrow inputs — 2 by default, expands up to 10 as you connect. Auto-detects and displays type + colour on each input socket. |
| **Pipe OUT 988** | 🦇988/Utility | Unpack a PIPE from Pipe IN 988 back into individual signals. Outputs restore the original order, types, colours, and labels. |

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
│   ├── node_dac_algorithm.py       #   DaC Algorithm 988
│   ├── node_divide_image_select.py #   Divide Image Select 988
│   ├── node_combine_tiles.py       #   Combine Tiles 988
│   ├── node_dac_data_scale.py      #   DAC Data Scale 988
│   ├── node_ratio_calculator.py    #   Ratio Calculator 988
│   ├── node_ratio_to_size.py       #   Ratio to Size 988
│   ├── node_load_images_list.py    #   Load Images into List 988
│   ├── node_seed_shifter.py        #   Seed Shifter 988
│   ├── node_sequence_generator.py  #   Sequence Generator 988
│   ├── node_simple_config.py       #   Simple Config 988
│   ├── node_display_ui.py          #   Display UI 988
│   ├── node_pipe_merge.py          #   Pipe IN 988
│   ├── node_pipe_unpack.py         #   Pipe OUT 988
│   ├── _pipe_utils.py       #   Pipe/Bus utilities
│   ├── _config_manager.py   #   Configuration management
│   ├── _model_fetcher.py    #   LM Studio model cache
│   ├── _type_helpers.py     #   Shared type utilities
│   ├── _dac_shared.py       #   DaC shared helpers
│   └── _image_ratios.py     #   Image ratio helpers
├── js/                      # Frontend extensions
│   ├── lm_studio/
│   │   ├── index.js         #   Extension entry point
│   │   ├── model_refresh.mjs
│   │   └── templates.mjs
│   └── steudio/
│       ├── index.js         #   Extension entry point
│       └── show_text.mjs    #   Display UI support
│   └── pipe/
│       └── index.js         #   Pipe IN/OUT: autogrow + type colouring
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