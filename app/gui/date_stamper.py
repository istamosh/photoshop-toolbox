"""Module for adding date stamps to images using Pillow."""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont

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
            convert_frame, text="Browse Image", command=self.browse_image
        )
        self.browse_btn.pack(side="left", padx=5)

        self.stamp_btn = ttk.Button(
            convert_frame, text="Add Date Stamp", command=self.add_date_stamp
        )
        self.stamp_btn.pack(side="left")

        # Status Label
        self.status_label = ttk.Label(self.parent, text="")
        self.status_label.pack(pady=5)

    def add_date_stamp(self):
        """Add date/time stamp to image and save as JPEG."""
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select an image file first")
            return

        try:
            # Open original image
            input_path = self.file_path_var.get()
            img = Image.open(input_path)

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Create draw object
            draw = ImageDraw.Draw(img)

            # Calculate text size and position
            width, height = img.size
            min_dimension = min(width, height)
            font_size = int(min_dimension * 0.03)  # 3% of shorter dimension

            # Try to use Arial, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            # Format date and time
            current_date = datetime.now().strftime("%d-%m-%Y")
            current_time = datetime.now().strftime("%H:%M")
            date_text = f"{current_date}\n{current_time}"

            # Calculate text position
            margin = int(min_dimension * 0.02)  # 2% margin
            text_bbox = draw.textbbox((0, 0), date_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = width - text_width - margin
            y = height - text_height - margin

            # Draw text shadow/outline for better visibility
            offset = max(1, int(font_size * 0.05))  # Outline thickness
            for dx, dy in [
                (-offset, -offset),
                (-offset, offset),
                (offset, -offset),
                (offset, offset),
            ]:
                draw.text((x + dx, y + dy), date_text, font=font, fill="white")

            # Draw main text
            draw.text((x, y), date_text, font=font, fill="black")

            # Create output filename with date stamp
            file_dir = os.path.dirname(input_path)
            file_name = os.path.basename(input_path)
            name, ext = os.path.splitext(file_name)
            date_str = datetime.now().strftime("%y%m%d")
            output_path = os.path.join(file_dir, f"{date_str}_{name}.jpg")

            # Save the image with high quality
            img.save(output_path, "JPEG", quality=95)

            self.status_label.config(
                text=f"Successfully saved image with date stamp: {os.path.basename(output_path)}",
                foreground="green",
            )

        except Exception as e:
            self.status_label.config(
                text=f"Error adding date stamp: {str(e)}", foreground="red"
            )

    def browse_image(self):
        """Open file dialog to select an image file."""
        filetypes = [("Image files", "*.jpg;*.jpeg;*.png;*.bmp")]
        filename = filedialog.askopenfilename(
            title="Select Image File", filetypes=filetypes
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_label.config(
                text=f"Selected file: {os.path.basename(filename)}", foreground="black"
            )
