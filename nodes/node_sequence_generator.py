"""Sequence Generator 988 — generate sequences from compact expressions."""


class SequenceGen988:
    DESCRIPTION = "Generate a sequence of numbers. Syntax: x...y+z (step), x...y#z (evenly spaced), x,y,z (literal list)."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "expression": ("STRING", {"multiline": False, "dynamicPrompts": False, "default": "0...1+0.1"}),
            },
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING")
    RETURN_NAMES = ("int_list", "float_list", "info")
    OUTPUT_IS_LIST = (True, True, False)
    OUTPUT_TOOLTIPS = ("Integer sequence", "Float sequence", "Human-readable summary")
    OUTPUT_NODE = True
    FUNCTION = "generate"
    CATEGORY = "\U0001f987988/Number"

    def generate(self, expression):
        parts = expression.split(",")
        result = []

        def parse_num(s):
            try:
                return float(s.strip())
            except ValueError:
                return 0.0

        for part in parts:
            part = part.strip()
            if "..." in part:
                if "#" in part:
                    start, rest = part.split("...")
                    end, count = rest.split("#")
                    s, e, n = parse_num(start), parse_num(end), int(parse_num(count))
                    if n == 1:
                        result.append(round(s, 2))
                    else:
                        step = (e - s) / (n - 1)
                        for i in range(n):
                            result.append(round(s + i * step, 2))
                else:
                    start, rest = part.split("...")
                    end_step = rest.split("+")
                    s = parse_num(start)
                    e = parse_num(end_step[0])
                    step = abs(parse_num(end_step[1])) if len(end_step) > 1 else 1.0
                    if s > e:
                        step = -step
                    cur = s
                    while (step > 0 and cur <= e) or (step < 0 and cur >= e):
                        result.append(round(cur, 2))
                        cur += step
            else:
                result.append(round(parse_num(part), 2))

        seq_int = list(map(int, result))
        seq_float = [round(v, 2) for v in result]
        info = f"{len(seq_int)} INT: {seq_int}\n{len(seq_float)} FLOAT: {seq_float}"
        return {"ui": {"text": info}, "result": (seq_int, seq_float, info)}


NODE_CLASS_MAPPINGS = {"SequenceGen988": SequenceGen988}
NODE_DISPLAY_NAME_MAPPINGS = {"SequenceGen988": "Sequence Generator 988"}