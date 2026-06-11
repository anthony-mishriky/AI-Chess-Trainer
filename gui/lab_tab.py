# ==============================================================================
# Author/Instagram: @anthony_mishriky
# LinkedIn: www.linkedin.com/in/anthony-mishriky
# Email: anthonymishrikyprivate@gmail.com
# ==============================================================================
import customtkinter as ctk
import json
import os
import shutil
import threading
import chess
import chess.engine
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LabTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=40, pady=(20, 0))
        ctk.CTkLabel(header_frame, text="The Lab", font=("Arial", 32, "bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Refresh Data", fg_color="#333333", hover_color="#444444", command=self.refresh_data).pack(side="right", pady=10)
        
        self.graph_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=(40, 10), pady=20)
        
        self.stats_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=15)
        self.stats_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 40), pady=20)
        
        self.controls_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=15, height=100)
        self.controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=40, pady=(0, 20))
        
        self.setup_controls()
        self.refresh_data()

    def get_settings(self):
        try:
            with open("data/settings.json", "r") as f:
                return json.load(f)
        except Exception:
            return {"player_name": "Human", "peak_elo": 500}

    def save_settings(self, settings_data):
        os.makedirs("data", exist_ok=True)
        try:
            with open("data/settings.json", "w") as f:
                json.dump(settings_data, f, indent=4)
        except Exception:
            pass

    def setup_controls(self):
        name_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        name_frame.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(name_frame, text="Player Name:", font=("Arial", 14)).pack(side="left", padx=(0, 10))
        self.name_entry = ctk.CTkEntry(name_frame, width=150)
        self.name_entry.insert(0, self.get_settings().get("player_name", "Human"))
        self.name_entry.pack(side="left", padx=(0, 10))
        ctk.CTkButton(name_frame, text="Save Name", width=100, fg_color="#3a7ebf", hover_color="#1f538d", command=self.save_name).pack(side="left")
        
        ctk.CTkButton(self.controls_frame, text="Reset Memory", fg_color="#8B0000", hover_color="#5C0000", command=self.reset_memory).pack(side="right", padx=20, pady=20)
        ctk.CTkButton(self.controls_frame, text="Export Brain", fg_color="#15B53B", hover_color="#108A2D", command=self.export_brain).pack(side="right", padx=10, pady=20)

    def save_name(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            settings = self.get_settings()
            settings["player_name"] = new_name
            self.save_settings(settings)
            self.refresh_data()

    def refresh_data(self):
        for widget in self.graph_frame.winfo_children(): widget.destroy()
        for widget in self.stats_frame.winfo_children(): widget.destroy()
            
        file_path = "data/match_history.json"
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
            
        elo_history = [500]
        current_elo = 500
        wins = losses = draws = 0
        K_FACTOR = 32 
        
        for match in data:
            result = match.get("result")
            opponent_elo = current_elo 
            
            expected_score = 1 / (1 + 10 ** ((opponent_elo - current_elo) / 400))
            
            if result == "win":
                actual_score = 1.0
                wins += 1
            elif result == "loss":
                actual_score = 0.0
                losses += 1
            else:
                actual_score = 0.5
                draws += 1
                
            elo_change = round(K_FACTOR * (actual_score - expected_score))
            current_elo += elo_change
            elo_history.append(current_elo)
            
        peak_elo = max(elo_history)
        
        settings = self.get_settings()
        if settings.get("peak_elo", 500) != peak_elo:
            settings["peak_elo"] = peak_elo
            self.save_settings(settings)
            
        player_name = settings.get("player_name", "Human")
            
        fig = Figure(figsize=(6, 4), dpi=100, facecolor='#1E1E1E')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1E1E1E')
        ax.plot(elo_history, color='#15B53B', linewidth=2, marker='o')
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('#333333')
            
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill="both", padx=10, pady=10)
        
        ctk.CTkLabel(self.stats_frame, text=f"{player_name}'s Analytics", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(self.stats_frame, text=f"Total Games: {len(data)}", font=("Arial", 16)).pack(pady=5)
        ctk.CTkLabel(self.stats_frame, text=f"Wins: {wins} | Losses: {losses} | Draws: {draws}", font=("Arial", 16)).pack(pady=5)
        ctk.CTkLabel(self.stats_frame, text=f"Current ELO: {current_elo}", font=("Arial", 24, "bold"), text_color="#3a7ebf").pack(pady=(20, 5))
        ctk.CTkLabel(self.stats_frame, text=f"Peak ELO: {peak_elo}", font=("Arial", 16, "bold"), text_color="#15B53B").pack(pady=(0, 20))
        
        self.blind_spot_label = ctk.CTkLabel(self.stats_frame, text="Tactical Blind Spot: Scanning Engine...", font=("Arial", 14, "italic"), text_color="#A0A0A0")
        self.blind_spot_label.pack(pady=20)

        if data:
            threading.Thread(target=self.calculate_blind_spot, args=(data,), daemon=True).start()
        else:
            self.blind_spot_label.configure(text="Tactical Blind Spot: Play more games to scan!")
        
    def calculate_blind_spot(self, data):
        engine_path = "engine_bin/stockfish"
        if os.path.exists(engine_path + ".exe"): engine_path += ".exe"
        if not os.path.exists(engine_path):
            self.after(0, lambda: self.blind_spot_label.configure(text="Tactical Blind Spot: Stockfish not found."))
            return

        blundered_squares = {}
        try:
            engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            
            # Analyze up to the last 5 games to keep loading times fast
            for match in data[-5:]:
                board = chess.Board()
                prev_score = 0.0
                
                for move_uci in match.get("move_list", []):
                    move = chess.Move.from_uci(move_uci)
                    
                    # Quick lightning calculation (depth=8 is near instant)
                    info = engine.analyse(board, chess.engine.Limit(depth=8))
                    score_obj = info["score"].white()
                    current_score = 10.0 if score_obj.is_mate() and score_obj.mate() > 0 else -10.0 if score_obj.is_mate() else score_obj.score(mate_score=1000) / 100.0

                    if board.turn == chess.WHITE:
                        drop = prev_score - current_score
                    else:
                        drop = current_score - prev_score

                    # A drop of more than 1.5 points evaluates to a Blunder
                    if drop > 1.5:
                        target_square = chess.square_name(move.to_square)
                        blundered_squares[target_square] = blundered_squares.get(target_square, 0) + 1

                    prev_score = current_score
                    board.push(move)

            engine.quit()

            if blundered_squares:
                worst_square = max(blundered_squares, key=blundered_squares.get)
                message = f"Tactical Blind Spot: You blunder heavily on {worst_square.upper()}"
            else:
                message = "Tactical Blind Spot: No major blunders detected recently!"

            self.after(0, lambda: self.blind_spot_label.configure(text=message, text_color="#D2691E"))
            
        except Exception as e:
            self.after(0, lambda: self.blind_spot_label.configure(text="Tactical Blind Spot: Scan Failed"))

    def reset_memory(self):
        file_path = "data/match_history.json"
        if os.path.exists(file_path): os.remove(file_path)
        self.save_settings({"player_name": self.get_settings().get("player_name", "Human"), "peak_elo": 500})
        self.refresh_data()

    def export_brain(self):
        file_path = "data/match_history.json"
        if os.path.exists(file_path):
            try: shutil.copy(file_path, "exported_brain.json")
            except Exception: pass