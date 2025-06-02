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
        self.last_minute = None  # Track last used minute
        self.current_hour = None  # Track current hour for batch processing
        self.output_dir = tk.StringVar()  # Working directory for output
        self.setup_ui()

    def setup_ui(self):
        # Main Frame
        convert_frame = ttk.LabelFrame(self.parent, text="Date Stamper", padding="10")
        convert_frame.pack(fill="x", padx=5, pady=5)

        # File selection frame
        file_frame = ttk.Frame(convert_frame)
        file_frame.pack(fill="x", pady=(0, 10))

        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(
            file_frame, textvariable=self.file_path_var, width=50
        )
        self.file_path_entry.pack(side="left", padx=(0, 5))

        # Add buttons frame
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(side="left")

        self.browse_btn = ttk.Button(
            button_frame, text="Browse Image", command=self.browse_image
        )
        self.browse_btn.pack(side="left", padx=5)

        self.browse_batch_btn = ttk.Button(
            button_frame, text="Browse Folder", command=self.browse_folder
        )
        self.browse_batch_btn.pack(side="left", padx=5)

        # Output directory selection
        output_frame = ttk.Frame(convert_frame)
        output_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(output_frame, text="Working Folder:").pack(side="left", padx=5)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(
            side="left", padx=5
        )

        # Browse output directory button
        ttk.Button(
            output_frame, text="Browse", command=self.select_output_directory
        ).pack(side="left", padx=5)

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

        # Process buttons frame
        process_frame = ttk.Frame(convert_frame)
        process_frame.pack(pady=(0, 5))

        self.stamp_btn = ttk.Button(
            process_frame, text="Add Date Stamp", command=self.add_date_stamp
        )
        self.stamp_btn.pack(side="left", padx=5)

        self.batch_stamp_btn = ttk.Button(
            process_frame, text="Process Folder", command=self.process_folder
        )
        self.batch_stamp_btn.pack(side="left", padx=5)

        # Status Label
        self.status_label = ttk.Label(self.parent, text="")
        self.status_label.pack(pady=5)

    def adjust_time(self, input_hour, input_minute):
        """Adjust time with sequential minutes."""
        # Initialize time tracking if this is the first image
        if self.last_minute is None:
            self.last_minute = (
                input_minute - 1
            )  # Start one minute before so first increment matches input
            if input_hour >= 11:
                start = self.start_hour.get()
                end = self.end_hour.get()
                if start > end:
                    start, end = end, start
                self.current_hour = random.randint(start, end)
            else:
                self.current_hour = input_hour

        # Increment minute for each image
        self.last_minute = (self.last_minute + 1) % 60

        # If minutes roll over or we're past 11:00, possibly get new hour
        if self.last_minute == 0 or (input_hour >= 11 and self.current_hour is None):
            start = self.start_hour.get()
            end = self.end_hour.get()
            if start > end:
                start, end = end, start
            self.current_hour = random.randint(start, end)

        # Use randomized hour if after 11:00, otherwise use input hour
        display_hour = self.current_hour if input_hour >= 11 else input_hour
        return f"{display_hour:02d}:{self.last_minute:02d}"

    def browse_folder(self):
        """Open folder dialog to select a directory of images."""
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.file_path_var.set(folder)
            self.status_label.config(
                text=f"Selected folder: {os.path.basename(folder)}", foreground="black"
            )

    def process_folder(self):
        """Process all images in the selected folder."""
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select a folder first")
            return

        folder_path = self.file_path_var.get()
        if not os.path.isdir(folder_path):
            messagebox.showerror("Error", "Please select a valid folder")
            return

        # Get output folder
        output_folder = None
        if self.output_dir.get():
            output_folder = self.get_next_output_folder()
        else:
            use_source = messagebox.askyesno(
                "No Working Folder",
                "No working folder selected. Do you want to save in the source location?",
            )
            if not use_source:
                return

        # Reset time tracking for new batch
        self.last_minute = None
        self.current_hour = None
        processed_count = 0
        error_count = 0

        # Get list of image files
        image_files = [
            f
            for f in os.listdir(folder_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
        ]

        if not image_files:
            messagebox.showinfo("Info", "No image files found in the selected folder")
            return

        # Sort files to ensure consistent order
        image_files.sort()

        # Process each image
        for filename in image_files:
            input_path = os.path.join(folder_path, filename)
            try:
                self.process_single_image(input_path, output_folder)
                processed_count += 1
                status_msg = (
                    f"Processing: {processed_count}/{len(image_files)} - {filename}"
                )
                if output_folder:
                    folder_num = os.path.basename(output_folder)
                    status_msg += f" (Output folder: {folder_num})"
                self.status_label.config(
                    text=status_msg,
                    foreground="black",
                )
                self.parent.update()  # Update UI
            except Exception as e:
                error_count += 1
                print(f"Error processing {filename}: {str(e)}")

        # Final status update
        if output_folder:
            folder_num = os.path.basename(output_folder)
            status = (
                f"Completed: {processed_count} images processed in folder {folder_num}"
            )
        else:
            status = f"Completed: {processed_count} images processed in source location"
        if error_count > 0:
            status += f", {error_count} errors"
        self.status_label.config(
            text=status, foreground="green" if error_count == 0 else "red"
        )

    def process_single_image(self, input_path, output_folder=None):
        """Process a single image file."""
        try:
            # Open original image
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

            # Calculate text position with margins
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

            # Determine output directory
            if output_folder:
                save_dir = output_folder
            else:
                save_dir = os.path.dirname(input_path)

            # Create output filename with date stamp
            file_name = os.path.basename(input_path)
            name, ext = os.path.splitext(file_name)
            date_str = now.strftime("%y%m%d")
            output_path = os.path.join(save_dir, f"{date_str}_{name}.jpg")

            # Save the image with high quality
            img.save(output_path, "JPEG", quality=95)

            return output_path

        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def add_date_stamp(self):
        """Add date/time stamp to single image and save as JPEG."""
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select an image file first")
            return

        # Get output folder
        output_folder = None
        if self.output_dir.get():
            output_folder = self.get_next_output_folder()
        else:
            use_source = messagebox.askyesno(
                "No Working Folder",
                "No working folder selected. Do you want to save in the source location?",
            )
            if not use_source:
                return

        try:
            # Reset time tracking for single image
            self.last_minute = None
            self.current_hour = None
            output_path = self.process_single_image(
                self.file_path_var.get(), output_folder
            )

            if output_folder:
                folder_num = os.path.basename(output_folder)
                self.status_label.config(
                    text=f"Successfully saved image in folder {folder_num}: {os.path.basename(output_path)}",
                    foreground="green",
                )
            else:
                self.status_label.config(
                    text=f"Successfully saved image: {os.path.basename(output_path)}",
                    foreground="green",
                )
        except Exception as e:
            self.status_label.config(
                text=f"Error adding date stamp: {str(e)}",
                foreground="red",
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

    def get_next_output_folder(self):
        """Get the next available numbered folder in the output directory."""
        base_dir = self.output_dir.get()
        if not base_dir:
            return None

        # Find the next available number
        counter = 1
        while True:
            folder_name = str(counter)
            folder_path = os.path.join(base_dir, folder_name)
            if not os.path.exists(folder_path):
                # Create the directory
                os.makedirs(folder_path)
                return folder_path
            counter += 1

    def select_output_directory(self):
        """Open directory dialog to select output working folder."""
        directory = filedialog.askdirectory(title="Select Working Folder for Output")
        if directory:
            self.output_dir.set(directory)
            self.status_label.config(
                text=f"Selected working folder: {os.path.basename(directory)}",
                foreground="black",
            )
