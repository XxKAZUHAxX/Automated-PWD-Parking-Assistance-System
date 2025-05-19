import cv2
from ultralytics import YOLO
import easyocr

# Initialize EasyOCR reader (specify languages as needed)
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have a compatible GPU

license_plate_detector = YOLO('../weights/license_plate_detector.pt')

# Open video file
cap = cv2.VideoCapture('../video/sample_4.mp4')

# Define the vehicle classes of interest (e.g., car, motorcycle, bus, truck)
vehicles = [2, 3, 5, 7]

# This dictionary will store our results per frame
results = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Detect license plates in the frame
    lp_results = license_plate_detector(frame)[0]
    lp_detections = lp_results.boxes.data.tolist()
    annotated_frame = frame.copy()

    for lp in lp_detections:
        x1_lp, y1_lp, x2_lp, y2_lp, lp_score, lp_class_id = lp
        # Crop the detected license plate region
        lp_crop = frame[int(y1_lp):int(y2_lp), int(x1_lp):int(x2_lp)]
        # Convert to grayscale to potentially improve OCR accuracy and reduce computation
        lp_crop_gray = cv2.cvtColor(lp_crop, cv2.COLOR_BGR2GRAY)
        ocr_results = reader.readtext(lp_crop_gray, detail=0)
        plate_text = ocr_results[0].strip() if ocr_results else ""
        cv2.rectangle(annotated_frame, (int(x1_lp), int(y1_lp)), (int(x2_lp), int(y2_lp)), (0, 0, 255), 2)
        cv2.putText(annotated_frame, plate_text, (int(x1_lp), int(y1_lp) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # ------------------------------
    # 4. Display the annotated frame
    # ------------------------------
    annotated_frame = cv2.resize(annotated_frame, dsize=None, fx=0.7, fy=0.7)
    cv2.imshow("Vehicle & License Plate Detection and Tracking", annotated_frame)
    if cv2.waitKey(0) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
