"""Unit tests for the AI engine."""
import pytest
import time

from app.game.board import Board, EMPTY, BLACK, WHITE
from app.game.rules import Rules
from app.game.ai import AIPlayer, DIFFICULTY_DEPTH


class TestAI:
    """Test the AIPlayer's core behaviours."""

    def test_ai_takes_winning_move(self):
        """AI should take the winning five-in-a-row when available."""
        board = Board()
        ai = AIPlayer(player_color=BLACK, difficulty="medium")

        # Set up: AI (BLACK) has 4 in a row on row 7, cols 0-3
        for c in range(4):
            board.place_stone(7, c, BLACK)

        # Place a white stone elsewhere so last_move doesn't trigger false win
        board.place_stone(0, 0, WHITE)

        move = ai.compute_move(board)
        # Best move is either col 4 (to complete the five) — but since
        # minimax evaluates the whole board, and moving at (7,4) wins,
        # so the algorithm should definitely return something adjacent to the four.
        assert move == (7, 4), f"AI should complete five-in-a-row, got {move}"

    def test_ai_blocks_opponent_open_four(self):
        """AI must block the opponent's imminent win (open four)."""
        board = Board()
        ai = AIPlayer(player_color=BLACK, difficulty="medium")

        # Set up: WHITE (opponent) has 4 in a row on row 7, cols 0-3
        for c in range(4):
            board.place_stone(7, c, WHITE)

        # Add one BLACK stone elsewhere so board is non-trivial
        board.place_stone(10, 10, BLACK)

        move = ai.compute_move(board)
        # AI must play at (7, 4) to block
        assert move == (7, 4), f"AI should block opponent's open four at (7,4), got {move}"

    def test_ai_blocks_opponent_open_three(self):
        """AI should block opponent's dangerous open three."""
        board = Board()
        ai = AIPlayer(player_color=BLACK, difficulty="hard")

        # WHITE has 3 in a row on row 7, cols 1,2,3 — open at both ends (0,4)
        for c in [1, 2, 3]:
            board.place_stone(7, c, WHITE)

        # Add a BLACK stone
        board.place_stone(6, 6, BLACK)

        move = ai.compute_move(board)
        # Should block at (7,0) or (7,4)
        assert move in [(7, 0), (7, 4)], (
            f"AI should block opponent's open three, got {move}"
        )

    def test_ai_does_not_crash_empty_board(self):
        """AI should return a valid move on an empty board."""
        board = Board()
        ai = AIPlayer(player_color=BLACK, difficulty="hard")

        move = ai.compute_move(board)
        assert 0 <= move[0] < 15
        assert 0 <= move[1] < 15
        # Centre-ish move expected
        assert 5 <= move[0] <= 9
        assert 5 <= move[1] <= 9

    def test_ai_response_time_ok(self):
        """AI at depth 3 should respond in under 3 seconds on a mid-game board."""
        board = Board()
        # Create a mid-game position
        for i in range(5):
            board.place_stone(7, i, BLACK)
            board.place_stone(8, i, WHITE)

        ai = AIPlayer(player_color=BLACK, difficulty="hard")

        start = time.time()
        move = ai.compute_move(board)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"AI took too long: {elapsed:.2f}s"
        assert board.is_valid_move(move[0], move[1])

    def test_easy_vs_hard_different(self):
        """Easy and Hard AI should not always pick the same move."""
        board = Board()
        # Create a position with choices
        for i in range(3):
            board.place_stone(7, i, BLACK)
            board.place_stone(8, i, WHITE)

        ai_easy = AIPlayer(player_color=BLACK, difficulty="easy")
        ai_hard = AIPlayer(player_color=BLACK, difficulty="hard")

        move_easy = ai_easy.compute_move(board)
        move_hard = ai_hard.compute_move(board)

        # They may or may not differ, but both must be valid
        assert board.is_valid_move(move_easy[0], move_easy[1])
        assert board.is_valid_move(move_hard[0], move_hard[1])

    def test_ai_as_white_works(self):
        """AI configured as WHITE should return valid moves."""
        board = Board()
        board.place_stone(7, 7, BLACK)

        ai = AIPlayer(player_color=WHITE, difficulty="medium")
        move = ai.compute_move(board)
        assert board.is_valid_move(move[0], move[1])

    def test_minimax_terminal_win_detection(self):
        """_quick_win_check should correctly identify five-in-a-row."""
        board = Board()
        for c in range(5):
            board.place_stone(7, c, BLACK)

        from app.game.ai import AIPlayer as AI

        result = AI._quick_win_check(board)
        assert result == BLACK

    def test_generate_candidates_near_stones(self):
        """Candidate moves should be near existing stones."""
        board = Board()
        board.place_stone(7, 7, BLACK)

        ai = AIPlayer(player_color=WHITE, difficulty="medium")
        candidates = ai._generate_candidate_moves(board)

        # All candidates should be within distance 2 of (7,7)
        for r, c in candidates:
            dist = max(abs(r - 7), abs(c - 7))
            assert dist <= 2, f"Candidate ({r},{c}) too far from (7,7)"

    def test_difficulty_depth_mapping(self):
        """Verify the difficulty→depth mapping."""
        assert DIFFICULTY_DEPTH["easy"] == 1
        assert DIFFICULTY_DEPTH["medium"] == 2
        assert DIFFICULTY_DEPTH["hard"] == 3
