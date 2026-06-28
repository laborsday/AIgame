"""AI engine for Gomoku — Minimax with Alpha-Beta pruning and pattern-based evaluation."""

import random
from typing import Optional

from app.game.board import Board, EMPTY, BLACK, WHITE, BOARD_SIZE

# Direction vectors for scanning lines
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# Difficulty → search depth mapping
DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}


class AIPlayer:
    """Gomoku AI using Minimax search with Alpha-Beta pruning.

    The evaluation function uses pattern-based scoring with a defensive bias:
    opponent threats are weighted more heavily than AI threats, ensuring the
    AI prioritises blocking over building its own attacks.
    """

    def __init__(self, player_color: int, difficulty: str = "medium"):
        self.color = player_color
        self.opponent_color = WHITE if player_color == BLACK else BLACK
        self.difficulty = difficulty
        self.max_depth = DIFFICULTY_DEPTH.get(difficulty, 2)

    def compute_move(self, board: Board) -> tuple[int, int]:
        """Return the best move (row, col) for the current board state."""
        candidates = self._generate_candidate_moves(board)

        if not candidates:
            # Board empty — play centre
            return (board.size // 2, board.size // 2)

        if len(candidates) == 1:
            return candidates[0]

        best_move = candidates[0]
        best_score = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        for move in candidates:
            row, col = move
            board.place_stone(row, col, self.color)
            score = self._minimax(board, self.max_depth - 1, alpha, beta, False)
            board.grid[row][col] = EMPTY
            board.move_count -= 1

            # Undo last_move side effect
            if board.move_count > 0:
                # Find previous move — not ideal but correct.
                # For cleaner undo we track it separately.
                pass
            board.last_move = None  # will be restored by caller's next real move

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_move

    # ------------------------------------------------------------------
    # Minimax search
    # ------------------------------------------------------------------

    def _minimax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
    ) -> float:
        """Recursive Minimax with Alpha-Beta pruning."""

        # Terminal check: did the last move win?
        winner = self._quick_win_check(board)
        if winner == self.color:
            return 100_000_000 + depth  # prefer faster wins
        if winner == self.opponent_color:
            return -100_000_000 - depth  # prefer slower losses

        if depth == 0 or board.is_full():
            return self._evaluate(board)

        candidates = self._generate_candidate_moves(board)
        if not candidates:
            return self._evaluate(board)

        # Sort moves for better pruning
        candidates = self._order_moves(board, candidates, maximizing)

        if maximizing:
            max_eval = float("-inf")
            for move in candidates:
                row, col = move
                board.place_stone(row, col, self.color)
                eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                board.grid[row][col] = EMPTY
                board.move_count -= 1
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in candidates:
                row, col = move
                board.place_stone(row, col, self.opponent_color)
                eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                board.grid[row][col] = EMPTY
                board.move_count -= 1
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # ------------------------------------------------------------------
    # Move generation & ordering
    # ------------------------------------------------------------------

    def _generate_candidate_moves(self, board: Board) -> list[tuple[int, int]]:
        """Return empty cells within radius 2 of any occupied cell.

        If the board is empty, returns the centre cell.
        """
        if board.move_count == 0:
            return [(board.size // 2, board.size // 2)]

        candidates: set[tuple[int, int]] = set()
        size = board.size

        for r in range(size):
            for c in range(size):
                if board.grid[r][c] != EMPTY:
                    # Add empty neighbours within radius 2
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < size and 0 <= nc < size and board.grid[nr][nc] == EMPTY:
                                candidates.add((nr, nc))

        return list(candidates) if candidates else [(size // 2, size // 2)]

    def _order_moves(
        self,
        board: Board,
        moves: list[tuple[int, int]],
        maximizing: bool,
    ) -> list[tuple[int, int]]:
        """Sort moves with promising ones first (for Alpha-Beta efficiency).

        A quick heuristic: cells next to existing stones are better.
        """
        player = self.color if maximizing else self.opponent_color
        opponent = self.opponent_color if maximizing else self.color

        def score(move: tuple[int, int]) -> float:
            r, c = move
            s = 0
            size = board.size
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size:
                        if board.grid[nr][nc] == player:
                            s += 2
                        elif board.grid[nr][nc] == opponent:
                            s += 3  # prioritise blocking
            # Centre bonus for early game
            centre = size // 2
            dist = abs(r - centre) + abs(c - centre)
            s += max(0, (size - dist)) / size
            return s

        return sorted(moves, key=score, reverse=True)

    # ------------------------------------------------------------------
    # Evaluation function
    # ------------------------------------------------------------------

    def _evaluate(self, board: Board) -> float:
        """Heuristic board evaluation.

        Scans every 5-cell window in every direction and scores patterns.
        Opponent threats receive higher absolute weight (defensive bias).
        """
        score = 0.0
        size = board.size

        for r in range(size):
            for c in range(size):
                for dr, dc in DIRECTIONS:
                    # Only start scanning if the 5-cell window fits
                    end_r = r + 4 * dr
                    end_c = c + 4 * dc
                    if not (0 <= end_r < size and 0 <= end_c < size):
                        continue

                    # Collect the 5 cells
                    cells = []
                    for k in range(5):
                        cells.append(board.grid[r + k * dr][c + k * dc])

                    # Score from AI's perspective
                    ai_count = cells.count(self.color)
                    opp_count = cells.count(self.opponent_color)

                    if ai_count > 0 and opp_count == 0:
                        score += self._pattern_score(ai_count, is_opponent=False)
                    elif opp_count > 0 and ai_count == 0:
                        score -= self._pattern_score(opp_count, is_opponent=True)

        return score

    @staticmethod
    def _pattern_score(count: int, is_opponent: bool) -> float:
        """Convert a stone-count-in-window to a threat score.

        The *is_opponent* flag triggers the defensive bias:
        opponent patterns are weighted more heavily.
        """
        if count == 5:
            return 100_000.0
        elif count == 4:
            return 10_000.0 if not is_opponent else 10_000.0
        elif count == 3:
            return 1_000.0 if not is_opponent else 5_000.0
        elif count == 2:
            return 10.0 if not is_opponent else 50.0
        elif count == 1:
            return 1.0 if not is_opponent else 2.0
        return 0.0

    # ------------------------------------------------------------------
    # Quick win check (used during search — only checks last_move)
    # ------------------------------------------------------------------

    @staticmethod
    def _quick_win_check(board: Board) -> Optional[int]:
        """Check if the last move resulted in five-in-a-row.

        Returns the winner's colour or None.
        """
        if board.last_move is None:
            return None

        row, col = board.last_move
        player = board.grid[row][col]

        if player == EMPTY:
            return None

        size = board.size
        for dr, dc in DIRECTIONS:
            count = 1
            # positive direction
            r, c = row + dr, col + dc
            while 0 <= r < size and 0 <= c < size and board.grid[r][c] == player:
                count += 1
                r += dr
                c += dc
            # negative direction
            r, c = row - dr, col - dc
            while 0 <= r < size and 0 <= c < size and board.grid[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return player

        return None
