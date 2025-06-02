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
                    self.update_single_file(file_path)

                    processed += 1
                    progress = (processed / total_files) * 100
                    self.progress.set(progress)
                    self.status.set(f"Updating: {processed}/{total_files} - {filename}")
                    self.parent.update()

            else:
                # Process single file
                self.update_single_file(path)
                self.progress.set(100)

            if self.is_processing:
                self.status.set("Update complete")

        except Exception as e:
            self.status.set(f"Error during update: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.reset_ui()

    def update_single_file(self, file_path):
        """Update date in a single PSD file."""
        try:
            with Session() as ps:
                app = ps.app  # Get the Photoshop application object
                doc = app.open(file_path)  # Open document through app object
                today = datetime.today().strftime("%d-%m-%Y")

                text_layers_updated = self._process_layers(doc, today)

                if text_layers_updated:
                    self._save_document(doc)
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
            new_text = f"{today}\r{time_part}"
            text_item.contents = new_text

            # Verify if it worked
            updated = text_item.contents
            return "\r" in updated

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

    def _save_document(self, doc):
        """Save the document."""
        try:
            # Save the document in place (PSD format)
            doc.save()
            self.status.set(
                f"Successfully saved document: {os.path.basename(doc.fullName)}"
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

    def _process_layers(self, doc, today):
        """Process all layers in the document for date updates."""
        try:
            layers = list(doc.artLayers)
        except Exception as layer_error:
            raise Exception(f"Failed to access document layers: {str(layer_error)}")

        self.status.set(f"Processing {len(layers)} layers...")
        text_layers_updated = False

        for layer in layers:
            try:
                if self._process_text_layer(layer, today):
                    text_layers_updated = True
            except Exception:
                continue

        return text_layers_updated

    def _process_text_layer(self, layer, today):
        """Process a single text layer for date update."""
        try:
            text_item = layer.textItem
            if not text_item:
                return False

            layer_name = layer.name
            current_text = text_item.contents

            # Try to split the text into date and time parts
            normalized_text = current_text.replace("\r", " ").replace("\n", " ")
            parts = normalized_text.split()

            if len(parts) == 2 and ":" in parts[1]:
                time_part = parts[1]
                self.status.set(f"Attempting to update layer {layer_name}...")

                if self._update_text_layer(text_item, today, time_part):
                    self.status.set(f"Successfully updated layer: {layer_name}")
                    return True
                else:
                    self.status.set(
                        f"Failed to update layer {layer_name} - could not set line break"
                    )

            return False

        except Exception as update_error:
            self.status.set(f"Error updating layer {layer_name}: {str(update_error)}")
            return False

    def _save_document(self, doc):
        """Save the document."""
        try:
            # Save the document in place (PSD format)
            doc.save()
            self.status.set(
                f"Successfully saved document: {os.path.basename(doc.fullName)}"
            )

        except Exception as save_error:
            raise Exception(f"Failed to save document: {str(save_error)}")
