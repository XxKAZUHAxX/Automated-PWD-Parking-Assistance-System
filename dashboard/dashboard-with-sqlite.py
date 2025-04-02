import sqlite3
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar

working_dir = os.getcwd()
DATABASE = working_dir+"/users.db"


class DashboardApp(ttk.Window):
    def __init__(self, theme="flatly"):
        # Initialize ttkbootstrap Window with a chosen theme
        super().__init__(themename=theme)
        self.title("Dashboard")
        self.geometry("900x500")

        # Initialize database connection and ensure table exists
        self.conn = sqlite3.connect(DATABASE)
        self.create_table()

        # Use the provided style without reassigning it.
        self.style.configure("TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"),
                             foreground="white", background="#007BFF")
        self.style.map("Treeview.Heading", background=[("active", "#0056b3"), ("!disabled", "#007BFF")])

        # Create a main container frame to hold sidebar + content
        container = ttk.Frame(self)
        container.pack(side="right", fill="both", expand=True)

        # Create and pack the sidebar on the left
        self.sidebar = SideBar(self, container)
        self.sidebar.pack(side="left", fill="y")

        # Dictionary to store the frames for easy switching
        self.frames = {}
        for PageClass in (MainPage, RegisterPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the main page by default
        self.show_frame("MainPage")

    def create_table(self):
        """Create the users table if it does not exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER,
                plate_number TEXT
            )
        """)
        self.conn.commit()

    def get_all_users(self):
        """Return all user records from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT first_name, last_name, age, plate_number FROM users")
        return cursor.fetchall()

    def show_frame(self, page_name):
        """Bring the specified frame to the front."""
        frame = self.frames[page_name]
        frame.tkraise()
        # If we're showing the MainPage, update the table data
        if page_name == "MainPage":
            frame.update_tree()


class SideBar(ttk.Frame):
    """Sidebar with navigation buttons."""

    def __init__(self, parent, container):
        super().__init__(parent, padding=(10, 10))
        self.container = container
        self.controller = parent
        self.create_widgets()

    def create_widgets(self):
        # Title or brand at the top (optional)
        brand_label = ttk.Label(self, text="MENU", font=("Helvetica", 14, "bold"))
        brand_label.pack(pady=(0, 20), padx=10)

        # Button to show the Main Page
        main_btn = ttk.Button(
            self,
            text="Main Page",
            bootstyle=PRIMARY,
            command=lambda: self.controller.show_frame("MainPage")
        )
        main_btn.pack(pady=5, fill="x")

        # Button to show the Register Page
        register_btn = ttk.Button(
            self,
            text="Register",
            bootstyle=INFO,
            command=lambda: self.controller.show_frame("RegisterPage")
        )
        register_btn.pack(pady=5, fill="x")


class MainPage(ttk.Frame):
    """Frame that shows the 'Profile Details' table."""

    def __init__(self, parent, controller):
        super().__init__(parent, padding=(20, 20))
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        title_label = ttk.Label(self, text="Profile Details", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Create a Treeview as a table
        columns = ("first_name", "last_name", "age", "plate_number")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", bootstyle="info")
        self.tree.pack(pady=10, fill="both", expand=True)

        # Set headings
        self.tree.heading("first_name", text="FIRST NAME")
        self.tree.heading("last_name", text="LAST NAME")
        self.tree.heading("age", text="AGE")
        self.tree.heading("plate_number", text="PLATE NUMBER")

        # Set column widths (adjust as you see fit)
        self.tree.column("first_name", width=200, anchor="center")
        self.tree.column("last_name", width=200, anchor="center")
        self.tree.column("age", width=100, anchor="center")
        self.tree.column("plate_number", width=200, anchor="center")

    def update_tree(self):
        """Load data from the database and populate the treeview."""
        # Clear current content
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Fetch all users from the database
        for row in self.controller.get_all_users():
            self.tree.insert("", "end", values=row)


class RegisterPage(ttk.Frame):
    """Frame that shows a simple 'Register' form."""

    def __init__(self, parent, controller):
        super().__init__(parent, padding=(20, 20))
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="Register Page", font=("Helvetica", 16, "bold"))
        label.pack(pady=10)

        # Create StringVar variables for the form fields
        self.first_name_var = StringVar()
        self.last_name_var = StringVar()
        self.age_var = StringVar()
        self.plate_number_var = StringVar()

        # First Name
        fname_label = ttk.Label(self, text="First Name:")
        fname_label.pack(anchor="w", pady=(10, 0))
        fname_entry = ttk.Entry(self, textvariable=self.first_name_var)
        fname_entry.pack(anchor="w", fill="x")

        # Last Name
        lname_label = ttk.Label(self, text="Last Name:")
        lname_label.pack(anchor="w", pady=(10, 0))
        lname_entry = ttk.Entry(self, textvariable=self.last_name_var)
        lname_entry.pack(anchor="w", fill="x")

        # Age
        age_label = ttk.Label(self, text="Age:")
        age_label.pack(anchor="w", pady=(10, 0))
        age_entry = ttk.Entry(self, textvariable=self.age_var)
        age_entry.pack(anchor="w", fill="x")

        # Plate Number
        plate_label = ttk.Label(self, text="Plate Number:")
        plate_label.pack(anchor="w", pady=(10, 0))
        plate_entry = ttk.Entry(self, textvariable=self.plate_number_var)
        plate_entry.pack(anchor="w", fill="x")

        # Submit Button
        submit_button = ttk.Button(
            self,
            text="Submit",
            bootstyle=SUCCESS,
            command=self.submit_form
        )
        submit_button.pack(pady=20)

    def submit_form(self):
        # Get data from form
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        age = self.age_var.get().strip()
        plate_number = self.plate_number_var.get().strip()

        # Simple validation (you can extend this)
        if not (first_name and last_name and age and plate_number):
            print("All fields are required!")
            return

        try:
            age_int = int(age)
        except ValueError:
            print("Age must be a number!")
            return

        # Insert data into the database
        cursor = self.controller.conn.cursor()
        cursor.execute("""
            INSERT INTO users (first_name, last_name, age, plate_number)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, age_int, plate_number))
        self.controller.conn.commit()
        print("User registered successfully.")

        # Clear the fields
        self.first_name_var.set("")
        self.last_name_var.set("")
        self.age_var.set("")
        self.plate_number_var.set("")

        # Update the MainPage table to reflect new data
        self.controller.frames["MainPage"].update_tree()


if __name__ == "__main__":
    app = DashboardApp(theme="darkly")  # Try different themes like 'darkly', 'journal', etc.
    app.mainloop()
