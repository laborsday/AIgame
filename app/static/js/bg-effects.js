/**
 * Background effects: broken cards, scattered stones, robot face.
 * Subtle — not distracting.
 */

(function () {
    "use strict";

    // ── 1. Broken cards ─────────────────────────────────────────
    function spawnCards() {
        const layer = document.getElementById("cards-layer");
        if (!layer) return;

        const count = 6;
        for (let i = 0; i < count; i++) {
            const card = document.createElement("div");
            card.className = "card-debris";
            const w = 50 + Math.random() * 40;  // 50-90px
            const h = 35 + Math.random() * 30;  // 35-65px
            const x = Math.random() * 90;        // % from left
            const y = Math.random() * 90;        // % from top
            const rot = (Math.random() - 0.5) * 60; // -30 to +30 deg

            card.style.cssText = [
                `width:${w}px`, `height:${h}px`,
                `left:${x}%`, `top:${y}%`,
                `transform:rotate(${rot}deg)`,
            ].join(";");
            layer.appendChild(card);
        }
    }

    // ── 2. Scattered stones ─────────────────────────────────────
    function spawnStones() {
        const count = 12;
        for (let i = 0; i < count; i++) {
            const stone = document.createElement("div");
            stone.className = "stone-debris " + (i % 2 === 0 ? "black" : "white");
            const size = 18 + Math.random() * 22; // 18-40px
            const x = Math.random() * 94;
            const y = Math.random() * 94;

            stone.style.cssText = [
                `width:${size}px`, `height:${size}px`,
                `left:${x}%`, `top:${y}%`,
            ].join(";");
            document.body.appendChild(stone);
        }
    }

    // ── 3. Robot face (green dot-matrix on canvas) ───────────────
    const ROBOT_FACES = {
        // Each face is a 16x16 grid of 0/1 bits. 1 = lit dot.
        // Face A: goofy smile 😜
        faceA: [
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,
            0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,
            0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,
            0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,1,1,0,0,0,0,0,0,0,0,1,1,0,0,
            0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        ],
        // Face B: derp 😛 (tongue out)
        faceB: [
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,
            0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,
            0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,
            0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,
            0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,
            0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        ],
        // Face C: X_X dead/dizzy
        faceC: [
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,
            0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,
            0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,
            0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,
            0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,
            0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,
            0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
            0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
        ],
    };

    let currentFace = "faceA";
    const GRID = 16; // 16x16 dot matrix
    const canvas = document.getElementById("robot-canvas");
    if (!canvas) return;

    const rctx = canvas.getContext("2d");
    const SIZE = canvas.width; // square canvas

    function drawRobot(faceKey) {
        rctx.clearRect(0, 0, SIZE, SIZE);
        const bits = ROBOT_FACES[faceKey];
        if (!bits) return;

        const dotR = SIZE / GRID / 2 * 0.9;
        const gap = SIZE / GRID;

        // Glow halo
        rctx.save();
        rctx.globalAlpha = 0.15;
        const haloGrad = rctx.createRadialGradient(SIZE/2, SIZE/2, SIZE*0.3, SIZE/2, SIZE/2, SIZE*0.8);
        haloGrad.addColorStop(0, "#00ff88");
        haloGrad.addColorStop(1, "transparent");
        rctx.fillStyle = haloGrad;
        rctx.fillRect(0, 0, SIZE, SIZE);
        rctx.restore();

        // Draw dots
        for (let row = 0; row < GRID; row++) {
            for (let col = 0; col < GRID; col++) {
                if (bits[row * GRID + col]) {
                    const cx = col * gap + gap / 2;
                    const cy = row * gap + gap / 2;

                    // Glow ring
                    rctx.beginPath();
                    rctx.arc(cx, cy, dotR * 1.6, 0, Math.PI * 2);
                    rctx.fillStyle = "rgba(0,255,136,0.15)";
                    rctx.fill();

                    // Core dot
                    rctx.beginPath();
                    rctx.arc(cx, cy, dotR, 0, Math.PI * 2);
                    const dotGrad = rctx.createRadialGradient(cx-dotR*0.3, cy-dotR*0.3, 0, cx, cy, dotR);
                    dotGrad.addColorStop(0, "#ccffdd");
                    dotGrad.addColorStop(0.5, "#00ff88");
                    dotGrad.addColorStop(1, "#008844");
                    rctx.fillStyle = dotGrad;
                    rctx.fill();
                }
            }
        }
    }

    // Cycle faces every 4 seconds
    const faces = ["faceA", "faceB", "faceC"];
    let idx = 0;

    function cycleFace() {
        currentFace = faces[idx % faces.length];
        drawRobot(currentFace);
        idx++;
    }

    drawRobot(currentFace);
    setInterval(cycleFace, 4000);

    // ── Init ────────────────────────────────────────────────────
    spawnCards();
    spawnStones();
})();
