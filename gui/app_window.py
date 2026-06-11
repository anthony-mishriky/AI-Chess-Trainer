import customtkinter as ctk
from gui.live_board_tab import LiveBoardTab
from gui.archive_tab import ArchiveTab
from gui.lab_tab import LabTab
from gui.sandbox_tab import SandboxTab

class ChessApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AI Chess Trainer")
        self.geometry("1280x800")
        self.configure(fg_color="#121212")
        
        self.tab_view = ctk.CTkTabview(self, fg_color="#1E1E1E", segmented_button_selected_color="#15B53B", segmented_button_selected_hover_color="#108A2D")
        self.tab_view.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tab_view.add("The Arena")
        self.tab_view.add("The Archive")
        self.tab_view.add("The Lab")
        self.tab_view.add("The Sandbox")
        
        self.arena = LiveBoardTab(self.tab_view.tab("The Arena"))
        self.arena.pack(expand=True, fill="both")
        
        self.archive = ArchiveTab(self.tab_view.tab("The Archive"))
        self.archive.pack(expand=True, fill="both")
        
        self.lab = LabTab(self.tab_view.tab("The Lab"))
        self.lab.pack(expand=True, fill="both")
        
        self.sandbox = SandboxTab(self.tab_view.tab("The Sandbox"))
        self.sandbox.pack(expand=True, fill="both")
        
        self.tab_view.configure(command=self.on_tab_change)
        
        self.watermark = ctk.CTkLabel(self, text="@anthony_mishriky", font=("Arial", 13, "bold"), text_color="#2A2A2A")
        self.watermark.place(relx=1.0, rely=1.0, x=-5, y=-10, anchor="se")

    def on_tab_change(self):
        current_tab = self.tab_view.get()
        if current_tab == "The Archive":
            self.archive.load_history()
        elif current_tab == "The Lab":
            self.lab.refresh_data()
        elif current_tab == "The Arena":
            self.arena.update_ui_labels()