"""Board class for Gomoku — manages the 15x15 grid and stone placement."""

from typing import Optional

BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2


class Board:
    """A 15x15 Gomoku board.

    Attributes:
        size: Board dimension (default 15).
        grid: 2D list of integers (0=EMPTY, 1=BLACK, 2=WHITE).
        last_move: (row, col) of the most recent move, or None.
    """

    def __init__(self, size: int = BOARD_SIZE):
        self.size = size
        self.grid = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.last_move: Optional[tuple[int, int]] = None
        self.move_count: int = 0

    def place_stone(self, row: int, col: int, player: int) -> bool:
        """Place a stone for *player* at (row, col).

        Returns True on success, False if the cell is occupied or out of bounds.
        """
        if not self.is_valid_move(row, col):
            return False
        self.grid[row][col] = player
        self.last_move = (row, col)
        self.move_count += 1
        return True

    def is_valid_move(self, row: int, col: int) -> bool:
        """Check whether (row, col) is a legal move."""
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        return self.grid[row][col] == EMPTY

    def is_full(self) -> bool:
        """Return True if the board has no empty cells."""
        return self.move_count >= self.size * self.size

    def get_state(self) -> list[list[int]]:
        """Return a deep-copied 2D list of the current board state."""
        return [row[:] for row in self.grid]

    def reset(self):
        """Clear the board for a new game."""
        self.grid = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.last_move = None
        self.move_count = 0
