import cv2

def main():
    # 1. Open default webcam (index 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Error: Could not open webcam")

    # 2. Read and display frames until 'q' is pressed
    while True:
        ret, frame = cap.read()            # Capture frame-by-frame
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Webcam", frame)        # Display the frame

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

    # 3. When everything done, release capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
