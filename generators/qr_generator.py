from pathlib import Path
from typing import Optional
from PIL import Image
import qrcode
import qrcode.constants


class QRGenerator:
    @staticmethod
    def generate(
        data: str,
        foreground_color: str = "#000000",
        background_color: str = "#FFFFFF",
        logo_path: Optional[str] = None,
        max_size: int = 1200,
    ) -> Image.Image:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=20,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color=foreground_color, back_color=background_color).convert("RGBA")
        image = QRGenerator._resize_to_max(image, max_size)

        if logo_path:
            image = QRGenerator._add_logo(image, logo_path)
        return image

    @staticmethod
    def _resize_to_max(image: Image.Image, max_size: int) -> Image.Image:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return image

    @staticmethod
    def _add_logo(image: Image.Image, logo_path: str) -> Image.Image:
        logo = Image.open(Path(logo_path)).convert("RGBA")
        max_logo_width = int(image.width * 0.2)
        logo.thumbnail((max_logo_width, max_logo_width), Image.Resampling.LANCZOS)

        logo_position = (
            (image.width - logo.width) // 2,
            (image.height - logo.height) // 2,
        )
        combined = Image.alpha_composite(image, Image.new("RGBA", image.size, (255, 255, 255, 0)))
        combined.paste(logo, logo_position, logo)
        return combined
