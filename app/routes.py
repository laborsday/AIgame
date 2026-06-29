"""Route definitions for the Gomoku web application."""
import random

from flask import Blueprint, jsonify, render_template, request, session

from app.game.board import Board, EMPTY, BLACK, WHITE, BOARD_SIZE
from app.game.rules import Rules
from app.game.ai import AIPlayer
from app.game.skill_rules import (
    Skill,
    SkillGameState,
    SKILL_NAMES,
    SKILL_EMOJI,
    MAX_HP,
    MAX_HAND_SIZE,
    ai_decide_skill,
)

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
    sound_on = session.get("sound_on", True)
    return render_template("game.html", sound_on=sound_on)


@bp.route("/settings")
def settings():
    """Render the settings page."""
    difficulty = session.get("difficulty", "medium")
    sound_on = session.get("sound_on", True)
    return render_template("settings.html", difficulty=difficulty, sound_on=sound_on)


@bp.route("/api/save_settings", methods=["POST"])
def save_settings():
    """Save user settings to the session."""
    data = request.get_json(silent=True) or {}
    difficulty = data.get("difficulty", "medium")
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    session["difficulty"] = difficulty

    sound_on = data.get("sound_on", True)
    session["sound_on"] = sound_on

    return jsonify({"ok": True, "difficulty": difficulty, "sound_on": sound_on})


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


# ═══════════════════════════════════════════════════════════════
# Skill mode routes
# ═══════════════════════════════════════════════════════════════


def _get_skill_state():
    """Reconstruct SkillGameState from session."""
    if "skill_state" not in session:
        return None
    data = session["skill_state"]
    gs = SkillGameState(
        human_color=data["human_color"],
        difficulty=data.get("difficulty", "medium"),
    )
    board_data = data["board"]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            gs.board.grid[r][c] = board_data[r][c]
    gs.board.move_count = sum(
        1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board_data[r][c] != EMPTY
    )
    gs.current_turn = data["current_turn"]
    gs.game_over = data["game_over"]
    gs.winner = data["winner"]
    gs.human_hp = data["human_hp"]
    gs.ai_hp = data["ai_hp"]
    gs.human_hand = [Skill(s) for s in data["human_hand"]]
    gs.ai_hand = [Skill(s) for s in data["ai_hand"]]
    gs.human_fives = [set(tuple(st) for st in f) for f in data.get("human_fives", [])]
    gs.ai_fives = [set(tuple(st) for st in f) for f in data.get("ai_fives", [])]
    gs.human_frozen = data.get("human_frozen", False)
    gs.ai_frozen = data.get("ai_frozen", False)
    gs.turn_number = data.get("turn_number", 0)
    gs.last_human_move = tuple(data["last_human_move"]) if data.get("last_human_move") else None
    gs.last_ai_move = tuple(data["last_ai_move"]) if data.get("last_ai_move") else None
    return gs


def _save_skill_state(gs):
    """Persist skill game state to session."""
    session["skill_state"] = {
        "board": gs.board.get_state(),
        "human_color": gs.human_color,
        "ai_color": gs.ai_color,
        "current_turn": gs.current_turn,
        "game_over": gs.game_over,
        "winner": gs.winner,
        "human_hp": gs.human_hp,
        "ai_hp": gs.ai_hp,
        "human_hand": [s.value for s in gs.human_hand],
        "ai_hand": [s.value for s in gs.ai_hand],
        "human_fives": [[list(st) for st in gs.human_fives]],
        "ai_fives": [[list(st) for st in gs.ai_fives]],
        "human_frozen": gs.human_frozen,
        "ai_frozen": gs.ai_frozen,
        "turn_number": gs.turn_number,
        "difficulty": gs.difficulty,
        "last_human_move": list(gs.last_human_move) if gs.last_human_move else None,
        "last_ai_move": list(gs.last_ai_move) if gs.last_ai_move else None,
    }


@bp.route("/skill-game")
def skill_game():
    """Render the skill-mode game page."""
    sound_on = session.get("sound_on", True)
    return render_template("skill-game.html", sound_on=sound_on)


