const canvas = document.getElementById('generative-bg');
const ctx = canvas.getContext('2d');

let width, height;
let mouse = { x: -1000, y: -1000 };

function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    initGrid();
}

window.addEventListener('resize', resize);
// Track mouse movement
window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});
// Reset mouse when off screen
window.addEventListener('mouseout', () => {
    mouse.x = -1000;
    mouse.y = -1000;
});

// The text to repeat in the background. Pulls dynamically from the page title!
let rawText = document.title.toUpperCase().replace(/[^A-Z0-9]/g, '');
if (!rawText) rawText = "LUKASVDAGILIS";
const textChars = rawText.split('');
const charGrid = [];
const spacing = 35; // Grid density

function initGrid() {
    charGrid.length = 0;
    const cols = Math.ceil(width / spacing) + 1;
    const rows = Math.ceil(height / spacing) + 1;

    for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
            charGrid.push({
                originX: x * spacing,
                originY: y * spacing,
                char: textChars[(x + y) % textChars.length]
            });
        }
    }
}

// Initial setup
resize();

function draw() {
    ctx.clearRect(0, 0, width, height);

    // Clean system typography to match the site
    ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 0; i < charGrid.length; i++) {
        const p = charGrid[i];

        const dx = mouse.x - p.originX;
        const dy = mouse.y - p.originY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // Base state
        let angle = 0;
        let opacity = 0.04; // Extremely subtle base opacity
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;

        let r = 17, g = 17, b = 17;

        const maxDist = 200; // Interaction radius

        if (dist < maxDist && mouse.x !== -1000) {
            const force = (maxDist - dist) / maxDist; // 0 (edge) to 1 (center)

            // Calculate angle pointing AT the mouse (+90deg so the top faces mouse)
            angle = Math.atan2(dy, dx) + Math.PI / 2;

            // Increase opacity near the mouse making it "light up"
            opacity = 0.04 + force * 0.3;

            // Flocking away: push the letter away from the mouse
            offsetX = -(dx / dist) * force * 15;
            offsetY = -(dy / dist) * force * 15;

            // Scale up slightly for emphasis
            scale = 1 + force * 0.5;

            // Transition color to light pink (255, 182, 193) dynamically
            r = 17 + (255 - 17) * force;
            g = 17 + (182 - 17) * force;
            b = 17 + (193 - 17) * force;
        } else {
            // Idle animation: very slow ambient wave pointing
            const time = Date.now() * 0.0005;
            angle = Math.sin(p.originX * 0.01 + time) * 0.3 + Math.cos(p.originY * 0.01 + time) * 0.3;
        }

        ctx.save();
        ctx.translate(p.originX + offsetX, p.originY + offsetY);
        ctx.rotate(angle);
        ctx.scale(scale, scale);

        ctx.fillStyle = `rgba(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}, ${opacity})`;
        ctx.fillText(p.char, 0, 0);

        ctx.restore();
    }

    requestAnimationFrame(draw);
}

draw();
