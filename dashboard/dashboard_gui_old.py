import tkinter as tk
from tkinter import ttk


class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dashboard")
        self.geometry("500x400")

        # Create a main container to hold the sidebar and the content area
        container = tk.Frame(self)
        container.pack(side="right", fill="both", expand=True)

        # Create and pack the sidebar on the left
        self.sidebar = SideBar(self, container)
        self.sidebar.pack(side="left", fill="y")

        # Dictionary to store the frames so we can easily switch between them
        self.frames = {}

        for PageClass in (MainPage, RegisterPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=container, controller=self)
            self.frames[page_name] = frame
            # Use grid to stack frames on top of each other
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the MainPage by default
        self.show_frame("MainPage")

    def show_frame(self, page_name):
        """Bring the specified frame to the front."""
        frame = self.frames[page_name]
        frame.tkraise()


class SideBar(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(parent, bg="#f0f0f0", width=150)
        self.container = container
        self.controller = parent
        self.create_widgets()

    def create_widgets(self):
        # Button to show the main page (table)
        main_btn = tk.Button(
            self, text="Main Page",
            command=lambda: self.controller.show_frame("MainPage")
        )
        main_btn.pack(pady=10, padx=10, fill="x")

        # Button to show the register page
        register_btn = tk.Button(
            self, text="Register",
            command=lambda: self.controller.show_frame("RegisterPage")
        )
        register_btn.pack(pady=10, padx=10, fill="x")


class MainPage(tk.Frame):
    """Frame that shows the 'Profile Details' table."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self, text="PROFILE DETAILS", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Create a Treeview as a table
        columns = ("first_name", "last_name", "age", "plate_number")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        # Set headings
        self.tree.heading("first_name", text="FIRST NAME")
        self.tree.heading("last_name", text="LAST NAME")
        self.tree.heading("age", text="AGE")
        self.tree.heading("plate_number", text="PLATE NUMBER")

        # Optionally set column widths
        self.tree.column("first_name", width=100, anchor=tk.CENTER)
        self.tree.column("last_name", width=100, anchor=tk.CENTER)
        self.tree.column("age", width=50, anchor=tk.CENTER)
        self.tree.column("plate_number", width=100, anchor=tk.CENTER)

        self.tree.pack(pady=10, fill="x", expand=True)

        # Sample data
        data = [
            ("Naomi", "Meghana", 30, 'NBC 1234'),
            ("Ravi", "Naubir", 27, 'AKA 1023'),
            ("Sharma", "Monte", 34, 'AGA 1625'),
        ]

        # Insert sample data into the table
        for row in data:
            self.tree.insert("", "end", values=row)


class RegisterPage(tk.Frame):
    """Frame that shows a simple 'Register' form (placeholder)."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Register Page", font=("Helvetica", 16, "bold"))
        label.pack(pady=20)

        # Here you can add labels, entries, and buttons
        # for an actual registration form


if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
