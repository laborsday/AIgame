"""Skill-mode game engine — HP bars, skill cards, and bleed mechanics."""

import random
from enum import Enum
from typing import Optional

from app.game.board import Board, EMPTY, BLACK, WHITE, BOARD_SIZE
from app.game.rules import Rules

# ── Skill types ───────────────────────────────────────────────
class Skill(Enum):
    FEI_SHA_ZOU_SHI = "feisha"     # 飞沙走石: remove opponent stone
    TOU_TIAN_HUAN_RI = "toutian"   # 偷天换日: convert opponent stone to yours
    WU_XIE_KE_JI = "wuxie"         # 无懈可击: counter (react to opponent skill)
    JING_RU_ZHI_SHUI = "jingru"    # 静如止水: freeze opponent 1 turn

# Skill name display
SKILL_NAMES = {
    Skill.FEI_SHA_ZOU_SHI: "飞沙走石",
    Skill.TOU_TIAN_HUAN_RI: "偷天换日",
    Skill.WU_XIE_KE_JI: "无懈可击",
    Skill.JING_RU_ZHI_SHUI: "静如止水",
}

SKILL_EMOJI = {
    Skill.FEI_SHA_ZOU_SHI: "🪨",
    Skill.TOU_TIAN_HUAN_RI: "🔄",
    Skill.WU_XIE_KE_JI: "🛡️",
    Skill.JING_RU_ZHI_SHUI: "❄️",
}

# Draw pool weights
SKILL_POOL = (
    [Skill.FEI_SHA_ZOU_SHI] * 40
    + [Skill.TOU_TIAN_HUAN_RI] * 15
    + [Skill.WU_XIE_KE_JI] * 20
    + [Skill.JING_RU_ZHI_SHUI] * 25
)

MAX_HAND_SIZE = 3
MAX_HP = 5
SKILL_GRANT_INTERVAL = 5  # every N turns


class SkillGameState:
    """Full game state for skill mode."""

    def __init__(self, human_color: int, difficulty: str = "medium"):
        self.board = Board()
        self.human_color = human_color
        self.ai_color = WHITE if human_color == BLACK else BLACK
        self.current_turn = BLACK  # Black always goes first
        self.game_over = False
        self.winner = 0  # 0=none, 1=human, 2=ai, 3=draw

        # HP
        self.human_hp = MAX_HP
        self.ai_hp = MAX_HP

        # Skills
        self.human_hand: list[Skill] = []
        self.ai_hand: list[Skill] = []

        # Active five-in-a-rows (per player)
        self.human_fives: list[set[tuple[int, int]]] = []  # list of 5-stone sets
        self.ai_fives: list[set[tuple[int, int]]] = []

        # Freeze status
        self.human_frozen = False
        self.ai_frozen = False

        # Turn counter
        self.turn_number = 0

        # Difficulty
        self.difficulty = difficulty

        # Last move tracking
        self.last_human_move: Optional[tuple[int, int]] = None
        self.last_ai_move: Optional[tuple[int, int]] = None

    def to_dict(self, hide_ai_hand: bool = True) -> dict:
        """Serialize state for the frontend."""
        return {
            "board": self.board.get_state(),
            "human_color": self.human_color,
            "ai_color": self.ai_color,
            "current_turn": self.current_turn,
            "game_over": self.game_over,
            "winner": self.winner,
            "human_hp": self.human_hp,
            "ai_hp": self.ai_hp,
            "human_hand": [s.value for s in self.human_hand],
            "ai_hand": [
                "?" if hide_ai_hand else s.value for s in self.ai_hand
            ],
            "ai_hand_count": len(self.ai_hand),
            "human_frozen": self.human_frozen,
            "ai_frozen": self.ai_frozen,
            "turn_number": self.turn_number,
            "last_human_move": list(self.last_human_move) if self.last_human_move else None,
            "last_ai_move": list(self.last_ai_move) if self.last_ai_move else None,
        }

    # ── Draw skill ─────────────────────────────────────────────
    @staticmethod
    def draw_skill() -> Skill:
        """Draw a random skill card (weighted)."""
        return random.choice(SKILL_POOL)

    def grant_skills(self):
        """Grant a skill card to each player if turn is on interval."""
        if self.turn_number > 0 and self.turn_number % SKILL_GRANT_INTERVAL == 0:
            if len(self.human_hand) < MAX_HAND_SIZE:
                self.human_hand.append(self.draw_skill())
            if len(self.ai_hand) < MAX_HAND_SIZE:
                self.ai_hand.append(self.draw_skill())

    # ── Five-in-a-row detection & bleed ────────────────────────
    def check_fives(self, player_color: int) -> list[set[tuple[int, int]]]:
        """Return all distinct 5-in-a-row sets for the given player."""
        fives = []
        board = self.board
        grid = board.grid
        size = board.size
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(size):
            for c in range(size):
                if grid[r][c] != player_color:
                    continue
                for dr, dc in dirs:
                    # Check if this is the start of a 5-in-a-row
                    # (no same-color stone before it)
                    pr, pc = r - dr, c - dc
                    if 0 <= pr < size and 0 <= pc < size and grid[pr][pc] == player_color:
                        continue

                    # Collect consecutive stones
                    stones: set[tuple[int, int]] = set()
                    cr, cc = r, c
                    while 0 <= cr < size and 0 <= cc < size and grid[cr][cc] == player_color:
                        stones.add((cr, cc))
                        cr += dr
                        cc += dc

                    if len(stones) == 5:
                        fives.append(stones)

        return fives

    def update_fives(self):
        """Update the tracked five-in-a-row sets for both players."""
        self.human_fives = self.check_fives(self.human_color)
        self.ai_fives = self.check_fives(self.ai_color)

    def apply_bleed(self):
        """At the start of the active player's turn, bleed from opponent fives."""
        if self.current_turn == self.human_color and self.ai_fives:
            self.human_hp -= len(self.ai_fives)
        elif self.current_turn == self.ai_color and self.human_fives:
            self.ai_hp -= len(self.human_fives)

    def check_game_over(self) -> bool:
        """Check if either player's HP is depleted."""
        if self.human_hp <= 0:
            self.human_hp = 0
            self.game_over = True
            self.winner = 2  # AI wins
            return True
        if self.ai_hp <= 0:
            self.ai_hp = 0
            self.game_over = True
            self.winner = 1  # human wins
            return True
        if self.board.is_full():
            self.game_over = True
            self.winner = 3  # draw
            return True
        return False

    # ── Skill effects ──────────────────────────────────────────
    def use_skill_fei_sha(self, row: int, col: int, user_color: int) -> bool:
        """飞沙走石: remove opponent's stone at (row, col)."""
        target = self.board.grid[row][col]
        opponent = WHITE if user_color == BLACK else BLACK
        if target != opponent:
            return False
        self.board.grid[row][col] = EMPTY
        self.board.move_count -= 1
        self.update_fives()
        return True

    def use_skill_tou_tian(self, row: int, col: int, user_color: int) -> bool:
        """偷天换日: convert opponent's stone to yours."""
        target = self.board.grid[row][col]
        opponent = WHITE if user_color == BLACK else BLACK
        if target != opponent:
            return False
        self.board.grid[row][col] = user_color
        self.board.last_move = (row, col)
        self.update_fives()
        return True

    def use_skill_jing_ru(self, target_is_human: bool):
        """静如止水: freeze opponent's next turn."""
        if target_is_human:
            self.human_frozen = True
        else:
            self.ai_frozen = True


