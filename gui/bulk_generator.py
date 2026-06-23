import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Any, Dict
from PIL import Image
from utils.csv_handler import CSVHandler
from utils.export_manager import ExportManager
from utils.validators import ValidationError
from generators.qr_generator import QRGenerator
from generators.barcode_generator import BarcodeGenerator
from generators.image_composer import ImageComposer


class BulkGenerator:
    def __init__(self, parent: tk.Widget, preview_panel: Any, control_source: Any) -> None:
        self.frame = tk.Frame(parent, bg=control_source.frame.cget("bg"))
        self.preview_panel = preview_panel
        self.control_source = control_source
        self._build_controls()

    def _build_controls(self) -> None:
        label = tk.Label(self.frame, text="Bulk CSV Export", bg=self.frame.cget("bg"), fg="white", font=("Segoe UI", 12, "bold"))
        label.grid(row=0, column=0, sticky="w", padx=12, pady=(24, 8))

        self.csv_label = tk.Label(self.frame, text="No CSV loaded", bg=self.frame.cget("bg"), fg="white", anchor="w", font=("Segoe UI", 10))
        self.csv_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.upload_button = tk.Button(self.frame, text="Upload CSV", bg="#333333", fg="white", activebackground="#555555", relief="flat", command=self.upload_csv)
        self.upload_button.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        progress_label = tk.Label(self.frame, text="Progress", bg=self.frame.cget("bg"), fg="white", font=("Segoe UI", 10))
        progress_label.grid(row=3, column=0, sticky="w", padx=12, pady=(12, 4))

        self.progress_bar = ttk.Progressbar(self.frame, mode="determinate")
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.status_label = tk.Label(self.frame, text="Waiting to start", bg=self.frame.cget("bg"), fg="white", anchor="w", font=("Segoe UI", 10))
        self.status_label.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 8))

    def upload_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        self.csv_path = path
        self.csv_label.configure(text=Path(path).name)
        self._start_bulk_generation(path)

    def _start_bulk_generation(self, csv_path: str) -> None:
        thread = threading.Thread(target=self._process_csv, args=(csv_path,), daemon=True)
        thread.start()

    def _process_csv(self, csv_path: str) -> None:
        try:
            rows = CSVHandler.load_csv(csv_path)
            self.frame.after(0, lambda: self.progress_bar.configure(maximum=len(rows), value=0))
            self.frame.after(0, self._update_status, f"Generating 0 / {len(rows)}")
            output_files = []
            for index, row in enumerate(rows, start=1):
                config = self.control_source._collect_input()
                config.update(
                    {
                        "data": row["data"],
                        "heading": row["heading"],
                        "description": row["description"],
                    }
                )
                image = self._make_bulk_image(config)
                filename = f"{row['data']}.png"
                output_files.append((filename, image))
                self.frame.after(0, self.progress_bar.step, 1)
                self.frame.after(0, self._update_status, f"Generating {index} / {len(rows)}")
            self.frame.after(0, self._finalize_bulk_export, output_files)
        except ValidationError as exc:
            self.frame.after(0, lambda: messagebox.showerror("Validation Error", str(exc)))
            self.frame.after(0, self._update_status, "Validation failed")
        except Exception as exc:
            self.frame.after(0, lambda: messagebox.showerror("Bulk Export Error", f"Unable to create ZIP archive: {exc}"))
            self.frame.after(0, self._update_status, "Error during export")

    def _make_bulk_image(self, config: Dict[str, Any]) -> Image.Image:
        if config["code_type"] == "QR Code":
            code_image = QRGenerator.generate(
                config["data"],
                foreground_color=config["foreground_color"],
                background_color="transparent",
                logo_path=config["logo_path"],
                max_size=1200,
            )
        else:
            code_image = BarcodeGenerator.generate(
                config["data"],
                config["barcode_type"],
                foreground_color=config["foreground_color"],
                background_color=config["background_color"],
                width=1700,
                height=700,
            )
        composer = ImageComposer(
            width=2000,
            height=2000,
            background_color=config["background_color"],
            gradient_type=config["gradient_type"],
            gradient_start_color=config["gradient_start_color"],
            gradient_end_color=config["gradient_end_color"],
            background_image_path=config["background_image_path"],
            background_mode=config["background_mode"],
            heading=config["heading"],
            description=config["description"],
            font_family=config["font_family"],
            heading_size=config["heading_size"],
            description_size=config["description_size"],
            heading_style=config["font_style"],
            description_style=config["description_style"],
            foreground_color=config["foreground_color"],
            code_image=code_image,
        )
        return composer.compose()

    def _finalize_bulk_export(self, output_files: list[tuple[str, Image.Image]]) -> None:
        export_path = filedialog.asksaveasfilename(
            title="Save ZIP archive",
            defaultextension=".zip",
            filetypes=[("ZIP file", "*.zip")],
            initialfile="generated_codes.zip",
        )
        if not export_path:
            self._update_status("Export canceled")
            return
        try:
            ExportManager.create_zip(output_files, export_path)
            self._update_status("Bulk export complete")
            messagebox.showinfo("Bulk Export Complete", f"ZIP archive saved to {export_path}")
        except Exception as exc:
            messagebox.showerror("Bulk Export Error", f"Unable to create ZIP archive: {exc}")
            self._update_status("Error during export")

    def _update_status(self, text: str) -> None:
        self.status_label.configure(text=text)
