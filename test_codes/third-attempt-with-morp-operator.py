import cv2
from ultralytics import YOLO
import easyocr
import numpy as np

# Load models:
# - Vehicle model (YOLOv8 trained on COCO)
# - License plate detector (custom YOLOv8 model)
vehicle_model = YOLO('../weights/yolov8n.pt')
license_plate_detector = YOLO('../weights/license_plate_detector.pt')

# Initialize EasyOCR reader (set the language as needed, e.g., 'en' for English)
reader = easyocr.Reader(['en'], gpu=False)

# Open video file
cap = cv2.VideoCapture('../video/sample.mp4')

# Define vehicle classes of interest (e.g., car, motorcycle, bus, truck)
vehicles = [2, 3, 5, 7]

results = {}
frame_nmr = -1

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_nmr += 1
    results[frame_nmr] = {}

    # ------------------------------
    # 1. Track vehicles using YOLOv8 track API
    # ------------------------------
    track_results = vehicle_model.track(frame, persist=True)
    # Assume the first element contains detections for the current frame
    if len(track_results) > 0:
        vehicle_detections = track_results[0].boxes.data.tolist()
    else:
        vehicle_detections = []

    annotated_frame = frame.copy()

    # ------------------------------
    # 2. Detect license plates on the full frame
    # ------------------------------
    lp_results = license_plate_detector(frame)[0]
    lp_detections = lp_results.boxes.data.tolist()

    # ------------------------------
    # 3. For each tracked vehicle, associate a license plate and extract text
    # ------------------------------
    for det in vehicle_detections:
        # Unpack detection info. Adjust the order if needed.
        x1, y1, x2, y2, track_id, score, class_id = det
        if int(class_id) not in vehicles:
            continue

        # Draw the vehicle bounding box (green) and display tracking ID.
        cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(annotated_frame, f'ID: {int(track_id)}', (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        plate_associated = False

        for lp in lp_detections:
            x1_lp, y1_lp, x2_lp, y2_lp, lp_score, lp_class_id = lp
            # Calculate the center of the license plate detection.
            lp_center_x = (x1_lp + x2_lp) / 2
            lp_center_y = (y1_lp + y2_lp) / 2
            # Check if the center lies within the vehicle bounding box.
            if x1 < lp_center_x < x2 and y1 < lp_center_y < y2:
                plate_associated = True

                # Crop the license plate region.
                lp_crop = frame[int(y1_lp):int(y2_lp), int(x1_lp):int(x2_lp)]

                # ------------------------------
                # 4. Pre-process the license plate image
                # ------------------------------
                # Convert to grayscale.
                gray = cv2.cvtColor(lp_crop, cv2.COLOR_BGR2GRAY)
                # Apply bilateral filter to reduce noise while preserving edges.
                gray = cv2.bilateralFilter(gray, 10, 10, 17)
                # Use Canny edge detection.
                edges = cv2.Canny(gray, 30, 200)
                # Create a kernel for morphological operations.
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                # Perform morphological closing to connect gaps in edges.
                closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
                # Dilate the result to accentuate text outlines.
                processed_lp = cv2.dilate(closed, kernel, iterations=1)
                cv2.imshow("Morphological Operator Peek", processed_lp)
                cv2.waitKey(0)

                # ------------------------------
                # 5. Extract text using EasyOCR
                # ------------------------------
                # EasyOCR expects an image, so we pass the processed image.
                ocr_result = reader.readtext(processed_lp)
                # Combine detected text segments.
                plate_text = " ".join([res[1] for res in ocr_result]).strip()

                # Store results.
                results[frame_nmr][f'vehicle_{int(track_id)}'] = {
                    'vehicle_bbox': [x1, y1, x2, y2],
                    'license_plate_bbox': [x1_lp, y1_lp, x2_lp, y2_lp],
                    'plate_text': plate_text
                }

                # Draw the license plate bounding box (red) and overlay OCR result (blue).
                cv2.rectangle(annotated_frame, (int(x1_lp), int(y1_lp)), (int(x2_lp), int(y2_lp)), (0, 0, 255), 2)
                cv2.putText(annotated_frame, plate_text, (int(x1_lp), int(y1_lp) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                break  # Associate only one license plate per vehicle.

        # If no license plate is found, store vehicle info only.
        if not plate_associated:
            results[frame_nmr][f'vehicle_{int(track_id)}'] = {
                'vehicle_bbox': [x1, y1, x2, y2],
                'license_plate_bbox': None,
                'plate_text': None
            }

    # ------------------------------
    # 6. Display the annotated frame
    # ------------------------------
    annotated_frame = cv2.resize(annotated_frame, dsize=None, fx=0.7, fy=0.7)
    cv2.imshow("Vehicle & License Plate Detection", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
