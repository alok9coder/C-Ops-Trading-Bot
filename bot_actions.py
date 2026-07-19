import os
import random
import time
from dataclasses import dataclass
from typing import Tuple

import cv2
import easyocr
import numpy as np
import pyautogui
import pytesseract

# TODO: Replace these placeholder coordinates with calibrated values from the Critical Ops window.
PLACEHOLDER_WINDOW_TITLE = "Critical Ops"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Use the known standard Tesseract install path if available.
if os.path.isfile(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Region definitions are relative to the top-left corner of the game window.
REGION_DEFINITIONS = {
    "catalog_row_1": (50, 220, 1340, 100),
    "catalog_row_height": 90,
    "catalog_row_width": 1340,
    "price_column": (980, 10, 200, 70),
    "volume_column": (820, 10, 140, 70),
    "detail_lowest_sell": (980, 320, 180, 60),
    "detail_highest_buy": (980, 420, 180, 60),
    "bid_input_field": (930, 760, 260, 60),
    "confirm_bid_button": (1230, 820),
    "catalog_back_button": (120, 120),
    "by_type_button": (430, 120),
}

# OCR engine instance for reading English numerals/text from the UI.
OCR_READER = easyocr.Reader(["en"], gpu=False)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


@dataclass
class CatalogRow:
    # Holds a discovered skin entry from the listing screen.
    skin_name: str
    row_center: Tuple[int, int]
    price_value: int
    volume_value: int


def _humanized_pause(min_seconds: float = 0.25, max_seconds: float = 0.65) -> None:
    # Sleep for a randomized short duration so actions appear more human-like.
    time.sleep(random.uniform(min_seconds, max_seconds))


def _jitter_point(x: int, y: int, radius: int = 5) -> Tuple[int, int]:
    # Add a small random offset to the target coordinates.
    return x + random.randint(-radius, radius), y + random.randint(-radius, radius)


def _safe_move_to(x: int, y: int) -> None:
    # Move the mouse smoothly and with jitter to mimic a real user.
    jittered = _jitter_point(x, y)
    duration = random.uniform(0.18, 0.42)
    pyautogui.moveTo(jittered[0], jittered[1], duration=duration)


def locate_game_window() -> pyautogui.Window:
    # Find the Critical Ops window by its title and activate it.
    windows = pyautogui.getWindowsWithTitle(PLACEHOLDER_WINDOW_TITLE)
    if not windows:
        raise RuntimeError(f"Game window not found. Make sure the title contains '{PLACEHOLDER_WINDOW_TITLE}'.")
    window = windows[0]
    if not window.isActive:
        window.activate()
        _humanized_pause(0.5, 1.0)
    return window


def get_window_position() -> Tuple[int, int, int, int]:
    # Return the screen coordinates of the active game window.
    window = locate_game_window()
    return window.left, window.top, window.width, window.height


def _crop_region(relative_region: Tuple[int, int, int, int]) -> np.ndarray:
    # Capture a screenshot of a relative region inside the game window.
    left, top, _, _ = get_window_position()
    x, y, w, h = relative_region
    screenshot = pyautogui.screenshot(region=(left + x, top + y, w, h))
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    # Convert the image to grayscale and threshold it for cleaner OCR input.
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def extract_text_from_region(region_name: str) -> str:
    # Read OCR text from a named region in the game UI.
    if region_name not in REGION_DEFINITIONS:
        raise ValueError(f"Unknown OCR region: {region_name}")
    image = _crop_region(REGION_DEFINITIONS[region_name])
    preprocessed = preprocess_for_ocr(image)
    text_segments = OCR_READER.readtext(preprocessed, detail=0, paragraph=False)
    return " ".join(text_segments).strip()


def parse_numeric_value(text: str) -> int:
    # Extract digits from OCR text and convert them into an integer.
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def click_point(x: int, y: int) -> None:
    # Click a screen point with humanized movement and pause.
    _safe_move_to(x, y)
    pyautogui.click()
    _humanized_pause(0.25, 0.55)


def click_region_center(region_name: str) -> Tuple[int, int]:
    # Click the center of a named region and return the clicked coordinates.
    left, top, _, _ = get_window_position()
    x, y, w, h = REGION_DEFINITIONS[region_name]
    center_x = left + x + w // 2
    center_y = top + y + h // 2
    click_point(center_x, center_y)
    return center_x, center_y


def safe_type_string(value: str) -> None:
    # Clear an input field and type a numeric string with slight delays.
    pyautogui.hotkey("ctrl", "a")
    _humanized_pause(0.12, 0.22)
    pyautogui.press("backspace")
    _humanized_pause(0.12, 0.22)
    pyautogui.write(value, interval=random.uniform(0.04, 0.12))
    _humanized_pause(0.18, 0.32)


def activate_by_type_filter() -> None:
    # Click the marketplace filter button to ensure the listing is filtered by type.
    click_region_center("by_type_button")


def scan_catalog_rows(target_skins: list[str]) -> list[CatalogRow]:
    # Scan the visible rows in the catalog and return matching target skins.
    left, top, _, _ = get_window_position()
    rows = []
    base_x, base_y, width, height = REGION_DEFINITIONS["catalog_row_1"]
    row_height = REGION_DEFINITIONS["catalog_row_height"]

    for row_index in range(7):
        row_x = left + base_x
        row_y = top + base_y + row_index * row_height
        row_center = (row_x + width // 2, row_y + row_height // 2)
        crop = pyautogui.screenshot(region=(row_x, row_y, width, row_height))
        row_image = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)

        text = OCR_READER.readtext(preprocess_for_ocr(row_image), detail=0, paragraph=False)
        if not text:
            continue
        combined = " ".join(text)
        for skin_name in target_skins:
            if skin_name.lower() in combined.lower():
                price_image = pyautogui.screenshot(region=(row_x + REGION_DEFINITIONS["price_column"][0], row_y + REGION_DEFINITIONS["price_column"][1], REGION_DEFINITIONS["price_column"][2], REGION_DEFINITIONS["price_column"][3]))
                amount_image = pyautogui.screenshot(region=(row_x + REGION_DEFINITIONS["volume_column"][0], row_y + REGION_DEFINITIONS["volume_column"][1], REGION_DEFINITIONS["volume_column"][2], REGION_DEFINITIONS["volume_column"][3]))
                price_text = " ".join(OCR_READER.readtext(preprocess_for_ocr(cv2.cvtColor(np.array(price_image), cv2.COLOR_RGB2BGR)), detail=0, paragraph=False))
                volume_text = " ".join(OCR_READER.readtext(preprocess_for_ocr(cv2.cvtColor(np.array(amount_image), cv2.COLOR_RGB2BGR)), detail=0, paragraph=False))
                rows.append(
                    CatalogRow(
                        skin_name=skin_name,
                        row_center=row_center,
                        price_value=parse_numeric_value(price_text),
                        volume_value=parse_numeric_value(volume_text),
                    )
                )
                break
    return rows


def open_skin_detail(row_center: Tuple[int, int]) -> None:
    # Open the detailed view for a selected skin entry.
    click_point(row_center[0], row_center[1])
    _humanized_pause(1.0, 1.8)


def extract_skin_detail_prices() -> tuple[int, int]:
    # Read the detailed lowest sell and highest buy prices from the detail view.
    lowest_sell_text = extract_text_from_region("detail_lowest_sell")
    highest_buy_text = extract_text_from_region("detail_highest_buy")
    return parse_numeric_value(lowest_sell_text), parse_numeric_value(highest_buy_text)


def place_bid(target_amount: int) -> None:
    # Enter a bid amount and confirm the offer in the UI.
    click_region_center("bid_input_field")
    safe_type_string(str(target_amount))
    click_region_center("confirm_bid_button")
    _humanized_pause(1.0, 1.6)


def return_to_catalog() -> None:
    # Return to the catalog listing after viewing a detail page.
    click_region_center("catalog_back_button")
    _humanized_pause(0.8, 1.4)
