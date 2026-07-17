import platform
# BYPASS WINDOWS WMI HANG: Force Python to return a dummy Windows version 
# instantly. This stops darkdetect/customtkinter from freezing on startup!
platform.win32_ver = lambda *args, **kwargs: ("10", "", "", "")

import customtkinter as ctk
from gui.app_window import ChessApp

def main():
    # Force CustomTkinter into dark mode directly
    ctk.set_appearance_mode("dark")

    app = ChessApp()
    app.mainloop()


if __name__ == "__main__":
    main()