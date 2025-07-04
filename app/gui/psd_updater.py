"""Photoshop file date updater tool."""

__all__ = ["PSDDateUpdater"]

import os
import time
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from photoshop import Session, Photoshop

from .psd_updater.window import PSDUpdaterWindow
from .psd_updater.models import TimeInfo, LocationInfo
from .psd_updater.processor import TextLayerProcessor, DocumentProcessor
from .psd_updater.constants import LayerKind, DateTimeFormats, TextSizing, Justification, Secondhand


class PSDDateUpdater(PSDUpdaterWindow):
    """Main class for updating dates in PSD files."""

    def __init__(self, parent):
        super().__init__(parent)
        # Window UI is handled by parent class

    def _update_text_layer(self, text_item, today, time_part):
        """Update text layer with new date while preserving time and location."""
        try:
            # Get current settings
            custom_date = self.custom_date.get().strip()
            custom_time = self.custom_time.get().strip()

            # Get location information from text widget
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
                # Generate time with randomized seconds for non-batch processing
                now = datetime.now()
                random_seconds = random.randint(Secondhand.MIN, Secondhand.MAX)
                final_time = f"{now.hour:02d}.{now.minute:02d}.{random_seconds:02d}"
                self.current_batch_time = None

            # Use custom date if provided and valid, format with month name
            if custom_date and len(custom_date.split("/")) == 3:
                from .psd_updater.models import format_date_with_month_name
                final_date = format_date_with_month_name(custom_date)
            else:
                # Convert today's date to month name format
                today_obj = datetime.strptime(today, "%d-%m-%Y")
                from .psd_updater.constants import DateTimeFormats
                month_name = DateTimeFormats.MONTH_NAMES[today_obj.month]
                final_date = f"{today_obj.day:02d} {month_name} {today_obj.year}"

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

        # Reset batch time counter
        self.current_batch_time = None

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

    def _analyze_layers(self):
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

    def _has_type17_near_datetime(self, doc, datetime_layer):
        """Check if there's a Type 17 layer above the datetime layer."""
        try:
            layers = list(doc.artLayers)

            # Only check layers above the datetime layer
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

    def _analyze_single_layer(self, layer):
        """Analyze a single layer."""
        try:
            layer_name = layer.name
            layer_kind = layer.kind
            layer_visible = "Visible" if layer.visible else "Hidden"

            self.results_text.insert(tk.END, f"Layer: {layer_name}\n")
            self.results_text.insert(tk.END, f"Type: {layer_kind}\n")
            self.results_text.insert(tk.END, f"Status: {layer_visible}\n")

            # Analyze text properties if it's a text layer
            if hasattr(layer, "textItem") and layer.textItem:
                self._analyze_text_properties(layer)

            self.results_text.insert(tk.END, "-" * 50 + "\n")
            self.results_text.see(tk.END)
            self.status.set(f"Analyzed layer: {layer_name}")

        except Exception:
            self.results_text.insert(tk.END, f"Error analyzing layer: {layer_name}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n")

    def _extract_and_set_location_info(self, text_content):
        """Extract location information from text content and set it in the location textbox."""
        try:
            # Split the content by carriage return or newline
            lines = text_content.replace("\r", "\n").split("\n")

            # First line typically contains date and time, skip it
            if len(lines) > 1:
                # Join the remaining lines (location info) with newlines
                location_info = "\n".join(
                    line.strip() for line in lines[1:] if line.strip()
                )

                # Clear existing content and insert new content
                self.location_text.delete("1.0", tk.END)
                if location_info:
                    self.location_text.insert("1.0", location_info)

                return True
        except Exception as e:
            self.status.set(f"Error extracting location info: {str(e)}")
        return False

    def _analyze_text_properties(self, layer):
        """Analyze text properties of a layer."""
        try:
            text_item = layer.textItem
            text_content = text_item.contents
            self.results_text.insert(tk.END, "Text Properties:\n")
            self.results_text.insert(tk.END, f"  Content: {text_content}\n")

            # Normalize content
            normalized_content = text_content.replace("\r", "\n")
            lines = [
                line.strip() for line in normalized_content.split("\n") if line.strip()
            ]

            # Check if this might be a datetime layer
            if len(lines) >= 1:
                # Handle month name format (DD Month YYYY HH.MM.SS)
                first_line_parts = lines[0].split()
                if len(first_line_parts) >= 4:
                    from .psd_updater.constants import DateTimeFormats
                    month_names = list(DateTimeFormats.MONTH_NAMES.values())
                    
                    # Check if second part is a month name
                    if len(first_line_parts) >= 4 and first_line_parts[1] in month_names:
                        try:
                            # Extract date and time from "DD Month YYYY HH.MM.SS" format
                            day = first_line_parts[0]
                            month_name = first_line_parts[1]
                            year = first_line_parts[2]
                            time_part = first_line_parts[3]
                            
                            # Convert month name to number
                            month_num = next(k for k, v in DateTimeFormats.MONTH_NAMES.items() if v == month_name)
                            date_part = f"{day}/{month_num:02d}/{year}"
                            
                            self.custom_date.set(date_part)
                            self.custom_time.set(time_part)
                            
                            # Set location info if present
                            if len(lines) > 1:
                                location_info = LocationInfo.from_text("\n".join(lines[1:]))
                                self.location_text.delete("1.0", tk.END)
                                if location_info:
                                    self.location_text.insert("1.0", "\n".join(location_info.as_list))
                            else:
                                self.location_text.delete("1.0", tk.END)
                        except (ValueError, StopIteration):
                            pass
                
                # Handle old format (separate date and time lines)
                elif (
                    len(lines) == 2
                    and ("-" in lines[0] or "/" in lines[0])
                    and ":" in lines[1]
                ):
                    date_part = lines[0].replace("-", "/")
                    time_part = lines[1].replace(":", ".")
                    self.custom_date.set(date_part)
                    self.custom_time.set(time_part)
                    self.location_text.delete("1.0", tk.END)

                # Handle old new format (date time on first line, locations follow)
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

            # Display properties
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
                        # Check for datetime pattern - support multiple formats:
                        # New format: "DD Month YYYY HH.MM.SS"
                        # Old formats: "/" in text and "." in text, or "-" in text and ":" in text
                        is_datetime = False
                        
                        # Check for month name format
                        from .psd_updater.constants import DateTimeFormats
                        month_names = DateTimeFormats.MONTH_NAMES.values()
                        for month_name in month_names:
                            if month_name in text_content:
                                is_datetime = True
                                break
                        
                        # Check for old formats
                        if not is_datetime:
                            is_datetime = (
                                ("/" in text_content and "." in text_content) or 
                                ("-" in text_content and ":" in text_content)
                            )
                        
                        if is_datetime:
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
                first_line = current_text.split("\r")[0] if "\r" in current_text else current_text.split("\n")[0]
                
                # Check for month name format (DD Month YYYY HH.MM.SS)
                parts = first_line.split()
                if len(parts) >= 4:
                    from .psd_updater.constants import DateTimeFormats
                    month_names = list(DateTimeFormats.MONTH_NAMES.values())
                    if parts[1] in month_names and "." in parts[3]:
                        time_part = parts[3].replace(".", ":")
                        should_update = True
                
                # Check old formats if not month name format
                if not should_update:
                    if "/" in current_text and "." in current_text:
                        # Old new format
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
