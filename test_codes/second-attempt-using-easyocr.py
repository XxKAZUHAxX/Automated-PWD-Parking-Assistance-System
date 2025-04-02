import cv2
from ultralytics import YOLO
import easyocr

# Initialize EasyOCR reader (specify languages as needed)
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have a compatible GPU

# Load models:
# - The vehicle model (using YOLOv8 trained on COCO)
# - The license plate detector (a custom-trained YOLOv8 model)
vehicle_model = YOLO('../weights/yolov8n.pt')
license_plate_detector = YOLO('../weights/license_plate_detector.pt')

# Open video file
cap = cv2.VideoCapture('../video/sample.mp4')

# Define the vehicle classes of interest (e.g., car, motorcycle, bus, truck)
vehicles = [2, 3, 5, 7]

# This dictionary will store our results per frame
results = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    # ------------------------------
    # 1. Track vehicles using YOLOv8 track API
    # ------------------------------
    track_results = vehicle_model.track(frame, persist=True)

    if len(track_results) > 0:
        vehicle_detections = track_results[0].boxes.data.tolist()
    else:
        vehicle_detections = []

    # We'll use a copy of the frame for drawing annotations.
    annotated_frame = frame.copy()

    # ------------------------------
    # 2. Detect license plates on the full frame
    # ------------------------------
    lp_results = license_plate_detector(frame)[0]
    lp_detections = lp_results.boxes.data.tolist()

    # For each tracked vehicle, check for associated license plate detection.
    for det in vehicle_detections:
        # Unpack detection data:
        # Adjust the order below if your model outputs a different order.
        x1, y1, x2, y2, track_id, score, class_id = det
        # Filter detections to only vehicle classes of interest.
        if int(class_id) not in vehicles:
            continue

        # Draw the vehicle bounding box (green) and overlay the tracking ID.
        cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(annotated_frame, f'ID: {int(track_id)}', (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Assume no license plate is associated until found.
        plate_associated = False

        # ------------------------------
        # 3. Associate license plate detection with the vehicle
        # ------------------------------
        for lp in lp_detections:
            x1_lp, y1_lp, x2_lp, y2_lp, lp_score, lp_class_id = lp
            # Calculate the center of the license plate detection.
            lp_center_x = (x1_lp + x2_lp) / 2
            lp_center_y = (y1_lp + y2_lp) / 2
            # Check if the center of the license plate is within the vehicle bounding box.
            if x1 < lp_center_x < x2 and y1 < lp_center_y < y2:
                plate_associated = True

                # Crop the license plate region from the frame.
                lp_crop = frame[int(y1_lp):int(y2_lp), int(x1_lp):int(x2_lp)]
                # Run OCR on the cropped license plate image using EasyOCR.

                # process license plate
                license_plate_crop_gray = cv2.cvtColor(lp_crop, cv2.COLOR_BGR2GRAY)

                ocr_results = reader.readtext(license_plate_crop_gray, detail=0)  # detail=0 returns only the text
                plate_text = ocr_results[0].strip() if ocr_results else ""

                # Draw the license plate bounding box (red) and overlay the OCR result (blue).
                cv2.rectangle(annotated_frame, (int(x1_lp), int(y1_lp)), (int(x2_lp), int(y2_lp)), (0, 0, 255), 2)
                cv2.putText(annotated_frame, plate_text, (int(x1_lp), int(y1_lp) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                # Once a matching license plate is found, exit the loop.
                break

    # ------------------------------
    # 4. Display the annotated frame
    # ------------------------------
    annotated_frame = cv2.resize(annotated_frame, dsize=None, fx=0.7, fy=0.7)
    cv2.imshow("Vehicle & License Plate Detection and Tracking", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
