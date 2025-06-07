"""Image search functionality."""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import imagehash
from PIL import Image


class ImageSearchApp:
    def __init__(self, parent):
        self.parent = parent
        self.root = self.parent.winfo_toplevel()

        # Variables
        self.reference_image_path = tk.StringVar()
        self.search_directory = tk.StringVar()
        self.threshold = tk.DoubleVar(value=90)  # Default threshold 90% similarity
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
        hash_types.grid(row=2, column=1, sticky="w", padx=5)  # Threshold slider
        threshold_frame = ttk.LabelFrame(self.parent, text="Similarity Threshold")
        threshold_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Value display frame
        value_frame = ttk.Frame(threshold_frame)
        value_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Create StringVar to format the threshold value
        self.threshold_display = tk.StringVar()
        self.threshold.trace_add(
            "write",
            lambda *args: self.threshold_display.set(f"{self.threshold.get():.1f}%"),
        )
        tk.Label(value_frame, textvariable=self.threshold_display).pack()

        # Slider
        threshold_slider = ttk.Scale(
            threshold_frame,
            from_=1,
            to=100,
            variable=self.threshold,
            orient="horizontal",
        )
        threshold_slider.pack(fill="x", padx=5, pady=(0, 5))

        # Progress and Status section
        progress_frame = ttk.LabelFrame(self.parent, text="Progress")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Progress bar in its own row
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 0))

        # Status text below progress bar
        tk.Label(
            progress_frame,
            textvariable=self.status,
            wraplength=500,  # Allow status text to wrap
            justify="center",
        ).pack(pady=5)

        # Results area with quick jump button frame
        results_frame = ttk.Frame(self.parent)
        results_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # Results text
        self.results_text = tk.Text(results_frame, height=15, width=70)
        self.results_text.pack(side="left", fill="both", expand=True)

        # Scrollbar for results
        scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.results_text.configure(yscrollcommand=scrollbar.set)

        # Make results text clickable
        self.results_text.tag_configure("path_link", foreground="blue", underline=1)
        self.results_text.tag_bind(
            "path_link",
            "<Button-1>",
            lambda e: self.open_file_location(
                self.results_text.tag_names(tk.CURRENT)[1]
            ),
        )

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
        """Open file dialog to select a reference image."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.reference_image_path.set(file_path)
            self.status.set(f"Selected reference image: {os.path.basename(file_path)}")

    def select_directory(self):
        """Open directory dialog to select search directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.search_directory.set(directory)
            self.status.set(f"Selected directory: {directory}")

    def calculate_image_hash(self, image_path, hash_type="phash"):
        """Calculate the perceptual hash of an image."""
        try:
            img = Image.open(image_path)
            if hash_type == "phash":
                return imagehash.phash(img)
            else:  # ahash
                return imagehash.average_hash(img)
        except Exception as e:
            self.result_queue.put(("error", f"Error processing {image_path}: {e}"))
            return None

    def calculate_similarity_score(self, hash1, hash2):
        """Calculate a similarity score between two image hashes (0-100%, higher is more similar)."""
        if hash1 is None or hash2 is None:
            return 0.0

        try:
            hash_size = len(hash1.hash) * len(hash1.hash[0])  # Total bits in hash
            hamming_distance = hash1 - hash2  # Number of different bits
            similarity = 100.0 * (
                1 - (hamming_distance / hash_size)
            )  # Convert to similarity percentage
            return max(0.0, min(100.0, similarity))  # Ensure result is between 0-100
        except Exception:
            return 0.0

    def start_search(self):
        """Start the image search process."""
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
        """Cancel the ongoing search process."""
        if self.is_searching:
            self.is_searching = False
            self.status.set("Search cancelled")
            self.progress_bar.stop()
            self.search_button.config(state="normal")
            self.cancel_button.config(state="disabled")

    def check_queue(self):
        """Check for messages from the search thread."""
        while True:
            try:
                msg_type, message = self.result_queue.get_nowait()

                if msg_type == "status":
                    self.status.set(message)
                elif msg_type == "result":
                    self.results_text.insert(tk.END, message)
                elif msg_type == "path_link":
                    # Insert clickable path
                    start = self.results_text.index("end-1c")
                    self.results_text.insert(tk.END, message)
                    end = self.results_text.index("end-1c")
                    self.results_text.tag_add("path_link", start, end)
                    self.results_text.tag_add(
                        message, start, end
                    )  # Store path in tag for click handler
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
        """Search for similar images in the specified directory."""
        try:
            reference_path = self.reference_image_path.get()
            search_dir = self.search_directory.get()
            threshold = float(
                self.threshold.get()
            )  # Now represents similarity threshold directly
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
                (
                    "result",
                    f"Using {hash_type}, minimum similarity threshold: {threshold}%\n\n",
                )
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

                        # Skip reference image itself
                        if img_path == reference_path:
                            continue

                        img_hash = self.calculate_image_hash(img_path, hash_type)
                        if img_hash:
                            similarity = self.calculate_similarity_score(
                                ref_hash, img_hash
                            )
                            if similarity >= threshold:
                                similar_images.append((img_path, similarity))

            # Sort and display results
            if self.is_searching:  # Only show results if not cancelled
                similar_images.sort(
                    key=lambda x: x[1], reverse=True
                )  # Sort by similarity (highest first)
                if similar_images:
                    self.result_queue.put(
                        ("result", f"Found {len(similar_images)} similar images:\n\n")
                    )
                    for path, similarity in similar_images:
                        result_text = f"Similarity: {similarity:.1f}%\nPath: "
                        self.result_queue.put(("result", result_text))
                        # Add clickable path with tag
                        self.result_queue.put(("path_link", path))
                        self.result_queue.put(("result", "\n\n"))
                else:
                    self.result_queue.put(
                        (
                            "result",
                            f"No images found with similarity >= {threshold}%.\n",
                        )
                    )

                self.result_queue.put(
                    (
                        "status",
                        f"Search complete. Found {len(similar_images)} similar images out of {total_processed} processed.",
                    )
                )

        except Exception as e:
            self.result_queue.put(("error", str(e)))
        finally:
            self.result_queue.put(("done", None))

    def open_file_location(self, file_path):
        """Open the file explorer at the location of the file."""
        import subprocess

        subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])
