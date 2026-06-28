/**
 * 技能五子棋 — Skill Mode Frontend
 */

const SkillGame = (function () {
    "use strict";

    const BOARD_SIZE = 15;
    const EMPTY = 0;
    const BLACK = 1;
    const WHITE = 2;

    // DOM
    const canvas = document.getElementById("board-canvas");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status-message");
    const overlay = document.getElementById("overlay");
    const overlayEmoji = document.getElementById("overlay-emoji");
    const overlayTitle = document.getElementById("overlay-title");
    const overlayMessage = document.getElementById("overlay-message");
    const confettiCanvas = document.getElementById("confetti-canvas");
    const confettiCtx = confettiCanvas.getContext("2d");

    // State
    let boardData = [];
    let humanColor = BLACK;
    let aiColor = WHITE;
    let currentTurn = BLACK;
    let gameOver = false;
    let humanHP = 5, aiHP = 5;
    let humanHand = [], aiHandCount = 0;
    let humanFrozen = false, aiFrozen = false;
    let lastHumanMove = null, lastAiMove = null;
    let turnNumber = 0;
    let hoverPos = null;
    let stoneScale = 1.0;
    let animFrameId = null;
    let clickLocked = false;
    let hoverDrawPending = false;
    let skillMode = null; // skill being used: 'feisha'|'toutian'|'jingru'|null
    let confettiParticles = [], confettiAnimId = null;

    // Layout
    let cellSize, padding, boardPixelSize;

    // ── Skill name mapping ─────────────────────────────────────
    const SKILL_INFO = {
        feisha: { name: "飞沙走石", emoji: "🪨", desc: "移除对方一颗棋子" },
        toutian: { name: "偷天换日", emoji: "🔄", desc: "对方棋子变成你的" },
        wuxie: { name: "无懈可击", emoji: "🛡️", desc: "抵消对方技能" },
        jingru: { name: "静如止水", emoji: "❄️", desc: "冻住对方一回合" },
    };

    // ═══════════════════════════════════════════════════════════
    // Canvas
    // ═══════════════════════════════════════════════════════════
    function resizeCanvas() {
        const maxSize = Math.min(window.innerWidth * 0.55, window.innerHeight - 60, 550);
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
        confettiCanvas.width = window.innerWidth;
        confettiCanvas.height = window.innerHeight;
        draw();
    }
    window.addEventListener("resize", resizeCanvas);

    function draw() {
        drawBoard();
        drawStones();
        drawMarkers();
        drawHover();
    }

    function drawBoard() {
        const grad = ctx.createLinearGradient(0, 0, boardPixelSize, boardPixelSize);
        grad.addColorStop(0, "#e6c97a"); grad.addColorStop(0.5, "#c8943e"); grad.addColorStop(1, "#e6c97a");
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, boardPixelSize, boardPixelSize);
        ctx.strokeStyle = "#5d3a1a"; ctx.lineWidth = 0.8;
        for (let i = 0; i < BOARD_SIZE; i++) {
            const y = padding + i * cellSize;
            ctx.beginPath(); ctx.moveTo(padding, y); ctx.lineTo(padding + (BOARD_SIZE - 1) * cellSize, y); ctx.stroke();
            const x = padding + i * cellSize;
            ctx.beginPath(); ctx.moveTo(x, padding); ctx.lineTo(x, padding + (BOARD_SIZE - 1) * cellSize); ctx.stroke();
        }
        const starPoints = [[3,3],[3,7],[3,11],[7,3],[7,7],[7,11],[11,3],[11,7],[11,11]];
        for (const [r,c] of starPoints) {
            ctx.beginPath(); ctx.arc(padding + c*cellSize, padding + r*cellSize, cellSize*0.12, 0, Math.PI*2);
            ctx.fillStyle = "#5d3a1a"; ctx.fill();
        }
    }

    function drawStones() {
        for (let r = 0; r < BOARD_SIZE; r++) {
            if (!boardData[r]) continue;
            for (let c = 0; c < BOARD_SIZE; c++) {
                if (boardData[r][c] === EMPTY) continue;
                const x = padding + c * cellSize, y = padding + r * cellSize;
                let scale = 1.0;
                if (lastHumanMove && lastHumanMove[0]===r && lastHumanMove[1]===c) scale = stoneScale;
                if (lastAiMove && lastAiMove[0]===r && lastAiMove[1]===c) scale = stoneScale;
                drawStone(x, y, cellSize*0.44*scale, boardData[r][c]);
            }
        }
    }

    function drawStone(x, y, radius, color) {
        ctx.save();
        ctx.beginPath(); ctx.arc(x+2, y+2, radius, 0, Math.PI*2);
        ctx.fillStyle = "rgba(0,0,0,0.25)"; ctx.fill(); ctx.restore();
        const grad = ctx.createRadialGradient(x-radius*0.3, y-radius*0.3, radius*0.1, x, y, radius);
        if (color === BLACK) { grad.addColorStop(0,"#666"); grad.addColorStop(0.6,"#222"); grad.addColorStop(1,"#000"); }
        else { grad.addColorStop(0,"#fff"); grad.addColorStop(0.6,"#e8e8e8"); grad.addColorStop(1,"#bbb"); }
        ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI*2); ctx.fillStyle = grad; ctx.fill();
        ctx.strokeStyle = color===BLACK?"rgba(0,0,0,0.8)":"rgba(150,150,150,0.6)";
        ctx.lineWidth = 0.5; ctx.stroke();
    }

    function drawMarkers() {
        const markers = [];
        if (lastHumanMove) markers.push({r:lastHumanMove[0], c:lastHumanMove[1]});
        if (lastAiMove) markers.push({r:lastAiMove[0], c:lastAiMove[1]});
        for (const m of markers) {
            const x = padding + m.c*cellSize, y = padding + m.r*cellSize;
            drawStar(x, y, cellSize*0.2, "#FFD700", "#FFA500");
        }
    }

    function drawStar(cx, cy, r, fill, stroke) {
        ctx.save(); ctx.beginPath();
        for (let i=0; i<10; i++) {
            const rad = i%2===0?r:r*0.45;
            const a = Math.PI/5*i - Math.PI/2;
            const x = cx+Math.cos(a)*rad, y = cy+Math.sin(a)*rad;
            if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
        }
        ctx.closePath(); ctx.fillStyle=fill; ctx.fill();
        ctx.strokeStyle=stroke; ctx.lineWidth=1; ctx.stroke(); ctx.restore();
    }

    function drawHover() {
        if (!hoverPos || gameOver || currentTurn!==humanColor) return;
        const x = padding + hoverPos.col*cellSize, y = padding + hoverPos.row*cellSize;
        if (boardData[hoverPos.row] && boardData[hoverPos.row][hoverPos.col]!==EMPTY) return;
        ctx.save(); ctx.globalAlpha = 0.35;
        drawStone(x, y, cellSize*0.44, humanColor);
        ctx.restore();
    }

    function pixelToGrid(px, py) {
        const col = Math.round((px-padding)/cellSize), row = Math.round((py-padding)/cellSize);
        if (col<0||col>=BOARD_SIZE||row<0||row>=BOARD_SIZE) return null;
        const cx = padding+col*cellSize, cy = padding+row*cellSize;
        if (Math.sqrt((px-cx)**2+(py-cy)**2) > cellSize*0.44) return null;
        return {row,col};
    }

    // ── Events ─────────────────────────────────────────────────
    canvas.addEventListener("click", function(e) {
        if (gameOver || clickLocked) return;
        if (currentTurn !== humanColor && !skillMode) return;
        const rect = canvas.getBoundingClientRect();
        const sx = boardPixelSize/rect.width, sy = boardPixelSize/rect.height;
        const px = (e.clientX-rect.left)*sx, py = (e.clientY-rect.top)*sy;
        const grid = pixelToGrid(px, py);
        if (!grid) return;

        if (skillMode) {
            // Using a skill
            if (skillMode === "feisha" || skillMode === "toutian") {
                // Must click an opponent stone
                if (boardData[grid.row][grid.col] !== aiColor) return;
                useSkill(skillMode, grid.row, grid.col);
                skillMode = null;
                document.getElementById("skill-active-msg").textContent = "";
            }
            return;
        }

        if (currentTurn !== humanColor) return;
        if (boardData[grid.row][grid.col] !== EMPTY) return;
        makeMove(grid.row, grid.col);
    });

    canvas.addEventListener("mousemove", function(e) {
        const rect = canvas.getBoundingClientRect();
        const sx = boardPixelSize/rect.width, sy = boardPixelSize/rect.height;
        const px = (e.clientX-rect.left)*sx, py = (e.clientY-rect.top)*sy;
        const grid = pixelToGrid(px, py);
        if (grid && !gameOver && (currentTurn===humanColor||skillMode) &&
            ((!skillMode && boardData[grid.row]&&boardData[grid.row][grid.col]===EMPTY) ||
             (skillMode==="feisha"||skillMode==="toutian"))) {
            hoverPos = grid;
        } else { hoverPos = null; }
        if (!hoverDrawPending) { hoverDrawPending=true; requestAnimationFrame(()=>{draw();hoverDrawPending=false;}); }
    });

    canvas.addEventListener("mouseleave", ()=>{hoverPos=null;draw();});

    // ── API ────────────────────────────────────────────────────
    async function makeMove(row, col) {
        try {
            clickLocked = true;
            currentTurn = 0;
            boardData[row][col] = humanColor;
            lastHumanMove = [row, col];
            statusEl.textContent = "AI 思考中...";
            draw();
            SoundFX.playPlace();

            const resp = await fetch("/api/skill_move", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({row, col}),
            });
            const data = await resp.json();
            if (data.error) {
                boardData[row][col] = EMPTY; lastHumanMove = null;
                statusEl.textContent = data.error;
                currentTurn = humanColor; draw(); clickLocked = false;
                return;
            }
            updateState(data);
            if (data.status === "human_wins") {
                endGame("win", data.message);
            } else if (data.status === "ai_wins") {
                endGame("lose", data.message);
            } else {
                currentTurn = humanColor;
                statusEl.textContent = data.message;
                stoneScale = 1.0;
                animateStone();
            }
            draw();
            clickLocked = false;
        } catch(err) {
            statusEl.textContent = "网络错误";
            currentTurn = humanColor; clickLocked = false;
        }
    }

    async function newGame() {
        try {
            const resp = await fetch("/api/skill_new_game", {method:"POST"});
            const data = await resp.json();
            updateState(data);
            currentTurn = data.current_turn;
            gameOver = data.game_over;
            humanHP = data.human_hp; aiHP = data.ai_hp;
            humanHand = data.human_hand || [];
            aiHandCount = data.ai_hand_count || 0;
            turnNumber = data.turn_number || 0;
            statusEl.textContent = data.message;
            updateHP();
            updateHands();
            hideOverlay();
            stopConfetti();
            skillMode = null;
            document.getElementById("skill-active-msg").textContent = "";
            stoneScale = 1.0;
            draw();
        } catch(err) { statusEl.textContent = "无法开始游戏"; }
    }

    async function useSkill(skillKey, row, col) {
        try {
            const body = {skill: skillKey};
            if (row !== undefined) body.row = row;
            if (col !== undefined) body.col = col;
            const resp = await fetch("/api/use_skill", {
                method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify(body),
            });
            const data = await resp.json();
            if (data.error) { statusEl.textContent = data.error; return; }
            updateState(data);
            statusEl.textContent = data.message;
            if (data.status === "human_wins") endGame("win", data.message);
            else if (data.status === "ai_wins") endGame("lose", data.message);
            stoneScale = 1.0;
            draw();
        } catch(err) { statusEl.textContent = "技能使用失败"; }
    }

    // ── State sync ─────────────────────────────────────────────
    function updateState(data) {
        if (data.board) boardData = data.board;
        if (data.human_color) humanColor = data.human_color;
        if (data.ai_color) aiColor = data.ai_color;
        if (data.current_turn !== undefined) currentTurn = data.current_turn;
        if (data.game_over !== undefined) gameOver = data.game_over;
        if (data.human_hp !== undefined) humanHP = data.human_hp;
        if (data.ai_hp !== undefined) aiHP = data.ai_hp;
        if (data.human_hand) humanHand = data.human_hand;
        if (data.ai_hand_count !== undefined) aiHandCount = data.ai_hand_count;
        if (data.human_frozen !== undefined) humanFrozen = data.human_frozen;
        if (data.ai_frozen !== undefined) aiFrozen = data.ai_frozen;
        if (data.turn_number !== undefined) turnNumber = data.turn_number;
        if (data.last_human_move) lastHumanMove = data.last_human_move;
        else if (data.last_human_move === null) lastHumanMove = null;
        if (data.last_ai_move) lastAiMove = data.last_ai_move;
        else if (data.last_ai_move === null) lastAiMove = null;
        updateHP();
        updateHands();
        updateTurnBadge();
    }

    function updateHP() {
        document.getElementById("human-hp-fill").style.width = (humanHP/5*100)+"%";
        document.getElementById("human-hp-text").textContent = humanHP+"/5";
        document.getElementById("ai-hp-fill").style.width = (aiHP/5*100)+"%";
        document.getElementById("ai-hp-text").textContent = aiHP+"/5";
    }

    function updateHands() {
        // Human hand
        const slots = document.querySelectorAll("#human-hand .card-slot");
        for (let i = 0; i < 3; i++) {
            const slot = slots[i];
            if (i < humanHand.length) {
                const s = humanHand[i];
                const info = SKILL_INFO[s] || {name:s, emoji:"?"};
                slot.className = "card-slot card-filled card-" + s;
                slot.innerHTML = `<span class="card-emoji">${info.emoji}</span><span class="card-name">${info.name}</span>`;
                slot.onclick = function() { activateSkill(s); };
            } else {
                slot.className = "card-slot card-empty";
                slot.innerHTML = "";
                slot.onclick = null;
            }
        }
        // AI hand (backs)
        const aiSlots = document.querySelectorAll("#ai-hand .card-slot");
        for (let i = 0; i < 3; i++) {
            if (i < aiHandCount) aiSlots[i].className = "card-slot card-back";
            else aiSlots[i].className = "card-slot card-empty-back";
        }
    }

    function updateTurnBadge() {
        const badge = document.getElementById("turn-badge");
        if (gameOver) badge.textContent = "";
        else if (humanFrozen) badge.textContent = "❄️ 冰冻";
        else if (currentTurn === humanColor) badge.textContent = "你的回合";
        else badge.textContent = "AI 回合";
    }

    function activateSkill(skillKey) {
        if (gameOver || currentTurn !== humanColor) return;
        if (skillMode === skillKey) { skillMode = null; document.getElementById("skill-active-msg").textContent = ""; return; }
        skillMode = skillKey;
        const info = SKILL_INFO[skillKey];
        document.getElementById("skill-active-msg").textContent = info.emoji + " " + info.name + "：" + info.desc;
        if (skillKey === "jingru") { useSkill("jingru"); skillMode = null; document.getElementById("skill-active-msg").textContent = ""; }
    }

    function endGame(type, msg) {
        gameOver = true; currentTurn = 0;
        statusEl.textContent = msg;
        if (type === "win") { SoundFX.playWin(); setTimeout(()=>showOverlay("win",msg), 600); }
        else if (type==="lose") { SoundFX.playLose(); setTimeout(()=>showOverlay("lose",msg), 600); }
        else { setTimeout(()=>showOverlay("draw",msg), 600); }
    }

    function showOverlay(type, msg) {
        overlay.classList.add("show");
        if (type==="win") { overlayEmoji.textContent="🎉👑🥇"; overlayTitle.textContent="你赢了！"; startConfetti(); }
        else if (type==="lose") { overlayEmoji.textContent="💀😈"; overlayTitle.textContent="AI赢了！"; }
        else { overlayEmoji.textContent="🤝"; overlayTitle.textContent="平局！"; }
        overlayMessage.textContent = msg;
    }

    function hideOverlay() { overlay.classList.remove("show"); }

    function animateStone() {
        stoneScale = 0.01;
        const start = performance.now(), dur = 250;
        function step(now) {
            const t = Math.min((now-start)/dur, 1);
            stoneScale = 1-Math.pow(1-t,3);
            draw();
            if (t<1) animFrameId = requestAnimationFrame(step);
            else { stoneScale=1; draw(); }
        }
        if (animFrameId) cancelAnimationFrame(animFrameId);
        animFrameId = requestAnimationFrame(step);
    }

    function startConfetti() {
        confettiParticles = [];
        for (let i=0;i<120;i++) confettiParticles.push({
            x:Math.random()*window.innerWidth, y:Math.random()*-window.innerHeight,
            w:Math.random()*10+4, h:Math.random()*6+3,
            color:["#ff6b6b","#feca57","#54a0ff","#5f27cd","#ff9ff3","#1dd1a1","#fff"][Math.floor(Math.random()*7)],
            vy:Math.random()*3+1, vx:(Math.random()-0.5)*2, rot:Math.random()*360, rotV:(Math.random()-0.5)*10, opacity:1,
        });
        animateConfetti();
    }

    function animateConfetti() {
        confettiCtx.clearRect(0,0,confettiCanvas.width,confettiCanvas.height);
        let done=true;
        for(const p of confettiParticles) {
            p.y+=p.vy; p.x+=p.vx; p.rot+=p.rotV; p.vy+=0.02;
            if(p.y>window.innerHeight+50){p.opacity-=0.005;if(p.opacity<=0)continue;}
            done=false;
            confettiCtx.save(); confettiCtx.translate(p.x,p.y); confettiCtx.rotate(p.rot*Math.PI/180);
            confettiCtx.globalAlpha=p.opacity; confettiCtx.fillStyle=p.color;
            confettiCtx.fillRect(-p.w/2,-p.h/2,p.w,p.h); confettiCtx.restore();
        }
        if(!done) confettiAnimId=requestAnimationFrame(animateConfetti);
    }

    function stopConfetti() {
        if(confettiAnimId) cancelAnimationFrame(confettiAnimId);
        confettiParticles=[]; confettiCtx.clearRect(0,0,confettiCanvas.width,confettiCanvas.height);
    }

    // ── Init ───────────────────────────────────────────────────
    if (window.__SOUND_ENABLED__ !== undefined) SoundFX.setEnabled(window.__SOUND_ENABLED__);
    document.getElementById("btn-new-game").addEventListener("click", newGame);
    document.getElementById("btn-hint").addEventListener("click", async ()=>{
        if(gameOver||currentTurn!==humanColor)return;
        const r=await fetch("/api/skill_hint",{method:"POST"});
        const d=await r.json();
        if(d.row!==undefined) statusEl.textContent="提示: "+String.fromCharCode(65+d.col)+(d.row+1);
    });
    resizeCanvas();
    setTimeout(newGame, 300);

    return { newGame };
})();
