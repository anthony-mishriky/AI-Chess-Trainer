# ==============================================================================
# Author/Instagram: @anthony_mishriky
# LinkedIn: www.linkedin.com/in/anthony-mishriky
# Email: anthonymishrikyprivate@gmail.com
# ==============================================================================
import json
import os
import random
import chess
import chess.engine

class AIOpponent:
    def __init__(self, history_file="data/match_history.json"):
        self.history_file = history_file
        self.engine_path = "engine_bin/stockfish"
        if os.path.exists(self.engine_path + ".exe"):
            self.engine_path += ".exe"
        self.base_elo = 300
        self.engine = None
        try:
            if os.path.exists(self.engine_path):
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
        except Exception:
            pass

    def get_target_elo(self):
        if not os.path.exists(self.history_file):
            return self.base_elo
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
            wins = sum(1 for match in data if match.get('outcome') == 'win')
            losses = sum(1 for match in data if match.get('outcome') == 'loss')
            elo = self.base_elo + (wins * 50) - (losses * 50)
            return max(300, min(elo, 2500))
        except Exception:
            return self.base_elo

    def get_move(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        if not self.engine:
            return random.choice(legal_moves)
        try:
            target_elo = self.get_target_elo()
            # Run a brief, safe evaluation burst to fetch the top move choices
            info = self.engine.analyse(board, chess.engine.Limit(time=0.1), multipv=5)
            valid_moves = []
            if isinstance(info, list):
                for line in info:
                    if "pv" in line and len(line["pv"]) > 0:
                        valid_moves.append(line["pv"][0])
            elif "pv" in info and len(info["pv"]) > 0:
                valid_moves.append(info["pv"][0])
                
            if not valid_moves:
                return random.choice(legal_moves)
                
            # Sabotage logic based on current target Elo
            if target_elo <= 400:
                if len(valid_moves) >= 4 and random.random() < 0.7:
                    return valid_moves[3]
                return random.choice(valid_moves)
            elif target_elo <= 800:
                if len(valid_moves) >= 3 and random.random() < 0.6:
                    return valid_moves[2]
                return valid_moves[0]
            elif target_elo <= 1200:
                if len(valid_moves) >= 2 and random.random() < 0.4:
                    return valid_moves[1]
                return valid_moves[0]
            else:
                return valid_moves[0]
        except Exception:
            return random.choice(legal_moves)

    def close(self):
        if self.engine:
            self.engine.quit()