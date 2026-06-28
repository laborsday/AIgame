"""Unit tests for the Rules class — win detection."""
import pytest

from app.game.board import Board, BLACK, WHITE
from app.game.rules import Rules


class TestRules:
    def test_no_winner_empty_board(self):
        board = Board()
        board.last_move = None
        assert Rules.check_win(board) is None

    def test_win_horizontal(self):
        board = Board()
        for c in range(5):
            board.place_stone(7, c, BLACK)
        assert Rules.check_win(board) == BLACK

    def test_win_vertical(self):
        board = Board()
        for r in range(5):
            board.place_stone(r, 3, WHITE)
        assert Rules.check_win(board) == WHITE

    def test_win_diagonal_down(self):
        board = Board()
        for i in range(5):
            board.place_stone(i, i, BLACK)
        assert Rules.check_win(board) == BLACK

    def test_win_diagonal_up(self):
        board = Board()
        for i in range(5):
            board.place_stone(10 - i, i, WHITE)
        assert Rules.check_win(board) == WHITE

    def test_win_at_edge(self):
        board = Board()
        # Five in a row starting at col 10 to col 14
        for c in range(10, 15):
            board.place_stone(0, c, BLACK)
        assert Rules.check_win(board) == BLACK

    def test_four_in_a_row_is_not_win(self):
        board = Board()
        for c in range(4):
            board.place_stone(7, c, BLACK)
        assert Rules.check_win(board) is None

    def test_interrupted_five_is_not_win(self):
        board = Board()
        board.place_stone(7, 0, BLACK)
        board.place_stone(7, 1, BLACK)
        board.place_stone(7, 2, BLACK)
        board.place_stone(7, 3, WHITE)  # interruption
        board.place_stone(7, 4, BLACK)
        board.place_stone(7, 5, BLACK)
        board.place_stone(7, 6, BLACK)
        board.place_stone(7, 7, BLACK)
        assert Rules.check_win(board) is None

    def test_six_in_a_row_is_win(self):
        board = Board()
        for c in range(6):
            board.place_stone(7, c, BLACK)
        assert Rules.check_win(board) == BLACK

    def test_check_only_last_move(self):
        """Ensure only the last move's stone is checked for win."""
        board = Board()
        # Place 4 black stones in a row (not win)
        for c in range(4):
            board.place_stone(7, c, BLACK)
        assert Rules.check_win(board) is None
        # Place next black — but place white elsewhere first to change last_move
        board.place_stone(0, 0, WHITE)
        assert Rules.check_win(board) is None  # last move was white at (0,0)

    def test_is_draw_full_board(self):
        board = Board(3)
        # Fill without anyone winning
        for r in range(3):
            for c in range(3):
                board.place_stone(r, c, BLACK if (r + c) % 2 == 0 else WHITE)
        assert Rules.is_draw(board)
