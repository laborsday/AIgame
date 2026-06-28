/**
 * 技能五子棋 — Frontend Game Logic
 * Canvas-based Gomoku board with sandiao (沙雕) style
 */

(function () {
    "use strict";

    // ── Constants ──────────────────────────────────────────────
    const BOARD_SIZE = 15;
    const EMPTY = 0;
    const BLACK = 1;
    const WHITE = 2;

    // ── DOM refs ───────────────────────────────────────────────
    const canvas = document.getElementById("board-canvas");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status-message");
    const overlay = document.getElementById("overlay");
    const overlayEmoji = document.getElementById("overlay-emoji");
    const overlayTitle = document.getElementById("overlay-title");
    const overlayMessage = document.getElementById("overlay-message");
    const confettiCanvas = document.getElementById("confetti-canvas");
    const confettiCtx = confettiCanvas.getContext("2d");

    // ── State ──────────────────────────────────────────────────
    let boardData = [];           // 15x15, 0/1/2
    let humanColor = BLACK;      // player's stone colour
    let aiColor = WHITE;
    let currentTurn = BLACK;     // whose turn
    let gameOver = false;
    let lastMove = null;         // {row, col} of the most recent stone
    let humanLastMove = null;    // human's last move for marking
    let aiLastMove = null;       // AI's last move for marking
    let hoverPos = null;         // {row, col} where mouse is hovering
    let stoneScale = 1.0;        // animation: current scale of last-placed stone
    let animFrameId = null;
    let hoverDrawPending = false;
    let clickLocked = false;  // prevent double-clicks

    // Layout computed values
    let cellSize, padding, boardPixelSize;

    // ── Canvas Setup ───────────────────────────────────────────
    function resizeCanvas() {
        const maxSize = Math.min(window.innerWidth - 30, window.innerHeight - 280, 600);
        const dpr = window.devicePixelRatio || 1;
        boardPixelSize = maxSize;

        canvas.width = boardPixelSize * dpr;
        canvas.height = boardPixelSize * dpr;
        canvas.style.width = boardPixelSize + "px";
        canvas.style.height = boardPixelSize + "px";
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);

        padding = boardPixelSize / (BOARD_SIZE + 1);
        cellSize = (boardPixelSize - padding * 2) / (BOARD_SIZE - 1);

        // Confetti canvas
        confettiCanvas.width = window.innerWidth;
        confettiCanvas.height = window.innerHeight;

        draw();
    }

    window.addEventListener("resize", resizeCanvas);

    // ── Drawing ────────────────────────────────────────────────
    function draw() {
        drawBoard();
        drawStones();
        drawLastMoveMarkers();
        drawHoverPreview();
    }

    function drawBoard() {
        // Wood-grain background
        const woodGrad = ctx.createLinearGradient(0, 0, boardPixelSize, boardPixelSize);
        woodGrad.addColorStop(0, "#e6c97a");
        woodGrad.addColorStop(0.3, "#d4a54a");
        woodGrad.addColorStop(0.6, "#c8943e");
        woodGrad.addColorStop(1, "#e6c97a");
        ctx.fillStyle = woodGrad;
        ctx.fillRect(0, 0, boardPixelSize, boardPixelSize);

        // Grid lines
        ctx.strokeStyle = "#5d3a1a";
        ctx.lineWidth = 0.8;

        for (let i = 0; i < BOARD_SIZE; i++) {
            // Horizontal
            const y = padding + i * cellSize;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(padding + (BOARD_SIZE - 1) * cellSize, y);
            ctx.stroke();

            // Vertical
            const x = padding + i * cellSize;
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, padding + (BOARD_SIZE - 1) * cellSize);
            ctx.stroke();
        }

        // Star points (天元 + 四星)
        const starPoints = [
            [3, 3], [3, 7], [3, 11],
            [7, 3], [7, 7], [7, 11],
            [11, 3], [11, 7], [11, 11],
        ];
        for (const [r, c] of starPoints) {
            const x = padding + c * cellSize;
            const y = padding + r * cellSize;
            ctx.beginPath();
            ctx.arc(x, y, cellSize * 0.12, 0, Math.PI * 2);
            ctx.fillStyle = "#5d3a1a";
            ctx.fill();
        }

        // Coordinate labels
        ctx.fillStyle = "#5d3a1a";
        ctx.font = `${cellSize * 0.32}px 'Noto Sans SC', sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        for (let i = 0; i < BOARD_SIZE; i++) {
            // Column labels (A-O)
            const label = String.fromCharCode(65 + i);
            ctx.fillText(label, padding + i * cellSize, padding * 0.35);

            // Row labels (1-15)
            ctx.fillText(String(i + 1), padding * 0.35, padding + i * cellSize);
        }
    }

    function drawStones() {
        for (let r = 0; r < BOARD_SIZE; r++) {
            for (let c = 0; c < BOARD_SIZE; c++) {
                if (boardData[r] && boardData[r][c] !== EMPTY) {
                    const x = padding + c * cellSize;
                    const y = padding + r * cellSize;
                    const radius = cellSize * 0.44;

                    // Check if this is the most recently placed stone (for animation)
                    let scale = 1.0;
                    if (lastMove && lastMove.row === r && lastMove.col === c) {
                        scale = stoneScale;
                    }

                    drawStone(x, y, radius * scale, boardData[r][c]);
                }
            }
        }
    }

    function drawStone(x, y, radius, color) {
        // Shadow
        ctx.save();
        ctx.beginPath();
        ctx.arc(x + 2, y + 2, radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0,0,0,0.25)";
        ctx.fill();
        ctx.restore();

        // Stone body
        const grad = ctx.createRadialGradient(
            x - radius * 0.3, y - radius * 0.3, radius * 0.1,
            x, y, radius
        );

        if (color === BLACK) {
            grad.addColorStop(0, "#666");
            grad.addColorStop(0.6, "#222");
            grad.addColorStop(1, "#000");
        } else {
            grad.addColorStop(0, "#fff");
            grad.addColorStop(0.6, "#e8e8e8");
            grad.addColorStop(1, "#bbb");
        }

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        // Subtle border
        ctx.strokeStyle = color === BLACK ? "rgba(0,0,0,0.8)" : "rgba(150,150,150,0.6)";
        ctx.lineWidth = 0.5;
        ctx.stroke();
    }

    function drawLastMoveMarkers() {
        // Draw a gold star on the last human move and last AI move
        const markers = [];
        if (humanLastMove) markers.push({ ...humanLastMove, color: humanColor });
        if (aiLastMove) markers.push({ ...aiLastMove, color: aiColor });

        for (const m of markers) {
            if (m.row === undefined || m.col === undefined) continue;
            const x = padding + m.col * cellSize;
            const y = padding + m.row * cellSize;
            const starR = cellSize * 0.2;

            drawStar(x, y, starR, "#FFD700", "#FFA500");
        }
    }

    function drawStar(cx, cy, r, fillColor, strokeColor) {
        const spikes = 5;
        const outerR = r;
        const innerR = r * 0.45;

        ctx.save();
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
            const radius = i % 2 === 0 ? outerR : innerR;
            const angle = (Math.PI / spikes) * i - Math.PI / 2;
            const x = cx + Math.cos(angle) * radius;
            const y = cy + Math.sin(angle) * radius;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.restore();
    }

    function drawHoverPreview() {
        if (!hoverPos || gameOver || currentTurn !== humanColor) return;

        const x = padding + hoverPos.col * cellSize;
        const y = padding + hoverPos.row * cellSize;
        const radius = cellSize * 0.44;

        // Only if cell is empty
        if (boardData[hoverPos.row] && boardData[hoverPos.row][hoverPos.col] !== EMPTY) return;

        ctx.save();
        ctx.globalAlpha = 0.35;
        drawStone(x, y, radius, humanColor);
        ctx.restore();
    }

    // ── Coordinate mapping ─────────────────────────────────────
    function pixelToGrid(px, py) {
        const col = Math.round((px - padding) / cellSize);
        const row = Math.round((py - padding) / cellSize);

        if (col < 0 || col >= BOARD_SIZE || row < 0 || row >= BOARD_SIZE) return null;

        // Check proximity to the intersection
        const cx = padding + col * cellSize;
        const cy = padding + row * cellSize;
        const dist = Math.sqrt((px - cx) ** 2 + (py - cy) ** 2);

        if (dist > cellSize * 0.44) return null;

        return { row, col };
    }

    // ── Event handlers ─────────────────────────────────────────
    canvas.addEventListener("click", function (e) {
        if (gameOver) return;
        if (currentTurn !== humanColor) return;
        if (clickLocked) return;  // debounce

        const rect = canvas.getBoundingClientRect();
        const scaleX = boardPixelSize / rect.width;
        const scaleY = boardPixelSize / rect.height;
        const px = (e.clientX - rect.left) * scaleX;
        const py = (e.clientY - rect.top) * scaleY;

        const grid = pixelToGrid(px, py);
        if (!grid) return;

        // Check occupied
        if (boardData[grid.row][grid.col] !== EMPTY) return;

        makeMove(grid.row, grid.col);
    });

    canvas.addEventListener("mousemove", function (e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = boardPixelSize / rect.width;
        const scaleY = boardPixelSize / rect.height;
        const px = (e.clientX - rect.left) * scaleX;
        const py = (e.clientY - rect.top) * scaleY;

        const grid = pixelToGrid(px, py);
        if (
            grid &&
            boardData[grid.row] &&
            boardData[grid.row][grid.col] === EMPTY &&
            !gameOver &&
            currentTurn === humanColor
        ) {
            hoverPos = grid;
        } else {
            hoverPos = null;
        }
        // Throttle redraw — skip if already pending via RAF
        if (!hoverDrawPending) {
            hoverDrawPending = true;
            requestAnimationFrame(() => {
                draw();
                hoverDrawPending = false;
            });
        }
    });

    canvas.addEventListener("mouseleave", function () {
        hoverPos = null;
        draw();
    });

    // ── API calls ──────────────────────────────────────────────
    async function makeMove(row, col) {
        try {
            clickLocked = true;
            statusEl.textContent = "AI 正在思考...";
            currentTurn = 0; // lock board

            const resp = await fetch("/api/move", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ row, col }),
            });

            const data = await resp.json();

            if (data.error) {
                statusEl.textContent = "❌ " + data.error;
                currentTurn = humanColor; // unlock
                return;
            }

            // Update state
            boardData = data.board;
            humanLastMove = data.human_move
                ? { row: data.human_move[0], col: data.human_move[1] }
                : null;
            aiLastMove = data.ai_move
                ? { row: data.ai_move[0], col: data.ai_move[1] }
                : null;
            lastMove = aiLastMove || humanLastMove;

            if (data.status === "human_wins") {
                gameOver = true;
                currentTurn = 0;
                statusEl.textContent = data.message;
                animateStone();
                setTimeout(() => showOverlay("win", data.message), 600);
            } else if (data.status === "ai_wins") {
                gameOver = true;
                currentTurn = 0;
                statusEl.textContent = data.message;
                animateStone();
                setTimeout(() => showOverlay("lose", data.message), 600);
            } else if (data.status === "draw") {
                gameOver = true;
                currentTurn = 0;
                statusEl.textContent = data.message;
                animateStone();
                setTimeout(() => showOverlay("draw", data.message), 600);
            } else {
                // playing
                currentTurn = humanColor;
                statusEl.textContent = data.message;
                animateStone();
            }

            draw();
            clickLocked = false;
        } catch (err) {
            statusEl.textContent = "网络错误，请刷新页面";
            currentTurn = humanColor;
            clickLocked = false;
        }
    }

    async function newGame() {
        try {
            const resp = await fetch("/api/new_game", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
            });

            const data = await resp.json();

            boardData = data.board;
            humanColor = data.human_color;
            aiColor = data.ai_color;
            currentTurn = data.current_turn;
            gameOver = data.game_over;
            lastMove = data.last_move
                ? { row: data.last_move[0], col: data.last_move[1] }
                : null;
            humanLastMove = null;
            aiLastMove = data.last_move && data.current_turn === humanColor ? null
                : data.last_move ? { row: data.last_move[0], col: data.last_move[1] } : null;

            // Update UI
            updateColorBadges();
            updateTurnIndicator();
            statusEl.textContent = data.message;
            hideOverlay();
            stopConfetti();
            stoneScale = 1.0;

            draw();
        } catch (err) {
            statusEl.textContent = "❌ 无法开始新游戏，请检查网络";
        }
    }

    async function askHint() {
        if (gameOver || currentTurn !== humanColor) return;

        try {
            const resp = await fetch("/api/hint", { method: "POST" });
            const data = await resp.json();

            if (data.error) {
                statusEl.textContent = "❌ " + data.error;
                return;
            }

            // Briefly highlight the hint position
            const hintRow = data.row;
            const hintCol = data.col;

            // Flash the hint
            let flashes = 0;
            const maxFlashes = 4;
            const flashInterval = setInterval(() => {
                if (flashes >= maxFlashes || gameOver) {
                    clearInterval(flashInterval);
                    hoverPos = null;
                    draw();
                    return;
                }

                if (flashes % 2 === 0) {
                    // Draw a glowing ring at hint position
                    hoverPos = { row: hintRow, col: hintCol };
                    const x = padding + hintCol * cellSize;
                    const y = padding + hintRow * cellSize;

                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(x, y, cellSize * 0.5, 0, Math.PI * 2);
                    ctx.strokeStyle = "#54a0ff";
                    ctx.lineWidth = 3;
                    ctx.shadowColor = "#54a0ff";
                    ctx.shadowBlur = 15;
                    ctx.stroke();
                    ctx.restore();
                } else {
                    hoverPos = null;
                }

                draw();
                if (flashes % 2 === 0) {
                    // Re-draw highlight on top (already drawn in draw())
                }
                flashes++;
            }, 250);

            statusEl.textContent = `💡 提示：试试 ${String.fromCharCode(65 + hintCol)}${hintRow + 1} ？`;
        } catch (err) {
            statusEl.textContent = "❌ 提示获取失败";
        }
    }

    // ── UI Helpers ─────────────────────────────────────────────
    function updateColorBadges() {
        const humanIcon = document.getElementById("human-stone-icon");
        const aiIcon = document.getElementById("ai-stone-icon");
        const humanText = document.getElementById("human-color-text");
        const aiText = document.getElementById("ai-color-text");

        humanIcon.className = "stone-icon " + (humanColor === BLACK ? "black" : "white");
        aiIcon.className = "stone-icon " + (aiColor === BLACK ? "black" : "white");
        humanText.textContent = humanColor === BLACK ? "黑棋" : "白棋";
        aiText.textContent = aiColor === BLACK ? "黑棋" : "白棋";
    }

    function updateTurnIndicator() {
        const indicator = document.getElementById("turn-indicator");
        if (gameOver) {
            indicator.textContent = "";
        } else if (currentTurn === humanColor) {
            indicator.textContent = "— 该你了";
        } else {
            indicator.textContent = "— AI 思考中...";
        }
    }

    function showOverlay(type, message) {
        overlay.classList.add("show");

        if (type === "win") {
            overlayEmoji.textContent = "🎉👑🥇";
            overlayTitle.textContent = "你赢了！";
            overlayMessage.textContent = message;
            startConfetti();
        } else if (type === "lose") {
            overlayEmoji.textContent = "🤖💀😈";
            overlayTitle.textContent = "AI 赢了！";
            overlayMessage.textContent = message;
        } else {
            overlayEmoji.textContent = "🤝";
            overlayTitle.textContent = "平局！";
            overlayMessage.textContent = message;
        }
    }

    function hideOverlay() {
        overlay.classList.remove("show");
    }

    // ── Stone-placement animation ──────────────────────────────
    function animateStone() {
        stoneScale = 0.01;
        const startTime = performance.now();
        const duration = 250;

        function step(now) {
            const elapsed = now - startTime;
            const t = Math.min(elapsed / duration, 1.0);
            // Ease-out (cubic)
            stoneScale = 1 - Math.pow(1 - t, 3);
            draw();

            if (t < 1) {
                animFrameId = requestAnimationFrame(step);
            } else {
                stoneScale = 1.0;
                draw();
            }
        }

        if (animFrameId) cancelAnimationFrame(animFrameId);
        animFrameId = requestAnimationFrame(step);
    }

    // ── Confetti ───────────────────────────────────────────────
    let confettiParticles = [];
    let confettiAnimId = null;

    function startConfetti() {
        confettiParticles = [];
        for (let i = 0; i < 120; i++) {
            confettiParticles.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * -window.innerHeight,
                w: Math.random() * 10 + 4,
                h: Math.random() * 6 + 3,
                color: ["#ff6b6b", "#feca57", "#54a0ff", "#5f27cd", "#ff9ff3", "#1dd1a1", "#fff"][
                    Math.floor(Math.random() * 7)
                ],
                vy: Math.random() * 3 + 1,
                vx: (Math.random() - 0.5) * 2,
                rot: Math.random() * 360,
                rotV: (Math.random() - 0.5) * 10,
                opacity: 1,
            });
        }
        animateConfetti();
    }

    function animateConfetti() {
        confettiCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);

        let allDone = true;

        for (const p of confettiParticles) {
            p.y += p.vy;
            p.x += p.vx;
            p.rot += p.rotV;
            p.vy += 0.02; // gravity

            if (p.y > window.innerHeight + 50) {
                p.opacity -= 0.005;
                if (p.opacity <= 0) continue;
            }
            allDone = false;

            confettiCtx.save();
            confettiCtx.translate(p.x, p.y);
            confettiCtx.rotate((p.rot * Math.PI) / 180);
            confettiCtx.globalAlpha = p.opacity;
            confettiCtx.fillStyle = p.color;
            confettiCtx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            confettiCtx.restore();
        }

        if (!allDone) {
            confettiAnimId = requestAnimationFrame(animateConfetti);
        }
    }

    function stopConfetti() {
        if (confettiAnimId) cancelAnimationFrame(confettiAnimId);
        confettiParticles = [];
        confettiCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
    }

    // ── Button bindings ────────────────────────────────────────
    document.getElementById("btn-new-game").addEventListener("click", newGame);
    document.getElementById("btn-hint").addEventListener("click", askHint);

    // ── Init ───────────────────────────────────────────────────
    resizeCanvas();
    // Auto-start a game
    setTimeout(newGame, 300);

    // Expose for overlay button
    window.game = { newGame, askHint };
})();
