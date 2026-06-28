# 🀄 技能五子棋 — AI 人机对战

一款基于 Python Flask + Canvas 的五子棋（Gomoku）人机对战网页游戏，带沙雕风格的 UI 和三档 AI 难度。

## 快速开始

### 环境要求
- Python 3.11+
- 浏览器（Chrome / Edge / Firefox 均可）

### 安装与运行

```bash
# 1. 创建虚拟环境
python3.11 -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务器
python run.py
```

浏览器打开 [http://127.0.0.1:5000](http://127.0.0.1:5000) 即可开始游戏！

## 游戏规则

- **棋盘**：15×15 标准五子棋棋盘
- **目标**：横、竖、斜任意方向率先连成五子者获胜
- **先手**：每局随机分配，人类可能执黑（先手）或执白（后手）
- **黑色始终先走**（传统规则）

## AI 难度

| 难度 | 搜索深度 | 说明 |
|---|---|---|
| 🍼 简单 | depth=1 | AI 只看当前局面，适合新手练习 |
| ⚔️ 中等 | depth=2 | AI 有基本攻防意识，休闲对局 |
| 💀 困难 | depth=3 | AI 深度计算，需要认真思考才能取胜 |

AI 采用 **Minimax + Alpha-Beta 剪枝** 算法，结合启发式棋型评估函数（活四、活三、眠三等），优先封堵对手威胁。

## 功能

- 🎮 人机对战（随机先手）
- 🤖 三档 AI 难度
- 💡 提示功能（AI 推荐落子）
- ⭐ 最后落子金色五角星标记
- ✨ 落子弹入动画
- 🎉 胜利撒花特效
- 💬 沙雕搞笑文案

## 项目结构

```
软件工程实践/
├── run.py                 # 入口文件
├── requirements.txt       # Python 依赖
├── README.md
├── app/
│   ├── __init__.py        # Flask 工厂函数
│   ├── routes.py          # API 路由 (/api/new_game, /api/move, /api/hint)
│   ├── game/
│   │   ├── __init__.py
│   │   ├── board.py       # 棋盘逻辑 (15x15)
│   │   ├── rules.py       # 胜负判定
│   │   └── ai.py          # AI 引擎 (Minimax + Alpha-Beta)
│   ├── static/
│   │   ├── css/style.css   # 沙雕风格样式
│   │   └── js/game.js      # Canvas 前端逻辑
│   └── templates/
│       └── index.html      # 游戏页面
└── tests/
    ├── test_board.py       # 棋盘单元测试
    ├── test_rules.py       # 胜负判定测试
    └── test_ai.py          # AI 行为测试
```

## API 接口

| 端点 | 方法 | 说明 |
|---|---|---|
| `/` | GET | 游戏页面 |
| `/api/new_game` | POST | 开始新游戏，参数 `{"difficulty": "medium"}` |
| `/api/move` | POST | 人类落子，参数 `{"row": int, "col": int}` |
| `/api/hint` | POST | 获取 AI 推荐落子 |

## 运行测试

```bash
pip install pytest
pytest tests/ -v
```

## License

课程实践项目 — 仅供学习使用。
