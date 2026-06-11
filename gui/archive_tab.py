# ==============================================================================
# Author/Instagram: @anthony_mishriky
# LinkedIn: www.linkedin.com/in/anthony-mishriky
# Email: anthonymishrikyprivate@gmail.com
# ==============================================================================
import customtkinter as ctk
import json
import os
import chess
import chess.engine
import threading
import tkinter as tk
from PIL import Image, ImageTk

class ArchiveTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(20, 0))
        ctk.CTkLabel(header_frame, text="Match Archive", font=("Arial", 32, "bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Refresh Data", fg_color="#333333", hover_color="#444444", command=self.load_history).pack(side="right", pady=10)
        
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.table_frame.pack(expand=True, fill="both", padx=40, pady=20)
        self.table_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        self.square_size = 60
        self.images = {}
        self.load_images()
        self.load_history()

    def load_images(self):
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        for piece in pieces:
            color = 'w' if piece.isupper() else 'b'
            filename = f"assets/{color}{piece.upper()}.png"
            if os.path.exists(filename):
                try:
                    img = Image.open(filename).resize((self.square_size, self.square_size), Image.Resampling.LANCZOS)
                    self.images[piece] = ImageTk.PhotoImage(img)
                except Exception:
                    self.images[piece] = None

    def load_history(self):
        for widget in self.table_frame.winfo_children(): widget.destroy()
            
        headers = ["Date", "Match Name", "Result", "Moves", "Action"]
        for col, text in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=text, font=("Arial", 16, "bold"), text_color="#A0A0A0").grid(row=0, column=col, padx=10, pady=(10, 20), sticky="ew")
            
        file_path = "data/match_history.json"
        if not os.path.exists(file_path):
            ctk.CTkLabel(self.table_frame, text="No matches recorded yet.", font=("Arial", 16, "italic")).grid(row=1, column=0, columnspan=5, pady=40)
            return
            
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
            
        if not data:
            ctk.CTkLabel(self.table_frame, text="Archive is empty.", font=("Arial", 16, "italic")).grid(row=1, column=0, columnspan=5, pady=40)
            return
            
        for row, match in enumerate(reversed(data), start=1):
            bg_frame = ctk.CTkFrame(self.table_frame, fg_color="#242424" if row % 2 == 0 else "#2B2B2B", corner_radius=5)
            bg_frame.grid(row=row, column=0, columnspan=5, sticky="nsew", padx=5, pady=2)
            bg_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            ctk.CTkLabel(bg_frame, text=match.get("date", "Unknown"), font=("Arial", 14)).grid(row=0, column=0, pady=10)
            ctk.CTkLabel(bg_frame, text=match.get("name", "Game"), font=("Arial", 14)).grid(row=0, column=1, pady=10)
            
            result = match.get("result", "Draw")
            res_color = "#15B53B" if result == "win" else "#8B0000" if result == "loss" else "#BDB76B"
            ctk.CTkLabel(bg_frame, text=result.upper(), text_color=res_color, font=("Arial", 14, "bold")).grid(row=0, column=2, pady=10)
            ctk.CTkLabel(bg_frame, text=str(match.get("moves", 0)), font=("Arial", 14)).grid(row=0, column=3, pady=10)
            
            btn = ctk.CTkButton(bg_frame, text="Replay", width=100, fg_color="#3a7ebf", hover_color="#1f538d", command=lambda m=match: self.trigger_replay(m))
            btn.grid(row=0, column=4, pady=10)

    def trigger_replay(self, match_data):
        ReplayModal(self, match_data, self.images, self.square_size)


class ReplayModal(ctk.CTkToplevel):
    def __init__(self, master, match_data, images, square_size):
        super().__init__(master)
        
        self.title(f"Replay: {match_data.get('name')}")
        self.geometry("900x600")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.images = images
        self.square_size = square_size
        self.history_board = chess.Board() # Start at Standard Position
        
        self.move_stack = []
        for uci in match_data.get("move_list", []):
            self.move_stack.append(chess.Move.from_uci(uci))
            
        self.current_move_index = 0
        
        self.engine_path = "engine_bin/stockfish"
        if os.path.exists(self.engine_path + ".exe"): self.engine_path += ".exe"
            
        self.engine = None
        try:
            if os.path.exists(self.engine_path):
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        except Exception:
            pass
            
        self.setup_ui()
        self.draw_board()
        self.analyze_position()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        left_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", width=80)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.eval_bar = ctk.CTkProgressBar(left_frame, orientation="vertical", width=30, fg_color="#111111", progress_color="#DDDDDD")
        self.eval_bar.pack(expand=True, fill="y", pady=20)
        self.eval_bar.set(0.5)
        
        self.eval_label = ctk.CTkLabel(left_frame, text="0.0", font=("Arial", 16, "bold"))
        self.eval_label.pack(pady=10)
        
        center_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", width=500, height=500)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.canvas = tk.Canvas(center_frame, width=480, height=480, bg="#2B2B2B", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        
        right_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(right_frame, text="Controls", font=("Arial", 20, "bold")).pack(pady=20)
        
        nav_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        nav_frame.pack(pady=10)
        ctk.CTkButton(nav_frame, text="<", width=40, font=("Arial", 18, "bold"), command=self.prev_move).pack(side="left", padx=5)
        ctk.CTkButton(nav_frame, text=">", width=40, font=("Arial", 18, "bold"), command=self.next_move).pack(side="left", padx=5)

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#E0E0E0", "#708090"]
        for row in range(8):
            for col in range(8):
                square_idx = (7 - row) * 8 + col
                color = colors[(row + col) % 2]
                
                # Highlight last move
                if self.current_move_index > 0:
                    last_m = self.move_stack[self.current_move_index - 1]
                    if square_idx in (last_m.from_square, last_m.to_square):
                        color = "#BDB76B"

                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                piece = self.history_board.piece_at(square_idx)
                if piece and self.images.get(piece.symbol()):
                    self.canvas.create_image(x1 + self.square_size/2, y1 + self.square_size/2, image=self.images[piece.symbol()])

    def prev_move(self):
        if self.current_move_index > 0:
            self.history_board.pop()
            self.current_move_index -= 1
            self.draw_board()
            self.analyze_position()

    def next_move(self):
        if self.current_move_index < len(self.move_stack):
            self.history_board.push(self.move_stack[self.current_move_index])
            self.current_move_index += 1
            self.draw_board()
            self.analyze_position()

    def analyze_position(self):
        if not self.engine: return
        board_copy = self.history_board.copy()
        threading.Thread(target=self.run_engine, args=(board_copy,), daemon=True).start()

    def run_engine(self, board):
        try:
            info = self.engine.analyse(board, chess.engine.Limit(time=0.1))
            score = info["score"].white()
            val = 10.0 if score.is_mate() and score.mate() > 0 else -10.0 if score.is_mate() else score.score() / 100.0
            clamped_val = max(-5.0, min(5.0, val))
            bar_fill = (clamped_val + 5.0) / 10.0
            self.after(0, self.update_eval, val, bar_fill)
        except Exception: pass

    def update_eval(self, score, fill_ratio):
        self.eval_label.configure(text=f"{score:+.1f}")
        self.eval_bar.set(fill_ratio)

    def on_close(self):
        if self.engine: self.engine.quit()
        self.destroy()