"""Photoshop file date updater tool."""

import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import time
from photoshop import Session
from photoshop.api._core import Photoshop


class PSDDateUpdater:
    def __init__(self, parent):
        self.parent = parent
        self.status = tk.StringVar(value="Ready")
        self.psd_file_path = tk.StringVar()
        self.output_dir = tk.StringVar()  # Working directory for output

        # Custom date and time variables
        self.custom_date = tk.StringVar()  # For custom date input
        self.custom_time = tk.StringVar()  # For custom time input

        # Address and company information
        self.street_name = tk.StringVar()
        self.ward = tk.StringVar()
        self.subdistrict = tk.StringVar()
        self.district = tk.StringVar()
        self.province = tk.StringVar()
        self.company_name = tk.StringVar()

        self.progress = tk.DoubleVar(value=0.0)
        self.is_processing = False

        # Create widgets
        self.create_widgets()

        # Create results text widget
        self.results_text = tk.Text(self.parent, height=15, width=70)
        self.results_text.pack(pady=10, padx=5)

    def create_widgets(self):
        # File selection
        file_frame = ttk.Frame(self.parent)
        file_frame.pack(fill="x", pady=5)

        ttk.Label(file_frame, text="PSD File/Folder:").pack(side="left", padx=5)
        ttk.Entry(file_frame, textvariable=self.psd_file_path, width=50).pack(
            side="left", padx=5
        )

        # Button frame for file selection
        browse_frame = ttk.Frame(file_frame)
        browse_frame.pack(side="left")

        ttk.Button(browse_frame, text="Browse File", command=self.select_psd_file).pack(
            side="left", padx=5
        )
        ttk.Button(
            browse_frame, text="Browse Folder", command=self.select_psd_folder
        ).pack(side="left", padx=5)

        # Output directory selection
        output_frame = ttk.Frame(self.parent)
        output_frame.pack(fill="x", pady=5)

        ttk.Label(output_frame, text="Working Folder:").pack(side="left", padx=5)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(
            side="left", padx=5
        )
        ttk.Button(
            output_frame, text="Browse", command=self.select_output_directory
        ).pack(side="left", padx=5)

        # Custom Date/Time Frame
        datetime_frame = ttk.LabelFrame(
            self.parent, text="Custom Date/Time (Optional)", padding=10
        )
        datetime_frame.pack(fill="x", padx=5, pady=5)

        # Custom date field
        date_frame = ttk.Frame(datetime_frame)
        date_frame.pack(fill="x", pady=2)
        ttk.Label(date_frame, text="Date (DD/MM/YYYY):").pack(side="left", padx=5)
        ttk.Entry(date_frame, textvariable=self.custom_date, width=15).pack(
            side="left", padx=5
        )
        ttk.Label(date_frame, text="(Leave empty to use current date)").pack(
            side="left", padx=5
        )

        # Custom time field
        time_frame = ttk.Frame(datetime_frame)
        time_frame.pack(fill="x", pady=2)
        ttk.Label(time_frame, text="Time (HH.MM):").pack(side="left", padx=5)
        ttk.Entry(time_frame, textvariable=self.custom_time, width=10).pack(
            side="left", padx=5
        )
        ttk.Label(time_frame, text="(Leave empty to keep existing time)").pack(
            side="left", padx=5
        )

        # Address and Company Information Frame
        info_frame = ttk.LabelFrame(
            self.parent, text="Location Information", padding=10
        )
        info_frame.pack(fill="x", padx=5, pady=5)

        # Create grid for address fields
        fields = [
            ("Street Name:", self.street_name),
            ("Ward:", self.ward),
            ("Subdistrict:", self.subdistrict),
            ("District:", self.district),
            ("Province:", self.province),
            ("Company Name:", self.company_name),
        ]

        for i, (label_text, var) in enumerate(fields):
            ttk.Label(info_frame, text=label_text).grid(
                row=i, column=0, sticky="e", padx=5, pady=2
            )
            ttk.Entry(info_frame, textvariable=var, width=50).grid(
                row=i, column=1, sticky="ew", padx=5, pady=2
            )

        # Configure grid column to expand
        info_frame.columnconfigure(1, weight=1)

        # Progress bar
        progress_frame = ttk.Frame(self.parent)
        progress_frame.pack(fill="x", pady=5, padx=10)
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", variable=self.progress, length=300
        )
        self.progress_bar.pack(fill="x", expand=True)

        # Status
        ttk.Label(self.parent, textvariable=self.status).pack(pady=10)

        # Action buttons
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(pady=10)

        self.analyze_button = ttk.Button(
            button_frame, text="Analyze", command=self.analyze_files
        )
        self.analyze_button.pack(side="left", padx=5)

        self.update_button = ttk.Button(
            button_frame,
            text="Update Date",
            command=self.update_date,
            state="disabled",  # Disabled until analysis is done
        )
        self.update_button.pack(side="left", padx=5)

        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_processing,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=5)

    def select_psd_file(self):
        """Open file dialog to select a PSD file."""
        filetypes = [("Photoshop Files", "*.psd")]
        filename = filedialog.askopenfilename(
            title="Select PSD File", filetypes=filetypes
        )
        if filename:
            self.psd_file_path.set(filename)
            self.status.set(f"Selected file: {os.path.basename(filename)}")
            self.update_button.configure(state="disabled")
            self.results_text.delete(1.0, tk.END)

    def select_psd_folder(self):
        """Open folder dialog to select a directory with PSD files."""
        folder = filedialog.askdirectory(title="Select Folder with PSD Files")
        if folder:
            self.psd_file_path.set(folder)
            self.status.set(f"Selected folder: {os.path.basename(folder)}")
            self.update_button.configure(state="disabled")
            self.results_text.delete(1.0, tk.END)

    def select_output_directory(self):
        """Open directory dialog to select output working folder."""
        directory = filedialog.askdirectory(title="Select Working Folder for Output")
        if directory:
            self.output_dir.set(directory)
            self.status.set(f"Selected working folder: {os.path.basename(directory)}")

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

    def cancel_processing(self):
        """Cancel the ongoing processing."""
        if self.is_processing:
            self.is_processing = False
            self.status.set("Processing cancelled")
            self.progress.set(0)
            self.analyze_button.configure(state="normal")
            self.update_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")

    def analyze_files(self):
        """Analyze PSD files (single file or entire folder)."""
        path = self.psd_file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a PSD file or folder first")
            return

        self.is_processing = True
        self.analyze_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.update_button.configure(state="disabled")
        self.results_text.delete(1.0, tk.END)
        self.progress.set(0)

        try:
            if os.path.isdir(path):
                # Process folder
                psd_files = [f for f in os.listdir(path) if f.lower().endswith(".psd")]
                if not psd_files:
                    messagebox.showinfo(
                        "Info", "No PSD files found in the selected folder"
                    )
                    self.reset_ui()
                    return

                total_files = len(psd_files)
                processed = 0

                for filename in sorted(psd_files):
                    if not self.is_processing:
                        break

                    file_path = os.path.join(path, filename)
                    self.analyze_single_file(file_path)

                    processed += 1
                    progress = (processed / total_files) * 100
                    self.progress.set(progress)
                    self.status.set(
                        f"Analyzing: {processed}/{total_files} - {filename}"
                    )
                    self.parent.update()

            else:
                # Process single file
                if not path.lower().endswith(".psd"):
                    messagebox.showerror("Error", "Selected file is not a PSD file")
                    self.reset_ui()
                    return

                self.analyze_single_file(path)
                self.progress.set(100)

            if self.is_processing:
                self.status.set("Analysis complete")
                self.update_button.configure(state="normal")

        except Exception as e:
            self.status.set(f"Error during analysis: {str(e)}")
            messagebox.showerror("Error", str(e))

        finally:
            self.reset_ui()

    def analyze_single_file(self, file_path):
        """Analyze a single PSD file."""
        try:
            with Session() as ps:
                app = ps.app  # Get the Photoshop application object
                doc = app.open(file_path)  # Open document through app object

                # Document info
                self.results_text.insert(
                    tk.END, f"\n=== {os.path.basename(file_path)} ===\n"
                )
                self._analyze_document_info(doc)

                # Layer information
                self._analyze_layers(doc)

                doc.close()

        except Exception as e:
            self.results_text.insert(
                tk.END, f"Error analyzing {os.path.basename(file_path)}: {str(e)}\n"
            )
            raise

    def update_date(self):
        """Update the date in PSD files."""
        if not self.is_processing and not self.psd_file_path.get():
            return

        # Check if output directory is selected
        batch_folder = None
        if self.output_dir.get():
            # Create a new numbered folder for this batch
            batch_folder = self.get_next_output_folder()
        else:
            use_source = messagebox.askyesno(
                "No Working Folder",
                "No working folder selected. Do you want to save in the source location?",
            )
            if not use_source:
                return

        self.is_processing = True
        self.update_button.configure(state="disabled")
        self.analyze_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.set(0)

        path = self.psd_file_path.get()
        try:
            if os.path.isdir(path):
                # Process folder
                psd_files = [f for f in os.listdir(path) if f.lower().endswith(".psd")]
                total_files = len(psd_files)
                processed = 0

                for filename in sorted(psd_files):
                    if not self.is_processing:
                        break

                    file_path = os.path.join(path, filename)
                    self.update_single_file(file_path, batch_folder)

                    processed += 1
                    progress = (processed / total_files) * 100
                    self.progress.set(progress)
                    self.status.set(f"Updating: {processed}/{total_files} - {filename}")
                    self.parent.update()

            else:
                # Process single file
                self.update_single_file(path, batch_folder)
                self.progress.set(100)

            if self.is_processing:
                if batch_folder:
                    folder_num = os.path.basename(batch_folder)
                    self.status.set(
                        f"Update complete - All files saved in folder {folder_num}"
                    )
                else:
                    self.status.set("Update complete - Files saved in source location")

        except Exception as e:
            self.status.set(f"Error during update: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.reset_ui()

    def update_single_file(self, file_path, batch_folder=None):
        """Update date in a single PSD file."""
        try:
            with Session() as ps:
                app = ps.app  # Get the Photoshop application object
                doc = app.open(file_path)  # Open document through app object
                today = datetime.today().strftime("%d-%m-%Y")

                text_layers_updated = self._process_layers(doc, today)

                if text_layers_updated:
                    self._save_document(doc, batch_folder)
                    self.results_text.insert(
                        tk.END, f"Updated: {os.path.basename(file_path)}\n"
                    )
                else:
                    self.results_text.insert(
                        tk.END, f"No updates needed: {os.path.basename(file_path)}\n"
                    )

                doc.close()

        except Exception as e:
            self.results_text.insert(
                tk.END, f"Error updating {os.path.basename(file_path)}: {str(e)}\n"
            )
            raise

    def reset_ui(self):
        """Reset UI elements after processing."""
        self.is_processing = False
        self.analyze_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

    def _update_text_layer(self, text_item, today, time_part):
        """Update a text layer with new date while keeping the time."""
        try:
            # Check for custom date and time
            custom_date = self.custom_date.get().strip()
            custom_time = self.custom_time.get().strip()

            # Use custom date if provided and valid (DD/MM/YYYY format)
            if custom_date and len(custom_date.split("/")) == 3:
                final_date = custom_date
            else:
                final_date = today.replace("-", "/")

            # Use custom time if provided and valid (HH.MM format)
            if custom_time and "." in custom_time:
                final_time = custom_time
            else:
                final_time = time_part.replace(":", ".")

            # Format the final date and time
            date_time = f"{final_date} {final_time}"

            # Filter out empty location fields
            location_fields = [
                field
                for field in [
                    self.street_name.get(),
                    self.ward.get(),
                    self.subdistrict.get(),
                    self.district.get(),
                    self.province.get(),
                    self.company_name.get(),
                ]
                if field.strip()
            ]

            # Combine with proper line breaks
            all_fields = [date_time] + location_fields
            full_text = "\r".join(all_fields)

            # Update text content
            text_item.contents = full_text

            # Set right-alignment and attempt position adjustment
            try:
                # Right-justify the text
                text_item.justification = 3  # PsRightJustified = 3

                # Get the document and layer for positioning
                layer = text_item.parent
                doc = layer.parent

                # Get layer bounds
                bounds = layer.bounds  # Calculate padding and dimensions
                padding = min(doc.width, doc.height) * 0.05  # 5% of smaller dimension

                # Get current bounds and reset position to origin
                current_x = bounds[0]
                current_y = bounds[1]

                # Calculate the desired position in the bottom-right corner
                new_x = doc.width - (bounds[2] - bounds[0]) - padding
                new_y = doc.height - (bounds[3] - bounds[1]) - padding

                # Calculate the relative movement needed
                delta_x = new_x - current_x
                delta_y = new_y - current_y

                # Move layer by the relative difference
                layer.translate(delta_x, delta_y)

                # Verify position
                updated_bounds = layer.bounds
                if updated_bounds[3] > doc.height or updated_bounds[2] > doc.width:
                    # If text is still outside, adjust inward
                    adjust_x = max(0, updated_bounds[2] - doc.width + padding)
                    adjust_y = max(0, updated_bounds[3] - doc.height + padding)
                    layer.translate(-adjust_x, -adjust_y)
            except Exception as pos_error:
                self.status.set(
                    f"Warning: Could not adjust text position - {str(pos_error)}"
                )

            # Verify update
            updated = text_item.contents
            return len(updated.split("\r")) > 1

        except Exception as update_error:
            self.status.set(f"Error updating text: {str(update_error)}")
            return False

    def analyze_layers(self):
        """Analyze the layers in the selected PSD file."""
        # Reset progress and UI
        self.progress.set(0)
        self.analyze_button.configure(state="disabled")
        self.update_button.configure(state="disabled")
        self.results_text.delete(1.0, tk.END)

        psd_path = self.psd_file_path.get()
        if not psd_path:
            self.status.set("Please select a PSD file first")
            self.analyze_button.configure(state="normal")
            return

        if not os.path.exists(psd_path):
            self.status.set("Selected PSD file does not exist")
            self.analyze_button.configure(state="normal")
            return

        ps = None
        doc = None

        try:
            # Opening Photoshop (10%)
            self.status.set("Starting Photoshop...")
            self.progress.set(10)
            self.parent.update_idletasks()
            ps = Photoshop()

            try:
                self.status.set("Opening PSD file...")
                ps.open(psd_path)
            except Exception as open_error:
                raise Exception(f"Failed to open PSD file: {str(open_error)}")

            # Waiting for document (20%)
            self.progress.set(20)
            self.parent.update_idletasks()
            max_retries = 10
            doc = None

            for retry in range(max_retries):
                try:
                    doc = ps.app.activeDocument
                    break
                except Exception:
                    self.status.set(
                        f"Waiting for document to load (attempt {retry + 1}/{max_retries})..."
                    )
                    time.sleep(0.5)

            if doc is None:
                raise Exception("Could not access the document after multiple attempts")

            # Document info (30%)
            self.progress.set(30)
            self.parent.update_idletasks()
            self.results_text.insert(tk.END, "=== Document Information ===\n")

            try:
                self._analyze_document_info(doc)
            except Exception as info_error:
                self.results_text.insert(
                    tk.END, f"Error getting document info: {str(info_error)}\n\n"
                )

            # Layer information (40% - 90%)
            try:
                layers = list(doc.artLayers)
                total_layers = len(layers)
                self.results_text.insert(
                    tk.END, f"=== Layer Analysis ({total_layers} layers) ===\n\n"
                )

                for i, layer in enumerate(layers, 1):
                    # Update progress (40% - 90% based on layer count)
                    progress = 40 + (50 * (i / total_layers))
                    self.progress.set(progress)
                    self.parent.update_idletasks()

                    try:
                        self._analyze_single_layer(layer)
                    except Exception as layer_error:
                        error_info = (
                            f"Error analyzing layer: {str(layer_error)}\n"
                            + "-" * 50
                            + "\n"
                        )
                        self.results_text.insert(tk.END, error_info)
                        self.status.set(f"Error in layer analysis: {str(layer_error)}")
                        continue

                # Analysis complete (100%)
                self.progress.set(100)
                self.parent.update_idletasks()
                self.results_text.insert(tk.END, "\nAnalysis complete!")
                self.status.set("Layer analysis complete")

                # Enable the Update button since analysis is done
                self.update_button.configure(state="normal")

            except Exception as layer_error:
                raise Exception(f"Failed to analyze layers: {str(layer_error)}")

        except Exception as e:
            self.status.set(f"Error: {str(e)}")
            self.results_text.insert(tk.END, f"\nError: {str(e)}")
            self.progress.set(0)  # Reset progress on error

        finally:
            # Re-enable the Analyze button
            self.analyze_button.configure(state="normal")

    def _save_document(self, doc, batch_folder=None):
        """Save the document as both PSD and JPG with date prefix."""
        try:
            # Get original file path and create new paths with date prefix
            original_path = doc.fullName
            file_name = os.path.basename(original_path)
            name, ext = os.path.splitext(file_name)

            # Use provided batch folder or source location
            output_folder = batch_folder or os.path.dirname(original_path)
            if batch_folder is None:
                self.status.set("No output folder selected, saving in source location")

            # Create date prefix (YYMMDD)
            date_str = datetime.now().strftime("%y%m%d")

            # Create new filenames
            new_psd_path = os.path.join(output_folder, f"{date_str}_{name}.psd")
            new_jpg_path = os.path.join(output_folder, f"{date_str}_{name}.jpg")
            ver2_jpg_path = os.path.join(output_folder, f"{date_str}_{name}_ver2.jpg")

            with Session() as ps:
                # Save as PSD
                options = ps.PhotoshopSaveOptions()
                doc.saveAs(new_psd_path, options, True)  # True = save as copy

                # First JPG
                jpg_options = ps.JPEGSaveOptions(quality=12)  # Highest quality
                doc.saveAs(new_jpg_path, jpg_options, True)

                # Check for Type 17 layers above datetime layers
                for layer in doc.artLayers:
                    try:
                        if hasattr(layer, "textItem") and layer.textItem:
                            has_type17, found_layer, position = (
                                self._has_type17_near_datetime(doc, layer)
                            )
                            if has_type17 and found_layer:
                                # Remember the original visibility
                                original_visibility = found_layer.visible
                                found_layer.visible = False

                                # Save ver2 JPG
                                doc.saveAs(ver2_jpg_path, jpg_options, True)

                                # Restore original visibility
                                found_layer.visible = original_visibility

                                output_dir = os.path.basename(output_folder)
                                self.status.set(
                                    f"Saved in folder {output_dir}: {os.path.basename(new_psd_path)}, "
                                    f"{os.path.basename(new_jpg_path)}, and "
                                    f"{os.path.basename(ver2_jpg_path)} "
                                    f"(Type 17 layer {position} datetime hidden)"
                                )
                                return
                    except:
                        continue

            output_dir = os.path.basename(output_folder)
            self.status.set(
                f"Saved in folder {output_dir}: {os.path.basename(new_psd_path)} and "
                f"{os.path.basename(new_jpg_path)}"
            )

        except Exception as save_error:
            raise Exception(f"Failed to save document: {str(save_error)}")

    def _analyze_document_info(self, doc):
        """Analyze and display document information."""
        doc_name = doc.name
        doc_path = doc.fullName
        doc_width = doc.width
        doc_height = doc.height
        self.results_text.insert(tk.END, f"Name: {doc_name}\n")
        self.results_text.insert(tk.END, f"Path: {doc_path}\n")
        self.results_text.insert(tk.END, f"Size: {doc_width} x {doc_height}\n\n")

    def _analyze_layers(self, doc):
        """Analyze and display layer information."""
        layers = list(doc.artLayers)
        self.results_text.insert(
            tk.END, f"=== Layer Analysis ({len(layers)} layers) ===\n\n"
        )

        for layer in layers:
            try:
                self._analyze_single_layer(layer)
            except Exception as layer_error:
                error_info = (
                    f"Error analyzing layer: {str(layer_error)}\n" + "-" * 50 + "\n"
                )
                self.results_text.insert(tk.END, error_info)
                self.status.set(f"Error in layer analysis: {str(layer_error)}")
                continue

        self.results_text.insert(tk.END, "\nAnalysis complete!")
        self.status.set("Layer analysis complete")

    def _analyze_single_layer(self, layer):
        """Analyze and display information for a single layer."""
        layer_name = layer.name
        layer_kind = layer.kind
        layer_visible = "Unknown"
        try:
            layer_visible = "Visible" if layer.visible else "Hidden"
        except:
            pass

        self.results_text.insert(tk.END, f"Layer: {layer_name}\n")
        self.results_text.insert(tk.END, f"Type: {layer_kind}\n")
        self.results_text.insert(tk.END, f"Status: {layer_visible}\n")

        # Try to analyze text properties if it's a text layer
        try:
            self._analyze_text_properties(layer)
        except Exception:
            pass

        self.results_text.insert(tk.END, "-" * 50 + "\n")
        self.results_text.see(tk.END)  # Scroll to latest
        self.status.set(f"Analyzed layer: {layer_name}")

    def _analyze_text_properties(self, layer):
        """Analyze and display text properties for a text layer."""
        text_item = layer.textItem
        text_content = text_item.contents
        self.results_text.insert(tk.END, "Text Properties:\n")
        self.results_text.insert(tk.END, f"  Content: {text_content}\n")

        for prop in ["font", "size", "justification"]:
            try:
                value = getattr(text_item, prop)
                self.results_text.insert(tk.END, f"  {prop.capitalize()}: {value}\n")
            except:
                pass

    def _has_type17_near_datetime(self, doc, datetime_layer):
        """Check if there's a Type 17 layer above the datetime layer."""
        try:
            layers = list(doc.artLayers)

            # Only check layers above the datetime layer
            for layer in reversed(layers):
                if layer == datetime_layer:
                    break
                elif layer.kind == 17:
                    return True, layer, "above"

            return False, None, None
        except Exception as e:
            self.status.set(f"Error checking Type 17 layers: {str(e)}")
            return False, None, None

    def _process_layers(self, doc, today):
        """Process all layers in the document for date updates."""
        try:
            layers = list(doc.artLayers)
        except Exception as layer_error:
            raise Exception(f"Failed to access document layers: {str(layer_error)}")

        self.status.set(f"Processing {len(layers)} layers...")
        text_layers_updated = False
        has_type17_above_datetime = False
        type17_layer = None
        datetime_layer = None

        # First pass: analyze layer structure
        for i, layer in enumerate(layers):
            try:
                if hasattr(layer, "textItem") and layer.textItem:
                    text_content = layer.textItem.contents
                    # Check if it's a date/time layer by looking for date/time patterns
                    if ("/" in text_content and "." in text_content) or (
                        "\r" in text_content
                    ):
                        datetime_layer = layer
                        # Check if the previous layer is Type 17
                        if i > 0 and layers[i - 1].kind == 17:
                            has_type17_above_datetime = True
                            type17_layer = layers[i - 1]
                if datetime_layer and type17_layer:
                    break
            except Exception:
                continue

        # Second pass: process text layers
        for layer in layers:
            try:
                if hasattr(layer, "textItem"):
                    text_item = layer.textItem
                    if not text_item:
                        continue

                    current_text = text_item.contents
                    # Try to extract date and time
                    if "/" in current_text and "." in current_text:
                        # New format
                        first_line = current_text.split("\r")[0]
                        date_time = first_line.split()
                        if len(date_time) == 2:
                            time_part = date_time[1].replace(".", ":")
                            if ":" in time_part:
                                if self._update_text_layer(text_item, today, time_part):
                                    text_layers_updated = True
                    else:
                        # Old format
                        normalized_text = current_text.replace("\r", " ").replace(
                            "\n", " "
                        )
                        parts = normalized_text.split()
                        if len(parts) == 2 and ":" in parts[1]:
                            time_part = parts[1]
                            if self._update_text_layer(text_item, today, time_part):
                                text_layers_updated = True

            except Exception as update_error:
                self.status.set(f"Error updating layer: {str(update_error)}")
                continue

        return text_layers_updated
