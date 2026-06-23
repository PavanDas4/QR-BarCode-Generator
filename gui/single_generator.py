import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, font
from pathlib import Path
from typing import Any, Callable
from PIL import Image
from generators.qr_generator import QRGenerator
from generators.barcode_generator import BarcodeGenerator
from generators.image_composer import ImageComposer
from utils.font_manager import FontManager
from utils.validators import ValidationError, validate_heading, validate_description, validate_data_text
from gui.styles import PANEL, INPUT, TEXT, BORDER, BUTTON, BUTTON_HOVER, LABEL_FONT, INPUT_FONT, HEADER_FONT, BUTTON_FONT
from gui.preview_panel import PreviewPanel
from utils.export_manager import ExportManager


class Tooltip:
    """Display a tooltip on hover."""
    def __init__(self, widget: tk.Widget, text: Any) -> None:
        self.widget = widget
        self.get_text: Callable[[], str] = text if callable(text) else lambda: text
        self.tipwindow = None
        self.x = self.y = 0
        widget.bind("<Enter>", self.enter, add=True)
        widget.bind("<Leave>", self.leave, add=True)
        widget.bind("<Motion>", self.motion, add=True)

    def enter(self, event: tk.Event) -> None:
        self.motion(event)

    def motion(self, event: tk.Event) -> None:
        if self.tipwindow:
            return
        self.x = event.x_root + 10
        self.y = event.y_root + 10
        self.show_tip()

    def leave(self, event: tk.Event) -> None:
        self.hide_tip()

    def show_tip(self) -> None:
        if self.tipwindow:
            return
        text = self.get_text()
        if not text:
            return
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{self.x}+{self.y}")
        label = tk.Label(tw, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack(ipadx=1)

    def hide_tip(self) -> None:
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class SingleGenerator:
    def __init__(self, parent: tk.Widget, preview_parent: tk.Widget) -> None:
        self.frame = tk.Frame(parent, bg=PANEL)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)

        self.preview_panel = PreviewPanel(preview_parent)
        self.selected_bg_image_path = ""
        self.selected_logo_path = ""

        self._build_controls()

    def _build_controls(self) -> None:
        label = tk.Label(self.frame, text="Controls", bg=PANEL, fg=TEXT, font=HEADER_FONT)
        label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        self.scrollable_frame = self.frame

        row = 1
        self.code_type_var = tk.StringVar(value="QR Code")
        self.barcode_type_var = tk.StringVar(value="Code128")
        self.gradient_type_var = tk.StringVar(value="None")
        self.font_family_var = tk.StringVar(value="Segoe UI")
        self.heading_size_var = tk.IntVar(value=48)
        self.description_size_var = tk.IntVar(value=24)
        self.font_style_var = tk.StringVar(value="Bold")
        self.description_style_var = tk.StringVar(value="Normal")
        self.fg_color = "#000000"
        self.bg_color = "#FFFFFF"
        self.gradient_start_color = "#FFFFFF"
        self.gradient_end_color = "#2A2A2A"
        self.fg_color_swatch: tk.Label | None = None
        self.bg_color_swatch: tk.Label | None = None
        self.gradient_start_color_swatch: tk.Label | None = None
        self.gradient_end_color_swatch: tk.Label | None = None

        self._add_label(row, "Type")
        self._add_option_menu(row, self.code_type_var, ["QR Code", "Barcode"], self._toggle_barcode_options)
        row += 1

        self.barcode_frame = tk.Frame(self.scrollable_frame, bg=PANEL)
        self.barcode_frame.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 16))
        self._add_label_to(self.barcode_frame, 0, "Barcode")
        self._add_option_menu_to(self.barcode_frame, 0, self.barcode_type_var, ["Code128", "EAN13", "EAN8", "UPC", "ISBN"])
        row += 1

        self._add_label(row, "Data")
        self.data_input = self._add_text_placeholder(row, "Enter QR/Barcode payload")
        Tooltip(self.data_input, self._get_data_tooltip)
        row += 1

        self._add_label(row, "Heading")
        self.heading_input = self._add_entry_placeholder(row, "Enter heading")
        Tooltip(self.heading_input, self._get_heading_tooltip)
        row += 1

        self._add_label(row, "Description")
        self.description_input = self._add_entry_placeholder(row, "Enter description")
        Tooltip(self.description_input, self._get_description_tooltip)
        row += 1

        self._add_separator(row)
        row += 1

        self._add_label(row, "Font Family")
        self.font_menu = ttk.Combobox(self.scrollable_frame, textvariable=self.font_family_var, values=FontManager.get_system_fonts(), state="readonly")
        self.font_menu.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        row += 1

        self._add_label_with_value(row, "Heading Size", f"{self.heading_size_var.get()}px")
        self.heading_size_label = tk.Label(self.scrollable_frame, text=f"{self.heading_size_var.get()}px", bg=PANEL, fg=TEXT, font=INPUT_FONT)
        self._add_scale_with_label(row, self.heading_size_var, 24, 90, self.heading_size_label)
        Tooltip(self.heading_size_label, "Heading font size")
        row += 1

        self._add_label_with_value(row, "Description Size", f"{self.description_size_var.get()}px")
        self.description_size_label = tk.Label(self.scrollable_frame, text=f"{self.description_size_var.get()}px", bg=PANEL, fg=TEXT, font=INPUT_FONT)
        self._add_scale_with_label(row, self.description_size_var, 18, 60, self.description_size_label)
        Tooltip(self.description_size_label, "Description font size")
        row += 1

        self._add_label(row, "Heading Style")
        self._add_option_menu(row, self.font_style_var, ["Normal", "Bold", "Italic", "Bold Italic"])
        row += 1

        self._add_label(row, "Description Style")
        self._add_option_menu(row, self.description_style_var, ["Normal", "Bold", "Italic", "Bold Italic"])
        row += 1

        self.fg_color_swatch = self._add_color_picker(row, "Foreground Color", self._select_fg_color, self.fg_color)
        row += 1

        self.bg_color_swatch = self._add_color_picker(row, "Background Color", self._select_bg_color, self.bg_color)
        row += 1

        self._add_label(row, "Gradient")
        self._add_option_menu(row, self.gradient_type_var, ["None", "Vertical", "Horizontal", "Diagonal"])
        row += 1

        self.gradient_start_color_swatch = self._add_color_picker(row, "Gradient Start", self._select_gradient_start_color, self.gradient_start_color)
        row += 1

        self.gradient_end_color_swatch = self._add_color_picker(row, "Gradient End", self._select_gradient_end_color, self.gradient_end_color)
        row += 1

        self._add_label(row, "Background Image")
        self.bg_image_path_label = tk.Label(self.scrollable_frame, text="No file selected", bg=PANEL, fg=TEXT, anchor="w", font=INPUT_FONT)
        self.bg_image_path_label.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 4))
        row += 1

        self._add_button(row, "Browse Background Image", self._browse_background_image)
        row += 1

        self._add_label(row, "Background Mode")
        self.bg_image_mode_var = tk.StringVar(value="Fit")
        self._add_option_menu(row, self.bg_image_mode_var, ["Fit", "Fill", "Stretch", "Center"])
        row += 1

        self._add_label(row, "Center Logo")
        self.logo_path_label = tk.Label(self.scrollable_frame, text="No file selected", bg=PANEL, fg=TEXT, anchor="w", font=INPUT_FONT)
        self.logo_path_label.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 4))
        row += 1

        self._add_button(row, "Browse Center Logo", self._browse_logo_image)
        row += 1

        self._add_button(row, "Generate Preview", self.generate_preview)
        row += 1

        self._add_button(row, "Export PNG", self.download_png)
        row += 1

        self._toggle_barcode_options()


    def _add_label_with_value(self, row: int, text: str, value: str) -> None:
        label = tk.Label(self.scrollable_frame, text=f"{text}: {value}", bg=PANEL, fg=TEXT, font=LABEL_FONT)
        label.grid(row=row, column=0, sticky="w", padx=12, pady=(0, 2))

    def _add_scale_with_label(self, row: int, variable: tk.IntVar, minimum: int, maximum: int, label: tk.Label) -> None:
        frame = tk.Frame(self.scrollable_frame, bg=PANEL)
        frame.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        frame.grid_columnconfigure(0, weight=1)
        
        scale = ttk.Scale(frame, variable=variable, from_=minimum, to=maximum, orient="horizontal", command=lambda v: label.configure(text=f"{int(float(v))}px"))
        scale.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        label.grid(row=0, column=1, sticky="e")

    def _add_label(self, row: int, text: str) -> None:
        self._add_label_to(self.scrollable_frame, row, text)

    def _add_separator(self, row: int) -> None:
        separator = ttk.Separator(self.scrollable_frame, orient="horizontal")
        separator.grid(row=row, column=0, sticky="ew", padx=12, pady=12)

    def _add_label_to(self, parent: tk.Widget, row: int, text: str) -> None:
        label = tk.Label(parent, text=text, bg=PANEL, fg=TEXT, font=LABEL_FONT)
        label.grid(row=row, column=0, sticky="w", padx=12, pady=(0, 6))

    def _add_option_menu(self, row: int, variable: tk.StringVar, options: list[str], command: Any = None) -> ttk.Combobox:
        return self._add_option_menu_to(self.scrollable_frame, row, variable, options, command)

    def _add_option_menu_to(self, parent: tk.Widget, row: int, variable: tk.StringVar, options: list[str], command: Any = None) -> ttk.Combobox:
        option_menu = ttk.Combobox(parent, textvariable=variable, values=options, state="readonly")
        option_menu.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        if command:
            option_menu.bind("<<ComboboxSelected>>", lambda event: command())
        return option_menu

    def _add_entry_placeholder(self, row: int, placeholder: str) -> tk.Entry:
        entry = tk.Entry(self.scrollable_frame, bg=INPUT, fg=TEXT, insertbackground=TEXT, font=INPUT_FONT, bd=1, relief="solid")
        entry.placeholder_text = placeholder
        entry.placeholder_color = "#9ca3af"
        entry.default_fg_color = TEXT
        entry.insert(0, placeholder)
        entry.config(fg=entry.placeholder_color)
        entry.bind("<FocusIn>", self._clear_placeholder)
        entry.bind("<FocusOut>", self._show_placeholder)
        entry.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        return entry

    def _add_text_placeholder(self, row: int, placeholder: str) -> tk.Text:
        text_widget = tk.Text(self.scrollable_frame, height=4, wrap="word", bg=INPUT, fg=TEXT, insertbackground=TEXT, font=INPUT_FONT, bd=1, relief="solid", highlightthickness=0)
        text_widget.placeholder_text = placeholder
        text_widget.placeholder_color = "#9ca3af"
        text_widget.default_fg_color = TEXT
        text_widget.insert("1.0", placeholder)
        text_widget.config(fg=text_widget.placeholder_color)
        text_widget.bind("<FocusIn>", self._clear_placeholder)
        text_widget.bind("<FocusOut>", self._show_placeholder)
        text_widget.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        return text_widget

    def _clear_placeholder(self, event: tk.Event) -> None:
        widget = event.widget
        placeholder_text = getattr(widget, "placeholder_text", None)
        if not placeholder_text:
            return
        if widget.cget("fg") == getattr(widget, "placeholder_color", ""):
            if isinstance(widget, tk.Entry):
                widget.delete(0, "end")
            else:
                widget.delete("1.0", "end")
            widget.config(fg=getattr(widget, "default_fg_color", TEXT))

    def _show_placeholder(self, event: tk.Event) -> None:
        widget = event.widget
        placeholder_text = getattr(widget, "placeholder_text", None)
        if not placeholder_text:
            return
        if isinstance(widget, tk.Entry):
            if not widget.get().strip():
                widget.insert(0, placeholder_text)
                widget.config(fg=widget.placeholder_color)
        else:
            if not widget.get("1.0", "end").strip():
                widget.delete("1.0", "end")
                widget.insert("1.0", placeholder_text)
                widget.config(fg=widget.placeholder_color)

    def _get_widget_text(self, widget: tk.Widget) -> str:
        placeholder_color = getattr(widget, "placeholder_color", None)
        if placeholder_color and widget.cget("fg") == placeholder_color:
            return ""
        if isinstance(widget, tk.Entry):
            return widget.get().strip()
        return widget.get("1.0", "end").strip()

    def _get_data_tooltip(self) -> str:
        text = self._get_widget_text(self.data_input)
        length = len(text)
        if length > 1024:
            return f"Data too long: {length}/1024 chars"
        return f"QR/Barcode data length: {length}/1024 chars"

    def _get_heading_tooltip(self) -> str:
        text = self._get_widget_text(self.heading_input)
        length = len(text)
        if length > 25:
            return f"Heading too long: {length}/25 chars"
        return f"Heading length: {length}/25 chars"

    def _get_description_tooltip(self) -> str:
        text = self._get_widget_text(self.description_input)
        length = len(text)
        if length > 75:
            return f"Description too long: {length}/75 chars"
        return f"Description length: {length}/75 chars"

    def _add_color_picker(self, row: int, text: str, command: Any, initial_color: str) -> tk.Label:
        container = tk.Frame(self.scrollable_frame, bg=PANEL)
        container.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))
        container.grid_columnconfigure(1, weight=1)

        label = tk.Label(container, text=text, bg=PANEL, fg=TEXT, font=LABEL_FONT)
        label.grid(row=0, column=0, sticky="w")

        btn = tk.Button(container, text=f"Choose {text}", bg=BUTTON, fg=TEXT, activebackground=BUTTON_HOVER, relief="flat", command=command)
        btn.grid(row=0, column=1, sticky="e")

        swatch = tk.Label(container, bg=initial_color, width=3, relief="ridge", bd=1)
        swatch.grid(row=0, column=2, sticky="e", padx=(8, 0))
        return swatch

    def _add_button(self, row: int, text: str, command: Any) -> None:
        button = tk.Button(self.scrollable_frame, text=text, bg=BUTTON, fg=TEXT, activebackground=BUTTON_HOVER, relief="flat", command=command, font=BUTTON_FONT)
        button.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 8))

    def _toggle_barcode_options(self) -> None:
        if self.code_type_var.get() == "Barcode":
            self.barcode_frame.grid()
        else:
            self.barcode_frame.grid_remove()

    def _select_fg_color(self) -> None:
        selected = colorchooser.askcolor(color=self.fg_color, title="Choose Foreground Color")
        if selected[1]:
            self.fg_color = selected[1]
            if self.fg_color_swatch:
                self.fg_color_swatch.configure(bg=self.fg_color)

    def _select_bg_color(self) -> None:
        selected = colorchooser.askcolor(color=self.bg_color, title="Choose Background Color")
        if selected[1]:
            self.bg_color = selected[1]
            if self.bg_color_swatch:
                self.bg_color_swatch.configure(bg=self.bg_color)

    def _select_gradient_start_color(self) -> None:
        selected = colorchooser.askcolor(color=self.gradient_start_color, title="Choose Gradient Start Color")
        if selected[1]:
            self.gradient_start_color = selected[1]
            if self.gradient_start_color_swatch:
                self.gradient_start_color_swatch.configure(bg=self.gradient_start_color)

    def _select_gradient_end_color(self) -> None:
        selected = colorchooser.askcolor(color=self.gradient_end_color, title="Choose Gradient End Color")
        if selected[1]:
            self.gradient_end_color = selected[1]
            if self.gradient_end_color_swatch:
                self.gradient_end_color_swatch.configure(bg=self.gradient_end_color)

    def _browse_background_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")],
        )
        if path:
            self.selected_bg_image_path = path
            self.bg_image_path_label.configure(text=Path(path).name)

    def _browse_logo_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Center Logo",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp")],
        )
        if path:
            self.selected_logo_path = path
            self.logo_path_label.configure(text=Path(path).name)

    def _collect_input(self) -> dict[str, Any]:
        data_text = self._get_widget_text(self.data_input)
        heading = self._get_widget_text(self.heading_input)
        description = self._get_widget_text(self.description_input)
        validate_data_text(data_text)
        validate_heading(heading)
        validate_description(description)

        return {
            "code_type": self.code_type_var.get(),
            "barcode_type": self.barcode_type_var.get(),
            "data": data_text,
            "heading": heading,
            "description": description,
            "font_family": self.font_family_var.get(),
            "heading_size": int(self.heading_size_var.get()),
            "description_size": int(self.description_size_var.get()),
            "font_style": self.font_style_var.get(),
            "description_style": self.description_style_var.get(),
            "foreground_color": self.fg_color,
            "background_color": self.bg_color,
            "gradient_type": self.gradient_type_var.get(),
            "gradient_start_color": self.gradient_start_color,
            "gradient_end_color": self.gradient_end_color,
            "background_image_path": self.selected_bg_image_path,
            "background_mode": self.bg_image_mode_var.get(),
            "logo_path": self.selected_logo_path,
        }

    def generate_preview(self) -> None:
        try:
            config = self._collect_input()
            image = self._make_image(config, size=600)
            self.preview_panel.update_preview(image)
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except Exception as exc:
            messagebox.showerror("Preview Error", f"Unable to generate preview: {exc}")

    def download_png(self) -> None:
        try:
            config = self._collect_input()
            file_path = filedialog.asksaveasfilename(
                title="Save HD PNG",
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                initialfile="code.png",
            )
            if not file_path:
                return
            image = self._make_image(config, size=2000)
            ExportManager.save_png(image, file_path)
            messagebox.showinfo("Export Complete", f"PNG saved to {file_path}")
        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc))
        except Exception as exc:
            messagebox.showerror("Export Error", f"Unable to save PNG: {exc}")

    def _make_image(self, config: dict[str, Any], size: int) -> Image.Image:
        if config["code_type"] == "QR Code":
            code_image = QRGenerator.generate(
                config["data"],
                foreground_color=config["foreground_color"],
                background_color="transparent",
                logo_path=config["logo_path"],
                max_size=int(size * 0.6),
            )
        else:
            code_image = BarcodeGenerator.generate(
                config["data"],
                config["barcode_type"],
                foreground_color=config["foreground_color"],
                background_color="#FFFFFF",
                width=int(size * 0.85),
                height=int(size * 0.35),
            )

        composer = ImageComposer(
            width=size,
            height=size,
            background_color="#FFFFFF",
            gradient_type="None",
            gradient_start_color="#FFFFFF",
            gradient_end_color="#FFFFFF",
            background_image_path="",
            background_mode="Fit",
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
