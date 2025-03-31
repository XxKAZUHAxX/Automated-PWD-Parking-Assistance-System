from ultralytics import YOLO
import cv2

# load models
coco_model = YOLO('weights/yolov8n.pt')

# load video
cap = cv2.VideoCapture('video/sample.mp4')

vehicles = [2, 3, 5, 7]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detections = coco_model(frame)[0]
    print(detections)
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)

    resized_frame = cv2.resize(frame, (640, 480))
    cv2.imshow('frame', resized_frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()