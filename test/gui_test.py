import tkinter as tk
from tkinter import ttk, font

# Defining color palette constants
DARK_GRAY = "#2E2E2E"
LIGHT_GRAY = "#3E3E3E"
WHITE = "#FFFFFF"
BLACK = "#000000"

# Creating the main window
window = tk.Tk()
window.title("GUI Test")
window.geometry("800x600")
window.configure(bg=DARK_GRAY)

# Grid configuration of the main window
window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=3)
window.grid_rowconfigure(2, weight=1)

window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)

# Frames to occupy the grid space
title_frame = ttk.Frame(window, padding=10, style="TFrame")
title_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

button_frame = ttk.Frame(window, padding=10, style="TFrame")
button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

on_screen_frame = ttk.Frame(window, padding=10, style="TFrame")
on_screen_frame.grid(row=1, column=0, sticky="nsew")

totals_frame = ttk.Frame(window, padding=10, style="TFrame")
totals_frame.grid(row=1, column=1, sticky="nsew")

# Configuring grids for the frames
title_frame.grid_rowconfigure(0, weight=1)
title_frame.grid_columnconfigure(0, weight=1)

on_screen_frame.grid_rowconfigure(0, weight=1)
on_screen_frame.grid_rowconfigure(1, weight=1)
on_screen_frame.grid_rowconfigure(2, weight=1)
on_screen_frame.grid_rowconfigure(3, weight=1)
on_screen_frame.grid_rowconfigure(4, weight=1)
on_screen_frame.grid_rowconfigure(5, weight=1)

totals_frame.grid_rowconfigure(0, weight=1)
totals_frame.grid_rowconfigure(1, weight=1)
totals_frame.grid_rowconfigure(2, weight=1)
totals_frame.grid_rowconfigure(3, weight=1)
totals_frame.grid_rowconfigure(4, weight=1)
totals_frame.grid_rowconfigure(5, weight=1)

button_frame.grid_rowconfigure(0, weight=1)
button_frame.grid_columnconfigure(0, weight=1)

# Style configuration
style = ttk.Style()
style.configure("TFrame", background=DARK_GRAY) 

reset_button = ttk.Button(button_frame, text="Reset", command=lambda: print("Reset button clicked"))
reset_button.grid(row=0, column=0, sticky="nsew")

title_text = tk.Label(title_frame, text="Nuts counter", font=("Helvetica", 24), bg=DARK_GRAY, fg=WHITE)
title_text.grid(row=0, column=0, sticky="nsew")

window.mainloop()