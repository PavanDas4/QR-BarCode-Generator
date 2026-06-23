from typing import Tuple
from PIL import Image


class GradientGenerator:
    @staticmethod
    def create_gradient(width: int, height: int, start_color: str, end_color: str, mode: str) -> Image.Image:
        gradient = Image.new("RGB", (width, height), start_color)
        start_rgb = GradientGenerator._hex_to_rgb(start_color)
        end_rgb = GradientGenerator._hex_to_rgb(end_color)

        if mode == "Vertical":
            for y in range(height):
                ratio = y / max(1, height - 1)
                color = GradientGenerator._interpolate(start_rgb, end_rgb, ratio)
                gradient.paste(Image.new("RGB", (width, 1), color), (0, y))
        elif mode == "Horizontal":
            for x in range(width):
                ratio = x / max(1, width - 1)
                color = GradientGenerator._interpolate(start_rgb, end_rgb, ratio)
                gradient.paste(Image.new("RGB", (1, height), color), (x, 0))
        else:
            for y in range(height):
                for x in range(width):
                    ratio = ((x / max(1, width - 1)) + (y / max(1, height - 1))) / 2
                    color = GradientGenerator._interpolate(start_rgb, end_rgb, ratio)
                    gradient.putpixel((x, y), color)
        return gradient

    @staticmethod
    def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
        color = color.lstrip("#")
        if len(color) == 3:
            color = "".join([ch * 2 for ch in color])
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _interpolate(start_rgb: Tuple[int, int, int], end_rgb: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
        return (
            int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio),
            int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio),
            int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio),
        )
