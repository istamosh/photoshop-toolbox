import tkinter as tk
from tkinter import filedialog, ttk
import imagehash
from PIL import Image
import os
from pathlib import Path
import threading
import queue
import time
from datetime import datetime
from photoshop import Session
from photoshop.api._core import Photoshop


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Tools")

        # Create menu
        self.create_menu()

        # Create main container
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Welcome message
        self.welcome_label = ttk.Label(
            self.main_frame,
            text="Welcome! Please select a tool from the Tools menu.",
            font=("Arial", 12),
        )
        self.welcome_label.pack(pady=20)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Image Finder", command=self.show_image_finder)
        tools_menu.add_command(label="PSD Date Updater", command=self.show_psd_updater)
        tools_menu.add_separator()
        tools_menu.add_command(label="Exit", command=self.root.quit)

    def show_image_finder(self):
        self.clear_main_frame()
        ImageSearchApp(self.main_frame)

    def show_psd_updater(self):
        self.clear_main_frame()
        PSDDateUpdater(self.main_frame)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()


class PSDDateUpdater:
    def __init__(self, parent):
        self.parent = parent
        self.status = tk.StringVar(value="Ready")
        self.psd_file_path = tk.StringVar()

        # Create widgets
        self.create_widgets()

        # Create results text widget
        self.results_text = tk.Text(self.parent, height=15, width=70)
        self.results_text.pack(pady=10, padx=5)

    def create_widgets(self):
        # File selection
        file_frame = ttk.Frame(self.parent)
        file_frame.pack(fill="x", pady=5)

        ttk.Label(file_frame, text="PSD File:").pack(side="left", padx=5)
        ttk.Entry(file_frame, textvariable=self.psd_file_path, width=50).pack(
            side="left", padx=5
        )
        ttk.Button(file_frame, text="Browse", command=self.select_psd_file).pack(
            side="left", padx=5
        )

        # Status
        ttk.Label(self.parent, textvariable=self.status).pack(pady=10)

        # Analyze and Update buttons
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="Analyze Layers", command=self.analyze_layers
        ).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Update Date", command=self.update_date).pack(
            side="left", padx=5
        )

    def select_psd_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Photoshop Files", "*.psd")])
        if file_path:
            self.psd_file_path.set(file_path)
            self.status.set(f"Selected file: {os.path.basename(file_path)}")
            self.results_text.delete(1.0, tk.END)

    def analyze_layers(self):
        psd_path = self.psd_file_path.get()
        if not psd_path:
            self.status.set("Please select a PSD file first")
            return

        if not os.path.exists(psd_path):
            self.status.set("Selected PSD file does not exist")
            return

        ps = None
        doc = None

        try:
            self.status.set("Starting Photoshop...")
            ps = Photoshop()

            try:
                self.status.set("Opening PSD file...")
                ps.open(psd_path)
            except Exception as open_error:
                raise Exception(f"Failed to open PSD file: {str(open_error)}")

            # Wait for document to be opened and get active document
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

            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "=== Document Information ===\n")

            # Get document info
            try:
                doc_name = doc.name
                doc_path = doc.fullName
                doc_width = doc.width
                doc_height = doc.height
                self.results_text.insert(tk.END, f"Name: {doc_name}\n")
                self.results_text.insert(tk.END, f"Path: {doc_path}\n")
                self.results_text.insert(
                    tk.END, f"Size: {doc_width} x {doc_height}\n\n"
                )
            except Exception as info_error:
                self.results_text.insert(
                    tk.END, f"Error getting document info: {str(info_error)}\n\n"
                )

            # Get layer information
            try:
                layers = list(doc.artLayers)
                self.results_text.insert(
                    tk.END, f"=== Layer Analysis ({len(layers)} layers) ===\n\n"
                )

                for layer in layers:
                    try:
                        # Basic layer info
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

                        # Try to detect if this is a text layer by presence of textItem
                        try:
                            text_item = layer.textItem
                            text_content = text_item.contents
                            self.results_text.insert(tk.END, "Text Properties:\n")
                            self.results_text.insert(
                                tk.END, f"  Content: {text_content}\n"
                            )

                            # Try to get additional text properties
                            try:
                                font = text_item.font
                                self.results_text.insert(tk.END, f"  Font: {font}\n")
                            except:
                                pass

                            try:
                                size = text_item.size
                                self.results_text.insert(tk.END, f"  Size: {size}\n")
                            except:
                                pass

                            try:
                                just = text_item.justification
                                self.results_text.insert(
                                    tk.END, f"  Justification: {just}\n"
                                )
                            except:
                                pass
                        except Exception as text_error:
                            pass

                        self.results_text.insert(tk.END, "-" * 50 + "\n")
                        self.results_text.see(tk.END)  # Scroll to latest
                        self.status.set(f"Analyzed layer: {layer_name}")

                    except Exception as layer_error:
                        error_info = (
                            f"Error analyzing layer: {str(layer_error)}\n"
                            + "-" * 50
                            + "\n"
                        )
                        self.results_text.insert(tk.END, error_info)
                        self.status.set(f"Error in layer analysis: {str(layer_error)}")
                        continue

                self.results_text.insert(tk.END, "\nAnalysis complete!")
                self.status.set("Layer analysis complete")

            except Exception as layer_error:
                raise Exception(f"Failed to analyze layers: {str(layer_error)}")

        except Exception as e:
            self.status.set(f"Error: {str(e)}")
            self.results_text.insert(tk.END, f"\nError: {str(e)}")

        finally:
            # Don't close Photoshop after analysis
            self.status.set("Analysis complete")

    def update_date(self):
        ps = None
        doc = None

        try:
            doc = None
            try:
                doc = Photoshop().app.activeDocument
            except:
                self.status.set("No document is open in Photoshop")
                return

            today = datetime.today().strftime("%d-%m-%Y")
            text_layers_updated = False

            # Get all layers
            try:
                layers = list(doc.artLayers)
            except Exception as layer_error:
                raise Exception(f"Failed to access document layers: {str(layer_error)}")

            self.status.set(f"Processing {len(layers)} layers...")

            for layer in layers:
                try:
                    # Try to detect if this is a text layer by presence of textItem
                    text_item = layer.textItem
                    if text_item:
                        layer_name = layer.name
                        current_text = text_item.contents

                        # Try to split the text into date and time parts
                        try:
                            parts = current_text.split()
                            if (
                                len(parts) == 2 and ":" in parts[1]
                            ):  # Check if it has a time component
                                time_part = parts[1]
                                new_text = f"{today} {time_part}"

                                self.status.set(
                                    f"Updating layer {layer_name} from '{current_text}' to '{new_text}'"
                                )
                                text_item.contents = new_text

                                # Verify the change
                                updated_text = text_item.contents
                                if updated_text.strip() == new_text.strip():
                                    text_layers_updated = True
                                    self.status.set(
                                        f"Successfully updated layer: {layer_name}"
                                    )
                                else:
                                    self.status.set(
                                        f"Failed to update layer {layer_name} - text verification failed"
                                    )

                        except Exception as update_error:
                            self.status.set(
                                f"Error updating layer {layer_name}: {str(update_error)}"
                            )
                            continue

                except Exception:
                    # Not a text layer or other error, skip it
                    continue

            if text_layers_updated:
                # Get file path from original document
                file_path = doc.fullName
                file_name, ext = os.path.splitext(file_path)
                new_path = f"{file_name}_updated{ext}"

                try:
                    # Try to save the document
                    doc.saveAs(new_path)
                    self.status.set(
                        f"Successfully saved to: {os.path.basename(new_path)}"
                    )
                except Exception as save_error:
                    raise Exception(f"Failed to save document: {str(save_error)}")
            else:
                self.status.set("No text layers were updated")

        except Exception as e:
            self.status.set(f"Error: {str(e)}")

        finally:
            # Don't close Photoshop after update
            pass


