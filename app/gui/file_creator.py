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
            current_date = datetime.now().strftime("%d-%m-%Y")
            current_time = datetime.now().strftime("%H:%M")

            # Open Photoshop and create new document from JPG
            with Session() as ps:
                app = ps.app
                doc = app.open(jpg_path)

                # Get document dimensions
                width = doc.width
                height = doc.height
                margin = width * 0.02  # 2% of width as margin

                # Create text layer
                text_layer = doc.artLayers.add()
                text_layer.kind = 2  # TextLayer
                text_item = text_layer.textItem
                # Set text with bottom right alignment
                text_item.contents = f"{current_date}\r{current_time}"
                text_item.size = 32
                text_item.position = [
                    width - 50,
                    height - 50,
                ]  # Start near bottom right
                text_item.kind = 2  # Ensures it's a text layer
                text_item.justification = 2  # Right alignment

                # Get bounds and calculate offset
                bounds = text_layer.bounds
                text_width = bounds[2] - bounds[0]
                text_height = bounds[3] - bounds[1]

                # Move to bottom right with margin
                text_item.position = [
                    width - margin - text_width,
                    height - margin - text_height,
                ]

                # Set the text color to black
                text_color = ps.SolidColor()
                text_color.rgb.red = 0
                text_color.rgb.green = 0
                text_color.rgb.blue = 0
                text_item.color = text_color

                # Apply layer styles for stroke
                idxTo = app.stringIDToTypeID
                desc = ps.ActionDescriptor()

                # Enable stroke
                desc.putBoolean(idxTo("strokeEnabled"), True)
                # Set stroke color to white
                strokeDesc = ps.ActionDescriptor()
                strokeDesc.putDouble(idxTo("red"), 255)
                strokeDesc.putDouble(idxTo("green"), 255)
                strokeDesc.putDouble(idxTo("blue"), 255)
                desc.putObject(idxTo("strokeColor"), idxTo("RGBColor"), strokeDesc)
                # Set stroke size
                desc.putUnitDouble(
                    idxTo("strokeStyleLineWidth"), idxTo("pixelsUnit"), stroke_size
                )

                # Apply the styles
                text_layer.applyLayerStyle(desc)

                # Save as PSD
                options = ps.PhotoshopSaveOptions()
                doc.saveAs(psd_path, options, True)
                doc.close()

            self.status_label.config(
                text=f"Successfully added date stamp to: {os.path.basename(psd_path)}",
                foreground="green",
            )
        except Exception as e:
            self.status_label.config(
                text=f"Error adding date stamp: {str(e)}", foreground="red"
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
