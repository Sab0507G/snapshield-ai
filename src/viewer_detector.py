import cv2


def detect_viewers(camera_index=0):
    """Detect visible faces from the webcam."""

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    camera = cv2.VideoCapture(camera_index)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam. Check macOS camera permissions."
        )

    # Give the camera a moment to initialize
    for _ in range(10):
        ret, frame = camera.read()

    camera.release()

    if not ret:
        raise RuntimeError("Could not read frame from webcam.")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Improve contrast for face detection
    gray = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=4,
        minSize=(40, 40)
    )

    viewer_count = len(faces)

    if viewer_count == 0:
        status = "NO VIEWER"
    elif viewer_count == 1:
        status = "SINGLE VIEWER"
    else:
        status = "POTENTIAL UNAUTHORIZED VIEWER"

    return {
        "viewer_count": viewer_count,
        "status": status,
        "faces": faces
    }


if __name__ == "__main__":
    result = detect_viewers()

    print("\n======================================")
    print("       SNAPSHIELD VIEWER DETECTOR")
    print("======================================")
    print(f"Viewer count : {result['viewer_count']}")
    print(f"Status       : {result['status']}")
    print("======================================")