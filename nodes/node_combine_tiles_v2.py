"""Combine Tiles 988 v2 — merge tiles with auto-resize to match DAC_DATA dimensions."""
import torch
from comfy.utils import common_upscale
from ._dac_shared import create_tile_coordinates, blend_tile_mask

BLEND_MODES = [
    "auto (actual + cap)",
    "actual overlap only",
    "cap 128px",
]


class CombineTilesV2988:
    DESCRIPTION = "Combine processed tiles back into a single image. Auto-resizes tiles to match DAC_DATA tile dimensions when a mismatch is detected, using NVIDIA RTX VSR."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "dac_data": ("DAC_DATA",),
                "blend_mode": (BLEND_MODES, {"default": "auto (actual + cap)"}),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "matrix", "info")
    OUTPUT_TOOLTIPS = ("Combined full-resolution image", "Visual tile matrix string", "Detailed resize and blend diagnostic info")
    FUNCTION = "execute"
    CATEGORY = "\U0001f987988/Image"

    def _resize_tile_exact(self, tile, target_w, target_h):
        _, H, W, _ = tile.shape
        if H == target_h and W == target_w:
            return tile, "none (exact match)"

        try:
            import nvvfx
            nvvfx_ctx = nvvfx.VideoSuperRes(nvvfx.effects.QualityLevel.ULTRA)
            nvvfx_sr = nvvfx_ctx.__enter__()
            out_w = max(8, round(target_w / 8) * 8)
            out_h = max(8, round(target_h / 8) * 8)
            nvvfx_sr.output_width = out_w
            nvvfx_sr.output_height = out_h
            nvvfx_sr.load()
            frames_chw = tile.movedim(-1, 1).cuda().contiguous()
            upscaled = []
            for j in range(frames_chw.shape[0]):
                dlpack_out = nvvfx_sr.run(frames_chw[j]).image
                upscaled.append(torch.from_dlpack(dlpack_out).clone())
            result = torch.stack(upscaled, dim=0).movedim(1, -1).cpu()
            nvvfx_ctx.__exit__(None, None, None)

            method = "nvidia_rtx_vsr"
            if result.shape[2] != target_w or result.shape[1] != target_h:
                result = common_upscale(result.movedim(-1, 1), target_w, target_h, "lanczos", crop="disabled").movedim(1, -1)
                method = "nvidia_rtx_vsr + lanczos (RTX output corrected to exact size)"
            return result, method
        except ImportError:
            result = common_upscale(tile.movedim(-1, 1), target_w, target_h, "lanczos", crop="disabled").movedim(1, -1)
            return result, "lanczos (fallback \u2014 nvvfx not available)"

    def _calc_effective_overlap(self, coords, tw, th, ox, oy, mode):
        all_x = sorted(set(cx for cx, cy in coords))
        all_y = sorted(set(cy for cx, cy in coords))

        actual_ox = ox
        actual_oy = oy
        if len(all_x) > 1:
            step_x = min(all_x[i + 1] - all_x[i] for i in range(len(all_x) - 1))
            actual_ox = max(0, tw - step_x)
        if len(all_y) > 1:
            step_y = min(all_y[i + 1] - all_y[i] for i in range(len(all_y) - 1))
            actual_oy = max(0, th - step_y)

        cap10_x = max(tw // 10, 128)
        cap10_y = max(th // 10, 128)

        if mode == "auto (actual + cap)":
            return min(actual_ox, cap10_x), min(actual_oy, cap10_y), actual_ox, actual_oy
        elif mode == "actual overlap only":
            return actual_ox, actual_oy, actual_ox, actual_oy
        elif mode == "cap 128px":
            return min(actual_ox, 128), min(actual_oy, 128), actual_ox, actual_oy
        return ox, oy, actual_ox, actual_oy

    def execute(self, images, dac_data, blend_mode):
        if isinstance(dac_data, list):
            dac_data = dac_data[0]
        if isinstance(blend_mode, list):
            blend_mode = blend_mode[0]

        out = [images[i] for i in range(len(images))]
        images_t = torch.stack(out).squeeze(1)

        uw = dac_data["upscaled_width"]
        uh = dac_data["upscaled_height"]
        ox = dac_data["overlap_x"]
        oy = dac_data["overlap_y"]
        gx = dac_data["grid_x"]
        gy = dac_data["grid_y"]
        to = dac_data["tile_order"]
        target_tw = dac_data["tile_width"]
        target_th = dac_data["tile_height"]

        actual_tw = images_t.shape[2]
        actual_th = images_t.shape[1]

        method_used = "none"
        if actual_tw != target_tw or actual_th != target_th:
            print(f"[988] Combine Tiles v2: tile size mismatch "
                  f"({actual_tw}x{actual_th} != {target_tw}x{target_th}), auto-resizing...")
            resized = []
            for i in range(images_t.shape[0]):
                tile = images_t[i].unsqueeze(0)
                resized_tile, method = self._resize_tile_exact(tile, target_tw, target_th)
                if i == 0:
                    method_used = method
                resized.append(resized_tile)
            images_t = torch.cat(resized, dim=0)

        tw = images_t.shape[2]
        th = images_t.shape[1]

        coords, matrix = create_tile_coordinates(uw, uh, tw, th, ox, oy, gx, gy, to)
        effective_ox, effective_oy, real_ox, real_oy = self._calc_effective_overlap(
            coords, tw, th, ox, oy, blend_mode
        )

        output = torch.zeros((1, uh, uw, 3), dtype=torch.float64, device=images_t.device)
        weight_sum = torch.zeros((1, uh, uw, 1), dtype=torch.float64, device=images_t.device)

        for idx, (cx, cy) in enumerate(coords):
            tile = images_t[idx].to(torch.float64)
            mask = blend_tile_mask(cx, cy, tw, th, uw, uh, effective_ox, effective_oy).to(torch.float64)
            output[:, cy:cy + th, cx:cx + tw, :] += tile * mask
            weight_sum[:, cy:cy + th, cx:cx + tw, :] += mask

        output = (output / weight_sum.clamp(min=1e-8)).to(images_t.dtype)

        matrix_ui = "DaC Matrix:\n" + "\n".join(" ".join(row) for row in matrix)

        before_aspect = actual_tw / actual_th if actual_th > 0 else 0
        after_aspect = target_tw / target_th if target_th > 0 else 0
        stretched = abs(before_aspect - after_aspect) > 0.001
        before_div8 = actual_tw % 8 == 0 and actual_th % 8 == 0
        after_div8 = target_tw % 8 == 0 and target_th % 8 == 0

        cfg_pct = ox / tw * 100 if tw > 0 else 0
        cfg_pct_y = oy / th * 100 if th > 0 else 0
        real_pct = real_ox / tw * 100 if tw > 0 else 0
        real_pct_y = real_oy / th * 100 if th > 0 else 0

        info = (
            f"\u2501 Combine Tiles 988 v2 \u2501\n"
            f"\u2503 Blend mode:               {blend_mode}\n"
            f"\u2503 Resize needed:            {'YES' if method_used != 'none' else 'NO'}\n"
            f"\u2503 Original tile size:       {actual_tw}x{actual_th}\n"
            f"\u2503 Target tile size:         {target_tw}x{target_th}\n"
            f"\u2503 Resize method:            {method_used}\n"
            f"\u2503 Aspect ratio:             {actual_tw}:{actual_th} -> {target_tw}:{target_th} "
            f"{'(stretched)' if stretched else '(preserved)'}\n"
            f"\u2503 Divisible by 8 before:    {'Yes' if before_div8 else 'No'}\n"
            f"\u2503 Divisible by 8 after:     {'Yes' if after_div8 else 'No'}\n"
            f"\u2503 Overlap (configured):     X={ox}px ({cfg_pct:.1f}%)  Y={oy}px ({cfg_pct_y:.1f}%)\n"
            f"\u2503 Overlap (actual):         X={real_ox}px ({real_pct:.1f}%)  Y={real_oy}px ({real_pct_y:.1f}%)\n"
            f"\u2503 Overlap (effective):      X={effective_ox}px  Y={effective_oy}px\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        )
        return (output, matrix_ui, info)


NODE_CLASS_MAPPINGS = {"CombineTilesV2988": CombineTilesV2988}
NODE_DISPLAY_NAME_MAPPINGS = {"CombineTilesV2988": "Combine Tiles 988 v2"}
