"""Unit tests for the Board class."""
import pytest

from app.game.board import Board, EMPTY, BLACK, WHITE


class TestBoard:
    def test_new_board_is_empty(self):
        board = Board()
        assert board.move_count == 0
        assert board.last_move is None
        for row in board.grid:
            assert all(cell == EMPTY for cell in row)

    def test_place_stone_valid(self):
        board = Board()
        assert board.place_stone(7, 7, BLACK)
        assert board.grid[7][7] == BLACK
        assert board.last_move == (7, 7)
        assert board.move_count == 1

    def test_place_stone_occupied(self):
        board = Board()
        board.place_stone(7, 7, BLACK)
        assert not board.place_stone(7, 7, WHITE)
        assert board.grid[7][7] == BLACK  # unchanged

    def test_place_stone_out_of_bounds(self):
        board = Board()
        assert not board.place_stone(-1, 0, BLACK)
        assert not board.place_stone(0, -1, BLACK)
        assert not board.place_stone(15, 0, BLACK)
        assert not board.place_stone(0, 15, BLACK)

    def test_is_valid_move(self):
        board = Board()
        assert board.is_valid_move(0, 0)
        assert board.is_valid_move(14, 14)
        assert not board.is_valid_move(-1, 0)
        assert not board.is_valid_move(0, 15)
        board.place_stone(0, 0, BLACK)
        assert not board.is_valid_move(0, 0)

    def test_is_full(self):
        board = Board(3)  # smaller test board
        for r in range(3):
            for c in range(3):
                assert not board.is_full()
                board.place_stone(r, c, BLACK if (r + c) % 2 == 0 else WHITE)
        assert board.is_full()

    def test_get_state_returns_copy(self):
        board = Board()
        state = board.get_state()
        state[0][0] = BLACK
        assert board.grid[0][0] == EMPTY

    def test_reset(self):
        board = Board()
        board.place_stone(7, 7, BLACK)
        board.place_stone(8, 8, WHITE)
        board.reset()
        assert board.move_count == 0
        assert board.last_move is None
        for row in board.grid:
            assert all(cell == EMPTY for cell in row)
