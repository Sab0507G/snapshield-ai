import mss
from PIL import Image


def capture_screen(output_path="screenshots/screen.png"):
    """
    Capture the primary monitor and save it as an image.
    """

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        image = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb
        )

        image.save(output_path)

    print(f"Screenshot saved to: {output_path}")


if __name__ == "__main__":
    capture_screen()