import time

from .screen_capture import capture_screen
from .ocr_engine import extract_text_with_boxes
from .sensitive_detector import detect_sensitive_data
from .privacy_engine import calculate_risk
from .protector import protect_sensitive_regions
from .viewer_detector import detect_viewers


def run_monitor(interval=5, max_scans=10):
    print("\n========================================")
    print("        SNAPSHIELD AI MONITOR")
    print("========================================")
    print(f"Scan interval : {interval} seconds")
    print(f"Maximum scans : {max_scans}")
    print("Press Ctrl+C to stop.\n")

    try:
        for scan_number in range(1, max_scans + 1):

            print("\n========================================")
            print(f"SNAPSHIELD SCAN #{scan_number}")
            print("========================================")

            # --------------------------------------------------
            # 1. Capture screen
            # --------------------------------------------------
            screen_path = "screenshots/monitor_screen.png"
            protected_path = "screenshots/protected_screen.png"

            capture_screen(screen_path)

            # --------------------------------------------------
            # 2. OCR
            # --------------------------------------------------
            ocr_results = extract_text_with_boxes(screen_path)

            print(f"\nOCR text regions : {len(ocr_results)}")

            # --------------------------------------------------
            # 3. Detect sensitive information
            # --------------------------------------------------
            detections = detect_sensitive_data(ocr_results)

            print(f"Sensitive detections : {len(detections)}")

            if detections:
                for item in detections:
                    print(
                        f"  - {item['type']}: "
                        f"{item['text']} "
                        f"(confidence={item['confidence']:.1f})"
                    )
            else:
                print("  No sensitive information detected.")

            # --------------------------------------------------
            # 4. Detect visible viewers
            # --------------------------------------------------
            try:
                viewer_result = detect_viewers()

                viewer_count = viewer_result["viewer_count"]
                viewer_status = viewer_result["status"]

            except RuntimeError as e:
                print(f"\n⚠️ Webcam unavailable: {e}")

                # Continue screen-only monitoring
                viewer_count = 1
                viewer_status = "WEBCAM UNAVAILABLE"

            print(f"\nViewers : {viewer_count}")
            print(f"Viewer status : {viewer_status}")

            # --------------------------------------------------
            # 5. Calculate combined privacy risk
            # --------------------------------------------------
            risk = calculate_risk(
                detections,
                viewer_count=viewer_count
            )

            print("\n----------------------------------------")
            print("PRIVACY ASSESSMENT")
            print("----------------------------------------")
            print(f"Risk Level   : {risk['level']}")
            print(f"Risk Score   : {risk['score']}/100")
            print(f"Data Score   : {risk['raw_score']}")
            print(f"Viewer Risk  : {risk['viewer_risk']}")
            print(f"Viewer Count : {risk['viewer_count']}")

            if risk["potential_unauthorized_viewer"]:
                print("⚠️ POTENTIAL UNAUTHORIZED VIEWER DETECTED")

            # --------------------------------------------------
            # 6. Protect sensitive regions
            # --------------------------------------------------
            if detections:
                protect_sensitive_regions(
                    screen_path,
                    detections,
                    protected_path
                )

                print("🛡️ Sensitive regions protected.")
            else:
                print("No sensitive regions require protection.")

            print("----------------------------------------")

            # --------------------------------------------------
            # 7. Wait before next scan
            # --------------------------------------------------
            if scan_number < max_scans:
                print(f"\nNext scan in {interval} seconds...")

                for remaining in range(interval, 0, -1):
                    print(
                        f"\rNext scan in {remaining} seconds...",
                        end="",
                        flush=True
                    )
                    time.sleep(1)

                print()

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")

    print("\n========================================")
    print("       SNAPSHIELD MONITOR STOPPED")
    print("========================================")


if __name__ == "__main__":
    run_monitor()