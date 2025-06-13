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

        self._create_input_controls()
        self._create_search_options()
        self._create_threshold_control()

    def _create_input_controls(self):
        """Create file and directory selection controls."""
        # Reference image selection
        tk.Label(self.parent, text="Reference Image:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        tk.Entry(self.parent, textvariable=self.reference_image_path, width=50).grid(
            row=0, column=1, padx=5
        )
        tk.Button(
            self.parent, text="Browse", command=self.callbacks["select_reference"]
        ).grid(row=0, column=2, padx=5)

        # Search directory selection
        tk.Label(self.parent, text="Search Directory:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
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
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        hash_types = ttk.Combobox(
            self.parent, textvariable=self.hash_type, values=["phash", "ahash"]
        )
        hash_types.grid(row=2, column=1, sticky="w", padx=5)

        # Stop on first match checkbox
        ttk.Checkbutton(
            self.parent, text="Stop on First Match", variable=self.stop_on_first_match
        ).grid(row=2, column=2, sticky="w", padx=5)

    def _create_threshold_control(self):
        """Create threshold slider control."""
        threshold_frame = ttk.LabelFrame(self.parent, text="Similarity Threshold")
        threshold_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Value display
        threshold_display = tk.StringVar()
        self.threshold.trace_add(
            "write", lambda *args: threshold_display.set(f"{self.threshold.get():.1f}%")
        )
        tk.Label(threshold_frame, textvariable=threshold_display).pack()

        # Slider
        ttk.Scale(
            threshold_frame,
            from_=1,
            to=100,
            variable=self.threshold,
            orient="horizontal",
        ).pack(fill="x", padx=5, pady=(0, 5))


class ProgressSection:
    """Progress and status display section."""

    def __init__(self, parent):
        self.parent = parent
        self.status = tk.StringVar(value="Ready")

        progress_frame = ttk.LabelFrame(parent, text="Progress")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress_bar.pack(fill="x", padx=10, pady=(5, 0))

        tk.Label(
            progress_frame, textvariable=self.status, wraplength=500, justify="center"
        ).pack(pady=5)


class ResultsArea:
    """Results display area with clickable paths."""

    def __init__(self, parent, on_path_click):
        self.parent = parent

        results_frame = ttk.Frame(parent)
        results_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        self.results_text = tk.Text(results_frame, height=15, width=70)
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
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)

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
