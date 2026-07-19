import os
import shutil
import time
import pyautogui
import pytesseract
from PIL import Image


def _configure_tesseract() -> str:
    """Locate and configure the Tesseract executable for this Windows environment."""
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH", "")
            return candidate

    resolved = shutil.which("tesseract")
    if resolved:
        pytesseract.pytesseract.tesseract_cmd = resolved
        return resolved

    raise RuntimeError("Tesseract is not installed or could not be found on this machine.")


TESSERACT_EXE = _configure_tesseract()
print(f"Using Tesseract at: {TESSERACT_EXE}")


def run_hello_world_bot():
    print("=== STARTING BOT IN 3 SECONDS ===")
    print("Quick! Switch to your target window now.")
    time.sleep(3)

    sample_region = (0, 0, 1920, 1200)
    screenshot = pyautogui.screenshot(region=sample_region)
    screenshot.save("bot_vision_test.png")
    print("Captured screenshot saved as 'bot_vision_test.png'")

    print("Reading text from the region...")
    detected_text = pytesseract.image_to_string(screenshot).strip()
    print(f"OCR Result found: '\n\n{detected_text}\n\n'")

    center_x = 0 + (1920 // 2)
    center_y = 0 + (1200 // 2)

    print(f"Moving mouse to center position: ({center_x}, {center_y})")
    pyautogui.moveTo(center_x, center_y, duration=1.5)

    print("Clicking the screen...")
    pyautogui.click()
    time.sleep(0.5)

    message = "Bot action successful!\n"
    print(f"Typing text: '{message}'")
    pyautogui.write(message, interval=0.1)

    print("\n=== BOT RUN COMPLETE ===")


if __name__ == "__main__":
    run_hello_world_bot()
