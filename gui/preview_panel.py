import tkinter as tk
from PIL import Image, ImageTk
from gui.styles import PANEL, BORDER, TEXT


class PreviewPanel:
    def __init__(self, parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=PANEL, bd=1, relief="solid")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.title_label = tk.Label(
            self.frame,
            text="Live Preview",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self.preview_border = tk.Frame(self.frame, bg=BORDER, bd=1)
        self.preview_border.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.preview_border.grid_columnconfigure(0, weight=1)
        self.preview_border.grid_rowconfigure(0, weight=1)

        self.preview_label = tk.Label(self.preview_border, bg="#FFFFFF")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.image_tk = None

    def update_preview(self, image: Image.Image) -> None:
        preview = image.copy()
        preview.thumbnail((600, 600), Image.Resampling.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(preview)
        self.preview_label.configure(image=self.image_tk)

    def clear_preview(self) -> None:
        self.preview_label.configure(image="")
        self.image_tk = None
