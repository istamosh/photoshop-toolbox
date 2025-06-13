"""Main image search application."""

import os
import queue
import threading
import subprocess
from tkinter import filedialog
from .ui_components import SearchControls, ProgressSection, ResultsArea, ControlButtons
from .search_engine import SearchEngine


class ImageSearchApp:
    """Main image search application."""

    def __init__(self, parent):
        self.parent = parent
        self.root = self.parent.winfo_toplevel()
        self.is_searching = False
        self.search_thread = None
        self.result_queue = queue.Queue()

        # Create UI Components
        self.search_controls = SearchControls(
            parent,
            {
                "select_reference": self.select_reference_image,
                "select_directory": self.select_directory,
            },
        )

        self.progress_section = ProgressSection(parent)
        self.results_area = ResultsArea(parent, self.open_file_location)
        self.control_buttons = ControlButtons(
            parent,
            {"start_search": self.start_search, "cancel_search": self.cancel_search},
        )

        # Setup periodic UI update
        self.parent.after(100, self.check_queue)

    def select_reference_image(self):
        """Open file dialog to select a reference image."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.search_controls.reference_image_path.set(file_path)
            self.progress_section.status.set(
                f"Selected reference image: {os.path.basename(file_path)}"
            )

    def select_directory(self):
        """Open directory dialog to select search directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.search_controls.search_directory.set(directory)
            self.progress_section.status.set(f"Selected directory: {directory}")

    def start_search(self):
        """Start the image search process."""
        if not self._validate_inputs():
            return

        self._prepare_for_search()
        self.search_thread = threading.Thread(target=self._execute_search)
        self.search_thread.daemon = True
        self.search_thread.start()

    def cancel_search(self):
        """Cancel the ongoing search process."""
        if self.is_searching:
            self.is_searching = False
            self.progress_section.status.set("Search cancelled")
            self.progress_section.progress_bar.stop()
            self.control_buttons.search_button.config(state="normal")
            self.control_buttons.cancel_button.config(state="disabled")

    def check_queue(self):
        """Check for messages from the search thread."""
        while True:
            try:
                msg_type, message = self.result_queue.get_nowait()
                self._handle_queue_message(msg_type, message)
            except queue.Empty:
                break

        self.root.after(100, self.check_queue)

    def open_file_location(self, file_path):
        """Open the file explorer at the location of the file."""
        subprocess.run(["explorer", "/select,", os.path.normpath(file_path)])

    def _validate_inputs(self):
        """Validate required inputs before starting search."""
        if (
            not self.search_controls.reference_image_path.get()
            or not self.search_controls.search_directory.get()
        ):
            self.progress_section.status.set(
                "Please select both reference image and search directory"
            )
            return False
        return True

    def _prepare_for_search(self):
        """Prepare UI for search operation."""
        self.control_buttons.search_button.config(state="disabled")
        self.control_buttons.cancel_button.config(state="normal")
        self.is_searching = True
        self.progress_section.progress_bar.start(10)
        self.results_area.results_text.delete(1.0, "end")
        self.progress_section.status.set("Searching...")

    def _execute_search(self):
        """Execute the search operation."""
        search_engine = SearchEngine(
            reference_path=self.search_controls.reference_image_path.get(),
            search_dir=self.search_controls.search_directory.get(),
            threshold=float(self.search_controls.threshold.get()),
            hash_type=self.search_controls.hash_type.get(),
            stop_on_first=self.search_controls.stop_on_first_match.get(),
            result_queue=self.result_queue,
        )

        search_engine.search()
        self.result_queue.put(("done", None))

    def _handle_queue_message(self, msg_type, message):
        """Handle messages from the result queue."""
        if msg_type == "status":
            self.progress_section.status.set(message)
        elif msg_type == "result":
            self.results_area.results_text.insert("end", message)
        elif msg_type == "path_link":
            start = self.results_area.results_text.index("end-1c")
            self.results_area.results_text.insert("end", message)
            end = self.results_area.results_text.index("end-1c")
            self.results_area.results_text.tag_add("path_link", start, end)
            self.results_area.results_text.tag_add(message, start, end)
        elif msg_type == "error":
            self.results_area.results_text.insert("end", f"Error: {message}\n")
        elif msg_type == "done":
            self.progress_section.progress_bar.stop()
            self.control_buttons.search_button.config(state="normal")
            self.control_buttons.cancel_button.config(state="disabled")
            self.is_searching = False
