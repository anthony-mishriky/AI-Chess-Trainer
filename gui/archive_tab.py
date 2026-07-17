import customtkinter as ctk
import tkinter as tk
import chess
import chess.engine
import threading
import json
import os
from PIL import Image, ImageTk

class ArchiveTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.square_size = 60
        self.images = {}
        self.load_images()
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(20, 0))
        ctk.CTkLabel(header, text="Match Archive", font=("Arial", 32, "bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh", fg_color="#333333", command=self.load_history).pack(side="right")
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.table_frame.pack(expand=True, fill="both", padx=40, pady=20)
        self.load_history()

    def load_images(self):
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        for p in pieces:
            color = 'w' if p.isupper() else 'b'
            path = f"assets/{color}{p.upper()}.png"
            if os.path.exists(path):
                img = Image.open(path).resize((self.square_size, self.square_size), Image.Resampling.LANCZOS)
                self.images[p] = ImageTk.PhotoImage(img)

    def load_history(self):
        for w in self.table_frame.winfo_children(): w.destroy()
        path = "data/match_history.json"
        if not os.path.exists(path): return
        with open(path, "r") as f:
            try: data = json.load(f)
            except: data = []
        for i, match in enumerate(reversed(data), 1):
            row = ctk.CTkFrame(self.table_frame, fg_color="#242424" if i % 2 == 0 else "#2B2B2B")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=match.get("date")).pack(side="left", padx=20)
            ctk.CTkLabel(row, text=match.get("name")).pack(side="left", padx=20)
            res = match.get("result", "Draw")
            ctk.CTkLabel(row, text=res.upper(), text_color="#15B53B" if res=="win" else "#8B0000").pack(side="left", padx=20)
            ctk.CTkButton(row, text="Replay", width=80, command=lambda m=match: ReplayModal(self, m, self.images, self.square_size)).pack(side="right", padx=20)

class ReplayModal(ctk.CTkToplevel):
    def __init__(self, master, match, images, size):
        super().__init__(master)
        self.title(f"Replay: {match.get('name')}")
        self.geometry("900x600")
        self.attributes("-topmost", True)
        self.images, self.size = images, size
        self.board = chess.Board()
        self.moves = [chess.Move.from_uci(u) for u in match.get("move_list", [])]
        self.idx = 0
        self.engine = chess.engine.SimpleEngine.popen_uci("engine_bin/stockfish") if os.path.exists("engine_bin/stockfish") else None
        self.setup_ui()
        self.draw_board()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        self.eval_label = ctk.CTkLabel(self, text="0.0")
        self.eval_label.pack()
        self.eval_bar = ctk.CTkProgressBar(self, orientation="vertical")
        self.eval_bar.pack()
        self.canvas = tk.Canvas(self, width=480, height=480, bg="#2B2B2B")
        self.canvas.pack()
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text="<", width=40, command=self.prev).pack(side="left")
        ctk.CTkButton(btn_frame, text=">", width=40, command=self.next).pack(side="left")

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                idx = (7 - r) * 8 + c
                color = "#E0E0E0" if (r + c) % 2 == 0 else "#708090"
                x1, y1 = c * self.size, r * self.size
                self.canvas.create_rectangle(x1, y1, x1+self.size, y1+self.size, fill=color, outline="")
                piece = self.board.piece_at(idx)
                if piece and piece.symbol() in self.images:
                    self.canvas.create_image(x1+self.size/2, y1+self.size/2, image=self.images[piece.symbol()])

    def prev(self):
        if self.idx > 0:
            self.board.pop()
            self.idx -= 1
            self.draw_board()
            self.analyze()

    def next(self):
        if self.idx < len(self.moves):
            self.board.push(self.moves[self.idx])
            self.idx += 1
            self.draw_board()
            self.analyze()

    def analyze(self):
        if not self.engine: return
        threading.Thread(target=self.run_engine, args=(self.board.copy(),), daemon=True).start()

    def run_engine(self, board):
        info = self.engine.analyse(board, chess.engine.Limit(time=0.1))
        score = info["score"].white()
        val = 10.0 if score.is_mate() and score.mate() > 0 else -10.0 if score.is_mate() else score.score(mate_score=1000) / 100.0
        clamped = max(-10.0, min(10.0, val))
        self.after(0, lambda: (self.eval_label.configure(text=f"{clamped:+.1f}"), self.eval_bar.set((clamped + 10.0) / 20.0)))

    def on_close(self):
        if self.engine: self.engine.quit()
        self.destroy()