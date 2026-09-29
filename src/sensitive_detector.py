import re
from typing import List, Dict, Tuple


# =========================================================
# REGEX PATTERNS
# =========================================================

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])\+?\d[\d\s().-]{8,}\d(?![A-Za-z0-9])"
)

API_KEY_PATTERN = re.compile(
    r"\b(?:sk|pk|api|key|token)[_-][A-Za-z0-9_-]{8,}\b",
    re.IGNORECASE
)

PASSWORD_PATTERN = re.compile(
    r"\b(?:password|passwd|pwd|pass)\s*[:=]\s*\S+",
    re.IGNORECASE
)

CARD_PATTERN = re.compile(
    r"(?<!\d)(?:\d[ -]*){13,19}(?!\d)"
)


# =========================================================
# LUHN VALIDATION
# =========================================================

def luhn_check(number: str) -> bool:
    """
    Validate a card number using the Luhn algorithm.
    """

    digits = re.sub(r"\D", "", number)

    if not 13 <= len(digits) <= 19:
        return False

    total = 0

    for i, digit in enumerate(digits[::-1]):

        n = int(digit)

        if i % 2 == 1:

            n *= 2

            if n > 9:
                n -= 9

        total += n

    return total % 10 == 0


# =========================================================
# BOX UTILITIES
# =========================================================

