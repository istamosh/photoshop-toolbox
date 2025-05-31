"""Main entry point for the application."""

import tkinter as tk
from reverse_image_finder.gui import App


def main():
    root = tk.Tk()
    root.geometry("800x600")
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
