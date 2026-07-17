import customtkinter as ctk
import tkinter as tk
import chess
import time
import chess.engine
import threading
import os
import pygame
import random
import sqlite3
from PIL import Image, ImageTk
from core.ai_opponent import AIOpponent

class SandboxTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.__ip_signature = "@anthony_mishriky"
        self.board = chess.Board()
        self.ai_adaptive = AIOpponent()
        self.square_size = 85
        self.images = {}
        self.setup_mode = True
        self.editor_selected_piece = None
        self.player_color = chess.WHITE
        self.is_flipped = False
        self.selected_square = None
        self.last_move = None
        self.engine_path = "engine_bin/stockfish"
        if os.path.exists(self.engine_path + ".exe"):
            self.engine_path += ".exe"
        self.eval_engine = None
        try:
            if os.path.exists(self.engine_path):
                self.eval_engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        except Exception:
            pass
        self.load_images()
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_center_board()
        self.start_eval_loop()

    def load_images(self):
        for piece in ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']:
            color = 'w' if piece.isupper() else 'b'
            filename = f"assets/{color}{piece.upper()}.png"
            if os.path.exists(filename):
                try:
                    img = Image.open(filename).resize((self.square_size, self.square_size), Image.Resampling.LANCZOS)
                    self.images[piece] = ImageTk.PhotoImage(img)
                except Exception:
                    self.images[piece] = None

    def setup_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(self.left_frame, text="Sandbox Editor", font=("Arial", 24, "bold"), text_color="#D2691E").pack(pady=(20, 10))
        ctk.CTkLabel(self.left_frame, text="FEN String:", font=("Arial", 14, "bold")).pack(pady=(10, 2))
        self.fen_entry = ctk.CTkEntry(self.left_frame, width=200, fg_color="#121212")
        self.fen_entry.insert(0, self.board.fen())
        self.fen_entry.pack(pady=5, padx=20)
        btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="Load", width=60, fg_color="#333333", hover_color="#444444", command=self.load_fen).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Save", width=60, fg_color="#3a7ebf", hover_color="#1f538d", command=self.save_fen_dialog).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="My FENs", width=60, fg_color="#4B0082", hover_color="#300052", command=self.open_saved_fens).pack(side="left", padx=2)
        ctk.CTkLabel(self.left_frame, text="Sparring Settings", font=("Arial", 18, "bold")).pack(pady=(30, 10))
        play_as_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        play_as_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(play_as_frame, text="Play As", font=("Arial", 14)).pack(side="top", pady=(0, 2))
        self.side_dropdown = ctk.CTkOptionMenu(play_as_frame, values=["White", "Black"], fg_color="#D2691E", button_color="#A0522D", button_hover_color="#8B4513", command=self.set_player_side)
        self.side_dropdown.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(play_as_frame, text="⇅", width=30, font=("Arial", 16, "bold"), fg_color="#333333", hover_color="#444444", command=self.toggle_flip_board).pack(side="right")
        ctk.CTkLabel(self.left_frame, text="Opponent AI", font=("Arial", 14)).pack(pady=(10, 2))
        self.diff_dropdown = ctk.CTkOptionMenu(self.left_frame, values=["Adaptive Trainer", "Fixed Bot (1200 Elo)", "Max Stockfish (3200+)"], fg_color="#D2691E", button_color="#A0522D", button_hover_color="#8B4513")
        self.diff_dropdown.pack(pady=5, padx=20)
        eval_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        eval_frame.pack(pady=30, expand=True, fill="both")
        ctk.CTkLabel(eval_frame, text="Live Evaluation", font=("Arial", 16, "bold")).pack()
        self.eval_label = ctk.CTkLabel(eval_frame, text="0.0", font=("Arial", 20, "bold"), text_color="#A0A0A0")
        self.eval_label.pack(pady=10)
        self.eval_bar = ctk.CTkProgressBar(eval_frame, orientation="horizontal", width=150, fg_color="#111111", progress_color="#D2691E")
        self.eval_bar.pack(pady=5)
        self.eval_bar.set(0.5)

    def setup_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.editor_view = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.editor_view.pack(expand=True, fill="both")
        ctk.CTkLabel(self.editor_view, text="Piece Drawer", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self.editor_view, text="Click to select. Click board to place.", font=("Arial", 12)).pack(pady=(0, 10))
        ctk.CTkButton(self.editor_view, text="Eraser Tool", fg_color="#8B0000", hover_color="#5C0000", command=self.set_editor_trash).pack(pady=5)
        drawer_frame = ctk.CTkScrollableFrame(self.editor_view, fg_color="#121212", width=200, height=220)
        drawer_frame.pack(pady=10, padx=10)
        pieces = [('K', chess.KING, chess.WHITE), ('Q', chess.QUEEN, chess.WHITE), ('R', chess.ROOK, chess.WHITE),
                  ('B', chess.BISHOP, chess.WHITE), ('N', chess.KNIGHT, chess.WHITE), ('P', chess.PAWN, chess.WHITE),
                  ('k', chess.KING, chess.BLACK), ('q', chess.QUEEN, chess.BLACK), ('r', chess.ROOK, chess.BLACK),
                  ('b', chess.BISHOP, chess.BLACK), ('n', chess.KNIGHT, chess.BLACK), ('p', chess.PAWN, chess.BLACK)]
        for i, (symbol, pt, color) in enumerate(pieces):
            img = self.images.get(symbol)
            if img:
                btn = tk.Button(drawer_frame, image=img, bg="#2B2B2B", bd=0, activebackground="#D2691E", command=lambda s=symbol: self.set_editor_piece(s))
                btn.grid(row=i//2, column=i%2, padx=10, pady=10)
        ctk.CTkLabel(self.editor_view, text="Who Moves First?", font=("Arial", 14, "bold")).pack(pady=(15, 2))
        self.turn_dropdown = ctk.CTkOptionMenu(self.editor_view, values=["White to Move", "Black to Move"], fg_color="#333333", command=self.update_turn_fen)
        self.turn_dropdown.pack(pady=5)
        btn_row = ctk.CTkFrame(self.editor_view, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="Start Pos", width=70, fg_color="#3a7ebf", hover_color="#1f538d", command=self.set_starting_pos).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Chess960", width=70, fg_color="#9932CC", hover_color="#8A2BE2", command=self.set_chess960_pos).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Clear", width=70, fg_color="#8B0000", hover_color="#5C0000", command=self.clear_board).pack(side="left", padx=2)
        ctk.CTkButton(self.editor_view, text="START SPARRING", font=("Arial", 16, "bold"), fg_color="#15B53B", hover_color="#108A2D", height=50, command=self.start_sparring).pack(pady=20, padx=20, fill="x")
        self.play_view = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        ctk.CTkLabel(self.play_view, text="Sparring Active", font=("Arial", 20, "bold"), text_color="#D2691E").pack(pady=(20, 10))
        self.history_box = ctk.CTkTextbox(self.play_view, width=240, height=400, fg_color="#121212", font=("Consolas", 14))
        self.history_box.pack(pady=10, padx=10)
        ctk.CTkButton(self.play_view, text="Stop & Edit Board", fg_color="#8B0000", hover_color="#5C0000", command=self.stop_sparring).pack(pady=20)

    def setup_center_board(self):
        self.board_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", width=700, height=700)
        self.board_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.board_frame.grid_propagate(False)
        self.canvas = tk.Canvas(self.board_frame, width=680, height=680, bg="#2B2B2B", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.canvas.bind("<Button-1>", self.on_square_clicked)
        self.draw_board()

    def set_player_side(self, choice):
        if not self.setup_mode:
            return
        self.player_color = chess.BLACK if choice == "Black" else chess.WHITE
        self.is_flipped = (self.player_color == chess.BLACK)
        self.draw_board()

    def toggle_flip_board(self):
        self.is_flipped = not self.is_flipped
        self.draw_board()

    def set_editor_piece(self, symbol):
        self.editor_selected_piece = symbol

    def clear_board(self):
        self.board.clear_board()
        self.update_fen_entry()
        self.draw_board()

    def set_starting_pos(self):
        self.board.reset()
        self.update_fen_entry()
        self.draw_board()

    def update_turn_fen(self, choice):
        self.board.turn = chess.WHITE if choice == "White to Move" else chess.BLACK
        self.update_fen_entry()

    def load_fen(self):
        try:
            self.board.set_fen(self.fen_entry.get())
            self.turn_dropdown.set("White to Move" if self.board.turn == chess.WHITE else "Black to Move")
            self.draw_board()
        except ValueError:
            self.show_warning_modal("Invalid FEN", "The text provided is not a valid chess FEN string.")

    def copy_fen(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.fen_entry.get())

    def update_fen_entry(self):
        self.fen_entry.delete(0, 'end')
        self.fen_entry.insert(0, self.board.fen())

    def is_sandbox_board_valid(self, board):
        if len(board.pieces(chess.KING, chess.WHITE)) != 1:
            return False
        if len(board.pieces(chess.KING, chess.BLACK)) != 1:
            return False
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                if chess.square_rank(square) == 0 or chess.square_rank(square) == 7:
                    return False
        board.turn = not board.turn
        was_in_check = board.is_check()
        board.turn = not board.turn
        if was_in_check:
            return False
        return True

    def start_sparring(self):
        if self.is_sandbox_board_valid(self.board):
            self.setup_mode = False
            self.editor_view.pack_forget()
            self.play_view.pack(expand=True, fill="both")
            self.side_dropdown.configure(state="disabled")
            self.diff_dropdown.configure(state="disabled")
            self.board.clear_stack()
            self.history_box.delete("0.0", "end")
            self.last_move = self.selected_square = None
            if self.board.turn != self.player_color:
                self.trigger_ai_move()
        else:
            self.show_warning_modal("Invalid State", "• 1 King per side required\n• No pawns on 1st/8th ranks\n• Non-moving side cannot be in check")

    def stop_sparring(self):
        self.setup_mode = True
        self.play_view.pack_forget()
        self.editor_view.pack(expand=True, fill="both")
        self.side_dropdown.configure(state="normal")
        self.diff_dropdown.configure(state="normal")
        self.update_fen_entry()
        self.draw_board()

    def trigger_ai_move(self):
        threading.Thread(target=self.calculate_ai, args=(self.board.copy(),), daemon=True).start()

    def calculate_ai(self, board_copy):
        start_time = time.time()
        mode = self.diff_dropdown.get()
        if mode == "Max Stockfish (3200+)" and self.eval_engine:
            result = self.eval_engine.play(board_copy, chess.engine.Limit(time=0.5))
            move = result.move
        elif mode == "Fixed Bot (1200 Elo)" and self.eval_engine:
            result = self.eval_engine.play(board_copy, chess.engine.Limit(depth=5, time=0.1))
            move = result.move
        else:
            move = self.ai_adaptive.get_move(board_copy)
        execution_duration = time.time() - start_time
        if execution_duration < 0.5:
            time.sleep(0.5 - execution_duration)
        self.after(0, self.apply_ai_move, move)

    def apply_ai_move(self, move):
        if move and not self.setup_mode:
            self.board.push(move)
            self.last_move = move
            self.update_history()
            if self.board.is_game_over():
                self.show_warning_modal("Sparring Over", f"Result: {self.board.result()}")
            else:
                try:
                    pygame.mixer.Sound("assets/move.wav").play()
                except:
                    pass
            self.draw_board()

    def update_history(self):
        self.history_box.delete("0.0", "end")
        temp_board = chess.Board(self.fen_entry.get())
        history_text = ""
        moves = list(self.board.move_stack)
        for i in range(0, len(moves), 2):
            w_move = temp_board.san(moves[i])
            temp_board.push(moves[i])
            if i + 1 < len(moves):
                b_move = temp_board.san(moves[i+1])
                temp_board.push(moves[i+1])
            else:
                b_move = ""
            history_text += f"{(i//2) + 1}.  {w_move:<10}{b_move:>10}\n"
        self.history_box.insert("0.0", history_text)

    def draw_board(self):
        self.canvas.delete("all")
        self.canvas.create_text(340, 340, text="@anthony_mishriky", font=("Arial", 36, "bold"), fill="#2A2A2A", state="disabled")
        colors = ["#E0E0E0", "#708090"]
        file_names, rank_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], ['8', '7', '6', '5', '4', '3', '2', '1']
        if self.is_flipped:
            file_names, rank_names = list(reversed(file_names)), list(reversed(rank_names))
        for row in range(8):
            for col in range(8):
                square_idx = row * 8 + (7 - col) if self.is_flipped else (7 - row) * 8 + col
                color = colors[(row + col) % 2]
                text_color = colors[(row + col + 1) % 2]
                if not self.setup_mode:
                    if self.last_move and square_idx in (self.last_move.from_square, self.last_move.to_square):
                        color = "#BDB76B"
                    if self.selected_square == square_idx:
                        color = "#D2691E"
                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                font = ("Arial", 11, "bold")
                if col == 0:
                    self.canvas.create_text(x1 + 10, y1 + 14, text=rank_names[row], fill=text_color, font=font, anchor="w")
                if row == 7:
                    self.canvas.create_text(x2 - 10, y2 - 14, text=file_names[col], fill=text_color, font=font, anchor="e")
                piece = self.board.piece_at(square_idx)
                if piece and self.images.get(piece.symbol()):
                    self.canvas.create_image(x1 + self.square_size/2, y1 + self.square_size/2, image=self.images[piece.symbol()])
        if self.selected_square is not None and not self.setup_mode:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    to_col, to_row = (7 - (move.to_square % 8), move.to_square // 8) if self.is_flipped else (move.to_square % 8, 7 - (move.to_square // 8))
                    cx, cy = to_col * self.square_size + self.square_size / 2, to_row * self.square_size + self.square_size / 2
                    if self.board.piece_at(move.to_square):
                        self.canvas.create_oval(cx - 38, cy - 38, cx + 38, cy + 38, outline="#333333", width=5)
                    else:
                        self.canvas.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#333333", outline="")

    def get_square_from_coords(self, x, y):
        col, row = int(x // self.square_size), int(y // self.square_size)
        if col > 7 or col < 0 or row > 7 or row < 0:
            return None
        return row * 8 + (7 - col) if self.is_flipped else (7 - row) * 8 + col

    def on_square_clicked(self, event):
        square = self.get_square_from_coords(event.x, event.y)
        if square is None:
            return
        if self.setup_mode:
            if self.editor_selected_piece:
                p_char = self.editor_selected_piece
                color = chess.WHITE if p_char.isupper() else chess.BLACK
                p_type = chess.Piece.from_symbol(p_char).piece_type
                self.board.set_piece_at(square, chess.Piece(p_type, color))
            else:
                self.board.remove_piece_at(square)
            self.update_fen_entry()
            self.draw_board()
            return
        if self.board.turn != self.player_color:
            return
        if self.selected_square is None:
            if self.board.piece_at(square) and self.board.color_at(square) == self.board.turn:
                self.selected_square = square
        else:
            if square == self.selected_square:
                self.selected_square = None
            else:
                moving_piece = self.board.piece_at(self.selected_square)
                move = chess.Move(self.selected_square, square)
                if moving_piece and moving_piece.piece_type == chess.PAWN and (square // 8 == 0 or square // 8 == 7):
                    if chess.Move(self.selected_square, square, promotion=chess.QUEEN) in self.board.legal_moves:
                        move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.last_move = move
                    self.selected_square = None
                    self.update_history()
                    try:
                        pygame.mixer.Sound("assets/move.wav").play()
                    except:
                        pass
                    if self.board.is_game_over():
                        self.show_warning_modal("Sparring Over", f"Result: {self.board.result()}")
                    else:
                        self.trigger_ai_move()
                else:
                    self.selected_square = None
        self.draw_board()

    def start_eval_loop(self):
        threading.Thread(target=self.continuous_eval, daemon=True).start()

    def continuous_eval(self):
        last_fen = ""
        while True:
            time.sleep(0.5)
            if self.setup_mode and self.eval_engine and self.is_sandbox_board_valid(self.board) and self.board.fen() != last_fen:
                try:
                    last_fen = self.board.fen()
                    info = self.eval_engine.analyse(self.board, chess.engine.Limit(time=0.1))
                    white_score = info["score"].white()
                    if white_score.is_mate():
                        val = 10.0 if white_score.mate() > 0 else -10.0
                    else:
                        val = max(-10.0, min(10.0, white_score.score(mate_score=1000) / 100.0))
                    self.after(0, lambda v=val, f=(val + 10.0) / 20.0: self.update_eval_ui(v, f))
                except Exception:
                    pass

    def update_eval_ui(self, val, fill):
        self.eval_label.configure(text=f"{val:+.1f}")
        self.eval_bar.set(fill)

    def show_warning_modal(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Notification")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        try:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 200
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 100
            dialog.geometry(f"+{x}+{y}")
        except Exception:
            pass
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=title, font=("Arial", 20, "bold"), text_color="#D2691E").pack(pady=(20, 10))
        ctk.CTkLabel(dialog, text=message, font=("Arial", 14), justify="center", wraplength=360).pack(pady=(0, 20))
        ctk.CTkButton(dialog, text="Got It", width=100, command=dialog.destroy).pack()

    def set_editor_trash(self):
        self.editor_selected_piece = None

    def set_chess960_pos(self):
        idx = random.randint(0, 959)
        temp_board = chess.Board.from_chess960_pos(idx)
        self.board.set_fen(temp_board.fen())
        self.update_fen_entry()
        self.draw_board()

    def save_fen_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter a name for this position:", title="Save FEN")
        name = dialog.get_input()
        if name:
            conn = sqlite3.connect("saved_fens.db")
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS fens (id INTEGER PRIMARY KEY, name TEXT, fen TEXT)")
            cursor.execute("INSERT INTO fens (name, fen) VALUES (?, ?)", (name, self.fen_entry.get()))
            conn.commit()
            conn.close()

    def open_saved_fens(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Saved FENs")
        dialog.geometry("400x500")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)
        try:
            conn = sqlite3.connect("saved_fens.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name, fen FROM fens")
            records = cursor.fetchall()
            conn.close()
            if not records:
                ctk.CTkLabel(scroll_frame, text="No saved FENs found.").pack(pady=20)
                return
            for name, fen in records:
                row = ctk.CTkFrame(scroll_frame, fg_color="#1E1E1E")
                row.pack(fill="x", pady=5)
                ctk.CTkLabel(row, text=name, font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=10)
                ctk.CTkButton(row, text="Load", width=60, fg_color="#15B53B", hover_color="#108A2D", command=lambda f=fen: self.load_specific_fen(f, dialog)).pack(side="right", padx=10)
        except Exception:
            ctk.CTkLabel(scroll_frame, text="No database found yet.").pack(pady=20)

    def load_specific_fen(self, fen, dialog):
        self.board.set_fen(fen)
        self.update_fen_entry()
        self.draw_board()
        dialog.destroy()