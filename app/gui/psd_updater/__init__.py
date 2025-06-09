"""Package for PSD file date updating functionality."""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from photoshop import Session

from .window import PSDUpdaterWindow
from .models import TimeInfo, LocationInfo
from .processor import TextLayerProcessor, DocumentProcessor
from .constants import LayerKind, DateTimeFormats, TextSizing, Justification


class PSDDateUpdater(PSDUpdaterWindow):
    """Main class for updating dates in PSD files."""

    def __init__(self, parent):
        super().__init__(parent)

    def _reset_ui(self):
        """Reset UI elements after processing."""
        self.is_processing = False
        self.analyze_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

    def analyze_files(self):
        """Handle analyze files button click."""
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
                psd_files = [f for f in os.listdir(path) if f.lower().endswith(".psd")]
                if not psd_files:
                    messagebox.showinfo(
                        "Info", "No PSD files found in the selected folder"
                    )
                    self._reset_ui()
                    return

                total_files = len(psd_files)
                processed = 0

                for filename in sorted(psd_files):
                    if not self.is_processing:
                        break

                    file_path = os.path.join(path, filename)
                    self._analyze_single_file(file_path)

                    processed += 1
                    progress = (processed / total_files) * 100
                    self.progress.set(progress)
                    self.status.set(
                        f"Analyzing: {processed}/{total_files} - {filename}"
                    )
                    self.parent.update()

            else:
                if not path.lower().endswith(".psd"):
                    messagebox.showerror("Error", "Selected file is not a PSD file")
                    self._reset_ui()
                    return

                self._analyze_single_file(path)
                self.progress.set(100)

            if self.is_processing:
                self.status.set("Analysis complete")
                self.update_button.configure(state="normal")

        except Exception as e:
            self.status.set(f"Error during analysis: {str(e)}")
            messagebox.showerror("Error", str(e))
            self._reset_ui()

    def _analyze_single_file(self, file_path):
        """Analyze a single PSD file."""
        try:
            with Session() as ps:
                app = ps.app
                doc = app.open(file_path)

                self.results_text.insert(
                    tk.END, f"\n=== {os.path.basename(file_path)} ===\n"
                )
                self._analyze_document_info(doc)
                self._analyze_layers(doc)

                doc.close()
        except Exception as e:
            self.results_text.insert(
                tk.END, f"Error analyzing {os.path.basename(file_path)}: {str(e)}\n"
            )
            raise

    def _analyze_document_info(self, doc):
        """Analyze and display document information."""
        try:
            doc_info = DocumentProcessor.analyze_document(doc)
            self.results_text.insert(tk.END, f"Name: {doc_info['name']}\n")
            self.results_text.insert(tk.END, f"Path: {doc_info['path']}\n")
            self.results_text.insert(
                tk.END, f"Size: {doc_info['width']} x {doc_info['height']}\n\n"
            )
        except Exception as e:
            raise Exception(f"Error analyzing document: {str(e)}")

    def _analyze_layers(self, doc):
        """Analyze all layers in the document."""
        try:
            layers = list(doc.artLayers)
            self.results_text.insert(
                tk.END, f"=== Layer Analysis ({len(layers)} layers) ===\n\n"
            )

            for layer in layers:
                self._analyze_single_layer(layer)

            self.results_text.insert(tk.END, "\nAnalysis complete!")
            self.status.set("Layer analysis complete")
        except Exception as e:
            raise Exception(f"Error analyzing layers: {str(e)}")

    def _analyze_single_layer(self, layer):
        """Analyze a single layer."""
        try:
            layer_name = layer.name
            layer_kind = layer.kind
            layer_visible = "Visible" if layer.visible else "Hidden"

            self.results_text.insert(tk.END, f"Layer: {layer_name}\n")
            self.results_text.insert(tk.END, f"Type: {layer_kind}\n")
            self.results_text.insert(tk.END, f"Status: {layer_visible}\n")

            if hasattr(layer, "textItem") and layer.textItem:
                self._analyze_text_properties(layer)

            self.results_text.insert(tk.END, "-" * 50 + "\n")
            self.results_text.see(tk.END)
            self.status.set(f"Analyzed layer: {layer_name}")
        except Exception:
            self.results_text.insert(tk.END, f"Error analyzing layer\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n")

    def _analyze_text_properties(self, layer):
        """Analyze text properties of a layer."""
        try:
            text_item = layer.textItem
            text_content = text_item.contents
            self.results_text.insert(tk.END, "Text Properties:\n")
            self.results_text.insert(tk.END, f"  Content: {text_content}\n")

            # Extract datetime and location info if present
            lines = text_content.replace("\r", "\n").split("\n")
            lines = [line.strip() for line in lines if line.strip()]

            if len(lines) >= 1:
                self._handle_date_time_format(lines)

            # Display text properties
            for prop in ["font", "size", "justification"]:
                try:
                    value = getattr(text_item, prop)
                    self.results_text.insert(
                        tk.END, f"  {prop.capitalize()}: {value}\n"
                    )
                except:
                    pass

        except Exception:
            pass

    def _handle_date_time_format(self, lines):
        """Extract and handle date/time information from text lines."""
        # Handle old format (separate date and time lines)
        if len(lines) == 2 and ("-" in lines[0] or "/" in lines[0]) and ":" in lines[1]:
            date_part = lines[0].replace("-", "/")
            time_part = lines[1].replace(":", ".")
            self.custom_date.set(date_part)
            self.custom_time.set(time_part)
            self.location_text.delete("1.0", tk.END)

        # Handle new format (date time on first line, locations follow)
        elif (
            " " in lines[0]
            and ("/" in lines[0] or "-" in lines[0])
            and ("." in lines[0] or ":" in lines[0])
        ):
            date_time = lines[0].split(" ")
            if len(date_time) == 2:
                date_part = date_time[0].replace("-", "/")
                time_part = date_time[1].replace(":", ".")
                self.custom_date.set(date_part)
                self.custom_time.set(time_part)

                # Set location info if present
                if len(lines) > 1:
                    location_info = LocationInfo.from_text("\n".join(lines[1:]))
                    self.location_text.delete("1.0", tk.END)
                    if location_info:
                        self.location_text.insert(
                            "1.0", "\n".join(location_info.as_list)
                        )

    def update_date(self):
        """Handle update date button click."""
        if not self.is_processing and not self.psd_file_path.get():
            return

        # Reset batch time counter
        self.current_batch_time = None

        # Check output directory
        batch_folder = None
        if self.output_dir.get():
            batch_folder = self._get_next_output_folder()
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
                psd_files = [f for f in os.listdir(path) if f.lower().endswith(".psd")]
                total_files = len(psd_files)
                processed = 0

                for filename in sorted(psd_files):
                    if not self.is_processing:
                        break

                    file_path = os.path.join(path, filename)
                    self._update_single_file(file_path, batch_folder)

                    processed += 1
                    progress = (processed / total_files) * 100
                    self.progress.set(progress)
                    self.status.set(f"Updating: {processed}/{total_files} - {filename}")
                    self.parent.update()
            else:
                self._update_single_file(path, batch_folder)
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
            self._reset_ui()

    def _update_single_file(self, file_path, batch_folder=None):
        """Update date in a single PSD file."""
        try:
            with Session() as ps:
                app = ps.app
                doc = app.open(file_path)
                today = datetime.today().strftime(DateTimeFormats.DATE_FORMAT)

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

    def _process_layers(self, doc, today):
        """Process all layers for date updates."""
        try:
            layers = list(doc.artLayers)
        except Exception as e:
            raise Exception(f"Failed to access document layers: {str(e)}")

        self.status.set(f"Processing {len(layers)} layers...")
        text_layers_updated = False
        found_text_layer = None
        existing_datetime_layer = None

        # First pass: find suitable layers
        for layer in layers:
            try:
                if hasattr(layer, "textItem") and layer.textItem:
                    text_content = layer.textItem.contents.strip()
                    if text_content:
                        # Check for datetime pattern
                        if ("/" in text_content and "." in text_content) or (
                            "-" in text_content and ":" in text_content
                        ):
                            existing_datetime_layer = layer
                        elif not found_text_layer:
                            found_text_layer = layer
            except:
                continue

        # Update appropriate layer
        if found_text_layer and not existing_datetime_layer:
            try:
                # Get current time or custom time
                time_part = self.custom_time.get().strip().replace(".", ":")
                if not time_part:
                    now = datetime.now()
                    time_part = f"{now.hour:02d}:{now.minute:02d}"

                # Update layer
                if self._update_text_layer(found_text_layer.textItem, today, time_part):
                    text_layers_updated = True
                    self.results_text.insert(
                        tk.END,
                        f"Added date/time/location to existing text layer: {found_text_layer.name}\n",
                    )
            except Exception as e:
                self.status.set(f"Error updating text layer: {str(e)}")

        # Update existing datetime layer if found
        elif existing_datetime_layer:
            try:
                text_item = existing_datetime_layer.textItem
                current_text = text_item.contents
                should_update = False
                time_part = None

                # Check format and extract time
                if "/" in current_text and "." in current_text:
                    # New format
                    first_line = current_text.split("\r")[0]
                    date_time = first_line.split()
                    if len(date_time) == 2:
                        time_part = date_time[1].replace(".", ":")
                        should_update = True
                elif "\r" in current_text or "\n" in current_text:
                    # Old format
                    normalized_text = current_text.replace("\r", "\n")
                    lines = [l.strip() for l in normalized_text.split("\n")]
                    if len(lines) >= 2 and (":" in lines[1] or "." in lines[1]):
                        time_part = lines[1].replace(".", ":")
                        should_update = True

                if should_update and time_part:
                    if self._update_text_layer(text_item, today, time_part):
                        text_layers_updated = True

            except Exception as e:
                self.status.set(f"Error updating layer: {str(e)}")

        return text_layers_updated

    def _update_text_layer(self, text_item, today, time_part):
        """Update text layer with new date while preserving time and location."""
        try:
            custom_date = self.custom_date.get().strip()
            custom_time = self.custom_time.get().strip()

            # Get location information
            location_text = self.location_text.get("1.0", tk.END).strip()
            location_info = LocationInfo.from_text(location_text)

            # Update time
            time_info = None
            if custom_time and "." in custom_time:
                # Use batch time processing
                if self.current_batch_time is None:
                    time_info = TimeInfo.from_string(custom_time)
                    self.current_batch_time = time_info
                else:
                    time_info = self.current_batch_time.increment()
                    self.current_batch_time = time_info
                final_time = time_info.formatted
            else:
                final_time = time_part.replace(":", ".")
                self.current_batch_time = None

            # Use custom date if provided and valid
            final_date = (
                custom_date
                if custom_date and len(custom_date.split("/")) == 3
                else today.replace("-", "/")
            )

            # Update the text layer using the processor
            result = TextLayerProcessor.update_text_layer(
                text_item,
                final_date,
                final_time,
                location_info.as_list if location_info else None,
            )

            return result

        except Exception as e:
            self.status.set(f"Error updating text: {str(e)}")
            return False

    def _has_type17_near_datetime(self, doc, datetime_layer):
        """Check if there's a Type 17 layer above the datetime layer."""
        try:
            layers = list(doc.artLayers)
            for layer in reversed(layers):
                if layer == datetime_layer:
                    break
                elif layer.kind == LayerKind.TYPE_17.value:
                    return True, layer, "above"
            return False, None, None
        except Exception as e:
            self.status.set(f"Error checking Type 17 layers: {str(e)}")
            return False, None, None

    def _save_document(self, doc, batch_folder=None):
        """Save the document as both PSD and JPG with date prefix."""
        try:
            # Get original file path
            original_path = doc.fullName
            file_name = os.path.basename(original_path)
            name, ext = os.path.splitext(file_name)

            # Use provided batch folder or source location
            output_folder = batch_folder or os.path.dirname(original_path)
            if batch_folder is None:
                self.status.set("No output folder selected, saving in source location")

            # Create date prefix (YYMMDD)
            date_str = datetime.now().strftime(DateTimeFormats.SHORT_DATE_FORMAT)

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
                                # Create version with Type 17 layer hidden
                                original_visibility = found_layer.visible
                                found_layer.visible = False
                                doc.saveAs(ver2_jpg_path, jpg_options, True)
                                found_layer.visible = original_visibility

                                output_dir = os.path.basename(output_folder)
                                self.status.set(
                                    f"Saved in folder {output_dir}: "
                                    f"{os.path.basename(new_psd_path)}, "
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

        except Exception as e:
            raise Exception(f"Failed to save document: {str(e)}")


__all__ = [
    "PSDDateUpdater",
    "PSDUpdaterWindow",
    "TimeInfo",
    "LocationInfo",
    "TextLayerProcessor",
    "DocumentProcessor",
]
