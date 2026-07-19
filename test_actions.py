import time
import pyautogui
import pytesseract
from bot_actions import (
    REGION_DEFINITIONS,
    TESSERACT_CMD,
    get_window_position,
    _safe_move_to,
    _humanized_pause,
    click_region_center,
    safe_type_string,
    extract_text_from_region,
)


def print_window_info() -> None:
    # Print the coordinates and size of the detected game window.
    left, top, width, height = get_window_position()
    print("Detected game window position and size:")
    print(f"  left={left}, top={top}, width={width}, height={height}")


def test_ocr_region(region_name: str) -> None:
    # Perform OCR on a selected region and print the raw text result.
    print(f"Testing OCR on region '{region_name}'...")
    text = extract_text_from_region(region_name)
    print(f"OCR result for {region_name}: '{text}'")


def test_click_region(region_name: str) -> None:
    # Click the center of the selected UI region after a short countdown.
    left, top, _, _ = get_window_position()
    x, y, w, h = REGION_DEFINITIONS[region_name]
    center_x = left + x + w // 2
    center_y = top + y + h // 2
    print(f"Clicking center of region '{region_name}' at ({center_x}, {center_y}) in 3 seconds...")
    time.sleep(3)
    _safe_move_to(center_x, center_y)
    pyautogui.click()
    _humanized_pause(0.5, 1.0)
    print("Click completed.")


def test_text_entry(region_name: str, text: str) -> None:
    # Focus an input region and inject sample text safely.
    print(f"Testing text entry into region '{region_name}'...")
    center = click_region_center(region_name)
    print(f"Clicked input field at {center}. Typing now...")
    safe_type_string(text)
    print(f"Typed: {text}")


def main() -> None:
    # Run the helper test script for window detection, OCR, mouse clicks, and text injection.
    print("=== Critical Ops Bot Action Test ===")
    print(f"Tesseract command path: {TESSERACT_CMD}")
    print("Make sure the game window is visible and active on one monitor.")
    input("Press Enter to detect the game window and continue...")

    print_window_info()

    print("Available test regions:")
    for key in REGION_DEFINITIONS.keys():
        print(f"  - {key}")

    region_name = input("Enter a region name to OCR test: ").strip()
    if region_name in REGION_DEFINITIONS:
        test_ocr_region(region_name)
    else:
        print(f"Region '{region_name}' not found.")

    if input("Run click test on a region? (y/n): ").strip().lower() == "y":
        region_name = input("Enter a region name to click: ").strip()
        if region_name in REGION_DEFINITIONS:
            test_click_region(region_name)
        else:
            print(f"Region '{region_name}' not found.")

    if input("Run text entry test on an input region? (y/n): ").strip().lower() == "y":
        region_name = input("Enter the input field region name: ").strip()
        if region_name in REGION_DEFINITIONS:
            test_text = input("Enter the sample text to inject: ").strip()
            test_text_entry(region_name, test_text)
        else:
            print(f"Region '{region_name}' not found.")

    print("Test script complete. Review the results, then calibrate the region coordinates in bot_actions.py.")


if __name__ == "__main__":
    main()
