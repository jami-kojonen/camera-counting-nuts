import threading
import customtkinter

class title_frame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.title = customtkinter.CTkLabel(self, text="Nut counting software", fg_color="gray30", font=("Arial", 24), corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")


class on_screen_frame(customtkinter.CTkFrame):
    def __init__(self, master, values=None):
        super().__init__(master)

        # values = [m6, m8, m10, m12]
        self.values = values if values is not None else [0, 0, 0, 0, 0]

        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.grid_columnconfigure(0, weight=1)

        self.header = customtkinter.CTkLabel(self, text="On screen currently:", fg_color="gray30", font=("Arial", 16), corner_radius=6)
        self.header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.m6_var = customtkinter.StringVar()
        self.m6_var.set(f"M6: {self.values[0]}")
        self.m8_var = customtkinter.StringVar()
        self.m8_var.set(f"M8: {self.values[1]}")
        self.m10_var = customtkinter.StringVar()
        self.m10_var.set(f"M10: {self.values[2]}")
        self.m12_var = customtkinter.StringVar()
        self.m12_var.set(f"M12: {self.values[3]}")
        self.all_sizes_var = customtkinter.StringVar()
        self.all_sizes_var.set(f"All sizes: {self.values[4]}")

        self.m6_label = customtkinter.CTkLabel(self, textvariable=self.m6_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m6_label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m8_label = customtkinter.CTkLabel(self, textvariable=self.m8_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m8_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m10_label = customtkinter.CTkLabel(self, textvariable=self.m10_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m10_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m12_label = customtkinter.CTkLabel(self, textvariable=self.m12_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m12_label.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.all_sizes_label = customtkinter.CTkLabel(self, textvariable=self.all_sizes_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.all_sizes_label.grid(row=5, column=0, padx=10, pady=(10, 0), sticky="ew")





class totals_frame(customtkinter.CTkFrame):
    def __init__(self, master, values=None):
        super().__init__(master)

        # values = [m6, m8, m10, m12]
        self.values = values if values is not None else [0, 0, 0, 0, 0]

        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.grid_columnconfigure(0, weight=1)

        self.header = customtkinter.CTkLabel(self, text="Totals all time:", fg_color="gray30", font=("Arial", 16), corner_radius=6)
        self.header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.m6_var = customtkinter.StringVar()
        self.m6_var.set(f"M6: {self.values[0]}")
        self.m8_var = customtkinter.StringVar()
        self.m8_var.set(f"M8: {self.values[1]}")
        self.m10_var = customtkinter.StringVar()
        self.m10_var.set(f"M10: {self.values[2]}")
        self.m12_var = customtkinter.StringVar()
        self.m12_var.set(f"M12: {self.values[3]}")
        self.all_sizes_var = customtkinter.StringVar()
        self.all_sizes_var.set(f"All sizes: {self.values[4]}")

        self.m6_label = customtkinter.CTkLabel(self, textvariable=self.m6_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m6_label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m8_label = customtkinter.CTkLabel(self, textvariable=self.m8_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m8_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m10_label = customtkinter.CTkLabel(self, textvariable=self.m10_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m10_label.grid(row=3, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.m12_label = customtkinter.CTkLabel(self, textvariable=self.m12_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.m12_label.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.all_sizes_label = customtkinter.CTkLabel(self, textvariable=self.all_sizes_var, font=("Arial", 16), corner_radius=6, justify="left")
        self.all_sizes_label.grid(row=5, column=0, padx=10, pady=(10, 0), sticky="ew")


class button_frame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.reset_button = customtkinter.CTkButton(self, text="Reset", command=master.on_reset_press)
        self.reset_button.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="nsew")


class GUI(customtkinter.CTk):
    def __init__(self, current_values=None, total_values=None):
        super().__init__()

        self.title("Nut counting software")
        self.geometry("400x600")
        self.configure(bg="#2E2E2E")

        # This will be set by the main program
        self.reset_callback_function = None

        self.current_values = current_values if current_values is not None else [0, 0, 0, 0]
        self.total_values = total_values if total_values is not None else [0, 0, 0, 0]

        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=7)
        self.grid_rowconfigure(2, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.title_frame = title_frame(self)
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.button_frame = button_frame(self)
        self.button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        self.on_screen_frame = on_screen_frame(self, values=self.current_values)
        self.on_screen_frame.grid(row=1, column=0, sticky="nsew")

        self.totals_frame = totals_frame(self, values=self.total_values)
        self.totals_frame.grid(row=1, column=1, sticky="nsew")

    def set_reset_callback(self, callback_function):
        # This is used to pass an external function to this class
        # The external function will decide the behaviour of the reset button
        self.reset_callback_function = callback_function

    def on_reset_press(self):
        # This gets executed whenever the actual reset button is pressed
        # This does whatever the callback function has been set to by the main program
        # If no reset callback has been set, do nothing
        if self.reset_callback_function:
            self.reset_callback_function()

    def update_counts(self, current_values, total_values):
        # Update the displayed values in the frames
        self.on_screen_frame.m6_var.set(f"M6: {current_values[0]}")
        self.on_screen_frame.m8_var.set(f"M8: {current_values[1]}")
        self.on_screen_frame.m10_var.set(f"M10: {current_values[2]}")
        self.on_screen_frame.m12_var.set(f"M12: {current_values[3]}")
        self.on_screen_frame.all_sizes_var.set(f"All sizes: {current_values[4]}")

        self.totals_frame.m6_var.set(f"M6: {total_values[0]}")
        self.totals_frame.m8_var.set(f"M8: {total_values[1]}")
        self.totals_frame.m10_var.set(f"M10: {total_values[2]}")
        self.totals_frame.m12_var.set(f"M12: {total_values[3]}")
        self.totals_frame.all_sizes_var.set(f"All sizes: {total_values[4]}")


# current_values = [1, 2, 44, 2, 10]  # Example current values
# total_values = [10, 20, 30, 40, -2]  # Example total values

# app = App(current_values=current_values, total_values=total_values)
# app.mainloop()