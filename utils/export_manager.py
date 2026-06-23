import tempfile
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image


class ExportManager:
    @staticmethod
    def save_png(image: Image.Image, path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG", dpi=(300, 300))

    @staticmethod
    def create_zip(images: Iterable[tuple[str, Image.Image]], path: str) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temp_folder:
            temp_dir = Path(temp_folder)
            with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
                for filename, image in images:
                    temp_path = temp_dir / filename
                    image.save(temp_path, format="PNG", dpi=(300, 300))
                    archive.write(temp_path, arcname=filename)
