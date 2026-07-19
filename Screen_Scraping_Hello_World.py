import time
import pyautogui
import pytesseract
from PIL import Image

# WINDOWS USERS: Change this to your actual Tesseract installation path
# pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

def run_hello_world_bot():
    print("=== STARTING BOT IN 3 SECONDS ===")
    print("Quick! Switch to your target window now.")
    time.sleep(3)

    # 1. SCREEN SCRAPING (Capture top-left corner of your primary screen)
    # Box parameters: (left_x, toy_y, width, height)
    sample_region = (0, 0, 1920, 1200)
    screenshot = pyautogui.screenshot(region=sample_region)

    # Save image locally so you can physically see what the bot looked at
    screenshot.save("bot_vision_test.png")
    print("Captured screenshot saved as 'bot_vision_test.png'")

    # 2. OCR (Read text from the screen region)
    print("Reading text from the region...")
    detected_text = pytesseract.image_to_string(screenshot).strip()
    print(f"OCR Result found: '{detected_text}'")

    # 3. MOUSE ACTION (Move smoothly to the center of our region)
    # Center calculation: left + (width / 2), top + (height / 2)
    center_x = 0 + (1920 // 2)
    center_y = 0 + (1200 // 2)

    print(f"Moving mouse to center position: ({center_x}, {center_y})")
    pyautogui.moveTo(center_x, center_y, duration=1.5)
    # Takes 1.5 seconds to glide

    print("Clicking the screen...")
    pyautogui.click()
    time.sleep(0.5)
    # Quick pause after click

    # 4. KEYBOARD ACTION (Type a response)
    message = "Bot action successful!"
    print(f"Typing text: '{message}'")
    pyautogui.write(message, interval=0.1)
    # Type with a 100ms delay per character

    print("\n=== BOT RUN COMPLETE ===")

if __name__ == "__main__":
    run_hello_world_bot()
