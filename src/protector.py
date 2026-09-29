import cv2


# =========================================================
# Sensitive Region Protector
# =========================================================

def protect_sensitive_regions(image_path, detections, output_path):
    """
    Blur and highlight regions containing sensitive information.

    Handles:
    - EMAIL
    - PHONE
    - CARD_NUMBER
    - API_KEY
    - PASSWORD

    Adds type-specific padding so OCR bounding-box inaccuracies
    do not leave sensitive text exposed.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {image_path}"
        )

    image_height, image_width = image.shape[:2]

    protected_count = 0

    for item in detections:

        # -------------------------------------------------
        # Read detection information
        # -------------------------------------------------

        detection_type = str(
            item.get("type", "")
        ).upper()

        box = item.get("box")

        if not box or len(box) != 4:
            continue

        try:
            x, y, w, h = map(
                int,
                box
            )
        except (TypeError, ValueError):
            continue

        # -------------------------------------------------
        # Ignore invalid boxes
        # -------------------------------------------------

        if w <= 0 or h <= 0:
            continue

        # -------------------------------------------------
        # Type-specific padding
        #
        # Password/card need more protection because OCR
        # can produce a box that is slightly smaller than
        # the actual visible text.
        # -------------------------------------------------

        padding_map = {
            "EMAIL": 10,
            "PHONE": 10,
            "API_KEY": 12,
            "PASSWORD": 18,
            "CARD_NUMBER": 18,
        }

        padding_x = padding_map.get(
            detection_type,
            12
        )

        padding_y = max(
            10,
            padding_map.get(
                detection_type,
                12
            )
        )

        # -------------------------------------------------
        # Password-specific expansion
        #
        # Example:
        # Password: DemoPass123
        #
        # If OCR only detects part of the text, expand
        # significantly in the horizontal direction.
        # -------------------------------------------------

        if detection_type == "PASSWORD":

            padding_x = max(
                padding_x,
                int(w * 0.15)
            )

            padding_y = max(
                padding_y,
                int(h * 0.50)
            )

        # -------------------------------------------------
        # Card-specific expansion
        #
        # Card numbers may be split or have spaces between
        # groups. Expand horizontally to cover the complete
        # number.
        # -------------------------------------------------

        elif detection_type == "CARD_NUMBER":

            padding_x = max(
                padding_x,
                int(w * 0.10)
            )

            padding_y = max(
                padding_y,
                int(h * 0.60)
            )

        # -------------------------------------------------
        # Calculate protected region
        # -------------------------------------------------

        x1 = max(
            0,
            x - padding_x
        )

        y1 = max(
            0,
            y - padding_y
        )

        x2 = min(
            image_width,
            x + w + padding_x
        )

        y2 = min(
            image_height,
            y + h + padding_y
        )

        # -------------------------------------------------
        # Safety check
        # -------------------------------------------------

        if x2 <= x1 or y2 <= y1:
            continue

        region = image[
            y1:y2,
            x1:x2
        ]

        if region.size == 0:
            continue

        # -------------------------------------------------
        # Strong blur
        #
        # Larger kernel gives stronger protection.
        # -------------------------------------------------

        blurred = cv2.GaussianBlur(
            region,
            (41, 41),
            0
        )

        # -------------------------------------------------
        # Apply blur
        # -------------------------------------------------

        image[
            y1:y2,
            x1:x2
        ] = blurred

        # -------------------------------------------------
        # Visible protection rectangle
        # -------------------------------------------------

        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (255, 0, 0),
            3
        )

        protected_count += 1

        # -------------------------------------------------
        # Optional label
        #
        # Helps during demo/presentation.
        # -------------------------------------------------

        label = detection_type.replace(
            "_",
            " "
        )

        label_y = max(
            20,
            y1 - 6
        )

        cv2.putText(
            image,
            f"PROTECTED: {label}",
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 0, 0),
            2,
            cv2.LINE_AA
        )

    # =====================================================
    # Save protected image
    # =====================================================

    success = cv2.imwrite(
        output_path,
        image
    )

    if not success:
        raise IOError(
            f"Could not save protected image: {output_path}"
        )

    print(
        f"Protected image saved to: {output_path}"
    )

    print(
        f"Protected regions: {protected_count}"
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    test_detections = [

        {
            "type": "EMAIL",
            "value": "test@example.com",
            "box": (100, 100, 180, 25),
            "confidence": 98
        },

        {
            "type": "API_KEY",
            "value": "sk_test_1234567890abcdef",
            "box": (100, 200, 250, 25),
            "confidence": 96
        },

        {
            "type": "PASSWORD",
            "value": "Password: DemoPass123",
            "box": (100, 300, 250, 25),
            "confidence": 95
        },

        {
            "type": "CARD_NUMBER",
            "value": "4111 1111 1111 1111",
            "box": (100, 400, 250, 25),
            "confidence": 95
        }
    ]

    protect_sensitive_regions(
        "screenshots/screen.png",
        test_detections,
        "screenshots/protected_screen.png"
    )