@bp.route("/api/skill_new_game", methods=["POST"])
def skill_new_game():
    """Start a new skill-mode game."""
    difficulty = session.get("difficulty", "medium")
    human_color = random.choice([BLACK, WHITE])

    gs = SkillGameState(human_color=human_color, difficulty=difficulty)
    _save_skill_state(gs)

    response = gs.to_dict()
    response["message"] = "技能模式开战！第5回合开始发技能卡！"

    # AI goes first?
    if gs.ai_color == BLACK:
        gs.turn_number += 1
        gs.apply_bleed()
        gs.grant_skills()
        ai = AIPlayer(player_color=gs.ai_color, difficulty=difficulty)
        move = ai.compute_move(gs.board)
        gs.board.place_stone(move[0], move[1], gs.ai_color)
        gs.last_ai_move = move
        gs.current_turn = WHITE
        gs.update_fives()
        _save_skill_state(gs)
        response = gs.to_dict()
        response["message"] = "AI 先手落子，轮到你了！"

    return jsonify(response)


@bp.route("/api/skill_move", methods=["POST"])
def skill_move():
    """Human makes a move in skill mode."""
    gs = _get_skill_state()
    if not gs:
        return jsonify({"error": "没有进行中的游戏"}), 400
    if gs.game_over:
        return jsonify({"error": "游戏已结束"}), 400

    data = request.get_json(silent=True) or {}
    row = data.get("row")
    col = data.get("col")

    if row is None or col is None:
        return jsonify({"error": "参数缺失"}), 400
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return jsonify({"error": "坐标超出范围"}), 400
    if gs.current_turn != gs.human_color:
        return jsonify({"error": "现在不是你的回合"}), 400
    if not gs.board.is_valid_move(row, col):
        return jsonify({"error": "此处已有棋子"}), 400

    # Check frozen
    if gs.human_frozen:
        gs.human_frozen = False
        gs.current_turn = gs.ai_color
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": "你被冻住了！跳过此回合 ❄️"})

    # Human move
    gs.board.place_stone(row, col, gs.human_color)
    gs.last_human_move = (row, col)
    gs.update_fives()

    if gs.check_game_over():
        _save_skill_state(gs)
        msg = "你赢了！" if gs.winner == 1 else "你输了..."
        return jsonify({**gs.to_dict(), "message": msg, "status": _win_status(gs.winner)})

    # Switch to AI
    gs.current_turn = gs.ai_color
    gs.turn_number += 1
    gs.apply_bleed()

    if gs.check_game_over():
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": "AI 扣血过多，你赢了！", "status": "human_wins"})

    gs.grant_skills()
    _save_skill_state(gs)

    # AI frozen?
    if gs.ai_frozen:
        gs.ai_frozen = False
        gs.current_turn = gs.human_color
        gs.turn_number += 1
        gs.apply_bleed()
        if gs.check_game_over():
            _save_skill_state(gs)
            return jsonify({**gs.to_dict(), "message": "你扣血过多...", "status": "ai_wins"})
        gs.grant_skills()
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": "AI 被冻住了！再次轮到你了 ❄️", "status": "playing"})

    # AI move
    difficulty = session.get("difficulty", "medium")
    ai = AIPlayer(player_color=gs.ai_color, difficulty=difficulty)
    move = ai.compute_move(gs.board)
    gs.board.place_stone(move[0], move[1], gs.ai_color)
    gs.last_ai_move = move
    gs.update_fives()

    # ── AI uses a skill ──
    ai_skill_msg = ""
    ai_skill, sr, sc = ai_decide_skill(gs)
    if ai_skill is not None:
        if ai_skill == Skill.FEI_SHA_ZOU_SHI and sr is not None:
            gs.use_skill_fei_sha(sr, sc, gs.ai_color)
            gs.ai_hand.remove(Skill.FEI_SHA_ZOU_SHI)
            ai_skill_msg = f" AI 使用了飞沙走石！"
        elif ai_skill == Skill.TOU_TIAN_HUAN_RI and sr is not None:
            gs.use_skill_tou_tian(sr, sc, gs.ai_color)
            gs.ai_hand.remove(Skill.TOU_TIAN_HUAN_RI)
            ai_skill_msg = f" AI 使用了偷天换日！"
        elif ai_skill == Skill.JING_RU_ZHI_SHUI:
            gs.use_skill_jing_ru(target_is_human=True)
            gs.ai_hand.remove(Skill.JING_RU_ZHI_SHUI)
            ai_skill_msg = f" AI 使用了静如止水！你被冻住了 ❄️"
        gs.update_fives()

    if gs.check_game_over():
        gs.current_turn = 0
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": "AI 五连扣血，你输了！", "status": "ai_wins"})

    gs.current_turn = gs.human_color
    gs.turn_number += 1
    gs.apply_bleed()
    if gs.check_game_over():
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": "你扣血过多...", "status": "ai_wins"})

    gs.grant_skills()
    _save_skill_state(gs)
    notifications = ""
    if len(gs.human_hand) >= MAX_HAND_SIZE:
        notifications = " (手牌已满)"
    return jsonify(
        {**gs.to_dict(), "message": f"回合 #{gs.turn_number}{ai_skill_msg}{notifications}", "status": "playing"}
    )


