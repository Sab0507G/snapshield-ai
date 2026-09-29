import cv2
import pytesseract
from pytesseract import Output


def preprocess_image(image):
    """
    Prepare screenshot for OCR.
    """

    scale = 2

    enlarged = cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY
    )

    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return enlarged, processed


def run_ocr(image, config):
    """
    Run Tesseract OCR and return detected regions.
    """

    data = pytesseract.image_to_data(
        image,
        config=config,
        output_type=Output.DICT
    )

    results = []

    for i in range(len(data["text"])):

        text = data["text"][i].strip()

        if not text:
            continue

        try:
            confidence = float(data["conf"][i])
        except ValueError:
            continue

        if confidence < 25:
            continue

        results.append({
            "text": text,
            "confidence": confidence,
            "box": (
                int(data["left"][i]),
                int(data["top"][i]),
                int(data["width"][i]),
                int(data["height"][i])
            )
        })

    return results


def extract_text_with_boxes(image_path):
    """
    Extract text from screenshot using multiple OCR passes.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    enlarged, processed = preprocess_image(image)

    all_results = []

    # --------------------------------------------------
    # PASS 1 — NORMAL OCR
    # --------------------------------------------------

    normal_results = run_ocr(
        processed,
        "--psm 6"
    )

    for item in normal_results:

        x, y, w, h = item["box"]

        item["box"] = (
            int(x / 2),
            int(y / 2),
            int(w / 2),
            int(h / 2)
        )

        all_results.append(item)

    # --------------------------------------------------
    # PASS 2 — SPARSE TEXT OCR
    # Useful for isolated values such as API keys
    # --------------------------------------------------

    sparse_results = run_ocr(
        enlarged,
        "--psm 11"
    )

    for item in sparse_results:

        x, y, w, h = item["box"]

        item["box"] = (
            int(x / 2),
            int(y / 2),
            int(w / 2),
            int(h / 2)
        )

        all_results.append(item)

    # --------------------------------------------------
    # REMOVE EXACT DUPLICATES
    # --------------------------------------------------

    unique_results = []

    for item in all_results:

        duplicate = False

        for existing in unique_results:

            same_text = (
                item["text"].lower()
                == existing["text"].lower()
            )

            same_box = (
                abs(item["box"][0] - existing["box"][0]) < 5
                and
                abs(item["box"][1] - existing["box"][1]) < 5
            )

            if same_text and same_box:
                duplicate = True
                break

        if not duplicate:
            unique_results.append(item)

    return unique_results


if __name__ == "__main__":

    image_path = "screenshots/screen.png"

    results = extract_text_with_boxes(
        image_path
    )

    print("\nDetected text:\n")

    for item in results:

        print(
            f"{item['text']:<35} "
            f"confidence={item['confidence']:.1f} "
            f"box={item['box']}"
        )