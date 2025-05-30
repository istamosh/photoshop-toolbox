import tkinter as tk
from tkinter import filedialog, ttk
import imagehash
from PIL import Image
import os
from pathlib import Path
import threading
import queue


class ImageSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Similarity Search")

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
        self.root.after(100, self.check_queue)

    def create_widgets(self):
        # Reference image selection
        tk.Label(self.root, text="Reference Image:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(self.root, textvariable=self.reference_image_path, width=50).grid(
            row=0, column=1, padx=5
        )
        tk.Button(self.root, text="Browse", command=self.select_reference_image).grid(
            row=0, column=2, padx=5
        )

        # Search directory selection
        tk.Label(self.root, text="Search Directory:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(self.root, textvariable=self.search_directory, width=50).grid(
            row=1, column=1, padx=5
        )
        tk.Button(self.root, text="Browse", command=self.select_directory).grid(
            row=1, column=2, padx=5
        )

        # Hash type selection
        tk.Label(self.root, text="Hash Type:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        hash_types = ttk.Combobox(
            self.root, textvariable=self.hash_type, values=["phash", "ahash"]
        )
        hash_types.grid(row=2, column=1, sticky="w", padx=5)

        # Threshold slider
        tk.Label(self.root, text="Threshold:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        threshold_slider = ttk.Scale(
            self.root, from_=0, to=30, variable=self.threshold, orient="horizontal"
        )
        threshold_slider.grid(row=3, column=1, sticky="ew", padx=5)

        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)

        self.progress_bar = ttk.Progressbar(status_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", side="left", expand=True)

        tk.Label(status_frame, textvariable=self.status).pack(side="left", padx=5)

        # Results area
        self.results_text = tk.Text(self.root, height=15, width=70)
        self.results_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        # Buttons frame
        button_frame = ttk.Frame(self.root)
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
    app = ImageSearchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
