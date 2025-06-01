"""Module for adding date stamps to images using Pillow."""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import os
import random
from PIL import Image, ImageDraw, ImageFont

__all__ = ["DateStamperApp"]


class DateStamperApp:
    def __init__(self, parent):
        self.parent = parent
        self.start_hour = tk.IntVar(value=7)  # Default start hour
        self.end_hour = tk.IntVar(value=10)  # Default end hour
        self.setup_ui()

    def setup_ui(self):
        # Main Frame
        convert_frame = ttk.LabelFrame(self.parent, text="Date Stamper", padding="10")
        convert_frame.pack(fill="x", padx=5, pady=5)

        # File selection
        file_frame = ttk.Frame(convert_frame)
        file_frame.pack(fill="x", pady=(0, 10))

        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            file_frame, textvariable=self.file_path_var, width=50
        )
        self.file_path_entry.pack(side="left", padx=(0, 5))

        self.browse_btn = ttk.Button(
            file_frame, text="Browse Image", command=self.browse_image
        )
        self.browse_btn.pack(side="left", padx=5)

        # Time range frame
        time_frame = ttk.LabelFrame(convert_frame, text="Time Adjustment", padding="5")
        time_frame.pack(fill="x", pady=(0, 10))

        # Time range controls
        ttk.Label(time_frame, text="For times after 11:00, adjust to between:").pack(
            side="left", padx=5
        )

        ttk.Spinbox(
            time_frame, from_=0, to=23, width=3, textvariable=self.start_hour, wrap=True
        ).pack(side="left", padx=2)

        ttk.Label(time_frame, text="and").pack(side="left", padx=5)

        ttk.Spinbox(
            time_frame, from_=0, to=23, width=3, textvariable=self.end_hour, wrap=True
        ).pack(side="left", padx=2)

        ttk.Label(time_frame, text="hours").pack(side="left", padx=5)

        # Add Date Stamp button
        self.stamp_btn = ttk.Button(
            convert_frame, text="Add Date Stamp", command=self.add_date_stamp
        )
        self.stamp_btn.pack(pady=(0, 5))

        # Status Label
        self.status_label = ttk.Label(self.parent, text="")
        self.status_label.pack(pady=5)

    def adjust_time(self, current_hour, current_minute):
        """Adjust time if it's after 11:00."""
        if current_hour >= 11:
            start = self.start_hour.get()
            end = self.end_hour.get()
            # Ensure valid range
            if start > end:
                start, end = end, start
            adjusted_hour = random.randint(start, end)
            return f"{adjusted_hour:02d}:{current_minute:02d}"
        return f"{current_hour:02d}:{current_minute:02d}"

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
            font_size = int(min_dimension * 0.04)  # 4% of shorter dimension

            # Try to use Arial, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            # Get current time and adjust if needed
            now = datetime.now()
            current_date = now.strftime("%d-%m-%Y")
            adjusted_time = self.adjust_time(now.hour, now.minute)
            date_text = f"{current_date}\n{adjusted_time}"

            # Calculate text position with increased margins
            margin_x = int(min_dimension * 0.05)  # 5% horizontal margin
            margin_y = int(min_dimension * 0.06)  # 6% vertical margin

            # Get text size first for positioning
            text_bbox = draw.textbbox((0, 0), date_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            x = width - margin_x  # Right edge minus margin
            y = height - text_height - margin_y

            # Draw text shadow/outline for better visibility
            offset = max(1, int(font_size * 0.05))  # Outline thickness
            for dx, dy in [
                (-offset, -offset),
                (-offset, offset),
                (offset, -offset),
                (offset, offset),
            ]:
                draw.text(
                    (x + dx, y + dy),
                    date_text,
                    font=font,
                    fill="white",
                    align="right",
                    anchor="ra",
                )

            # Draw main text
            draw.text(
                (x, y), date_text, font=font, fill="black", align="right", anchor="ra"
            )

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
