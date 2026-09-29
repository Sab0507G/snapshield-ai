import os
import sys
import time
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from screen_capture import capture_screen
from ocr_engine import extract_text_with_boxes
from sensitive_detector import detect_sensitive_data
from privacy_engine import calculate_risk
from protector import protect_sensitive_regions


SCREENSHOT_PATH = "screenshots/screen.png"
PROTECTED_PATH = "screenshots/protected_screen.png"


st.set_page_config(
    page_title="SnapShield AI",
    page_icon="🛡️",
    layout="wide"
)


# -----------------------------
# Session state
# -----------------------------

if "scanned" not in st.session_state:
    st.session_state.scanned = False

if "detections" not in st.session_state:
    st.session_state.detections = []

if "risk" not in st.session_state:
    st.session_state.risk = {
        "level": "SAFE",
        "score": 0,
        "detections": []
    }


# -----------------------------
# Header
# -----------------------------

st.title("🛡️ SnapShield AI")
st.caption("On-Device Privacy Protection")

st.divider()


# -----------------------------
# Scan button
# -----------------------------

st.subheader("Screen Privacy Scanner")

st.info(
    "Click **Start Scan**, then switch to the window you want "
    "SnapShield to inspect. The screen will be captured automatically "
    "after the countdown."
)


if st.button(
    "🔍 Start Privacy Scan",
    type="primary",
    use_container_width=True
):

    countdown_placeholder = st.empty()

    # -------------------------
    # Countdown
    # -------------------------

    for remaining in range(10, 0, -1):

        countdown_placeholder.warning(
            f"🛡️ **Capture in {remaining} seconds**\n\n"
            "Switch to the screen you want SnapShield to protect."
        )

        time.sleep(1)

    countdown_placeholder.success(
        "📸 **Capturing screen...**"
    )

    # -------------------------
    # Capture
    # -------------------------

    with st.spinner("Capturing screen..."):
        capture_screen(SCREENSHOT_PATH)

    # -------------------------
    # OCR
    # -------------------------

    with st.spinner("Reading screen content with OCR..."):
        ocr_results = extract_text_with_boxes(
            SCREENSHOT_PATH
        )

    # -------------------------
    # Sensitive detection
    # -------------------------

    with st.spinner("Scanning for sensitive information..."):
        detections = detect_sensitive_data(
            ocr_results
        )

    # -------------------------
    # Risk calculation
    # -------------------------

    with st.spinner("Calculating privacy risk..."):
        risk = calculate_risk(
            detections
        )

    # -------------------------
    # Protection
    # -------------------------

    if detections:

        with st.spinner("Protecting sensitive regions..."):

            protect_sensitive_regions(
                SCREENSHOT_PATH,
                detections,
                PROTECTED_PATH
            )

    # -------------------------
    # Save results
    # -------------------------

    st.session_state.scanned = True
    st.session_state.detections = detections
    st.session_state.risk = risk

    countdown_placeholder.empty()

    st.rerun()


# -----------------------------
# Results
# -----------------------------

if st.session_state.scanned:

    risk = st.session_state.risk
    detections = st.session_state.detections

    st.divider()

    st.subheader("🔐 Privacy Risk")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Risk Score",
            f"{risk['score']}/100"
        )

    with col2:
        st.metric(
            "Risk Level",
            risk["level"]
        )

    with col3:
        st.metric(
            "Sensitive Regions",
            len(detections)
        )

    st.divider()

    # -------------------------
    # Detection results
    # -------------------------

    st.subheader(
        "🚨 Detected Sensitive Information"
    )

    if detections:

        for item in detections:

            detection_type = item["type"]
            confidence = item["confidence"]

            st.write(
                f"🔴 **{detection_type}** "
                f"— {confidence:.1f}% confidence"
            )

    else:

        st.success(
            "✅ No sensitive information detected."
        )

    st.divider()

    # -------------------------
    # Protected screen
    # -------------------------

    if os.path.exists(PROTECTED_PATH):

        st.subheader(
            "🛡️ Protected Screen"
        )

        st.image(
            PROTECTED_PATH,
            caption="Sensitive regions automatically protected",
            use_container_width=True
        )

    # -------------------------
    # Original screen
    # -------------------------

    if os.path.exists(SCREENSHOT_PATH):

        st.subheader(
            "🖥️ Original Screen"
        )

        with st.expander(
            "View original capture"
        ):

            st.image(
                SCREENSHOT_PATH,
                use_container_width=True
            )

    # -------------------------
    # Scan again
    # -------------------------

    st.divider()

    if st.button(
        "🔄 Scan Another Screen",
        use_container_width=True
    ):

        st.session_state.scanned = False
        st.session_state.detections = []
        st.session_state.risk = {
            "level": "SAFE",
            "score": 0,
            "detections": []
        }

        st.rerun()