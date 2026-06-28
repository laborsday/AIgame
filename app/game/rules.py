"""Win-detection rules for Gomoku (five-in-a-row)."""

from typing import Optional

from app.game.board import Board, EMPTY, BLACK, WHITE, BOARD_SIZE

# Direction vectors for the four axes: horizontal, vertical, diagonal-down, diagonal-up
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


class Rules:
    """Static methods for checking win / draw conditions."""

    @staticmethod
    def check_win(board: Board) -> Optional[int]:
        """Check if the last move resulted in five-in-a-row.

        Returns BLACK or WHITE if there's a winner, otherwise None.
        """
        if board.last_move is None:
            return None

        row, col = board.last_move
        player = board.grid[row][col]

        if player == EMPTY:
            return None

        for dr, dc in DIRECTIONS:
            count = 1  # the stone just placed
            # Count in the positive direction
            count += Rules._count_in_direction(board, row, col, dr, dc, player)
            # Count in the negative direction
            count += Rules._count_in_direction(board, row, col, -dr, -dc, player)

            if count >= 5:
                return player

        return None

    @staticmethod
    def is_draw(board: Board) -> bool:
        """Return True if the board is full and there is no winner."""
        return board.is_full()

    @staticmethod
    def _count_in_direction(
        board: Board, row: int, col: int, dr: int, dc: int, player: int
    ) -> int:
        """Count consecutive stones of *player* starting one step from (row, col)."""
        count = 0
        r, c = row + dr, col + dc
        size = board.size

        while 0 <= r < size and 0 <= c < size and board.grid[r][c] == player:
            count += 1
            r += dr
            c += dc

        return count