# ═══════════════════════════════════════════════════════════════
# AI skill decision engine
# ═══════════════════════════════════════════════════════════════

def ai_decide_skill(gs: SkillGameState) -> tuple[Skill | None, int | None, int | None]:
    """Decide which skill the AI should use and on which target.

    Returns (skill, target_row, target_col) or (None, None, None).
    """
    difficulty = gs.difficulty

    # Easy: never use skills
    if difficulty == "easy":
        return None, None, None

    if not gs.ai_hand:
        return None, None, None

    opponent = gs.human_color
    board = gs.board

    # ── Find the most threatening human stone ──
    # Priority: stones that are part of a 4-in-a-row first, then 3, then 2
    def threat_score(row: int, col: int) -> int:
        """Estimate how threatening a stone is to the AI."""
        if board.grid[row][col] != opponent:
            return -1
        s = 0
        dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in dirs:
            count = 1
            # positive
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == opponent:
                count += 1; r += dr; c += dc
            # negative
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] == opponent:
                count += 1; r -= dr; c -= dc
            s += count
        return s

    # Collect all opponent stones with threat scores
    threats = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            ts = threat_score(r, c)
            if ts > 0:
                threats.append((r, c, ts))

    threats.sort(key=lambda x: -x[2])  # most threatening first

    # ── Decide skill ──
    # Hard: can use any skill
    # Medium: only feisha

    # 1. feisha — remove most threatening stone
    if Skill.FEI_SHA_ZOU_SHI in gs.ai_hand and threats:
        return Skill.FEI_SHA_ZOU_SHI, threats[0][0], threats[0][1]

    if difficulty in ("hard",):
        # 2. toutian — convert most threatening stone to AI's
        if Skill.TOU_TIAN_HUAN_RI in gs.ai_hand and threats:
            return Skill.TOU_TIAN_HUAN_RI, threats[0][0], threats[0][1]

        # 3. jingru — freeze human when they have strong threats
        if Skill.JING_RU_ZHI_SHUI in gs.ai_hand and threats and threats[0][2] >= 4:
            return Skill.JING_RU_ZHI_SHUI, None, None

    return None, None, None
