import tkinter as tk
from tkinter import ttk
from gui.styles import BACKGROUND, PANEL, TEXT, BORDER
from gui.single_generator import SingleGenerator
from gui.bulk_generator import BulkGenerator


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("QR & Barcode Studio")
        self.root.geometry("1400x850")
        self.root.configure(bg=BACKGROUND)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_canvas = tk.Canvas(self.root, bg=BACKGROUND, highlightthickness=0, bd=0)
        self.root_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        self.root_scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_canvas.configure(yscrollcommand=self.root_scrollbar.set)

        self.main_frame = tk.Frame(self.main_canvas, bg=BACKGROUND)
        self.main_frame.grid_columnconfigure(0, weight=2)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.main_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.main_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.main_canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.left_panel = tk.Frame(self.main_frame, bg=PANEL, bd=1, relief="solid")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.left_panel.grid_columnconfigure(0, weight=1)

        self.right_panel = tk.Frame(self.main_frame, bg=PANEL, bd=1, relief="solid")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.single_generator = SingleGenerator(self.left_panel, self.right_panel)
        self.single_generator.frame.grid(row=0, column=0, sticky="nsew")

        self.bulk_generator = BulkGenerator(self.left_panel, self.single_generator.preview_panel, self.single_generator)
        self.bulk_generator.frame.grid(row=1, column=0, sticky="ew")

        self._build_preview_area()

    def _build_preview_area(self) -> None:
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.single_generator.preview_panel.frame.configure(bg=PANEL)
        self.single_generator.preview_panel.frame.grid(row=0, column=0, sticky="nsew")

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.num == 5 or event.delta < 0:
            self.main_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.main_canvas.yview_scroll(-1, "units")
