# =========================================================
# SNAPSHIELD AI
# Real-Time On-Device Privacy Monitor
# =========================================================

import os
import time

import streamlit as st

from screen_capture import capture_screen
from ocr_engine import extract_text_with_boxes
from sensitive_detector import detect_sensitive_information
from privacy_engine import calculate_risk
from protector import protect_sensitive_regions
from viewer_detector import detect_viewers


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

SCREENSHOT_DIR = os.path.join(
    BASE_DIR,
    "screenshots"
)

SCREEN_PATH = os.path.join(
    SCREENSHOT_DIR,
    "latest_screen.png"
)

PROTECTED_PATH = os.path.join(
    SCREENSHOT_DIR,
    "protected_screen.png"
)

os.makedirs(
    SCREENSHOT_DIR,
    exist_ok=True
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SnapShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main background */

    .stApp {
        background:
            linear-gradient(
                135deg,
                #0f172a 0%,
                #111827 50%,
                #020617 100%
            );
    }


    /* Main content */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }


    /* Header */

    .main-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 16px;
        margin-top: 4px;
        margin-bottom: 25px;
    }


    /* Cards */

    .dashboard-card {
        padding: 20px;
        border-radius: 16px;
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(148, 163, 184, 0.18);
        margin-bottom: 18px;
    }


    /* Metric cards */

    .metric-card {
        padding: 18px;
        border-radius: 14px;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.18);
        min-height: 120px;
    }

    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 27px;
        font-weight: 800;
    }


    /* Risk levels */

    .risk-safe {
        color: #22c55e;
    }

    .risk-warning {
        color: #f59e0b;
    }

    .risk-high {
        color: #ef4444;
    }


    /* Detection cards */

    .detection-card {
        padding: 14px 16px;
        border-radius: 12px;
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.16);
        margin-bottom: 10px;
    }


    /* Section titles */

    .section-title {
        font-size: 22px;
        font-weight: 750;
        margin-top: 10px;
        margin-bottom: 14px;
    }


    /* Footer */

    .footer {
        text-align: center;
        color: #94a3b8;
        padding-top: 20px;
        padding-bottom: 10px;
    }


    /* Countdown */

    .countdown-box {
        padding: 24px;
        margin: 15px 0;
        border-radius: 16px;
        text-align: center;
        background:
            rgba(30, 41, 59, 0.85);
        border:
            1px solid rgba(148, 163, 184, 0.25);
    }

    .countdown-number {
        font-size: 58px;
        font-weight: 900;
        margin: 8px 0;
    }

    .countdown-title {
        font-size: 20px;
        font-weight: 700;
    }

    .countdown-text {
        color: #94a3b8;
        font-size: 14px;
    }


    /* Streamlit buttons */

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
        min-height: 45px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "last_scan" not in st.session_state:
    st.session_state["last_scan"] = None

if "scan_number" not in st.session_state:
    st.session_state["scan_number"] = 0

if "scan_interval" not in st.session_state:
    st.session_state["scan_interval"] = 2

if "automatic_protection" not in st.session_state:
    st.session_state["automatic_protection"] = True

if "viewer_detection_enabled" not in st.session_state:
    st.session_state["viewer_detection_enabled"] = True


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_risk_class(level):

    if level == "HIGH RISK":
        return "risk-high"

    if level == "WARNING":
        return "risk-warning"

    return "risk-safe"


def get_risk_icon(level):

    if level == "HIGH RISK":
        return "🔴"

    if level == "WARNING":
        return "🟠"

    return "🟢"


def mask_sensitive_text(text):

    if not text:
        return ""

    text = str(text)

    if len(text) <= 6:
        return "••••••"

    return (
        text[:2]
        + "••••••"
        + text[-2:]
    )


