"""Module for adding date stamps to images using Photoshop."""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import os
from PIL import Image
from photoshop import Session
from photoshop.api._core import Photoshop

__all__ = ["DateStamperApp"]


class DateStamperApp:
    def __init__(self, parent):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Main Frame
        convert_frame = ttk.LabelFrame(self.parent, text="Date Stamper", padding="10")
        convert_frame.pack(fill="x", padx=5, pady=5)

        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            convert_frame, textvariable=self.file_path_var, width=50
        )
        self.file_path_entry.pack(side="left", padx=(0, 5))

        self.browse_btn = ttk.Button(
            convert_frame, text="Browse JPG", command=self.browse_jpg
        )
        self.browse_btn.pack(side="left", padx=5)

        self.convert_btn = ttk.Button(
            convert_frame, text="Add Date Stamp", command=self.convert_to_psd
        )
        self.convert_btn.pack(side="left")

        # Status Label
        self.status_label = ttk.Label(self.parent, text="")
        self.status_label.pack(pady=5)

    def convert_to_psd(self):
        """Convert JPG to PSD and add date/time text layer."""
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select a JPG file first")
            return

        try:
            jpg_path = self.file_path_var.get()
            psd_path = os.path.splitext(jpg_path)[0] + ".psd"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Open Photoshop and create new document from JPG
            with Session() as ps:
                app = ps.app
                doc = app.open(jpg_path)
                # Create text layer with current date/time
                text_layer = doc.artLayers.add()
                text_layer.kind = 2  # 2 is the enum value for text layer
                text_layer.textItem.contents = current_time
                text_layer.textItem.position = [20, 20]  # Position from top-left
                text_layer.textItem.size = 12  # Font size in points
                text_layer.textItem.color.rgb.red = 0  # Black text
                text_layer.textItem.color.rgb.green = 0
                text_layer.textItem.color.rgb.blue = 0

                # Save as PSD
                options = ps.PhotoshopSaveOptions()
                doc.saveAs(psd_path, options, True)
                doc.close()

            self.status_label.config(
                text=f"Successfully converted to PSD with date/time: {os.path.basename(psd_path)}",
                foreground="green",
            )
        except Exception as e:
            self.status_label.config(
                text=f"Error converting file: {str(e)}", foreground="red"
            )

    def browse_jpg(self):
        """Open file dialog to select a JPG file."""
        filetypes = [("JPEG files", "*.jpg;*.jpeg")]
        filename = filedialog.askopenfilename(
            title="Select JPG File", filetypes=filetypes
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_label.config(
                text=f"Selected file: {os.path.basename(filename)}", foreground="black"
            )
