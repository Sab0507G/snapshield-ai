def calculate_risk(detections, viewer_count=1):
    """
    Calculate privacy risk using:
    1. Sensitive information detected on the screen
    2. Number of visible webcam viewers

    Args:
        detections: List of sensitive-information detections.
        viewer_count: Number of visible faces detected by webcam.

    Returns:
        Dictionary containing the complete privacy assessment.
    """

    # Risk weights for different types of sensitive information
    weights = {
        "EMAIL": 10,
        "PHONE": 10,
        "CARD_NUMBER": 30,
        "PASSWORD": 40,
        "API_KEY": 50,
    }

    # ---------------------------------------------------------
    # 1. Calculate risk from sensitive screen information
    # ---------------------------------------------------------

    raw_score = sum(
        weights.get(item["type"], 10)
        for item in detections
    )

    # ---------------------------------------------------------
    # 2. Calculate additional risk from multiple viewers
    # ---------------------------------------------------------

    viewer_risk = 0

    if viewer_count >= 2:
        viewer_risk = 20

    # Combined score
    total_score = min(raw_score + viewer_risk, 100)

    # ---------------------------------------------------------
    # 3. Determine overall privacy risk level
    # ---------------------------------------------------------

    # Multiple viewers alone should trigger a warning.
    if viewer_count >= 2 and not detections:
        level = "WARNING"

    elif total_score >= 70:
        level = "HIGH RISK"

    elif total_score >= 30:
        level = "WARNING"

    else:
        level = "SAFE"

    # ---------------------------------------------------------
    # 4. Return complete risk assessment
    # ---------------------------------------------------------

    return {
        "level": level,
        "score": total_score,
        "raw_score": raw_score,
        "viewer_risk": viewer_risk,
        "viewer_count": viewer_count,
        "potential_unauthorized_viewer": viewer_count >= 2,
        "detections": detections,
    }


# -------------------------------------------------------------
# Simple standalone test
# -------------------------------------------------------------

if __name__ == "__main__":

    print("\n======================================")
    print("       SNAPSHIELD RISK ENGINE")
    print("======================================")

    # Test 1: Normal screen + one viewer
    result = calculate_risk([], 1)

    print("\nTest 1: Normal screen + 1 viewer")
    print(f"Risk Level : {result['level']}")
    print(f"Risk Score : {result['score']}/100")
    print(f"Viewer Count : {result['viewer_count']}")

    # Test 2: Normal screen + two viewers
    result = calculate_risk([], 2)

    print("\nTest 2: Normal screen + 2 viewers")
    print(f"Risk Level : {result['level']}")
    print(f"Risk Score : {result['score']}/100")
    print(f"Viewer Count : {result['viewer_count']}")
    print(
        f"Unauthorized Viewer Warning : "
        f"{result['potential_unauthorized_viewer']}"
    )

    # Test 3: API key + one viewer
    result = calculate_risk(
        [{"type": "API_KEY"}],
        1
    )

    print("\nTest 3: API key + 1 viewer")
    print(f"Risk Level : {result['level']}")
    print(f"Risk Score : {result['score']}/100")

    # Test 4: API key + two viewers
    result = calculate_risk(
        [{"type": "API_KEY"}],
        2
    )

    print("\nTest 4: API key + 2 viewers")
    print(f"Risk Level : {result['level']}")
    print(f"Risk Score : {result['score']}/100")
    print(
        f"Unauthorized Viewer Warning : "
        f"{result['potential_unauthorized_viewer']}"
    )

    print("\n======================================")
    print("             TEST COMPLETE")
    print("======================================")