import tkinter as tk
from tkinter import font
from pathlib import Path
from typing import Optional, List


class FontManager:
    @staticmethod
    def get_system_fonts() -> List[str]:
        root = tk.Tk()
        root.withdraw()
        families = sorted(font.families())
        root.destroy()
        return families

    @staticmethod
    def find_font(family: str, style: str) -> str:
        font_family = family or "Segoe UI"
        style_lower = style.lower()
        if "bold" in style_lower and "italic" in style_lower:
            variant = "BoldItalic"
        elif "bold" in style_lower:
            variant = "Bold"
        elif "italic" in style_lower:
            variant = "Italic"
        else:
            variant = "Regular"

        base_path = Path(__file__).resolve().parents[1] / "assets" / "fonts"
        return str(base_path / f"{font_family}-{variant}.ttf")
