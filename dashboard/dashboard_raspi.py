import sqlite3
import os
os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['YOLO_VERBOSE'] = 'false'
import cv2
import threading
import queue
import serial
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import StringVar, messagebox
from LicensePlateRecognitionSystemRaspi import VehicleLicensePlateSystem

working_dir = os.getcwd()
DATABASE = working_dir + "/users.db"

# Hyperparameter
# serial_port = 'COM4'
serial_port = '/dev/ttyACM0'     # Serial port for Raspberry Pi 5

# video_path_1 = 'video/sample_2.mp4'
video_path_1 = 0
video_path_2 = 2

class DashboardApp(ttk.Window):
    def __init__(self, theme="flatly"):
        super().__init__(themename=theme)
        self.title("Dashboard")
        self.geometry("1000x800")
        self.minsize(1000, 800)

        # Initialize database connection and ensure tables exist
        self.conn = sqlite3.connect(DATABASE, check_same_thread=False)
        self.create_table()
        self.create_parking_info_table()

        self.style.configure("TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"),
                             foreground="white", background="#007BFF")
        self.style.map("Treeview.Heading", background=[("active", "#0056b3"), ("!disabled", "#007BFF")])

        container = ttk.Frame(self)
        container.pack(side="right", fill="both", expand=True)

        self.sidebar = SideBar(self, container)
        self.sidebar.pack(side="left", fill="y")

        self.frames = {}
        for PageClass in (MainPage, RegisterPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainPage")

    def create_table(self):
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

    def create_parking_info_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_info (
                slot_number INTEGER PRIMARY KEY,
                slot_status TEXT,
                plate_number TEXT
            )
        """)
        self.conn.commit()
        cursor.execute("SELECT COUNT(*) FROM parking_info")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO parking_info (slot_number, slot_status, plate_number) VALUES (1, 'empty', '')")
            cursor.execute("INSERT INTO parking_info (slot_number, slot_status, plate_number) VALUES (2, 'empty', '')")
            self.conn.commit()

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT first_name, last_name, age, plate_number FROM users")
        return cursor.fetchall()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == "MainPage":
            frame.update_tree()

class SideBar(ttk.Frame):
    def __init__(self, parent, container):
        super().__init__(parent, padding=(10, 10))
        self.container = container
        self.controller = parent
        self.create_widgets()

    def create_widgets(self):
        brand_label = ttk.Label(self, text="MENU", font=("Helvetica", 14, "bold"))
        brand_label.pack(pady=(0, 20), padx=10)
        main_btn = ttk.Button(
            self,
            text="Main Page",
            bootstyle=PRIMARY,
            command=lambda: self.controller.show_frame("MainPage")
        )
        main_btn.pack(pady=5, fill="x")
        register_btn = ttk.Button(
            self,
            text="Register",
            bootstyle=INFO,
            command=lambda: self.controller.show_frame("RegisterPage")
        )
        register_btn.pack(pady=5, fill="x")

class MainPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=(20, 20))
        self.controller = controller
        self.recognition_thread1 = None
        self.recognition_thread2 = None
        self.create_widgets()
        # Start periodic refresh (every 5000 ms)
        self.refresh_data()
        # create the queue and start listener '/dev/ttyACM0'
        self.event_queue = queue.Queue()
        # before starting recognition threads:
        self.frame_queues = {
            1: queue.Queue(maxsize=1),
            2: queue.Queue(maxsize=1)
        }
        # Track which camera windows are open
        self.active_cams = {1: True, 2: True}
        # Events to tell workers to stop
        self.stop_events = {1: threading.Event(),
                            2: threading.Event()}
        # Kick off display loop
        self.after(30, self._display_frames)

        try: self.serial_port = serial.Serial(serial_port, 9600, timeout=1)
        except: pass
        threading.Thread(target=self._process_events, daemon=True).start()

    def create_widgets(self):
        title_label = ttk.Label(self, text="Profile Details", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Treeview for user profiles
        columns = ("first_name", "last_name", "age", "plate_number")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", bootstyle="info")
        self.tree.pack(pady=10, fill="both", expand=True)
        self.tree.heading("first_name", text="FIRST NAME")
        self.tree.heading("last_name", text="LAST NAME")
        self.tree.heading("age", text="AGE")
        self.tree.heading("plate_number", text="PLATE NUMBER")
        self.tree.column("first_name", width=200, anchor="center")
        self.tree.column("last_name", width=200, anchor="center")
        self.tree.column("age", width=100, anchor="center")
        self.tree.column("plate_number", width=200, anchor="center")

        # Section for parking information
        parking_label = ttk.Label(self, text="Parking Info", font=("Helvetica", 16, "bold"))
        parking_label.pack(pady=10)
        parking_columns = ("slot_number", "slot_status", "plate_number")
        self.parking_tree = ttk.Treeview(self, columns=parking_columns, show="headings", bootstyle="info")
        self.parking_tree.pack(pady=10, fill="both", expand=True)
        self.parking_tree.heading("slot_number", text="SLOT NUMBER")
        self.parking_tree.heading("slot_status", text="SLOT STATUS")
        self.parking_tree.heading("plate_number", text="PLATE NUMBER")
        self.parking_tree.column("slot_number", width=100, anchor="center")
        self.parking_tree.column("slot_status", width=100, anchor="center")
        self.parking_tree.column("plate_number", width=200, anchor="center")

        # Start button to launch the license plate recognition system
        self.start_button = ttk.Button(
            self,
            text="Start License Plate Recognition",
            bootstyle=SUCCESS,
            command=self.start_recognition
        )
        self.start_button.pack(pady=10)

        # Release button for parking slots
        self.release_button = ttk.Button(
            self,
            text="Release Selected Slot",
            bootstyle=WARNING,
            command=self.release_slot
        )
        self.release_button.pack(pady=10)

    def update_tree(self):
        # Update user profiles
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.controller.get_all_users():
            self.tree.insert("", "end", values=row)
        # Update parking info
        self.update_parking_tree()

    def update_parking_tree(self):
        for item in self.parking_tree.get_children():
            self.parking_tree.delete(item)
        cursor = self.controller.conn.cursor()
        cursor.execute("SELECT slot_number, slot_status, plate_number FROM parking_info ORDER BY slot_number ASC")
        rows = cursor.fetchall()
        for row in rows:
            self.parking_tree.insert("", "end", values=row)

    def refresh_data(self):
        # Periodically refresh treeviews (e.g., every 5 seconds)
        self.update_tree()
        self.after(5000, self.refresh_data)

    def start_recognition(self):
        if (self.recognition_thread1 and self.recognition_thread1.is_alive()) or \
                (self.recognition_thread2 and self.recognition_thread2.is_alive()):
            messagebox.showinfo("Info", "License plate recognition is already running.")
            return

        # Clear any previous stop flags
        self.stop_events[1].clear()
        self.stop_events[2].clear()
        self.recognition_thread1 = threading.Thread(target=self.run_worker, args=(1,video_path_1,), daemon=True)
        self.recognition_thread2 = threading.Thread(target=self.run_worker, args=(2,video_path_2,), daemon=True)
        self.recognition_thread1.start()
        self.recognition_thread2.start()
        messagebox.showinfo("Info", "Started license plate recognition.")

    def run_recognition(self, camNo, video_path):
        system = VehicleLicensePlateSystem(
            license_plate_model_path='weights/license_plate_detector.pt',
            db_path='users.db',
            event_queue = self.event_queue,
            camera_number=camNo
        )
        system.process_video(video_path)
        # Refresh the parking info after recognition stops
        self.update_parking_tree()

    def run_worker(self, camNo, video_path):
        system = VehicleLicensePlateSystem(
            license_plate_model_path='weights/license_plate_detector.pt',
            db_path='users.db',
            event_queue=self.event_queue,
            camera_number=camNo,
            frame_queue=self.frame_queues[camNo],  # pass the queue
            stop_event=self.stop_events[camNo]
        )
        system.process_video(video_path)
        # once done, you could push a sentinel or let the queue drain

    def release_slot(self):
        selected_item = self.parking_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a slot to release.")
            return

        slot_info = self.parking_tree.item(selected_item, 'values')
        slot_number = slot_info[0]

        cursor = self.controller.conn.cursor()
        cursor.execute("""
            UPDATE parking_info 
            SET slot_status = 'empty', plate_number = '' 
            WHERE slot_number = ?
        """, (slot_number,))
        self.controller.conn.commit()
        messagebox.showinfo("Info", f"Slot {slot_number} has been released.")
        cmd = f"{slot_number}:CLOSE\n".encode()
        self.serial_port.write(cmd)
        self.update_parking_tree()

    def _process_events(self):
        """Listener thread: handle match events from LPR thread."""
        while True:
            event, cam_no, plate = self.event_queue.get()
            if event == "match":
                cursor = self.controller.conn.cursor()
                # check current status
                cursor.execute("""
                    SELECT slot_status 
                    FROM parking_info 
                    WHERE slot_number=?
                    """, (cam_no,))
                status = cursor.fetchone()[0]
                # send open command to Arduino
                cmd = f"{cam_no}:OPEN\n".encode()
                self.serial_port.write(cmd)
            self.update_parking_tree()

    def _display_frames(self):
        still_any = False
        # 1) Show all active camera frames
        for camNo, q in self.frame_queues.items():
            if not self.active_cams.get(camNo, False):
                continue
            if not q.empty():
                frame = q.get()
                window_name = f"Cam {camNo}: License Plate Recognition"
                cv2.imshow(window_name, frame)
                still_any = True

        # 2) Poll keypress just ONCE per cycle
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # 3) Close & signal all active cams
            for camNo in list(self.active_cams.keys()):
                if self.active_cams[camNo]:
                    window_name = f"Cam {camNo}: License Plate Recognition"
                    cv2.destroyWindow(window_name)
                    self.active_cams[camNo] = False
                    self.stop_events[camNo].set()

        # 4) Continue looping if any window remains
        # if still_any:
        self.after(30, self._display_frames)


class RegisterPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding=(20, 20))
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        label = ttk.Label(self, text="Register Page", font=("Helvetica", 16, "bold"))
        label.pack(pady=10)

        self.first_name_var = StringVar()
        self.last_name_var = StringVar()
        self.age_var = StringVar()
        self.plate_number_var = StringVar()

        fname_label = ttk.Label(self, text="First Name:")
        fname_label.pack(anchor="w", pady=(10, 0))
        fname_entry = ttk.Entry(self, textvariable=self.first_name_var)
        fname_entry.pack(anchor="w", fill="x")

        lname_label = ttk.Label(self, text="Last Name:")
        lname_label.pack(anchor="w", pady=(10, 0))
        lname_entry = ttk.Entry(self, textvariable=self.last_name_var)
        lname_entry.pack(anchor="w", fill="x")

        age_label = ttk.Label(self, text="Age:")
        age_label.pack(anchor="w", pady=(10, 0))
        age_entry = ttk.Entry(self, textvariable=self.age_var)
        age_entry.pack(anchor="w", fill="x")

        plate_label = ttk.Label(self, text="Plate Number:")
        plate_label.pack(anchor="w", pady=(10, 0))
        plate_entry = ttk.Entry(self, textvariable=self.plate_number_var)
        plate_entry.pack(anchor="w", fill="x")

        submit_button = ttk.Button(
            self,
            text="Submit",
            bootstyle=SUCCESS,
            command=self.submit_form
        )
        submit_button.pack(pady=20)

    def submit_form(self):
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()
        age = self.age_var.get().strip()
        plate_number = self.plate_number_var.get().strip()

        if not (first_name and last_name and age and plate_number):
            messagebox.showwarning("Warning", "All fields are required!")
            return

        try:
            age_int = int(age)
        except ValueError:
            messagebox.showwarning("Warning", "Age must be a number!")
            return

        cursor = self.controller.conn.cursor()
        cursor.execute("""
            INSERT INTO users (first_name, last_name, age, plate_number)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, age_int, plate_number))
        self.controller.conn.commit()
        messagebox.showinfo("Info", "User registered successfully.")

        self.first_name_var.set("")
        self.last_name_var.set("")
        self.age_var.set("")
        self.plate_number_var.set("")
        self.controller.frames["MainPage"].update_tree()

if __name__ == "__main__":
    app = DashboardApp(theme="darkly")
    app.mainloop()
