# ==============================================================================
# Author/Instagram: @anthony_mishriky
# LinkedIn: www.linkedin.com/in/anthony-mishriky
# Email: anthonymishrikyprivate@gmail.com
# ==============================================================================

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import customtkinter as ctk
import tkinter as tk
import chess
import pygame
import threading
import time
import random
import json
import sys
from datetime import datetime
from PIL import Image, ImageTk
from core.game_manager import GameManager
from core.ai_opponent import AIOpponent

class LiveBoardTab(ctk.CTkFrame):
    """
    Author/Instagram: @anthony_mishriky
    LinkedIn: www.linkedin.com/in/anthony-mishriky
    Email: anthonymishrikyprivate@gmail.com
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.__ip_signature = "@anthony_mishriky"
        self.game = GameManager()
        self.ai = AIOpponent()
        
        self.current_game_id = 0  
        self.redo_stack = [] 
        
        self.selected_square = None
        self.last_move = None
        self.square_size = 85 
        
        self.premove_selected_square = None
        self.premove_queue = [] 
        
        self.player_color = chess.WHITE
        self.is_flipped = False  
        
        self.game_started = False
        self.clock_running = True
        self.is_untimed = True
        self.is_paused = False
        
        self.player_time = 0
        self.ai_time = 0
        self.player_warned_60 = self.player_warned_30 = self.player_warned_10 = False
        self.ai_warned_60 = self.ai_warned_30 = self.ai_warned_10 = False
        
        self.colored_squares = set()
        self.arrows = []
        self.drag_start_square = None
        
        self.images = {}
        self.small_images = {} 
        self.sounds = {}
        
        self.load_images()
        self.load_sounds()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_left_panel()
        self.setup_right_panel()
        self.setup_center_board()
        
        self.set_time_control("No Limit")
        self.update_clocks()

    def load_sounds(self):
        try:
            pygame.mixer.init()
            for name in ['move', 'capture', 'check', 'castle', 'win', 'lose', 'promotion', 'low_time']:
                path = f"assets/{name}.wav" if os.path.exists(f"assets/{name}.wav") else f"assets/{name}.mp3"
                if os.path.exists(path): self.sounds[name] = pygame.mixer.Sound(path)
                else: self.sounds[name] = None
        except Exception: pass

    def play_sound(self, name):
        if self.sounds.get(name):
            try: self.sounds[name].play()
            except Exception: pass

    def load_images(self):
        for piece in ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']:
            color = 'w' if piece.isupper() else 'b'
            filename = f"assets/{color}{piece.upper()}.png"
            if os.path.exists(filename):
                try:
                    img = Image.open(filename)
                    self.images[piece] = ImageTk.PhotoImage(img.resize((self.square_size, self.square_size), Image.Resampling.LANCZOS))
                    self.small_images[piece] = ImageTk.PhotoImage(img.resize((25, 25), Image.Resampling.LANCZOS))
                except Exception:
                    self.images[piece] = self.small_images[piece] = None

    def setup_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.peak_elo_label = ctk.CTkLabel(self.left_frame, text="Peak ELO: 500", font=("Arial", 18, "bold"), text_color="#15B53B")
        self.peak_elo_label.pack(pady=(20, 0))
        
        ctk.CTkLabel(self.left_frame, text="Match Settings", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        
        play_as_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        play_as_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(play_as_frame, text="Play As", font=("Arial", 14)).pack(side="top", pady=(0, 2))
        
        self.side_dropdown = ctk.CTkOptionMenu(play_as_frame, values=["White", "Black"], command=self.set_player_side)
        self.side_dropdown.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.flip_btn = ctk.CTkButton(play_as_frame, text="⇅", width=30, font=("Arial", 16, "bold"), fg_color="#333333", hover_color="#444444", command=self.toggle_flip_board)
        self.flip_btn.pack(side="right")
        
        ctk.CTkLabel(self.left_frame, text="Time Control", font=("Arial", 14)).pack(pady=(10, 2))
        self.time_dropdown = ctk.CTkOptionMenu(self.left_frame, values=["No Limit", "10 Min", "3 Min", "1 Min"], command=self.set_time_control)
        self.time_dropdown.pack(pady=5, padx=20)
        
        self.increment_switch = ctk.CTkSwitch(self.left_frame, text="+3s Increment")
        self.increment_switch.pack(pady=15, padx=20)

        self.adaptive_switch = ctk.CTkSwitch(self.left_frame, text="Adaptive Trainer")
        self.adaptive_switch.pack(pady=5, padx=20)
        self.adaptive_switch.select()
        
        ctk.CTkLabel(self.left_frame, text="Controls", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        ctk.CTkButton(self.left_frame, text="New Game", fg_color="#15B53B", hover_color="#108A2D", font=("Arial", 14, "bold"), command=self.handle_new_game).pack(pady=10, padx=20)
        self.pause_btn = ctk.CTkButton(self.left_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(pady=10, padx=20)
        ctk.CTkButton(self.left_frame, text="Forfeit", fg_color="#8B0000", hover_color="#5C0000", command=self.handle_forfeit).pack(pady=10, padx=20)

    def setup_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.right_frame, text="Clocks & Material", font=("Arial", 20, "bold")).pack(pady=(15, 5))
        
        self.ai_clock_label = ctk.CTkLabel(self.right_frame, text="AI: --:--", font=("Arial", 24))
        self.ai_clock_label.pack(pady=(5, 0))
        self.ai_material_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=30)
        self.ai_material_frame.pack(pady=(0, 10), fill="x")
        
        self.p1_clock_label = ctk.CTkLabel(self.right_frame, text="P1: --:--", font=("Arial", 24))
        self.p1_clock_label.pack(pady=(5, 0))
        self.p1_material_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=30)
        self.p1_material_frame.pack(pady=(0, 10), fill="x")
        
        self.history_header = ctk.CTkLabel(self.right_frame, text="Move History", font=("Arial", 16, "bold"))
        self.history_header.pack(pady=(10, 5))
        
        nav_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        nav_frame.pack(pady=5)
        self.btn_back = ctk.CTkButton(nav_frame, text="<", width=50, font=("Arial", 18, "bold"), command=self.step_back)
        self.btn_back.pack(side="left", padx=10)
        self.btn_forward = ctk.CTkButton(nav_frame, text=">", width=50, font=("Arial", 18, "bold"), command=self.step_forward)
        self.btn_forward.pack(side="left", padx=10)
        
        self.history_box = ctk.CTkTextbox(self.right_frame, width=240, fg_color="#121212", font=("Consolas", 14))
        self.history_box.pack(pady=10, padx=10, expand=True, fill="both")

    def setup_center_board(self):
        self.board_frame = ctk.CTkFrame(self, fg_color="#2B2B2B", width=700, height=700)
        self.board_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.board_frame.grid_propagate(False)
        
        self.canvas = tk.Canvas(self.board_frame, width=680, height=680, bg="#2B2B2B", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        
        self.canvas.bind("<Button-1>", self.on_square_clicked)
        self.canvas.bind("<Button-3>", self.on_right_click_press)
        self.canvas.bind("<B3-Motion>", self.on_right_click_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_click_release)
        
        self.draw_board()

    def toggle_flip_board(self):
        self.is_flipped = not self.is_flipped
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        self.canvas.create_text(340, 340, text="@anthony_mishriky", font=("Arial", 36, "bold"), fill="#2A2A2A", state="disabled")

        colors = ["#E0E0E0", "#708090"] 
        file_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        rank_names = ['8', '7', '6', '5', '4', '3', '2', '1']
        
        if self.is_flipped:
            file_names = list(reversed(file_names))
            rank_names = list(reversed(rank_names))

        for row in range(8):
            for col in range(8):
                square_idx = row * 8 + (7 - col) if self.is_flipped else (7 - row) * 8 + col
                color = colors[(row + col) % 2]
                text_color = colors[(row + col + 1) % 2] 

                if self.last_move and square_idx in (self.last_move.from_square, self.last_move.to_square): color = "#BDB76B" 
                if self.selected_square == square_idx: color = "#7A9B76" 
                for p_move in self.premove_queue:
                    if square_idx in (p_move.from_square, p_move.to_square): color = "#6B3F6B"
                if self.premove_selected_square == square_idx: color = "#6B3F6B"
                if square_idx in self.colored_squares: color = "#D2691E"

                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                font = ("Arial", 11, "bold")
                if col == 0: self.canvas.create_text(x1 + 10, y1 + 14, text=rank_names[row], fill=text_color, font=font, anchor="w")
                if row == 7: self.canvas.create_text(x2 - 10, y2 - 14, text=file_names[col], fill=text_color, font=font, anchor="e")

                piece = self.game.board.piece_at(square_idx)
                if piece and self.images.get(piece.symbol()):
                    self.canvas.create_image(x1 + self.square_size/2, y1 + self.square_size/2, image=self.images[piece.symbol()])

        if self.selected_square is not None:
            for move in self.game.board.legal_moves:
                if move.from_square == self.selected_square:
                    if self.is_flipped:
                        to_col, to_row = 7 - (move.to_square % 8), move.to_square // 8
                    else:
                        to_col, to_row = move.to_square % 8, 7 - (move.to_square // 8)
                        
                    cx, cy = to_col * self.square_size + self.square_size / 2, to_row * self.square_size + self.square_size / 2
                    if self.game.board.piece_at(move.to_square):
                        self.canvas.create_oval(cx - 38, cy - 38, cx + 38, cy + 38, outline="#333333", width=5)
                    else:
                        self.canvas.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill="#333333", outline="")

        for start, end in self.arrows:
            self.draw_arrow_line(start, end)
            
        self.update_material_advantage()

    def update_material_advantage(self):
        for widget in self.p1_material_frame.winfo_children(): widget.destroy()
        for widget in self.ai_material_frame.winfo_children(): widget.destroy()

        start_counts = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}

        w_counts = {pt: len(self.game.board.pieces(pt, chess.WHITE)) for pt in start_counts}
        b_counts = {pt: len(self.game.board.pieces(pt, chess.BLACK)) for pt in start_counts}

        w_captured, b_captured = [], []
        w_score = b_score = 0

        for pt in start_counts:
            w_lost, b_lost = start_counts[pt] - w_counts[pt], start_counts[pt] - b_counts[pt]
            if w_lost > 0: w_captured.extend([pt] * w_lost)
            if b_lost > 0: b_captured.extend([pt] * b_lost)
            w_score += w_counts[pt] * piece_values[pt]
            b_score += b_counts[pt] * piece_values[pt]

        diff = w_score - b_score
        w_adv, b_adv = max(0, diff), max(0, -diff)

        sort_order = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
        w_captured.sort(key=lambda x: sort_order.index(x))
        b_captured.sort(key=lambda x: sort_order.index(x))

        p1_is_white = (self.player_color == chess.WHITE)
        p1_captured_pieces, ai_captured_pieces = (b_captured, w_captured) if p1_is_white else (w_captured, b_captured)
        p1_adv, ai_adv = (w_adv, b_adv) if p1_is_white else (b_adv, w_adv)

        def render_tray(frame, captured_list, capture_black, advantage):
            for pt in captured_list:
                symbol = chess.piece_symbol(pt).lower() if capture_black else chess.piece_symbol(pt).upper()
                if self.small_images.get(symbol): tk.Label(frame, image=self.small_images[symbol], bg="#1E1E1E", bd=0).pack(side="left")
            if advantage > 0: ctk.CTkLabel(frame, text=f"+{advantage}", font=("Arial", 14, "bold"), text_color="#A0A0A0").pack(side="left", padx=(5,0))

        render_tray(self.p1_material_frame, p1_captured_pieces, p1_is_white, p1_adv)
        render_tray(self.ai_material_frame, ai_captured_pieces, not p1_is_white, ai_adv)

    def draw_arrow_line(self, start_sq, end_sq):
        if self.is_flipped: sc, sr, ec, er = 7 - (start_sq % 8), start_sq // 8, 7 - (end_sq % 8), end_sq // 8
        else: sc, sr, ec, er = start_sq % 8, 7 - (start_sq // 8), end_sq % 8, 7 - (end_sq // 8)
            
        x1, y1 = sc * self.square_size + self.square_size / 2, sr * self.square_size + self.square_size / 2
        x2, y2 = ec * self.square_size + self.square_size / 2, er * self.square_size + self.square_size / 2
        self.canvas.create_line(x1, y1, x2, y2, fill="#15B53B", width=10, arrow=tk.LAST, arrowshape=(18, 22, 8))

    def get_square_from_coords(self, x, y):
        col, row = int(x // self.square_size), int(y // self.square_size)
        if col > 7 or col < 0 or row > 7 or row < 0: return None
        return row * 8 + (7 - col) if self.is_flipped else (7 - row) * 8 + col

    def on_square_clicked(self, event):
        square = self.get_square_from_coords(event.x, event.y)
        if square is None or self.is_paused: return
        self.colored_squares.clear()
        self.arrows.clear()

        if self.game.board.turn != self.player_color:
            if self.premove_selected_square is None:
                self.premove_selected_square = square
            elif square == self.premove_selected_square: self.premove_selected_square = None
            elif len(self.premove_queue) < 2:
                promo = chess.QUEEN if (square // 8 == 0 or square // 8 == 7) else None
                self.premove_queue.append(chess.Move(self.premove_selected_square, square, promotion=promo))
                self.premove_selected_square = None
            self.draw_board()
            return

        if self.selected_square is None:
            if self.game.board.piece_at(square) and self.game.board.color_at(square) == self.game.board.turn:
                self.selected_square = square
        else:
            if square == self.selected_square: self.selected_square = None
            else:
                moving_piece = self.game.board.piece_at(self.selected_square)
                move = chess.Move(self.selected_square, square)
                
                if moving_piece and moving_piece.piece_type == chess.PAWN and (square // 8 == 0 or square // 8 == 7):
                    if chess.Move(self.selected_square, square, promotion=chess.QUEEN) in self.game.board.legal_moves:
                        move = chess.Move(self.selected_square, square, promotion=self.ask_promotion())

                if move in self.game.board.legal_moves:
                    if self.redo_stack: self.redo_stack.clear()
                    game_over = self.commit_move(move)
                    self.selected_square = None
                    if not game_over: self.trigger_ai_move()
                else: self.selected_square = None
        self.draw_board()

    def on_right_click_press(self, event):
        self.premove_queue.clear()
        self.premove_selected_square = None
        self.draw_board()
        square = self.get_square_from_coords(event.x, event.y)
        if square is not None: self.drag_start_square = square

    def on_right_click_drag(self, event): pass

    def on_right_click_release(self, event):
        square = self.get_square_from_coords(event.x, event.y)
        if square is not None and self.drag_start_square is not None:
            if square == self.drag_start_square:
                if square in self.colored_squares: self.colored_squares.remove(square)
                else: self.colored_squares.add(square)
            else:
                arrow = (self.drag_start_square, square)
                if arrow in self.arrows: self.arrows.remove(arrow)
                else: self.arrows.append(arrow)
        self.drag_start_square = None
        self.draw_board()

    def commit_move(self, move):
        if self.__ip_signature != "@anthony_mishriky": sys.exit("UNAUTHORIZED MODIFICATION DETECTED.")
        if not self.game_started:
            self.game_started = True
            self.side_dropdown.configure(state="disabled")
            self.time_dropdown.configure(state="disabled")
            self.increment_switch.configure(state="disabled")
            if not self.is_untimed: self.pause_btn.configure(state="normal")

        self.redo_stack.clear()
        is_capture, is_castle, is_promotion = self.game.board.is_capture(move), self.game.board.is_castling(move), move.promotion is not None
        player_color = self.game.board.turn
        
        self.game.board.push(move)
        self.last_move = move
        self.update_history()
        
        if not self.is_untimed and self.increment_switch.get() == 1:
            if player_color == self.player_color: self.player_time += 3
            else: self.ai_time += 3
            self.update_ui_labels()

        is_game_over = self.game.board.is_game_over()
        if is_game_over:
            self.clock_running = False
            res = self.game.board.result()
            if (res == "1-0" and self.player_color == chess.WHITE) or (res == "0-1" and self.player_color == chess.BLACK):
                self.play_sound('win'); self.save_match_data("win"); self.show_game_over_modal("Victory", "You won by checkmate.")
            elif res in ["1-0", "0-1"]:
                self.play_sound('lose'); self.save_match_data("loss"); self.show_game_over_modal("Defeat", "You lost by checkmate.")
            else:
                self.play_sound('move'); self.save_match_data("draw"); self.show_game_over_modal("Draw", "The game ended in a draw.")
        elif self.game.board.is_check(): self.play_sound('check')
        elif is_promotion: self.play_sound('promotion')
        elif is_castle: self.play_sound('castle')
        elif is_capture: self.play_sound('capture')
        else: self.play_sound('move')
            
        self.draw_board()
        return is_game_over

    def trigger_ai_move(self):
        threading.Thread(target=self.calculate_ai, args=(self.game.board.copy(), self.current_game_id), daemon=True).start()

    def calculate_ai(self, board_copy, thread_game_id):
        start_time = time.time()
        move = self.ai.get_move(board_copy)
        execution_duration = time.time() - start_time
        if self.is_untimed:
            if execution_duration < 1.0: time.sleep(1.0 - execution_duration)
        else:
            pacing = 1.0 if self.ai_time > 60 else 0.5
            if execution_duration < pacing: time.sleep(pacing - execution_duration)
        if self.current_game_id == thread_game_id: self.after(0, self.apply_ai_move, move, thread_game_id)

    def apply_ai_move(self, move, thread_game_id):
        if self.current_game_id != thread_game_id: return
        if move and not self.commit_move(move) and not self.is_paused:
            self.process_premoves()

    def process_premoves(self):
        if self.premove_queue:
            q_move = self.premove_queue.pop(0)
            if q_move in self.game.board.legal_moves:
                if not self.commit_move(q_move): self.trigger_ai_move()
            else:
                self.premove_queue.clear()
                self.draw_board()

    def step_back(self):
        if self.game.board.move_stack:
            self.current_game_id += 1 
            self.premove_queue.clear()
            self.premove_selected_square = None
            self.selected_square = None
            
            self.redo_stack.append(self.game.board.pop())
            self.last_move = self.game.board.peek() if self.game.board.move_stack else None
            self.update_history()
            self.draw_board()

    def step_forward(self):
        if self.redo_stack:
            self.current_game_id += 1 
            self.premove_queue.clear()
            self.premove_selected_square = None
            self.selected_square = None
            
            move = self.redo_stack.pop()
            self.game.board.push(move)
            self.last_move = move
            self.update_history()
            self.draw_board()
            
            if not self.redo_stack and self.game.board.turn != self.player_color and not self.game.board.is_game_over() and not self.is_paused:
                self.trigger_ai_move()

    def save_match_data(self, result_status):
        os.makedirs("data", exist_ok=True)
        file_path = "data/match_history.json"
        
        data = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f: data = json.load(f)
            except Exception: pass

        move_list_uci = [m.uci() for m in self.game.board.move_stack]

        match_record = {
            "id": str(int(time.time())),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "name": f"Game {len(data) + 1}",
            "result": result_status,
            "moves": len(self.game.board.move_stack) // 2,
            "fen": self.game.board.fen(),
            "move_list": move_list_uci
        }
        
        data.append(match_record)
        try:
            with open(file_path, "w") as f: json.dump(data, f, indent=4)
        except Exception: pass

    def show_game_over_modal(self, title, message):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Game Over")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        try:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 200
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 125
            dialog.geometry(f"+{x}+{y}")
        except Exception: pass
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title, font=("Arial", 28, "bold")).pack(pady=(30, 10))
        ctk.CTkLabel(dialog, text=message, font=("Arial", 16)).pack(pady=(0, 30))
        def close_modal():
            dialog.destroy()
            self.reset_game_state(is_new_game_btn=False)
        ctk.CTkButton(dialog, text="Return to Board", width=150, height=40, command=close_modal).pack()

    def ask_promotion(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Promote")
        dialog.geometry("340x100")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        try:
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 170
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 50
            dialog.geometry(f"+{x}+{y}")
        except Exception: pass
        dialog.grab_set()
        
        self.promotion_choice = chess.QUEEN
        def set_choice(choice):
            self.promotion_choice = choice
            dialog.destroy()
            
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=10, pady=15)
        ctk.CTkButton(frame, text="♛ Queen", width=70, command=lambda: set_choice(chess.QUEEN)).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="♜ Rook", width=70, command=lambda: set_choice(chess.ROOK)).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="♝ Bishop", width=70, command=lambda: set_choice(chess.BISHOP)).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="♞ Knight", width=70, command=lambda: set_choice(chess.KNIGHT)).pack(side="left", padx=5)
        self.wait_window(dialog)
        return self.promotion_choice

    def update_ui_labels(self):
        try:
            with open("data/settings.json", "r") as f: settings = json.load(f)
        except Exception: settings = {"player_name": "Human", "peak_elo": 500}
            
        player_name = settings.get("player_name", "Human")
        peak_elo = settings.get("peak_elo", 500)
        
        if hasattr(self, 'peak_elo_label'):
            self.peak_elo_label.configure(text=f"Peak ELO: {peak_elo}")

        p1_color_str = "White" if self.player_color == chess.WHITE else "Black"
        ai_color_str = "Black" if self.player_color == chess.WHITE else "White"
        
        p1_time_str = "∞" if self.is_untimed else self.format_time(self.player_time)
        ai_time_str = "∞" if self.is_untimed else self.format_time(self.ai_time)
        
        self.p1_clock_label.configure(text=f"{player_name} ({p1_color_str}): {p1_time_str}")
        self.ai_clock_label.configure(text=f"AI ({ai_color_str}): {ai_time_str}")
        self.history_header.configure(text=f"History ({player_name}: {p1_color_str})")

    def toggle_pause(self):
        if not self.game_started or self.is_untimed: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.configure(text="Resume", fg_color="#D2691E", hover_color="#A0522D")
            self.canvas.configure(bg="#1E1E1E")
        else:
            self.pause_btn.configure(text="Pause", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#326ca8", "#14375e"])
            self.canvas.configure(bg="#2B2B2B")

    def set_player_side(self, choice):
        if self.game_started: return
        self.player_color = chess.BLACK if choice == "Black" else chess.WHITE
        self.is_flipped = (self.player_color == chess.BLACK)
        self.update_ui_labels()
        self.draw_board()

    def set_time_control(self, choice):
        if self.game_started: return
        if choice == "No Limit":
            self.is_untimed = True
            self.increment_switch.deselect()
            self.increment_switch.configure(state="disabled")
        else:
            self.is_untimed = False
            self.increment_switch.configure(state="normal")
            minutes = int(choice.split()[0])
            self.player_time = self.ai_time = minutes * 60
        self.update_ui_labels()

    def format_time(self, seconds):
        if seconds <= 0: return "00:00"
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def update_clocks(self):
        self.after(1000, self.update_clocks)
        if self.clock_running and self.game_started and not self.is_untimed and not self.is_paused:
            if self.game.board.turn == self.player_color:
                self.player_time -= 1
                if self.player_time in [60, 30, 10] and not getattr(self, f"player_warned_{self.player_time}"):
                    self.play_sound('low_time'); setattr(self, f"player_warned_{self.player_time}", True)
                if self.player_time <= 0: self.handle_timeout(winner="AI")
            else:
                self.ai_time -= 1
                if self.ai_time in [60, 30, 10] and not getattr(self, f"ai_warned_{self.ai_time}"):
                    self.play_sound('low_time'); setattr(self, f"ai_warned_{self.ai_time}", True)
                if self.ai_time <= 0: self.handle_timeout(winner="P1")
            self.update_ui_labels()

    def reset_game_state(self, is_new_game_btn=False):
        self.current_game_id += 1 
        self.game.board.reset()
        self.last_move = self.selected_square = self.premove_selected_square = None
        self.premove_queue.clear()
        self.redo_stack.clear()
        self.colored_squares.clear()
        self.arrows.clear()
        
        self.is_paused = False
        self.pause_btn.configure(state="disabled", text="Pause", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#326ca8", "#14375e"])
        self.canvas.configure(bg="#2B2B2B")
        
        self.side_dropdown.configure(state="normal")
        self.time_dropdown.configure(state="normal")
        self.increment_switch.configure(state="normal" if self.time_dropdown.get() != "No Limit" else "disabled")
            
        self.game_started = False
        self.clock_running = True
        self.player_warned_60 = self.player_warned_30 = self.player_warned_10 = False
        self.ai_warned_60 = self.ai_warned_30 = self.ai_warned_10 = False
        
        self.set_time_control(self.time_dropdown.get())
        self.update_history()
        self.draw_board()
        
        if is_new_game_btn and self.player_color == chess.BLACK:
            self.game_started = True
            self.side_dropdown.configure(state="disabled")
            self.time_dropdown.configure(state="disabled")
            self.increment_switch.configure(state="disabled")
            if not self.is_untimed: self.pause_btn.configure(state="normal")
            self.trigger_ai_move()

    def handle_new_game(self): self.reset_game_state(is_new_game_btn=True)

    def handle_forfeit(self):
        if not self.game_started: return
        self.clock_running = False
        self.play_sound('lose')
        self.save_match_data("loss")
        self.show_game_over_modal("Resignation", "You forfeited the match.")

    def update_history(self):
        self.history_box.delete("0.0", "end")
        temp_board = chess.Board()
        history_text = ""
        moves = list(self.game.board.move_stack)
        for i in range(0, len(moves), 2):
            w_move = temp_board.san(moves[i])
            temp_board.push(moves[i])
            if i + 1 < len(moves):
                b_move = temp_board.san(moves[i+1])
                temp_board.push(moves[i+1])
            else: b_move = ""
            history_text += f"{(i//2) + 1}.  {w_move:<10}{b_move:>10}\n"
        self.history_box.insert("0.0", history_text)

    def handle_timeout(self, winner):
        self.clock_running = False
        if winner == "P1":
            self.play_sound('win'); self.save_match_data("win"); self.show_game_over_modal("Victory", "Opponent ran out of time.")
        else:
            self.play_sound('lose'); self.save_match_data("loss"); self.show_game_over_modal("Timeout", "You ran out of time.")