# ==============================================================================
# Author/Instagram: @anthony_mishriky
# LinkedIn: www.linkedin.com/in/anthony-mishriky
# Email: anthonymishrikyprivate@gmail.com
# ==============================================================================
import chess

class GameManager:
    def __init__(self):
        self.board = chess.Board()

    def make_move(self, uci_move: str) -> bool:
        try:
            move = chess.Move.from_uci(uci_move)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False

    def takeback(self):
        if len(self.board.move_stack) > 0:
            self.board.pop()

    def get_fen(self):
        return self.board.fen()
        
    def reset_game(self):
        self.board.reset()