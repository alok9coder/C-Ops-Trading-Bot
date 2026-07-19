import tkinter as tk
import pyautogui

class CoordinateWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Coords")
        
        # Keep window tiny and always on top of other games/apps
        self.root.geometry("400x100")
        self.root.attributes("-topmost", True)
        
        # Configure layout
        self.label_x = tk.Label(self.root, text="X: 0", font=("Arial", 16, "bold"), fg="blue")
        self.label_x.pack(pady=2)
        
        self.label_y = tk.Label(self.root, text="Y: 0", font=("Arial", 16, "bold"), fg="green")
        self.label_y.pack(pady=2)
        
        # Start the live update loop
        self.update_coordinates()
        self.root.mainloop()

    def update_coordinates(self):
        # Get live mouse position
        x, y = pyautogui.position()
        
        # Update the UI text
        self.label_x.config(text=f"X: {x}")
        self.label_y.config(text=f"Y: {y}")
        
        # Run this function again after 50 milliseconds (real-time feel)
        self.root.after(50, self.update_coordinates)

if __name__ == "__main__":
    CoordinateWindow()
