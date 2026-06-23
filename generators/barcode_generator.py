import tempfile
from pathlib import Path
from typing import Optional
from PIL import Image
import barcode
from barcode.writer import ImageWriter


class BarcodeGenerator:
    BARCODE_MAP = {
        "Code128": "code128",
        "EAN13": "ean13",
        "EAN8": "ean8",
        "UPC": "upc",
        "ISBN": "isbn13",
    }

    @staticmethod
    def generate(
        data: str,
        barcode_type: str,
        foreground_color: str = "#000000",
        background_color: str = "#FFFFFF",
        width: int = 1700,
        height: int = 700,
    ) -> Image.Image:
        barcode_name = BarcodeGenerator.BARCODE_MAP.get(barcode_type)
        if not barcode_name:
            raise ValueError(f"Unsupported barcode type: {barcode_type}")

        writer = ImageWriter()
        writer.dpi = 300
        writer.text_distance = 8
        writer.font_size = 32

        barcode_cls = barcode.get_barcode_class(barcode_name)
        rendered = barcode_cls(data, writer=writer)
        options = {
            "module_width": 0.2,
            "module_height": 15.0,
            "quiet_zone": 6.5,
            "foreground": foreground_color,
            "background": background_color,
        }
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temporary_file:
            temp_path = Path(temporary_file.name)
        try:
            rendered.write(temp_path, options=options)
            image = Image.open(temp_path).convert("RGBA")
            return image.resize((width, height), Image.Resampling.LANCZOS)
        finally:
            if temp_path.exists():
                temp_path.unlink()
