"""UI Components for the image search application."""

import tkinter as tk
from tkinter import ttk


class SearchControls:
    """UI controls for image search."""

    def __init__(self, parent, callbacks):
        self.parent = parent
        self.callbacks = callbacks

        # Variables
        self.reference_image_path = tk.StringVar()
        self.search_directory = tk.StringVar()
        self.threshold = tk.DoubleVar(value=90)
        self.hash_type = tk.StringVar(value="phash")
        self.stop_on_first_match = tk.BooleanVar(value=False)
        self.use_crop_resistant = tk.BooleanVar(value=False)
        self.crop_method = tk.StringVar(value="combined")
        self.use_crop_resistant = tk.BooleanVar(value=False)
        self.crop_method = tk.StringVar(value="combined")
        self.show_advanced = tk.BooleanVar(value=False)

        self._create_input_controls()
        self._create_search_options()
        self._create_advanced_options()
        self._create_threshold_control()

    def _toggle_advanced_options(self):
        """Toggle visibility of advanced options."""
        show = self.show_advanced.get()
        if show:
            self.advanced_frame.grid()
            self.toggle_button.config(text="▲ Hide Advanced Options (for finding cropped images)")
        else:
            self.advanced_frame.grid_remove()
            self.toggle_button.config(text="▼ Show Advanced Options (for finding cropped images)")

    def _create_input_controls(self):
        """Create file and directory selection controls."""
        # Reference image selection
        tk.Label(self.parent, text="Reference Image:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        tk.Entry(self.parent, textvariable=self.reference_image_path, width=50).grid(
            row=0, column=1, padx=5
        )
        tk.Button(
            self.parent, text="Browse", command=self.callbacks["select_reference"]
        ).grid(row=0, column=2, padx=5)

        # Search directory selection
        tk.Label(self.parent, text="Search Directory:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        tk.Entry(self.parent, textvariable=self.search_directory, width=50).grid(
            row=1, column=1, padx=5
        )
        tk.Button(
            self.parent, text="Browse", command=self.callbacks["select_directory"]
        ).grid(row=1, column=2, padx=5)

    def _create_search_options(self):
        """Create hash type and search options."""
        # Hash type selection
        tk.Label(self.parent, text="Hash Type:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        hash_types = ttk.Combobox(
            self.parent, textvariable=self.hash_type, values=["phash", "ahash"], width=10
        )
        hash_types.grid(row=2, column=1, sticky="w", padx=5)

        # Stop on first match checkbox
        ttk.Checkbutton(
            self.parent, text="Stop on First Match", variable=self.stop_on_first_match
        ).grid(row=2, column=2, sticky="w", padx=5)

    def _create_advanced_options(self):
        """Create advanced crop-resistant matching options."""
        # Toggle button for advanced options
        toggle_frame = ttk.Frame(self.parent)
        toggle_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        
        self.toggle_button = ttk.Checkbutton(
            toggle_frame,
            text="▼ Show Advanced Options (for finding cropped images)",
            variable=self.show_advanced,
            command=self._toggle_advanced_options
        )
        self.toggle_button.pack(anchor="w")
        
        # Advanced options frame - initially hidden
        self.advanced_frame = ttk.LabelFrame(self.parent, text="Advanced Crop-Resistant Matching")
        self.advanced_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=2)
        self.advanced_frame.grid_remove()  # Initially hidden
        
        # Crop-resistant matching checkbox
        crop_check = ttk.Checkbutton(
            self.advanced_frame, 
            text="Enable crop-resistant matching (slower, finds cropped images)", 
            variable=self.use_crop_resistant
        )
        crop_check.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=2)

        # Compact method selection row
        method_label = tk.Label(self.advanced_frame, text="Method:")
        method_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        crop_methods = ttk.Combobox(
            self.advanced_frame, 
            textvariable=self.crop_method, 
            values=["combined", "sift", "template", "histogram"],
            state="readonly",
            width=12
        )
        crop_methods.grid(row=1, column=1, sticky="w", padx=5)
        
        # Compact method info
        method_info = tk.Label(
            self.advanced_frame, 
            text="Combined=best • SIFT=features • Template=direct • Histogram=color",
            justify="left",
            font=("Arial", 7),
            fg="gray"
        )
        method_info.grid(row=1, column=2, sticky="w", padx=10, pady=2)

    def _create_threshold_control(self):
        """Create threshold slider control."""
        threshold_frame = ttk.LabelFrame(self.parent, text="Similarity Threshold")
        threshold_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=2)

        # Value display and slider in same row for compactness
        controls_frame = ttk.Frame(threshold_frame)
        controls_frame.pack(fill="x", padx=5, pady=2)
        
        threshold_display = tk.StringVar()
        self.threshold.trace_add(
            "write", lambda *args: threshold_display.set(f"{self.threshold.get():.1f}%")
        )
        tk.Label(controls_frame, textvariable=threshold_display, width=8).pack(side="left")

        # Slider
        ttk.Scale(
            controls_frame,
            from_=1,
            to=100,
            variable=self.threshold,
            orient="horizontal",
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))


class ProgressSection:
    """Progress and status display section."""

    def __init__(self, parent):
        self.parent = parent
        self.status = tk.StringVar(value="Ready")

        progress_frame = ttk.LabelFrame(parent, text="Progress")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=2)

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress_bar.pack(fill="x", padx=10, pady=2)

        tk.Label(
            progress_frame, textvariable=self.status, wraplength=500, justify="center"
        ).pack(pady=2)


class ResultsArea:
    """Results display area with clickable paths."""

    def __init__(self, parent, on_path_click):
        self.parent = parent

        results_frame = ttk.Frame(parent)
        results_frame.grid(row=7, column=0, columnspan=3, padx=5, pady=2, sticky="nsew")

        # Reduce text area height and make it more compact
        self.results_text = tk.Text(results_frame, height=8, width=70, wrap=tk.WORD)
        self.results_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.results_text.configure(yscrollcommand=scrollbar.set)

        # Configure clickable paths
        self.results_text.tag_configure("path_link", foreground="blue", underline=1)
        self.results_text.tag_bind(
            "path_link",
            "<Button-1>",
            lambda e: on_path_click(self.results_text.tag_names(tk.CURRENT)[1]),
        )


class ControlButtons:
    """Search control buttons."""

    def __init__(self, parent, callbacks):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=8, column=0, columnspan=3, pady=5)

        self.search_button = tk.Button(
            button_frame, text="Search", command=callbacks["start_search"]
        )
        self.search_button.pack(side="left", padx=5)

        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=callbacks["cancel_search"],
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=5)