def normalize_box(
    box: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:

    x, y, w, h = map(int, box)

    return (
        x,
        y,
        max(0, w),
        max(0, h)
    )


def merge_boxes(
    boxes: List[Tuple[int, int, int, int]]
) -> Tuple[int, int, int, int]:
    """
    Merge multiple OCR boxes into one enclosing box.
    """

    if not boxes:
        return (0, 0, 0, 0)

    normalized = [
        normalize_box(box)
        for box in boxes
        if box is not None
    ]

    if not normalized:
        return (0, 0, 0, 0)

    x1 = min(
        x
        for x, y, w, h in normalized
    )

    y1 = min(
        y
        for x, y, w, h in normalized
    )

    x2 = max(
        x + w
        for x, y, w, h in normalized
    )

    y2 = max(
        y + h
        for x, y, w, h in normalized
    )

    return (
        x1,
        y1,
        x2 - x1,
        y2 - y1
    )


def box_for_match(
    token_box: Tuple[int, int, int, int],
    token_text: str,
    match_start: int,
    match_end: int
) -> Tuple[int, int, int, int]:
    """
    Estimate the sub-box corresponding to a regex match.
    """

    x, y, w, h = normalize_box(token_box)

    if not token_text:
        return token_box

    start_ratio = match_start / len(token_text)
    end_ratio = match_end / len(token_text)

    new_x = int(
        x + w * start_ratio
    )

    new_width = max(
        10,
        int(
            w * (end_ratio - start_ratio)
        )
    )

    return (
        new_x,
        y,
        new_width,
        h
    )


# =========================================================
# OCR LINE GROUPING
# =========================================================

def boxes_are_same_line(
    box1: Tuple[int, int, int, int],
    box2: Tuple[int, int, int, int]
) -> bool:
    """
    Determine whether two OCR boxes belong to approximately
    the same text line.
    """

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    center1 = y1 + h1 / 2
    center2 = y2 + h2 / 2

    tolerance = max(
        10,
        int(max(h1, h2) * 0.8)
    )

    return abs(center1 - center2) <= tolerance


def group_ocr_lines(
    ocr_results: List[Dict]
) -> List[Dict]:
    """
    Group OCR tokens that belong to the same visual line.

    This is important because Tesseract can return:

        Password:
        DemoPass123

    as two separate OCR regions.

    Likewise a card can become:

        4111
        1111
        1111
        1111

    instead of one OCR region.
    """

    valid_items = []

    for item in ocr_results:

        text = str(
            item.get("text", "")
        ).strip()

        box = item.get(
            "box",
            (0, 0, 0, 0)
        )

        if not text:
            continue

        if not box or len(box) != 4:
            continue

        box = normalize_box(box)

        if box[2] <= 0 or box[3] <= 0:
            continue

        valid_items.append({
            "text": text,
            "confidence": float(
                item.get("confidence", 0)
            ),
            "box": box
        })

    # Sort top-to-bottom, then left-to-right
    valid_items.sort(
        key=lambda item: (
            item["box"][1],
            item["box"][0]
        )
    )

    lines = []

    for item in valid_items:

        placed = False

        for line in lines:

            # Compare against the line's first/representative box
            if boxes_are_same_line(
                item["box"],
                line["reference_box"]
            ):

                line["items"].append(item)

                line["reference_box"] = merge_boxes(
                    [
                        x["box"]
                        for x in line["items"]
                    ]
                )

                placed = True
                break

        if not placed:

            lines.append({
                "items": [item],
                "reference_box": item["box"]
            })

    # Sort each line horizontally
    for line in lines:

        line["items"].sort(
            key=lambda item: item["box"][0]
        )

        # Rebuild merged box
        line["box"] = merge_boxes(
            [
                item["box"]
                for item in line["items"]
            ]
        )

        # Build text
        line["text"] = " ".join(
            item["text"]
            for item in line["items"]
        )

        # Average confidence
        if line["items"]:

            line["confidence"] = sum(
                item["confidence"]
                for item in line["items"]
            ) / len(line["items"])

        else:
            line["confidence"] = 0

    return lines


# =========================================================
# NORMALIZATION FOR SENSITIVE DATA
# =========================================================

def normalize_card_text(text: str) -> str:
    """
    Normalize OCR card text while preserving digit groups.
    """

    return re.sub(
        r"[^0-9 -]",
        "",
        text
    )


def clean_card_value(text: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# =========================================================
# DETECTION
# =========================================================

def detect_sensitive_information(
    ocr_results: List[Dict]
) -> List[Dict]:
    """
    Detect sensitive information from OCR results.

    Supports both:
    - single OCR token detections
    - multi-token / same-line detections
    """

    detections = []

    # -----------------------------------------------------
    # First process individual OCR tokens
    # -----------------------------------------------------

    for item in ocr_results:

        text = str(
            item.get("text", "")
        ).strip()

        if not text:
            continue

        confidence = float(
            item.get("confidence", 0)
        )

        token_box = normalize_box(
            tuple(
                item.get(
                    "box",
                    (0, 0, 0, 0)
                )
            )
        )

        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------

        for match in EMAIL_PATTERN.finditer(text):

            detections.append({
                "type": "EMAIL",
                "value": match.group(),
                "confidence": confidence,
                "box": box_for_match(
                    token_box,
                    text,
                    match.start(),
                    match.end()
                )
            })

        # -------------------------------------------------
        # API KEY
        # -------------------------------------------------

        for match in API_KEY_PATTERN.finditer(text):

            detections.append({
                "type": "API_KEY",
                "value": match.group(),
                "confidence": confidence,
                "box": box_for_match(
                    token_box,
                    text,
                    match.start(),
                    match.end()
                )
            })

        # -------------------------------------------------
        # PASSWORD
        # -------------------------------------------------

        for match in PASSWORD_PATTERN.finditer(text):

            detections.append({
                "type": "PASSWORD",
                "value": match.group(),
                "confidence": confidence,
                "box": box_for_match(
                    token_box,
                    text,
                    match.start(),
                    match.end()
                )
            })

        # -------------------------------------------------
        # CARD NUMBER
        # -------------------------------------------------

        for match in CARD_PATTERN.finditer(
            normalize_card_text(text)
        ):

            value = match.group()

            digits = re.sub(
                r"\D",
                "",
                value
            )

            if luhn_check(digits):

                detections.append({
                    "type": "CARD_NUMBER",
                    "value": clean_card_value(value),
                    "confidence": confidence,
                    "box": box_for_match(
                        token_box,
                        text,
                        match.start(),
                        match.end()
                    )
                })

        # -------------------------------------------------
        # PHONE
        # -------------------------------------------------

        for match in PHONE_PATTERN.finditer(text):

            value = match.group().strip()

            digit_count = len(
                re.sub(
                    r"\D",
                    "",
                    value
                )
            )

            if digit_count < 10:
                continue

            detections.append({
                "type": "PHONE",
                "value": value,
                "confidence": confidence,
                "box": box_for_match(
                    token_box,
                    text,
                    match.start(),
                    match.end()
                )
            })

    # =====================================================
    # MULTI-TOKEN / LINE-LEVEL DETECTION
    # =====================================================

    lines = group_ocr_lines(
        ocr_results
    )

    for line in lines:

        line_text = line["text"]
        line_box = line["box"]
        confidence = line["confidence"]

        if not line_text:
            continue

        # -------------------------------------------------
        # PASSWORD
        # -------------------------------------------------

        password_match = PASSWORD_PATTERN.search(
            line_text
        )

        if password_match:

            detections.append({
                "type": "PASSWORD",
                "value": password_match.group(),
                "confidence": confidence,
                "box": line_box
            })

        # -------------------------------------------------
        # CARD NUMBER
        # -------------------------------------------------

        card_text = normalize_card_text(
            line_text
        )

        for match in CARD_PATTERN.finditer(
            card_text
        ):

            value = match.group()

            digits = re.sub(
                r"\D",
                "",
                value
            )

            if luhn_check(digits):

                detections.append({
                    "type": "CARD_NUMBER",
                    "value": clean_card_value(value),
                    "confidence": confidence,
                    "box": line_box
                })

        # -------------------------------------------------
        # PHONE
        # -------------------------------------------------

        for match in PHONE_PATTERN.finditer(
            line_text
        ):

            value = match.group().strip()

            digit_count = len(
                re.sub(
                    r"\D",
                    "",
                    value
                )
            )

            if digit_count < 10:
                continue

            # Avoid classifying a card as a phone
            digits = re.sub(
                r"\D",
                "",
                value
            )

            if luhn_check(digits):
                continue

            detections.append({
                "type": "PHONE",
                "value": value,
                "confidence": confidence,
                "box": line_box
            })

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    return deduplicate_detections(
        detections
    )


# =========================================================
# BOX OVERLAP
# =========================================================

def boxes_overlap(
    box1: Tuple[int, int, int, int],
    box2: Tuple[int, int, int, int],
    threshold: float = 0.5
) -> bool:

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    ax1 = x1
    ay1 = y1
    ax2 = x1 + w1
    ay2 = y1 + h1

    bx1 = x2
    by1 = y2
    bx2 = x2 + w2
    by2 = y2 + h2

    ix1 = max(
        ax1,
        bx1
    )

    iy1 = max(
        ay1,
        by1
    )

    ix2 = min(
        ax2,
        bx2
    )

    iy2 = min(
        ay2,
        by2
    )

    if ix2 <= ix1 or iy2 <= iy1:
        return False

    intersection = (
        (ix2 - ix1) *
        (iy2 - iy1)
    )

    area1 = w1 * h1
    area2 = w2 * h2

    smaller_area = min(
        area1,
        area2
    )

    if smaller_area == 0:
        return False

    return (
        intersection / smaller_area
    ) >= threshold


# =========================================================
# VALUE COMPARISON
# =========================================================

def same_value_or_substring(
    value1: str,
    value2: str
) -> bool:

    v1 = re.sub(
        r"\s+",
        "",
        str(value1)
    ).lower()

    v2 = re.sub(
        r"\s+",
        "",
        str(value2)
    ).lower()

    return (
        v1 == v2
        or v1 in v2
        or v2 in v1
    )


# =========================================================
# DEDUPLICATION
# =========================================================

def deduplicate_detections(
    detections: List[Dict]
) -> List[Dict]:
    """
    Remove duplicate detections while preserving
    the strongest/fullest detection.
    """

    if not detections:
        return []

    # Highest confidence first
    detections = sorted(
        detections,
        key=lambda x: (
            x.get("confidence", 0),
            x["box"][2] * x["box"][3]
        ),
        reverse=True
    )

    unique = []

    for detection in detections:

        duplicate = False

        for existing in unique:

            if (
                detection["type"]
                != existing["type"]
            ):
                continue

            # Same / partial OCR value
            if same_value_or_substring(
                detection["value"],
                existing["value"]
            ):

                duplicate = True
                break

            # Same visual region
            if boxes_overlap(
                detection["box"],
                existing["box"],
                threshold=0.3
            ):

                duplicate = True
                break

        if not duplicate:

            unique.append(
                detection
            )

    return unique


# =========================================================
# COMPATIBILITY WRAPPER
# =========================================================

def detect_sensitive_data(
    ocr_results
):

    return detect_sensitive_information(
        ocr_results
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("       SENSITIVE DETECTOR TEST")
    print("=" * 50)

    # -----------------------------------------------------
    # Test 1: Normal single-token OCR
    # -----------------------------------------------------

    test_ocr = [

        {
            "text": "test@example.com",
            "confidence": 94.8,
            "box": (100, 100, 255, 27)
        },

        {
            "text": "+919876543210",
            "confidence": 94.8,
            "box": (100, 150, 255, 27)
        },

        {
            "text": "sk_test_1234567890abcdef",
            "confidence": 94.8,
            "box": (100, 200, 350, 27)
        },

        # Password split into two OCR boxes
        {
            "text": "Password:",
            "confidence": 91.5,
            "box": (100, 250, 100, 27)
        },

        {
            "text": "DemoPass123",
            "confidence": 91.5,
            "box": (210, 250, 150, 27)
        },

        # Card split into four OCR boxes
        {
            "text": "4111",
            "confidence": 96.0,
            "box": (100, 300, 70, 27)
        },

        {
            "text": "1111",
            "confidence": 96.0,
            "box": (180, 300, 70, 27)
        },

        {
            "text": "1111",
            "confidence": 96.0,
            "box": (260, 300, 70, 27)
        },

        {
            "text": "1111",
            "confidence": 96.0,
            "box": (340, 300, 70, 27)
        },

        # Duplicate API key
        {
            "text": "sk_test_123456789",
            "confidence": 51.0,
            "box": (100, 400, 250, 27)
        },

        {
            "text": "sk_test_1234567890abcdef",
            "confidence": 91.0,
            "box": (100, 400, 350, 27)
        }
    ]

    # -----------------------------------------------------
    # Run detection
    # -----------------------------------------------------

    results = detect_sensitive_information(
        test_ocr
    )

    print("\nDetected sensitive information:\n")

    for item in results:

        print(
            f"[{item['type']}] "
            f"{item['value']} "
            f"confidence={item['confidence']:.1f} "
            f"box={item['box']}"
        )

    print(
        f"\nTotal detections: "
        f"{len(results)}"
    )

    # -----------------------------------------------------
    # Expected types
    # -----------------------------------------------------

    detected_types = {
        item["type"]
        for item in results
    }

    expected_types = {
        "EMAIL",
        "PHONE",
        "API_KEY",
        "PASSWORD",
        "CARD_NUMBER"
    }

    print("\nExpected detection types:")

    for detection_type in sorted(
        expected_types
    ):

        status = (
            "PASS"
            if detection_type in detected_types
            else "FAIL"
        )

        print(
            f"{detection_type:15} {status}"
        )

    # -----------------------------------------------------
    # Compatibility test
    # -----------------------------------------------------

    compatibility_results = detect_sensitive_data(
        test_ocr
    )

    print(
        "\nCompatibility function test:"
    )

    if len(results) == len(
        compatibility_results
    ):
        print("PASS")
    else:
        print("FAIL")

    print("\n" + "=" * 50)
    print("            TEST COMPLETE")
    print("=" * 50)