def get_viewer_count(viewer_result):

    if isinstance(viewer_result, dict):

        return int(
            viewer_result.get(
                "viewer_count",
                0
            )
        )

    try:
        return int(viewer_result)

    except Exception:
        return 0


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size:25px;
            font-weight:800;
            margin-bottom:5px;
        ">
            🛡️ SnapShield AI
        </div>

        <div style="
            color:#94a3b8;
            font-size:13px;
            margin-bottom:25px;
        ">
            Real-Time On-Device Privacy Monitor
        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # MONITORING
    # -----------------------------------------------------

    st.markdown(
        "### ⚙️ Monitoring"
    )

    st.caption(
        "Configure how SnapShield analyzes your screen."
    )


    scan_interval = st.slider(
        "Scan interval",
        min_value=2,
        max_value=10,
        value=st.session_state["scan_interval"],
        step=1
    )

    st.session_state["scan_interval"] = scan_interval


    automatic_protection = st.toggle(
        "Automatic protection",
        value=st.session_state[
            "automatic_protection"
        ]
    )

    st.session_state[
        "automatic_protection"
    ] = automatic_protection


    viewer_detection_enabled = st.toggle(
        "Viewer detection",
        value=st.session_state[
            "viewer_detection_enabled"
        ]
    )

    st.session_state[
        "viewer_detection_enabled"
    ] = viewer_detection_enabled


    st.divider()


    # -----------------------------------------------------
    # DETECTION MODULES
    # -----------------------------------------------------

    st.markdown(
        "### 🔎 Detection modules"
    )

    st.checkbox(
        "✉️ Email",
        value=True,
        disabled=True
    )

    st.checkbox(
        "📱 Phone",
        value=True,
        disabled=True
    )

    st.checkbox(
        "💳 Card Number",
        value=True,
        disabled=True
    )

    st.checkbox(
        "🔑 API Key",
        value=True,
        disabled=True
    )

    st.checkbox(
        "🔒 Password",
        value=True,
        disabled=True
    )

    st.checkbox(
        "👤 Viewer Detection",
        value=True,
        disabled=True
    )


    st.divider()


    st.caption(
        f"Configured scan interval: {scan_interval}s"
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    """
    <div class="main-title">
        🛡️ SnapShield AI
    </div>

    <div class="subtitle">
        Real-Time On-Device Privacy Monitor
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TOP CONTROL CARD
# =========================================================

control_col1, control_col2 = st.columns(
    [3, 1]
)


with control_col1:

    st.markdown(
        """
        <div class="dashboard-card">

        <div style="
            font-size:18px;
            font-weight:700;
        ">
            🔍 Screen Privacy Scanner
        </div>

        <div style="
            color:#94a3b8;
            font-size:14px;
            margin-top:6px;
        ">
            Capture your current screen and detect
            sensitive information and potential viewers.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with control_col2:

    st.write("")

    scan_clicked = st.button(
        "🔍 Scan Screen",
        use_container_width=True,
        type="primary"
    )


# =========================================================
# SCAN PIPELINE
# =========================================================

if scan_clicked:

    countdown_placeholder = st.empty()


    # -----------------------------------------------------
    # COUNTDOWN
    # -----------------------------------------------------

    for i in range(5, 0, -1):

        countdown_placeholder.markdown(
            f"""
            <div class="countdown-box">

                <div class="countdown-title">
                    📸 Preparing SnapShield Scan
                </div>

                <div class="countdown-number">
                    {i}
                </div>

                <div class="countdown-text">
                    Switch to the screen or browser tab
                    you want SnapShield to analyze.
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        time.sleep(1)


    # -----------------------------------------------------
    # CAPTURE MESSAGE
    # -----------------------------------------------------

    countdown_placeholder.markdown(
        """
        <div class="countdown-box">

            <div class="countdown-title">
                🛡️ CAPTURING SCREEN...
            </div>

            <div class="countdown-text">
                SnapShield is analyzing the current display.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # -----------------------------------------------------
    # 1. SCREEN CAPTURE
    # -----------------------------------------------------

    try:

        capture_screen(
            SCREEN_PATH
        )

    except Exception as e:

        countdown_placeholder.empty()

        st.error(
            f"❌ Screen capture failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # 2. OCR
    # -----------------------------------------------------

    try:

        ocr_results = extract_text_with_boxes(
            SCREEN_PATH
        )

    except Exception as e:

        countdown_placeholder.empty()

        st.error(
            f"❌ OCR failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # 3. SENSITIVE INFORMATION
    # -----------------------------------------------------

    try:

        detections = detect_sensitive_information(
            ocr_results
        )

    except Exception as e:

        countdown_placeholder.empty()

        st.error(
            f"❌ Sensitive-data detection failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # 4. VIEWER DETECTION
    # -----------------------------------------------------

    viewer_count = 0

    if viewer_detection_enabled:

        try:

            viewer_result = detect_viewers()

            viewer_count = get_viewer_count(
                viewer_result
            )

        except Exception as e:

            st.warning(
                f"⚠️ Viewer detection unavailable: {e}"
            )

            viewer_count = 0


    # -----------------------------------------------------
    # 5. RISK ENGINE
    # -----------------------------------------------------

    try:

        risk = calculate_risk(
            detections,
            viewer_count=viewer_count
        )

    except Exception as e:

        countdown_placeholder.empty()

        st.error(
            f"❌ Risk calculation failed: {e}"
        )

        st.stop()


    # -----------------------------------------------------
    # 6. PROTECTION
    # -----------------------------------------------------

    try:

        protect_sensitive_regions(
            SCREEN_PATH,
            detections,
            PROTECTED_PATH
        )

    except Exception as e:

        st.warning(
            f"⚠️ Protection image could not be generated: {e}"
        )


    # -----------------------------------------------------
    # 7. UPDATE SCAN NUMBER
    # -----------------------------------------------------

    st.session_state["scan_number"] += 1


    # -----------------------------------------------------
    # 8. SAVE RESULT
    # -----------------------------------------------------

    st.session_state["last_scan"] = {

        "ocr_results": ocr_results,

        "detections": detections,

        "viewer_count": viewer_count,

        "risk": risk,

        "screen_path": SCREEN_PATH,

        "protected_path": PROTECTED_PATH,

        "timestamp": time.strftime(
            "%H:%M:%S"
        ),

        "scan_number": st.session_state[
            "scan_number"
        ]
    }


    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------

    countdown_placeholder.empty()

    st.success(
        "✅ Screen captured and analyzed successfully."
    )

    st.rerun()


# =========================================================
# DISPLAY RESULTS
# =========================================================

result = st.session_state["last_scan"]


if result is not None:

    risk = result["risk"]

    detections = result["detections"]

    viewer_count = result["viewer_count"]

    risk_level = risk["level"]

    risk_score = risk["score"]

    ocr_results = result["ocr_results"]


    # =====================================================
    # METRIC CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)


    # -----------------------------------------------------
    # RISK
    # -----------------------------------------------------

    with col1:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Risk Level
                </div>

                <div class="metric-value {get_risk_class(risk_level)}">
                    {get_risk_icon(risk_level)}
                    {risk_level}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    with col2:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Privacy Risk Score
                </div>

                <div class="metric-value">
                    {risk_score}/100
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # -----------------------------------------------------
    # VIEWERS
    # -----------------------------------------------------

    with col3:

        viewer_icon = (
            "⚠️"
            if viewer_count >= 2
            else "👤"
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Detected Viewers
                </div>

                <div class="metric-value">
                    {viewer_icon} {viewer_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    # -----------------------------------------------------
    # SENSITIVE ITEMS
    # -----------------------------------------------------

    with col4:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    Sensitive Items
                </div>

                <div class="metric-value">
                    🔐 {len(detections)}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


    st.write("")


    # =====================================================
    # RISK WARNINGS
    # =====================================================

    if risk_level == "HIGH RISK":

        st.error(
            "🔴 HIGH RISK — Sensitive information detected. "
            "Review the protected screen before continuing."
        )

    elif risk_level == "WARNING":

        st.warning(
            "⚠️ PRIVACY WARNING — Review the detected "
            "information before continuing."
        )

    else:

        st.success(
            "🟢 SAFE — No significant privacy risk detected."
        )


    # -----------------------------------------------------
    # VIEWER WARNING
    # -----------------------------------------------------

    if viewer_count >= 2:

        st.warning(
            "👀 POTENTIAL UNAUTHORIZED VIEWER DETECTED — "
            "Multiple people are visible to the camera."
        )


    # =====================================================
    # LAST SCAN INFO
    # =====================================================

    st.caption(
        f"Last scan: {result['timestamp']} "
        f"• Scan #{result['scan_number']} "
        f"• OCR regions analyzed: {len(ocr_results)}"
    )


    # =====================================================
    # SENSITIVE INFORMATION
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            🔐 Sensitive Information
        </div>
        """,
        unsafe_allow_html=True
    )


    if detections:

        for item in detections:

            item_type = item.get(
                "type",
                "UNKNOWN"
            )

            text = item.get(
                "text",
                item.get(
                    "value",
                    ""
                )
            )

            confidence = item.get(
                "confidence",
                0
            )

            box = item.get(
                "box",
                None
            )


            # Don't expose the complete sensitive value
            # in the dashboard.

            masked_value = mask_sensitive_text(
                text
            )


            st.markdown(
                f"""
                <div class="detection-card">

                    <div style="
                        font-size:16px;
                        font-weight:700;
                    ">
                        🔒 {item_type}
                    </div>

                    <div style="
                        margin-top:5px;
                        font-family:monospace;
                    ">
                        {masked_value}
                    </div>

                    <div style="
                        margin-top:5px;
                        color:#94a3b8;
                        font-size:12px;
                    ">
                        Confidence: {confidence:.1f}%
                        {" • Region: " + str(box) if box else ""}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    else:

        st.info(
            "No sensitive information detected."
        )


    # =====================================================
    # SCREEN ANALYSIS
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            🖥️ Screen Analysis
        </div>
        """,
        unsafe_allow_html=True
    )


    screen_col1, screen_col2 = st.columns(2)


    # -----------------------------------------------------
    # ORIGINAL
    # -----------------------------------------------------

    with screen_col1:

        st.markdown(
            "### Original Screen"
        )

        if os.path.exists(
            result["screen_path"]
        ):

            st.image(
                result["screen_path"],
                use_container_width=True
            )

        else:

            st.warning(
                "Original screenshot not found."
            )


    # -----------------------------------------------------
    # PROTECTED
    # -----------------------------------------------------

    with screen_col2:

        st.markdown(
            "### 🛡️ Protected Screen"
        )

        if os.path.exists(
            result["protected_path"]
        ):

            st.image(
                result["protected_path"],
                use_container_width=True
            )

        else:

            st.info(
                "No protected screenshot available."
            )


    # =====================================================
    # ANALYSIS SUMMARY
    # =====================================================

    st.markdown(
        """
        <div class="section-title">
            📊 Analysis Summary
        </div>
        """,
        unsafe_allow_html=True
    )


    summary_col1, summary_col2, summary_col3 = st.columns(3)


    with summary_col1:

        st.metric(
            "OCR Regions",
            len(ocr_results)
        )


    with summary_col2:

        st.metric(
            "Sensitive Regions",
            len(detections)
        )


    with summary_col3:

        st.metric(
            "Viewers",
            viewer_count
        )


# =========================================================
# INITIAL STATE
# =========================================================

else:

    st.markdown(
        """
        <div class="dashboard-card"
             style="text-align:center;padding:50px 20px;">

            <div style="
                font-size:50px;
                margin-bottom:15px;
            ">
                🛡️
            </div>

            <div style="
                font-size:24px;
                font-weight:800;
            ">
                SnapShield is ready
            </div>

            <div style="
                color:#94a3b8;
                margin-top:8px;
            ">
                Click <b>Scan Screen</b> to analyze your
                current display for privacy risks.
            </div>

            <div style="
                color:#64748b;
                margin-top:15px;
                font-size:13px;
            ">
                You will have 5 seconds to switch to the
                screen you want to analyze.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div class="footer">

        <div style="
            font-size:17px;
            font-weight:700;
            color:#e2e8f0;
        ">
            🛡️ SnapShield AI
        </div>

        <div style="margin-top:5px;">
            Privacy-first AI for Snapdragon-powered PCs
        </div>

        <div style="
            margin-top:5px;
            font-size:12px;
        ">
            Local-first architecture · Real-time privacy monitoring
        </div>

    </div>
    """,
    unsafe_allow_html=True
)