class ImageSearchApp:
    def __init__(self, parent):
        self.parent = parent

        # Variables
        self.reference_image_path = tk.StringVar()
        self.search_directory = tk.StringVar()
        self.threshold = tk.DoubleVar(value=10)  # Default threshold
        self.hash_type = tk.StringVar(value="phash")  # Default hash type
        self.status = tk.StringVar(value="Ready")
        self.is_searching = False
        self.search_thread = None
        self.result_queue = queue.Queue()

        # Create UI
        self.create_widgets()

        # Setup periodic UI update
        self.parent.after(100, self.check_queue)

    def create_widgets(self):
        # Reference image selection
        tk.Label(self.parent, text="Reference Image:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(self.parent, textvariable=self.reference_image_path, width=50).grid(
            row=0, column=1, padx=5
        )
        tk.Button(self.parent, text="Browse", command=self.select_reference_image).grid(
            row=0, column=2, padx=5
        )

        # Search directory selection
        tk.Label(self.parent, text="Search Directory:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(self.parent, textvariable=self.search_directory, width=50).grid(
            row=1, column=1, padx=5
        )
        tk.Button(self.parent, text="Browse", command=self.select_directory).grid(
            row=1, column=2, padx=5
        )

        # Hash type selection
        tk.Label(self.parent, text="Hash Type:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        hash_types = ttk.Combobox(
            self.parent, textvariable=self.hash_type, values=["phash", "ahash"]
        )
        hash_types.grid(row=2, column=1, sticky="w", padx=5)

        # Threshold slider
        tk.Label(self.parent, text="Threshold:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        threshold_slider = ttk.Scale(
            self.parent, from_=0, to=30, variable=self.threshold, orient="horizontal"
        )
        threshold_slider.grid(row=3, column=1, sticky="ew", padx=5)

        # Status bar
        status_frame = ttk.Frame(self.parent)
        status_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)

        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", side="left", expand=True)

        tk.Label(status_frame, textvariable=self.status).pack(side="left", padx=5)

        # Results area
        self.results_text = tk.Text(self.parent, height=15, width=70)
        self.results_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        # Buttons frame
        button_frame = ttk.Frame(self.parent)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.search_button = tk.Button(
            button_frame, text="Search", command=self.start_search
        )
        self.search_button.pack(side="left", padx=5)

        self.cancel_button = tk.Button(
            button_frame, text="Cancel", command=self.cancel_search, state="disabled"
        )
        self.cancel_button.pack(side="left", padx=5)

    def select_reference_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.reference_image_path.set(file_path)
            self.status.set(f"Selected reference image: {os.path.basename(file_path)}")

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.search_directory.set(directory)
            self.status.set(f"Selected directory: {directory}")

    def calculate_image_hash(self, image_path, hash_type="phash"):
        try:
            img = Image.open(image_path)
            if hash_type == "phash":
                return imagehash.phash(img)
            else:  # ahash
                return imagehash.average_hash(img)
        except Exception as e:
            self.result_queue.put(("error", f"Error processing {image_path}: {e}"))
            return None

    def start_search(self):
        if not self.reference_image_path.get() or not self.search_directory.get():
            self.status.set("Please select both reference image and search directory")
            return

        self.search_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.is_searching = True
        self.progress_bar.start(10)

        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.status.set("Searching...")

        # Start search in a separate thread
        self.search_thread = threading.Thread(target=self.search_similar_images)
        self.search_thread.daemon = True
        self.search_thread.start()

    def cancel_search(self):
        if self.is_searching:
            self.is_searching = False
            self.status.set("Search cancelled")
            self.progress_bar.stop()
            self.search_button.config(state="normal")
            self.cancel_button.config(state="disabled")

    def check_queue(self):
        while True:
            try:
                msg_type, message = self.result_queue.get_nowait()

                if msg_type == "status":
                    self.status.set(message)
                elif msg_type == "result":
                    self.results_text.insert(tk.END, message)
                elif msg_type == "error":
                    self.results_text.insert(tk.END, f"Error: {message}\n")
                elif msg_type == "done":
                    self.progress_bar.stop()
                    self.search_button.config(state="normal")
                    self.cancel_button.config(state="disabled")
                    self.is_searching = False
                    break

            except queue.Empty:
                break

        self.root.after(100, self.check_queue)

    def search_similar_images(self):
        try:
            reference_path = self.reference_image_path.get()
            search_dir = self.search_directory.get()
            threshold = self.threshold.get()
            hash_type = self.hash_type.get()

            # Calculate reference image hash
            self.result_queue.put(("status", "Processing reference image..."))
            ref_hash = self.calculate_image_hash(reference_path, hash_type)
            if not ref_hash:
                self.result_queue.put(("error", "Failed to process reference image"))
                self.result_queue.put(("done", None))
                return

            self.result_queue.put(("status", "Searching for similar images..."))
            self.result_queue.put(
                ("result", f"Using {hash_type}, threshold: {threshold}\n\n")
            )

            # Search for similar images
            similar_images = []
            total_processed = 0

            for root_dir, _, files in os.walk(search_dir):
                if not self.is_searching:  # Check if search was cancelled
                    self.result_queue.put(("result", "\nSearch cancelled by user.\n"))
                    break

                for file in files:
                    if not self.is_searching:  # Check if search was cancelled
                        break

                    if file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
                        total_processed += 1
                        img_path = os.path.join(root_dir, file)
                        self.result_queue.put(("status", f"Processing: {file}"))

                        img_hash = self.calculate_image_hash(img_path, hash_type)
                        if img_hash:
                            hash_diff = ref_hash - img_hash
                            if hash_diff < threshold:
                                similar_images.append((img_path, hash_diff))

            # Sort and display results
            if self.is_searching:  # Only show results if not cancelled
                similar_images.sort(key=lambda x: x[1])
                if similar_images:
                    for path, diff in similar_images:
                        self.result_queue.put(
                            ("result", f"Similarity score: {diff}\nPath: {path}\n\n")
                        )
                else:
                    self.result_queue.put(("result", "No similar images found.\n"))

                self.result_queue.put(
                    ("status", f"Search complete. Processed {total_processed} images.")
                )

        except Exception as e:
            self.result_queue.put(("error", str(e)))
        finally:
            self.result_queue.put(("done", None))


def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
