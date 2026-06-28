"""Route definitions for the Gomoku web application."""
import random

from flask import Blueprint, jsonify, render_template, request, session

from app.game.board import Board, EMPTY, BLACK, WHITE, BOARD_SIZE
from app.game.rules import Rules
from app.game.ai import AIPlayer

bp = Blueprint("main", __name__)


def _get_board_from_session() -> Board:
    """Reconstruct a Board object from session data."""
    board = Board()
    if "board" in session:
        state = session["board"]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = state[r][c]
                if val != EMPTY:
                    board.grid[r][c] = val
                    board.move_count += 1
        if "last_move" in session and session["last_move"] is not None:
            board.last_move = tuple(session["last_move"])
    return board


def _save_board_to_session(board: Board):
    """Serialize the board and related state into the session."""
    session["board"] = board.get_state()
    session["last_move"] = list(board.last_move) if board.last_move else None
    session["move_count"] = board.move_count


def _get_game_state_dict(board: Board) -> dict:
    """Return a dict summarising the current game state."""
    board_data = board.get_state()
    return {
        "board": board_data,
        "human_color": session.get("human_color"),
        "ai_color": session.get("ai_color"),
        "current_turn": session.get("current_turn"),
        "game_over": session.get("game_over", False),
        "winner": session.get("winner", 0),
        "last_move": session.get("last_move"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@bp.route("/")
def index():
    """Render the home / landing page."""
    return render_template("index.html")


@bp.route("/game")
def game():
    """Render the game page."""
    return render_template("game.html")


@bp.route("/settings")
def settings():
    """Render the settings page."""
    difficulty = session.get("difficulty", "medium")
    return render_template("settings.html", difficulty=difficulty)


@bp.route("/api/save_settings", methods=["POST"])
def save_settings():
    """Save user settings to the session."""
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", "medium")
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    session["difficulty"] = difficulty
    return jsonify({"ok": True, "difficulty": difficulty})


@bp.route("/api/new_game", methods=["POST"])
def new_game():
    """Start a new game using the difficulty stored in the session."""
    difficulty = session.get("difficulty", "medium")

    # Randomly assign colours
    human_color = random.choice([BLACK, WHITE])
    ai_color = WHITE if human_color == BLACK else BLACK

    board = Board()

    # Store game state in session
    session["human_color"] = human_color
    session["ai_color"] = ai_color
    session["current_turn"] = BLACK  # Black always moves first
    session["game_over"] = False
    session["winner"] = 0
    session["difficulty"] = difficulty
    session["move_history"] = []
    session["last_move"] = None

    _save_board_to_session(board)

    response = {
        "board": board.get_state(),
        "human_color": human_color,
        "ai_color": ai_color,
        "current_turn": BLACK,
        "game_over": False,
        "winner": 0,
        "last_move": None,
        "message": _random_start_message(human_color),
    }

    # If AI goes first (AI is BLACK), make the AI's opening move now
    if ai_color == BLACK:
        ai = AIPlayer(player_color=ai_color, difficulty=difficulty)
        move = ai.compute_move(board)
        board.place_stone(move[0], move[1], ai_color)
        session["current_turn"] = WHITE
        session["last_move"] = [move[0], move[1]]
        session["move_history"] = [(move[0], move[1], ai_color)]
        _save_board_to_session(board)

        response["board"] = board.get_state()
        response["current_turn"] = WHITE
        response["last_move"] = [move[0], move[1]]
        response["message"] = "AI 先手落子，轮到你了！"

    return jsonify(response)


@bp.route("/api/move", methods=["POST"])
def make_move():
    """Process a human move and return the AI's response."""
    if session.get("game_over", False):
        return jsonify({"error": "游戏已结束，请开始新一局"}), 400

    data = request.get_json(silent=True) or {}
    row = data.get("row")
    col = data.get("col")

    if row is None or col is None:
        return jsonify({"error": "请提供 row 和 col 参数"}), 400

    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return jsonify({"error": "坐标超出棋盘范围"}), 400

    board = _get_board_from_session()
    human_color = session.get("human_color")
    ai_color = session.get("ai_color")
    current_turn = session.get("current_turn")

    if current_turn != human_color:
        return jsonify({"error": "现在不是你的回合"}), 400

    if not board.is_valid_move(row, col):
        return jsonify({"error": "这个位置已经有棋子了"}), 400

    # --- Human move ---
    board.place_stone(row, col, human_color)
    session["last_move"] = [row, col]
    human_move = [row, col]

    # Save to move history
    move_history = session.get("move_history", [])
    move_history.append((row, col, human_color))
    session["move_history"] = move_history
    _save_board_to_session(board)

    # Check win
    winner = Rules.check_win(board)
    if winner == human_color:
        session["game_over"] = True
        session["winner"] = human_color
        session["current_turn"] = 0
        _save_board_to_session(board)
        return jsonify(
            {
                "board": board.get_state(),
                "status": "human_wins",
                "last_move": [row, col],
                "human_move": human_move,
                "ai_move": None,
                "message": _random_win_message(),
            }
        )

    # Check draw
    if Rules.is_draw(board):
        session["game_over"] = True
        session["winner"] = 3
        session["current_turn"] = 0
        _save_board_to_session(board)
        return jsonify(
            {
                "board": board.get_state(),
                "status": "draw",
                "last_move": [row, col],
                "human_move": human_move,
                "ai_move": None,
                "message": "平局！棋盘满了，你们打成了平手 🤝",
            }
        )

    # --- AI move ---
    session["current_turn"] = ai_color
    difficulty = session.get("difficulty", "medium")
    ai = AIPlayer(player_color=ai_color, difficulty=difficulty)
    ai_move_tuple = ai.compute_move(board)

    board.place_stone(ai_move_tuple[0], ai_move_tuple[1], ai_color)
    session["last_move"] = [ai_move_tuple[0], ai_move_tuple[1]]
    move_history.append((ai_move_tuple[0], ai_move_tuple[1], ai_color))
    session["move_history"] = move_history
    _save_board_to_session(board)

    ai_move = [ai_move_tuple[0], ai_move_tuple[1]]

    # Check if AI won
    winner = Rules.check_win(board)
    if winner == ai_color:
        session["game_over"] = True
        session["winner"] = ai_color
        session["current_turn"] = 0
        _save_board_to_session(board)
        return jsonify(
            {
                "board": board.get_state(),
                "status": "ai_wins",
                "last_move": ai_move,
                "human_move": human_move,
                "ai_move": ai_move,
                "message": _random_lose_message(),
            }
        )

    # AI move done, back to human
    session["current_turn"] = human_color
    _save_board_to_session(board)

    return jsonify(
        {
            "board": board.get_state(),
            "status": "playing",
            "last_move": ai_move,
            "human_move": human_move,
            "ai_move": ai_move,
            "message": _random_turn_message(),
        }
    )


@bp.route("/api/hint", methods=["POST"])
def hint():
    """Return an AI-suggested move for the human player (does not modify board)."""
    if session.get("game_over", False):
        return jsonify({"error": "游戏已结束"}), 400

    board = _get_board_from_session()
    human_color = session.get("human_color")

    if session.get("current_turn") != human_color:
        return jsonify({"error": "请等 AI 落子后再请求提示"}), 400

    ai = AIPlayer(player_color=human_color, difficulty="hard")
    move = ai.compute_move(board)
    return jsonify({"row": move[0], "col": move[1]})


# ---------------------------------------------------------------------------
# Sandiao (沙雕) random messages
# ---------------------------------------------------------------------------


def _random_start_message(human_color: str) -> str:
    """Generate a random silly start-of-game message."""
    messages = [
        "🎮 新游戏开始！你执{}，加油嗷～",
        "🤖 AI 已就位，正在热身 CPU…你执{}！",
        "🀄 五子棋大战开幕！你执{}，别让 AI 太得意！",
        "💪 准备挨打吧！你执{}，AI 正在磨刀…",
        "🔥 战斗开始！你执{}，AI 表示毫无压力 💅",
    ]
    color_str = "黑棋 ♠" if human_color == BLACK else "白棋 ♡"
    return random.choice(messages).format(f"{color_str}")


def _random_win_message() -> str:
    """Generate a random over-the-top win message."""
    messages = [
        "🎉 你赢了！！！AI 开始怀疑人生…",
        "🏆 牛啊！AI 的 CPU 已经烧了 🔥",
        "👑 五子棋之王！AI 甘拜下风 🧎",
        "💥 暴打 AI！它说要回家找妈妈了…",
        "🥇 你是冠军！AI 连夜跑路中 🏃💨",
        "⭐ 绝杀！AI：这人类有点东西…",
    ]
    return random.choice(messages)


def _random_lose_message() -> str:
    """Generate a random funny lose message."""
    messages = [
        "😈 AI 赢了！它说：就这？就这？",
        "💀 你输了！！AI：我还没发力呢～",
        "🤖 GG！AI 正在屏幕后面偷笑…",
        "📉 败北！AI 建议你去练练再来 💅",
        "😅 惜败！AI 说这只是热身局～",
        "🎯 AI 绝杀！它让你先下一局？",
    ]
    return random.choice(messages)


def _random_turn_message() -> str:
    """Generate a random message for when it's the human's turn."""
    messages = [
        "轮到你了！AI 正在思考下一招…",
        "该你落子了～AI 表示很期待你的操作 👀",
        "你下！AI 正在偷偷分析你的套路…",
        "该你了！AI 说你下得不错（才怪）",
        "↑ 看到 AI 的落子了吗？现在该你了！",
        "你的回合！AI 说它让你三招 😏",
    ]
    return random.choice(messages)
