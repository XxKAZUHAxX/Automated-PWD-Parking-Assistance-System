import cv2
from ultralytics import YOLO
import easyocr
import sqlite3
import re


class VehicleLicensePlateSystem:
    def __init__(self, vehicle_model_path, license_plate_model_path, db_path='users.db'):
        # Initialize EasyOCR reader (use gpu=True if available)
        self.reader = easyocr.Reader(['en'], gpu=False)

        # Load YOLO models for vehicles and license plates
        self.vehicle_model = YOLO(vehicle_model_path)
        self.license_plate_detector = YOLO(license_plate_model_path)

        # Define the vehicle classes of interest (e.g., car, motorcycle, bus, truck)
        self.vehicles = [2, 3, 5, 7]

        # SQLite database path
        self.db_path = db_path

    def get_registered_plate_numbers(self):
        """Extract registered plate numbers from the 'users' table in the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT plate_number FROM users")
            rows = cursor.fetchall()
            # Extract plate numbers as a list (strip any whitespace and ensure uppercase)
            registered_plates = [row[0].strip().upper() for row in rows if row[0]]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            registered_plates = []
        finally:
            conn.close()
        return registered_plates

    def compare_plate_number(self, recognized_plate):
        """
        Compares the recognized plate number with the registered plates from the database.
        The recognized_plate is sanitized to include only uppercase letters and numbers.
        """
        # Clean and format the recognized plate: remove non-alphanumeric characters and force uppercase
        sanitized_plate = re.sub('[^A-Z0-9]', '', recognized_plate.upper())
        if not sanitized_plate:
            return False

        registered_plates = self.get_registered_plate_numbers()
        if sanitized_plate in registered_plates:
            print(f"Match found: {sanitized_plate}")
            return True
        else:
            print(f"No match for: {sanitized_plate}")
            return False

    def process_video(self, video_path):
        """Process video frames to detect vehicles and license plates, perform OCR, and compare results."""
        cap = cv2.VideoCapture(video_path)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 1. Track vehicles using YOLOv8 track API
            track_results = self.vehicle_model.track(frame, persist=True)
            vehicle_detections = track_results[0].boxes.data.tolist() if track_results else []

            annotated_frame = frame.copy()

            # 2. Detect license plates on the full frame
            lp_results = self.license_plate_detector(frame)[0]
            lp_detections = lp_results.boxes.data.tolist()

            # Process each tracked vehicle
            for det in vehicle_detections:
                # Unpack detection data:
                x1, y1, x2, y2, track_id, score, class_id = det
                # Only process vehicles of interest
                if int(class_id) not in self.vehicles:
                    continue

                # Draw vehicle bounding box and tracking ID
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(annotated_frame, f'ID: {int(track_id)}', (int(x1), int(y1) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                plate_associated = False

                # 3. Associate license plate detection with the vehicle
                for lp in lp_detections:
                    x1_lp, y1_lp, x2_lp, y2_lp, lp_score, lp_class_id = lp
                    lp_center_x = (x1_lp + x2_lp) / 2
                    lp_center_y = (y1_lp + y2_lp) / 2

                    # Check if the center of the license plate detection is within the vehicle bounding box.
                    if x1 < lp_center_x < x2 and y1 < lp_center_y < y2:
                        plate_associated = True
                        # Crop and process the license plate region
                        lp_crop = frame[int(y1_lp):int(y2_lp), int(x1_lp):int(x2_lp)]
                        lp_crop_gray = cv2.cvtColor(lp_crop, cv2.COLOR_BGR2GRAY)
                        ocr_results = self.reader.readtext(lp_crop_gray, detail=0)
                        plate_text = ocr_results[0].strip() if ocr_results else ""

                        # Compare recognized plate with database records.
                        self.compare_plate_number(plate_text)

                        # Draw the license plate bounding box and overlay the OCR result.
                        cv2.rectangle(annotated_frame, (int(x1_lp), int(y1_lp)), (int(x2_lp), int(y2_lp)), (0, 0, 255),
                                      2)
                        cv2.putText(annotated_frame, plate_text, (int(x1_lp), int(y1_lp) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                        # Once a matching license plate is found for this vehicle, exit the inner loop.
                        break

            # 4. Display the annotated frame
            annotated_frame = cv2.resize(annotated_frame, dsize=None, fx=0.7, fy=0.7)
            cv2.imshow("Vehicle & License Plate Detection and Tracking", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Create an instance of the system with paths to the models and database.
    system = VehicleLicensePlateSystem(
        vehicle_model_path='weights/yolov8n.pt',
        license_plate_model_path='weights/license_plate_detector.pt',
        db_path='users.db'
    )

    # Process the video file.
    system.process_video('video/sample.mp4')
