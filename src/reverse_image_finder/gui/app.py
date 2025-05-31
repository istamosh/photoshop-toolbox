"""Main application window and menu."""

import tkinter as tk
from tkinter import ttk

from .image_search import ImageSearchApp
from .psd_updater import PSDDateUpdater


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
