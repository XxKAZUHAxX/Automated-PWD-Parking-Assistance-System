import cv2
import os
os.environ['YOLO_AUTOINSTALL'] = 'false'
os.environ['YOLO_VERBOSE'] = 'false'
from ultralytics import YOLO
import easyocr
import sqlite3
import re
import time
import queue

class VehicleLicensePlateSystem:
    def __init__(self, license_plate_model_path, db_path='users.db', event_queue=None, camera_number=1, frame_queue=None, stop_event=None):
        self.event_queue = event_queue
        self.camera_number = camera_number
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.reader = easyocr.Reader(['en'], gpu=False)  # ← GPU=True now
        self.license_plate_detector = YOLO(license_plate_model_path)
        # self.license_plate_detector.to('cuda')
        self.db_path = db_path

    def get_registered_plate_numbers(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT plate_number FROM users")
            rows = cursor.fetchall()
            registered_plates = [row[0].strip().upper() for row in rows if row[0]]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            registered_plates = []
        finally:
            conn.close()
        return registered_plates

    def update_parking_info(self, plate_text):
        sanitized_plate = re.sub('[^A-Z0-9]', '', plate_text.upper())
        if not sanitized_plate:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT slot_number FROM parking_info WHERE slot_status = 'occupied' AND plate_number = ?", (sanitized_plate,))
        already_parked = cursor.fetchone()
        if already_parked:
            print(f"Plate {sanitized_plate} is already parked in slot {already_parked[0]}")
            conn.close()
            return
        cursor.execute("SELECT slot_number FROM parking_info WHERE slot_status = 'empty' ORDER BY slot_number ASC LIMIT 1")
        result = cursor.fetchone()
        if result:
            slot_number = result[0]
            cursor.execute("""
                UPDATE parking_info 
                SET slot_status = 'occupied', plate_number = ? 
                WHERE slot_number = ?
            """, (sanitized_plate, slot_number))
            conn.commit()
            if self.event_queue:
                self.event_queue.put(("match", self.camera_number, sanitized_plate))
            print(f"Updated slot {slot_number} with plate {sanitized_plate}")
        else:
            print("No available slot.")
        conn.close()

    def compare_plate_number(self, recognized_plate):
        sanitized_plate = re.sub('[^A-Z0-9]', '', recognized_plate.upper())
        if not sanitized_plate:
            return False

        registered_plates = self.get_registered_plate_numbers()
        if sanitized_plate in registered_plates:
            print(f"Match found: {sanitized_plate}")
            self.update_parking_info(sanitized_plate)
            return True
        else:
            print(f"No match for: {sanitized_plate}")
            return False

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        prev_time = time.time()
        while cap.isOpened() and not (self.stop_event and self.stop_event.is_set()):
            ret, frame = cap.read()
            if not ret:
                break
            # resized_frame = cv2.resize(frame, (1280, 720))
            resized_frame = frame

            # Set frame dimensions if desired (optional)
            # cap.set(3, 640)
            # cap.set(4, 480)

            current_time = time.time()
            elapsed_time = current_time - prev_time
            fps = 1.0 / elapsed_time if elapsed_time > 0 else 0
            prev_time = current_time

            # Detect license plates in the frame
            lp_results = self.license_plate_detector(resized_frame)[0]
            lp_detections = lp_results.boxes.data.tolist()
            annotated_frame = resized_frame.copy()

            for lp in lp_detections:
                x1_lp, y1_lp, x2_lp, y2_lp, lp_score, lp_class_id = lp
                # Crop the detected license plate region
                lp_crop = frame[int(y1_lp):int(y2_lp), int(x1_lp):int(x2_lp)]
                # Convert to grayscale to potentially improve OCR accuracy and reduce computation
                lp_crop_gray = cv2.cvtColor(lp_crop, cv2.COLOR_BGR2GRAY)
                ocr_results = self.reader.readtext(lp_crop_gray, detail=0)
                plate_text = ocr_results[0].strip() if ocr_results else ""
                # Perform plate comparison if text was detected
                if plate_text:
                    self.compare_plate_number(plate_text)
                # Annotate the frame
                cv2.rectangle(annotated_frame, (int(x1_lp), int(y1_lp)), (int(x2_lp), int(y2_lp)), (0, 0, 255), 2)
                cv2.putText(annotated_frame, plate_text, (int(x1_lp), int(y1_lp) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
            # Display the real-time FPS on the frame
            cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (50, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (50, 255, 0), 2)
            annotated_frame = cv2.resize(annotated_frame, (800, 600))
            if self.frame_queue:
                # overwrite the queue if it's full so only the latest frame is kept
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass
                self.frame_queue.put(annotated_frame)
        cap.release()
        return

if __name__ == "__main__":
    system = VehicleLicensePlateSystem(
        license_plate_model_path='weights/license_plate_detector.pt',
        db_path='users.db'
    )
    system.process_video('video/sample.mp4')
