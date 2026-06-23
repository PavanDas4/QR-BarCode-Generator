from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from generators.gradient_generator import GradientGenerator
from utils.font_manager import FontManager


class ImageComposer:
    def __init__(
        self,
        width: int,
        height: int,
        background_color: str,
        gradient_type: str,
        gradient_start_color: str,
        gradient_end_color: str,
        background_image_path: str,
        background_mode: str,
        heading: str,
        description: str,
        font_family: str,
        heading_size: int,
        description_size: int,
        heading_style: str,
        description_style: str,
        foreground_color: str,
        code_image: Image.Image,
    ) -> None:
        self.width = width
        self.height = height
        self.background_color = background_color
        self.gradient_type = gradient_type
        self.gradient_start_color = gradient_start_color
        self.gradient_end_color = gradient_end_color
        self.background_image_path = background_image_path
        self.background_mode = background_mode
        self.heading = heading
        self.description = description
        self.font_family = font_family
        self.heading_size = heading_size
        self.description_size = description_size
        self.heading_style = heading_style
        self.description_style = description_style
        self.foreground_color = foreground_color
        self.code_image = code_image.convert("RGBA")

    def compose(self) -> Image.Image:
        canvas = self._create_background()
        draw = ImageDraw.Draw(canvas)
        heading_font = self._get_font(self.heading_size, self.heading_style)
        description_font = self._get_font(self.description_size, self.description_style)

        margin = int(self.width * 0.06)
        bottom_padding = int(self.height * 0.06)

        heading_text = self.heading.strip()
        description_text = self.description.strip()

        bottom_lines = []
        if heading_text:
            bottom_lines.append((heading_text, heading_font))
        if description_text:
            bottom_lines.append((description_text, description_font))

        total_text_height = 0
        for line, font_obj in bottom_lines:
            wrapped = self._wrap_text(line, font_obj, self.width - margin * 2)
            for wrapped_line in wrapped:
                bbox = draw.textbbox((0, 0), wrapped_line, font=font_obj)
                total_text_height += bbox[3] - bbox[1] + 6

        code_y = int((self.height - self.code_image.height - total_text_height - bottom_padding) * 0.5)
        code_x = (self.width - self.code_image.width) // 2
        if code_y < margin:
            code_y = margin
        canvas.alpha_composite(self.code_image, (code_x, code_y))

        text_y = self.height - bottom_padding - total_text_height
        for line, font_obj in bottom_lines:
            wrapped = self._wrap_text(line, font_obj, self.width - margin * 2)
            for wrapped_line in wrapped:
                bbox = draw.textbbox((0, 0), wrapped_line, font=font_obj)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                x = (self.width - width) // 2
                draw.text((x, text_y), wrapped_line, font=font_obj, fill=self.foreground_color)
                text_y += height + 6

        return canvas

    def _create_background(self) -> Image.Image:
        if self.gradient_type != "None":
            background = GradientGenerator.create_gradient(
                self.width,
                self.height,
                self.gradient_start_color,
                self.gradient_end_color,
                self.gradient_type,
            ).convert("RGBA")
        else:
            background = Image.new("RGBA", (self.width, self.height), self.background_color)

        if self.background_image_path:
            background = self._apply_background_image(background)
        return background

    def _apply_background_image(self, canvas: Image.Image) -> Image.Image:
        image_path = Path(self.background_image_path)
        if not image_path.exists():
            return canvas
        try:
            source = Image.open(image_path).convert("RGBA")
        except Exception:
            return canvas

        canvas_ratio = canvas.width / canvas.height
        source_ratio = source.width / source.height

        if self.background_mode == "Fill":
            if source_ratio > canvas_ratio:
                target_height = canvas.height
                target_width = int(source_ratio * target_height)
            else:
                target_width = canvas.width
                target_height = int(target_width / source_ratio)
        elif self.background_mode == "Stretch":
            target_width = canvas.width
            target_height = canvas.height
        elif self.background_mode == "Center":
            target_width = source.width
            target_height = source.height
        else:  # Fit
            if source_ratio > canvas_ratio:
                target_width = canvas.width
                target_height = int(target_width / source_ratio)
            else:
                target_height = canvas.height
                target_width = int(source_ratio * target_height)

        resized = source.resize((target_width, target_height), Image.Resampling.LANCZOS)
        position = self._compute_bg_position(resized)
        layer = Image.new("RGBA", canvas.size)
        layer.paste(resized, position)
        return Image.alpha_composite(canvas, layer)

    def _compute_bg_position(self, image: Image.Image) -> tuple[int, int]:
        if self.background_mode == "Center":
            x = (self.width - image.width) // 2
            y = (self.height - image.height) // 2
        else:
            x = 0
            y = 0
        return x, y

    def _draw_centered_text(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, y: int, margin: int) -> int:
        wrapped = self._wrap_text(text, font, self.width - margin * 2)
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            x = (self.width - width) // 2
            draw.text((x, y), line, font=font, fill=self.foreground_color)
            y += height + 4
        return y

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current_line = ""
        dummy_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        for word in words:
            candidate = f"{current_line} {word}".strip()
            bbox = dummy_draw.textbbox((0, 0), candidate, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def _get_font(self, size: int, style: str) -> ImageFont.FreeTypeFont:
        font_path = FontManager.find_font(self.font_family, style)
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            return ImageFont.load_default()
