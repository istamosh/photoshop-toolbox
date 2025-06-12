"""Main UI window for PSD updater."""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from photoshop import Session
from .models import TimeInfo, LocationInfo
from .processor import TextLayerProcessor, DocumentProcessor
from .constants import DateTimeFormats
from .tooltip import ToolTip
from .location_storage import LocationStorage


class PSDUpdaterWindow:
    """Main window for the PSD file date updater."""

    def __init__(self, parent):
        self.parent = parent
        self._init_variables()
        self.location_storage = LocationStorage()  # Initialize location storage
        self._create_widgets()

    def _init_variables(self):
        """Initialize instance variables."""
        self.status = tk.StringVar(value="Ready")
        self.psd_file_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.custom_date = tk.StringVar()
        self.custom_time = tk.StringVar()
        self.progress = tk.DoubleVar(value=0.0)
        self.is_processing = False
        self.current_batch_time = None

    def _create_widgets(self):
        """Create and arrange UI widgets."""
        # Create main sections
        self._create_file_section()

        # Create a container frame for datetime and location sections
        container_frame = ttk.Frame(self.parent)
        container_frame.pack(fill="x", padx=5, pady=5)

        # Create datetime section in left half
        datetime_frame = ttk.LabelFrame(
            container_frame, text="Custom Date/Time (Optional)", padding=10
        )
        datetime_frame.pack(side="left", fill="both", expand=True, padx=(0, 2.5))
        self._create_datetime_content(datetime_frame)

        # Create location section in right half
        location_frame = ttk.LabelFrame(
            container_frame, text="Location Information", padding=10
        )
        location_frame.pack(side="left", fill="both", expand=True, padx=(2.5, 0))
        self._create_location_content(location_frame)

        self._create_progress_section()
        self._create_action_buttons()
        self._create_results_area()

    def _create_datetime_content(self, parent):
        """Create date/time input content."""
        # Date field
        date_frame = ttk.Frame(parent)
        date_frame.pack(fill="x", pady=2)
        ttk.Label(date_frame, text="Date (DD/MM/YYYY):").pack(side="left", padx=5)
        date_entry = ttk.Entry(date_frame, textvariable=self.custom_date, width=15)
        date_entry.pack(side="left", padx=5)
        ToolTip(date_entry, "Leave empty to use current date")

        # Time field
        time_frame = ttk.Frame(parent)
        time_frame.pack(fill="x", pady=(10, 2))
        ttk.Label(time_frame, text="Time (HH.MM):").pack(side="left", padx=5)
        time_entry = ttk.Entry(time_frame, textvariable=self.custom_time, width=10)
        time_entry.pack(side="left", padx=5)
        ToolTip(time_entry, "Leave empty to keep existing time")

    def _create_location_content(self, parent):
        """Create location information content."""
        # Location dropdown section
        dropdown_frame = ttk.Frame(parent)
        dropdown_frame.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Label(dropdown_frame, text="Select Location:").pack(side="left", padx=(0, 5))

        # Create and configure the combobox
        self.location_combobox = ttk.Combobox(dropdown_frame, width=40, state='readonly')
        self.location_combobox.pack(side="left", fill="x", expand=True)
        self._update_location_dropdown()

        # Bind selection event
        self.location_combobox.bind('<<ComboboxSelected>>', self._on_location_selected)

        # Help text for manual entry
        help_text = (
            "Enter location details (one per line):\n"
            "Street Name\nWard\nSubdistrict\nDistrict\n"
            "Province\nCompany Name"
        )
        ttk.Label(parent, text=help_text).pack(anchor="w", padx=5, pady=(0, 5))

        # Text area with scrollbar
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.location_text = tk.Text(text_frame, height=6, width=30)
        self.location_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.location_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.location_text.configure(yscrollcommand=scrollbar.set)

        # Button frame for save and delete
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=(5, 0))
        
        # Save button
        save_button = ttk.Button(
            button_frame, text="Save Location", command=self._save_location
        )
        save_button.pack(side="left", padx=5)
        
        # Delete button
        delete_button = ttk.Button(
            button_frame, text="Delete Location", command=self._delete_location
        )
        delete_button.pack(side="left", padx=5)

    def _update_location_dropdown(self):
        """Update the location dropdown with stored locations."""
        locations = self.location_storage.load_locations()
        # Create display strings for each location
        display_texts = []
        self._location_map = {}  # Store mapping of display text to location dict

        for location in locations:
            # Create a display text that shows street and company
            display_text = f"{location['street']} - {location['company']}"
            display_texts.append(display_text)
            self._location_map[display_text] = location

        self.location_combobox["values"] = display_texts
        if display_texts:
            self.location_combobox.set("Select a location...")

    def _on_location_selected(self, event):
        """Handle location selection from dropdown."""
        selected = self.location_combobox.get()
        if selected and selected != "Select a location...":
            location = self._location_map.get(selected)
            if location:
                # Clear existing text and insert new location details
                self.location_text.delete("1.0", tk.END)
                location_text = "\n".join(
                    location[field]
                    for field in [
                        "street",
                        "ward",
                        "subdistrict",
                        "district",
                        "province",
                        "company",
                    ]
                    if location[field]
                )
                self.location_text.insert("1.0", location_text)

    def _save_location(self):
        """Save the current location to storage."""
        location_text = self.location_text.get("1.0", "end-1c").strip()
        if location_text:
            if self.location_storage.add_location(location_text):
                self.status.set("Location saved successfully")
                self._update_location_dropdown()
            else:
                self.status.set("Location already exists")

    def _delete_location(self):
        """Delete the current location from storage."""
        location_text = self.location_text.get('1.0', 'end-1c').strip()
        if location_text:
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this location?"):
                if self.location_storage.delete_location(location_text):
                    self.status.set("Location deleted successfully")
                    self.location_text.delete('1.0', tk.END)
                    self._update_location_dropdown()
                    self.location_combobox.set("Select a location...")
                else:
                    self.status.set("Location not found")

    def _create_file_section(self):
        """Create file selection section."""
        file_frame = ttk.Frame(self.parent)
        file_frame.pack(fill="x", pady=5)

        # File selection
        ttk.Label(file_frame, text="PSD File/Folder:").pack(side="left", padx=5)
        ttk.Entry(file_frame, textvariable=self.psd_file_path, width=50).pack(
            side="left", padx=5
        )

        # Browse buttons
        browse_frame = ttk.Frame(file_frame)
        browse_frame.pack(side="left")
        ttk.Button(
            browse_frame, text="Browse File", command=self._browse_psd_file
        ).pack(side="left", padx=5)
        ttk.Button(
            browse_frame, text="Browse Folder", command=self._browse_psd_folder
        ).pack(side="left", padx=5)

        # Output directory
        output_frame = ttk.Frame(self.parent)
        output_frame.pack(fill="x", pady=5)
        ttk.Label(output_frame, text="Working Folder:").pack(side="left", padx=5)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(
            side="left", padx=5
        )
        ttk.Button(output_frame, text="Browse", command=self._browse_output_dir).pack(
            side="left", padx=5
        )

    def _create_progress_section(self):
        """Create progress bar and status section."""
        progress_frame = ttk.Frame(self.parent)
        progress_frame.pack(fill="x", pady=5, padx=10)
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", variable=self.progress, length=300
        )
        self.progress_bar.pack(fill="x", expand=True)
        ttk.Label(self.parent, textvariable=self.status).pack(pady=10)

    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.parent)
        button_frame.pack(pady=10)
        self.analyze_button = ttk.Button(
            button_frame, text="Analyze", command=self.analyze_files
        )
        self.analyze_button.pack(side="left", padx=5)
        self.update_button = ttk.Button(
            button_frame, text="Update Date", command=self.update_date, state="disabled"
        )
        self.update_button.pack(side="left", padx=5)
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_processing,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=5)

    def _create_results_area(self):
        """Create results text area."""
        self.results_text = tk.Text(self.parent, height=15, width=70)
        self.results_text.pack(pady=10, padx=5)

    def _browse_psd_file(self):
        """Open file dialog for selecting PSD file."""
        filename = filedialog.askopenfilename(
            title="Select PSD File", filetypes=[("Photoshop Files", "*.psd")]
        )
        if filename:
            self.psd_file_path.set(filename)
            self.status.set(f"Selected file: {os.path.basename(filename)}")
            self.update_button.configure(state="disabled")
            self.results_text.delete(1.0, tk.END)

    def _browse_psd_folder(self):
        """Open folder dialog for selecting directory with PSD files."""
        folder = filedialog.askdirectory(title="Select Folder with PSD Files")
        if folder:
            self.psd_file_path.set(folder)
            self.status.set(f"Selected folder: {os.path.basename(folder)}")
            self.update_button.configure(state="disabled")
            self.results_text.delete(1.0, tk.END)

    def _browse_output_dir(self):
        """Open folder dialog for selecting output directory."""
        directory = filedialog.askdirectory(title="Select Working Folder for Output")
        if directory:
            self.output_dir.set(directory)
            self.status.set(f"Selected working folder: {os.path.basename(directory)}")

    def _get_next_output_folder(self):
        """Get next available numbered folder in output directory."""
        base_dir = self.output_dir.get()
        if not base_dir:
            return None

        counter = 1
        while True:
            folder_name = str(counter)
            folder_path = os.path.join(base_dir, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                return folder_path
            counter += 1

    def analyze_files(self):
        """Handle analyze files button click."""
        raise NotImplementedError("Subclass must implement analyze_files")

    def update_date(self):
        """Handle update date button click."""
        raise NotImplementedError("Subclass must implement update_date")

    def cancel_processing(self):
        """Handle cancel button click."""
        if self.is_processing:
            self.is_processing = False
            self.status.set("Processing cancelled")
            self.progress.set(0)
            self.analyze_button.configure(state="normal")
            self.update_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