@bp.route("/api/use_skill", methods=["POST"])
def use_skill():
    """Use a skill card."""
    gs = _get_skill_state()
    if not gs:
        return jsonify({"error": "没有进行中的游戏"}), 400

    data = request.get_json(silent=True) or {}
    skill_str = data.get("skill")
    row = data.get("row")
    col = data.get("col")

    try:
        skill = Skill(skill_str)
    except (ValueError, TypeError):
        return jsonify({"error": "无效的技能"}), 400

    if skill not in gs.human_hand:
        return jsonify({"error": "你没有这张技能卡"}), 400

    # Frozen check
    if gs.human_frozen:
        return jsonify({"error": "你被冻住了，本回合不能使用技能 ❄️"}), 400

    gs.human_hand.remove(skill)

    msg = ""
    if skill == Skill.FEI_SHA_ZOU_SHI:
        if row is None or col is None:
            gs.human_hand.append(skill)
            return jsonify({"error": "飞沙走石需要点击棋盘上的对方棋子"}), 400
        ok = gs.use_skill_fei_sha(row, col, gs.human_color)
        if not ok:
            gs.human_hand.append(skill)
            return jsonify({"error": "目标不是对方棋子"}), 400
        msg = "飞沙走石！移除了对方的棋子"

    elif skill == Skill.TOU_TIAN_HUAN_RI:
        if row is None or col is None:
            gs.human_hand.append(skill)
            return jsonify({"error": "偷天换日需要点击棋盘上的对方棋子"}), 400
        ok = gs.use_skill_tou_tian(row, col, gs.human_color)
        if not ok:
            gs.human_hand.append(skill)
            return jsonify({"error": "目标不是对方棋子"}), 400
        msg = "偷天换日！对方的棋子变成你的了"

    elif skill == Skill.WU_XIE_KE_JI:
        gs.human_hand.append(skill)
        return jsonify({"error": "无懈可击只能在对方使用技能时触发"}), 400

    elif skill == Skill.JING_RU_ZHI_SHUI:
        gs.use_skill_jing_ru(target_is_human=False)
        msg = "静如止水！AI 下回合跳过"

    gs.update_fives()
    if gs.check_game_over():
        _save_skill_state(gs)
        return jsonify({**gs.to_dict(), "message": msg, "status": _win_status(gs.winner)})

    _save_skill_state(gs)
    return jsonify({**gs.to_dict(), "message": msg, "status": "playing"})


@bp.route("/api/skill_hint", methods=["POST"])
def skill_hint():
    """AI-suggested move for skill mode."""
    gs = _get_skill_state()
    if not gs or gs.game_over:
        return jsonify({"error": "无法提供提示"}), 400
    ai = AIPlayer(player_color=gs.human_color, difficulty="hard")
    move = ai.compute_move(gs.board)
    return jsonify({"row": move[0], "col": move[1]})


def _win_status(winner):
    if winner == 1:
        return "human_wins"
    elif winner == 2:
        return "ai_wins"
    return "draw"
