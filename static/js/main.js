const BORDER_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12',
    '#1abc9c', '#e67e22', '#e91e63', '#00bcd4', '#8bc34a'
];
const BG_COLORS = [
    '#fde8e8', '#dbeafe', '#d5f5e3', '#ede7f6', '#fef3cd',
    '#d1f2eb', '#fde8d0', '#fce4ec', '#d0f4f7', '#e8f5e9'
];

let clientId = '';
let questionNum = 0;
let usedBorderColors = [];
let usedBgColors = [];
let gameActive = false;

// Start button triggers fullscreen + pointer lock (requires user gesture)
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('start-button').addEventListener('click', startGame);
});

function startGame() {
    clientId = crypto.randomUUID();
    document.getElementById('client_id').value = clientId;
    gameActive = true;

    document.getElementById('start-screen').style.display = 'none';
    document.getElementById('game-wrapper').style.display = 'block';

    document.body.classList.add('pointer-locked');
    document.documentElement.requestFullscreen().then(() => {
        document.body.requestPointerLock();
    }).catch(() => {
        document.body.requestPointerLock();
    });

    loadNextQuestion();
}

function pickColors() {
    const availBorder = BORDER_COLORS.filter(c => !usedBorderColors.includes(c));
    const border = availBorder[Math.floor(Math.random() * availBorder.length)];
    usedBorderColors.push(border);

    const availBg = BG_COLORS.filter(c => !usedBgColors.includes(c));
    const bg = availBg[Math.floor(Math.random() * availBg.length)];
    usedBgColors.push(bg);

    return { border, bg };
}

function loadNextQuestion() {
    fetch(`/question?client_id=${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                document.getElementById('message').textContent = data.error;
                return;
            }
            renderProblem(data);
        });
}

function renderProblem(data) {
    const { border: borderColor, bg: bgColor } = pickColors();
    const problemBox = document.getElementById('problem-box');
    problemBox.style.border = `2px solid ${borderColor}`;
    problemBox.style.background = bgColor;

    const problemText = document.getElementById('problem-text');
    problemText.innerHTML = '';
    renderLatex(data.problem, problemText);

    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    const aimeContainer = document.getElementById('aime-input-container');

    if (data.options) {
        aimeContainer.style.display = 'none';
        for (const [letter, text] of Object.entries(data.options)) {
            const box = document.createElement('div');
            box.className = 'answerBox';
            box.dataset.value = letter;
            box.style.borderColor = borderColor;

            const label = document.createElement('span');
            label.className = 'option-label';
            label.textContent = `(${letter})`;
            box.appendChild(label);

            const content = document.createElement('span');
            content.className = 'option-content';
            renderLatex(text, content);
            box.appendChild(content);

            box.addEventListener('click', () => submitAnswer(letter));
            optionsContainer.appendChild(box);
        }
    } else {
        aimeContainer.style.display = 'flex';
        const input = document.getElementById('aime-answer');
        input.value = '';
        input.focus();
        document.getElementById('aime-submit').onclick = () => {
            submitAnswer(input.value.trim());
        };
        input.onkeydown = (e) => {
            if (e.key === 'Enter') submitAnswer(input.value.trim());
        };
    }

    document.getElementById('message').textContent = '';
    document.getElementById('message').className = '';
}

function renderLatex(text, element) {
    try {
        // Split on $...$ (LaTeX) and [IMG:...] (diagram images)
        const parts = text.split(/(\$[^$]+\$|\[IMG:[^\]]+\])/g);
        parts.forEach(part => {
            if (part.startsWith('$') && part.endsWith('$') && part.length > 1) {
                const math = part.slice(1, -1);
                const span = document.createElement('span');
                katex.render(math, span, { throwOnError: false });
                element.appendChild(span);
            } else if (part.startsWith('[IMG:') && part.endsWith(']')) {
                const fname = part.slice(5, -1);
                const img = document.createElement('img');
                img.src = `/static/images/${fname}`;
                img.className = 'problem-diagram';
                element.appendChild(img);
            } else if (part) {
                element.appendChild(document.createTextNode(part));
            }
        });
    } catch (e) {
        element.textContent = text;
    }
}

function submitAnswer(answer) {
    const msg = document.getElementById('message');

    fetch('/submit_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            answer: answer,
            client_id: clientId,
            question_num: questionNum
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.escaped) {
            document.getElementById(`seg-${questionNum}`).classList.add('filled');
            gameActive = false;
            document.body.classList.remove('pointer-locked');
            document.getElementById('game-container').style.display = 'none';
            document.getElementById('escape-screen').style.display = 'flex';
            document.exitPointerLock();
            if (document.fullscreenElement) document.exitFullscreen();
        } else if (data.correct) {
            document.getElementById(`seg-${questionNum}`).classList.add('filled');
            questionNum = data.question_num;
            msg.textContent = data.message;
            msg.className = 'message-correct';
            setTimeout(loadNextQuestion, 1500);
        } else {
            msg.textContent = data.message;
            msg.className = 'message-incorrect';
        }
    });
}

// Re-lock pointer if user breaks out mid-game
document.addEventListener('pointerlockchange', () => {
    if (!document.pointerLockElement && gameActive) {
        document.body.requestPointerLock();
    }
});

// Re-enter fullscreen if user exits mid-game
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement && gameActive) {
        document.documentElement.requestFullscreen().catch(() => {});
    }
});

// Block Escape key + AMC option keybindings (A-E)
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        return;
    }
    if (!gameActive) return;
    const letter = e.key.toUpperCase();
    if ('ABCDE'.includes(letter)) {
        const box = document.querySelector(`.answerBox[data-value="${letter}"]`);
        if (box) box.click();
    }
}, true);
