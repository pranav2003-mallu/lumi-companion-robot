document.addEventListener("DOMContentLoaded", () => {
    console.log("Robot Companion UI initialized.");

    // Select elements
    const face = document.querySelector(".face");
    const mediaContainer = document.getElementById("media-container");
    const mediaFrame = document.getElementById("media-frame");
    const closeMediaBtn = document.getElementById("close-media");

    // Default emotion setup
    let currentEmotion = "neutral";
    let isTalking = false;
    let dreamInterval = null;
    const dreamBubble = document.getElementById("dream-bubble");
    const dreamContent = dreamBubble ? dreamBubble.querySelector('.dream-content') : null;

    // Setup downloaded snoring audio for the UI
    const snoreSounds = [
        new Audio('snore1.mp3'),
        new Audio('snore2.mp3')
    ];
    let activeSnore = null;

    // Initialize snore traits
    snoreSounds.forEach(audio => {
        audio.loop = true;
        audio.volume = 0.6; // Adjust if they are too loud
    });

    // Set an emotion state string (e.g. 'happy', 'sad', 'angry')
    window.setEmotion = function (emotion) {
        if (!face) return;

        // Remove old states
        face.classList.remove('happy', 'sad', 'angry', 'surprised', 'confused', 'sleepy', 'laughing', 'love', 'star', 'dead', 'dizzy', 'wink', 'battery');

        if (emotion && emotion !== 'neutral') {
            face.classList.add(emotion);
        }
        currentEmotion = emotion;

        // Handle dream bubble logic for sleep state
        handleSleepDreams(emotion);
    };

    function handleSleepDreams(emotion) {
        if (!dreamBubble || !dreamContent) return;

        // Force stop ANY existing snore loops immediately before processing new states
        // This prevents overlapping sounds if the user rapidly clicks "Sleepy" multiple times
        snoreSounds.forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });

        // Clear existing dream loop
        if (dreamInterval) clearInterval(dreamInterval);

        if (emotion === 'sleepy') {
            // Show bubble randomly cycling dreams
            dreamBubble.classList.add("visible");
            changeDream(); // Set initial dream
            dreamInterval = setInterval(changeDream, 4000); // Change dream every 4 seconds

            // Pick a random snore sound
            activeSnore = snoreSounds[Math.floor(Math.random() * snoreSounds.length)];
            // Play snore audio (browsers require user interaction first, so it works perfectly if they click the button)
            activeSnore.play().catch(err => console.log("Audio play blocked by browser:", err));
        } else {
            // Hide bubble instantly if waking up
            dreamBubble.classList.remove("visible");
            // Stop all snores to guarantee silence
            snoreSounds.forEach(audio => {
                audio.pause();
                audio.currentTime = 0;
            });
            activeSnore = null;
        }
    }

    function changeDream() {
        if (!dreamContent) return;
        const dreams = [
            '<span class="zzz-anim">Zzz...</span>',
            '<span class="battery-anim">🪫</span>', // Low battery dream
            '<span class="battery-anim">🔋</span>'  // Charging dream
        ];
        // Pick random dream
        const randomDream = dreams[Math.floor(Math.random() * dreams.length)];
        dreamContent.innerHTML = randomDream;
    }

    // Make the robot mouth animate dynamically to feel like real speech
    let talkInterval;
    window.startTalking = function () {
        if (!face) return;
        isTalking = true;
        face.classList.add('talking');

        // Randomize mouth height rapidly to simulate syllables
        const mouth = face.querySelector('.mouth');
        if (mouth) {
            talkInterval = setInterval(() => {
                const randomHeight = 20 + Math.random() * 60; // Random height between 20px and 80px
                mouth.style.height = `${randomHeight}px`;
            }, 100); // Change shape every 100ms
        }
    };

    // Stop speaking animation
    window.stopTalking = function () {
        if (!face) return;
        isTalking = false;
        face.classList.remove('talking');

        // Reset dynamic animation
        if (talkInterval) clearInterval(talkInterval);
        const mouth = face.querySelector('.mouth');
        if (mouth) mouth.style.height = ''; // Reset inline style
    };

    // Switch from Face Mode to YouTube
    window.openYouTubeBrowser = function () {
        if (!mediaContainer || !mediaFrame) return;

        // Hide face, show media
        document.getElementById("face-container").style.opacity = '0';
        setTimeout(() => {
            document.getElementById("face-container").style.display = 'none';
            mediaContainer.classList.remove("hidden");

            const ytSearchBar = document.getElementById("youtube-search-bar");
            if (ytSearchBar) ytSearchBar.style.display = "flex";

            const ytSearchInput = document.getElementById("yt-search-input");
            if (ytSearchInput && ytSearchInput.value === "") {
                ytSearchInput.value = "Lumi AI Robot"; // Default search
            }
            searchYouTubeBtn();
        }, 500); // Wait for face fade out
    };

    window.searchYouTubeBtn = function () {
        const query = document.getElementById("yt-search-input").value;
        if (!query) return;

        // Send query to python backend which can bypass X-Frame-Options
        if (typeof ws !== 'undefined' && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "youtube_search", query: query }));
        } else {
            console.error("Not connected to Lumi backend.");
        }

        const ytSearchBar = document.getElementById("youtube-search-bar");
        if (ytSearchBar) ytSearchBar.style.display = "none";
    };

    // Switch from Face Mode to a specific YouTube video (Programmatic)
    window.playYouTube = function (videoId) {
        if (!mediaContainer || !mediaFrame) return;

        // Hide face, show media
        document.getElementById("face-container").style.opacity = '0';
        setTimeout(() => {
            document.getElementById("face-container").style.display = 'none';
            mediaContainer.classList.remove("hidden");

            // Construct YouTube embed URL
            mediaFrame.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&controls=1`;
        }, 500); // Wait for face fade out
    };

    // Close Media and return to face
    closeMediaBtn.addEventListener("click", () => {
        mediaContainer.classList.add("hidden");

        const ytSearchBar = document.getElementById("youtube-search-bar");
        if (ytSearchBar) ytSearchBar.style.display = "none";

        mediaFrame.src = ""; // Stop video

        const faceContainer = document.getElementById("face-container");
        faceContainer.style.display = 'flex';
        setTimeout(() => {
            faceContainer.style.opacity = '1';
        }, 50);
    });

    // Make eyes follow cursor or touch randomly for more lifelike feel
    const leftEye = document.querySelector('.eye.left .iris');
    const rightEye = document.querySelector('.eye.right .iris');

    document.addEventListener('mousemove', (e) => {
        if (!leftEye || !rightEye) return;
        const x = (e.clientX / window.innerWidth - 0.5) * 40;
        const y = (e.clientY / window.innerHeight - 0.5) * 40;

        // Limit movement to avoid looking broken
        leftEye.style.transform = `translate(${x}px, ${y}px)`;
        rightEye.style.transform = `translate(${x}px, ${y}px)`;
    });

    // Simulating random life events if no ROS command (just for local test feel)
    setInterval(() => {
        if (!isTalking && Math.random() > 0.8) {
            // Randomly look around 
            const rx = (Math.random() - 0.5) * 40;
            const ry = (Math.random() - 0.5) * 40;
            leftEye.style.transform = `translate(${rx}px, ${ry}px)`;
            rightEye.style.transform = `translate(${rx}px, ${ry}px)`;

            setTimeout(() => {
                // only reset if not being controlled by WebSocket 
                if (!window.wsControlledTracking) {
                    leftEye.style.transform = `translate(0px, 0px)`;
                    rightEye.style.transform = `translate(0px, 0px)`;
                }
            }, 1000 + Math.random() * 2000);
        }
    }, 4000);

    // ==========================================
    // WEBSOCKET BRIDGE - Connect to Python Backend (ROS2/Ollama)
    // ==========================================
    let ws;

    function connectWebSocket() {
        // Automatically connect to the IP of whatever device is serving the UI.
        // For example, if accessed via 192.168.1.15, the host will naturally be 192.168.1.15.
        const wsHostname = window.location.hostname || 'localhost';
        ws = new WebSocket('ws://' + wsHostname + ':8765');

        ws.onopen = () => {
            console.log("Connected to Lumi Brain WebSockets!");
            // setEmotion('happy'); // optionally show happy when brain connects
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("Command from brain:", data);

                // Handle Emotion Change
                if (data.type === 'emotion') {
                    window.setEmotion(data.value);
                }

                // Handle Talking State
                else if (data.type === 'speak') {
                    if (data.value === true) window.startTalking();
                    else window.stopTalking();
                }

                // Handle Live Eye Tracking
                // We expect x and y to be between roughly -20 and 20
                else if (data.type === 'look') {
                    window.wsControlledTracking = true; // disable random look
                    if (leftEye && rightEye) {
                        leftEye.style.transform = `translate(${data.x}px, ${data.y}px)`;
                        rightEye.style.transform = `translate(${data.x}px, ${data.y}px)`;
                    }
                }

                // Handle Entertainment triggers
                else if (data.type === 'youtube' || data.type === 'play_youtube') {
                    window.playYouTube(data.videoId);
                }
                else if (data.type === 'close_media') {
                    closeMediaBtn.click();
                }

            } catch (err) {
                console.error("Error parsing WS message:", err);
            }
        };

        ws.onclose = () => {
            console.log("Disconnected from Brain. Retrying in 3 seconds...");
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (err) => {
            console.error("WebSocket Error:", err);
            ws.close();
        };
    }

    // Start connection
    connectWebSocket();

    // ==========================================
    // GAME HUB LOGIC implementation
    // ==========================================
    const gameContainer = document.getElementById("game-container");
    const closeGameBtn = document.getElementById("close-game");
    const gameStatus = document.getElementById("game-status");

    // UI Panels
    const gameMenu = document.getElementById("game-menu");
    const tttBoard = document.getElementById("tic-tac-toe-board");
    const mathBoard = document.getElementById("math-game-board");
    const animalBoard = document.getElementById("animal-quiz-board");
    const gameActions = document.getElementById("game-actions");
    const backToMenuBtn = document.getElementById("back-to-menu");
    const restartGameBtn = document.getElementById("restart-game");

    let currentGame = null;

    // ----- SOUND EFFECTS (Web Audio API - No files needed) -----
    function playBeep(freq, type, duration) {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = type || 'sine';
            osc.frequency.setValueAtTime(freq, ctx.currentTime);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch (e) { }
    }

    function playWinSound() {
        playBeep(400, 'sine', 0.1);
        setTimeout(() => playBeep(600, 'sine', 0.2), 100);
        setTimeout(() => playBeep(800, 'sine', 0.3), 200);
    }

    function playLoseSound() {
        playBeep(400, 'sawtooth', 0.2);
        setTimeout(() => playBeep(300, 'sawtooth', 0.3), 150);
    }

    // ----- MENU LOGIC -----
    window.openGame = function () {
        if (!gameContainer) return;
        gameContainer.classList.remove("hidden");
        showMenu();
    };

    closeGameBtn.addEventListener("click", () => {
        gameContainer.classList.add("hidden");
        window.setEmotion('neutral');
    });

    if (backToMenuBtn) backToMenuBtn.addEventListener("click", showMenu);

    if (restartGameBtn) {
        restartGameBtn.addEventListener("click", () => {
            if (currentGame === "ttt") resetTicTacToe();
            if (currentGame === "math") nextMathQuestion();
            if (currentGame === "animal") nextAnimalQuestion();
            if (currentGame === "memory") resetMemoryGame();
            if (currentGame === "simon") startSimonLevel();
            if (currentGame === "word") startWordGuessLevel();
        });
    }

    function showMenu() {
        gameStatus.innerText = "Lumi's Game Hub";
        gameMenu.style.display = "flex";

        const allBoards = [
            "tic-tac-toe-board", "math-game-board", "animal-quiz-board",
            "memory-board", "simon-board", "word-board"
        ];

        allBoards.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add("hidden");
                el.style.display = "none";
            }
        });

        gameActions.classList.add("hidden");
        gameActions.style.display = "none";

        currentGame = null;
        window.setEmotion('happy');
    }

    // ----- TIC-TAC-TOE (MiniMax AI / Hard Mode) -----
    const cells = document.querySelectorAll("#tic-tac-toe-board .cell");
    let board = ["", "", "", "", "", "", "", "", ""];
    let gameActive = false;

    window.startTicTacToe = function () {
        currentGame = "ttt";
        gameMenu.style.display = "none";
        tttBoard.classList.remove("hidden");
        tttBoard.style.display = "grid";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";
        resetTicTacToe();
    };

    function resetTicTacToe() {
        board = ["", "", "", "", "", "", "", "", ""];
        gameActive = true;
        gameStatus.innerText = "Your Turn! (You are X)";
        cells.forEach(cell => {
            cell.innerText = "";
            cell.classList.remove("taken", "x", "o");
        });
        window.setEmotion('happy');
    }

    cells.forEach(cell => {
        cell.addEventListener("click", () => {
            const index = cell.getAttribute("data-index");
            if (board[index] !== "" || !gameActive || currentGame !== "ttt") return;

            // Player move - with SOUND
            playBeep(800, 'sine', 0.1); // Sound for X
            board[index] = "X";
            cell.innerText = "X";
            cell.classList.add("taken", "x");

            checkTicTacToeWinner();
            if (gameActive) {
                gameStatus.innerText = "Lumi is thinking...";
                window.setEmotion('surprised');
                setTimeout(lumiMove, 600);
            }
        });
    });

    function minimax(newBoard, player) {
        const availSpots = newBoard.map((s, i) => s === "" ? i : null).filter(s => s !== null);
        const winPatterns = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
        const checkWin = (b, p) => winPatterns.some(pat => b[pat[0]] === p && b[pat[1]] === p && b[pat[2]] === p);

        if (checkWin(newBoard, "X")) return { score: -10 };
        else if (checkWin(newBoard, "O")) return { score: 10 };
        else if (availSpots.length === 0) return { score: 0 };

        let moves = [];
        for (let i = 0; i < availSpots.length; i++) {
            let move = {};
            move.index = availSpots[i];
            newBoard[availSpots[i]] = player;
            if (player === "O") { move.score = minimax(newBoard, "X").score; }
            else { move.score = minimax(newBoard, "O").score; }
            newBoard[availSpots[i]] = "";
            moves.push(move);
        }

        let bestMove;
        if (player === "O") {
            let bestScore = -10000;
            for (let i = 0; i < moves.length; i++) {
                if (moves[i].score > bestScore) { bestScore = moves[i].score; bestMove = i; }
            }
        } else {
            let bestScore = 10000;
            for (let i = 0; i < moves.length; i++) {
                if (moves[i].score < bestScore) { bestScore = moves[i].score; bestMove = i; }
            }
        }
        return moves[bestMove];
    }

    function lumiMove() {
        if (!gameActive || currentGame !== "ttt") return;
        const bestSpot = minimax(board, "O").index;

        if (bestSpot !== undefined) {
            playBeep(400, 'square', 0.1); // Sound for O
            board[bestSpot] = "O";
            cells[bestSpot].innerText = "O";
            cells[bestSpot].classList.add("taken", "o");

            checkTicTacToeWinner();
            if (gameActive) {
                gameStatus.innerText = "Your Turn! (You are X)";
                window.setEmotion('happy');
            }
        }
    }

    function checkTicTacToeWinner() {
        const winPatterns = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
        let hasWinner = false; let winner = null;
        for (let pattern of winPatterns) {
            const [a, b, c] = pattern;
            if (board[a] && board[a] === board[b] && board[a] === board[c]) {
                hasWinner = true; winner = board[a]; break;
            }
        }

        if (hasWinner) {
            gameActive = false;
            if (winner === "X") {
                gameStatus.innerText = "You Won! 🎉";
                playWinSound();
                window.setEmotion('sad');
            } else {
                gameStatus.innerText = "Lumi Won! 🤖";
                playLoseSound();
                window.setEmotion('laughing');
            }
            return;
        }

        if (!board.includes("")) {
            gameActive = false;
            gameStatus.innerText = "It's a Draw! 🤝";
            playBeep(500, 'sine', 0.2);
            window.setEmotion('confused');
            return;
        }
    }

    // ----- MATH CHALLENGE -----
    const mathOptions = document.querySelectorAll('.math-option');
    const mathQuestion = document.getElementById('math-question');
    const mathScoreDisplay = document.getElementById('math-score');
    let correctMathAnswer = 0;
    let mathScore = 0;
    let mathQuestionsAnswered = 0;

    window.startMathGame = function () {
        currentGame = "math";
        gameMenu.style.display = "none";
        mathBoard.classList.remove("hidden");
        mathBoard.style.display = "flex";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";

        mathScore = 0;
        mathQuestionsAnswered = 0;
        mathScoreDisplay.innerText = `Score: 0 / 10`;
        mathOptions.forEach(btn => btn.style.display = "inline-block");

        nextMathQuestion();
    };

    function nextMathQuestion() {
        if (mathQuestionsAnswered >= 10) {
            gameStatus.innerText = `Quiz Complete! 🎉 You got ${mathScore} / 10`;
            mathQuestion.innerText = "Great Job!";
            mathScoreDisplay.innerText = "Finished!";
            mathOptions.forEach(btn => btn.style.display = "none");
            window.setEmotion(mathScore > 7 ? 'laughing' : 'happy');
            if (mathScore > 7) playWinSound();
            return;
        }

        mathOptions.forEach(btn => btn.style.display = "inline-block");
        gameStatus.innerText = `Question ${mathQuestionsAnswered + 1} of 10`;
        window.setEmotion('happy');

        let a = Math.floor(Math.random() * 10) + 1;
        let b = Math.floor(Math.random() * 10) + 1;
        let isAdd = Math.random() > 0.5;
        if (!isAdd && a < b) { let temp = a; a = b; b = temp; }

        correctMathAnswer = isAdd ? a + b : a - b;
        mathQuestion.innerText = `${a} ${isAdd ? '+' : '-'} ${b} = ?`;

        let answers = [correctMathAnswer];
        while (answers.length < 3) {
            let wrong = correctMathAnswer + Math.floor(Math.random() * 9) - 4;
            if (wrong !== correctMathAnswer && wrong >= 0 && !answers.includes(wrong)) {
                answers.push(wrong);
            }
        }
        answers.sort(() => Math.random() - 0.5);

        mathOptions.forEach((btn, i) => {
            btn.innerText = answers[i];
            btn.style.background = "#fff";
            btn.style.pointerEvents = "auto";
            btn.onclick = () => {
                mathOptions.forEach(b => b.style.pointerEvents = "none");
                mathQuestionsAnswered++;

                if (answers[i] === correctMathAnswer) {
                    playWinSound();
                    mathScore++;
                    mathScoreDisplay.innerText = `Score: ${mathScore} / 10`;
                    btn.style.background = "#a8ffb5";
                    gameStatus.innerText = "Correct! 🎉";
                    window.setEmotion('laughing');
                    setTimeout(nextMathQuestion, 1500);
                } else {
                    playLoseSound();
                    mathScoreDisplay.innerText = `Score: ${mathScore} / 10`;
                    btn.style.background = "#ffb5b5";
                    gameStatus.innerText = "Try again! 🤖";
                    window.setEmotion('sad');
                    setTimeout(() => {
                        btn.style.background = "#fff";
                        mathOptions.forEach(b => b.style.pointerEvents = "auto");
                        gameStatus.innerText = `Question ${mathQuestionsAnswered} of 10`;
                        window.setEmotion('happy');
                    }, 1000);
                }
            };
        });
    }

    // ----- ANIMAL QUIZ -----
    const animalCells = document.querySelectorAll('.animal-cell');
    const animalQuestion = document.getElementById('animal-question');
    const animals = [
        { name: "Dog", emoji: "🐶" }, { name: "Cat", emoji: "🐱" }, { name: "Tiger", emoji: "🐯" },
        { name: "Lion", emoji: "🦁" }, { name: "Bear", emoji: "🐻" }, { name: "Panda", emoji: "🐼" },
        { name: "Frog", emoji: "🐸" }, { name: "Cow", emoji: "🐮" }, { name: "Pig", emoji: "🐷" },
        { name: "Monkey", emoji: "🐵" }, { name: "Fox", emoji: "🦊" }, { name: "Mouse", emoji: "🐭" }
    ];

    window.startAnimalQuiz = function () {
        currentGame = "animal";
        gameMenu.style.display = "none";
        animalBoard.classList.remove("hidden");
        animalBoard.style.display = "flex";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";
        nextAnimalQuestion();
    };

    function nextAnimalQuestion() {
        gameStatus.innerText = "Animal Quiz!";
        window.setEmotion('happy');

        let shuffled = [...animals].sort(() => 0.5 - Math.random());
        let choices = shuffled.slice(0, 3);
        let correctAnimal = choices[Math.floor(Math.random() * choices.length)];

        animalQuestion.innerText = `Find the ${correctAnimal.name}!`;

        animalCells.forEach((cell, i) => {
            cell.innerText = choices[i].emoji;
            cell.style.background = "#fff";
            cell.style.pointerEvents = "auto";
            cell.onclick = () => {
                if (choices[i].name === correctAnimal.name) {
                    playWinSound();
                    cell.style.background = "#a8ffb5";
                    gameStatus.innerText = "You found it! 🎉";
                    window.setEmotion('laughing');
                    animalCells.forEach(c => c.style.pointerEvents = "none");
                    setTimeout(nextAnimalQuestion, 2000);
                } else {
                    playLoseSound();
                    cell.style.background = "#ffb5b5";
                    cell.style.pointerEvents = "none";
                    gameStatus.innerText = "Try again! 🤖";
                    window.setEmotion('confused');
                }
            };
        });
    }

    // ----- MEMORY MATCH -----
    const memoryEmojis = ["🍎", "🍌", "🍇", "🍉", "🍓", "🍒", "🥝", "🍍"];
    let memoryCards = [];
    let flippedCards = [];
    let matchesFound = 0;
    const memoryGrid = document.getElementById("memory-grid");

    window.startMemoryMatch = function () {
        currentGame = "memory";
        gameMenu.style.display = "none";
        document.getElementById("memory-board").classList.remove("hidden");
        document.getElementById("memory-board").style.display = "flex";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";
        resetMemoryGame();
    };

    window.resetMemoryGame = function () {
        matchesFound = 0;
        flippedCards = [];
        memoryGrid.innerHTML = "";
        gameStatus.innerText = "Memory Match!";
        window.setEmotion('happy');

        let deck = [...memoryEmojis, ...memoryEmojis].sort(() => 0.5 - Math.random());

        deck.forEach((emoji, i) => {
            let card = document.createElement("div");
            card.className = "memory-card";
            card.style.width = "80px";
            card.style.height = "80px";
            card.style.background = "#ddd";
            card.style.borderRadius = "10px";
            card.style.display = "flex";
            card.style.justifyContent = "center";
            card.style.alignItems = "center";
            card.style.fontSize = "40px";
            card.style.cursor = "pointer";
            card.dataset.val = emoji;
            card.dataset.index = i;
            card.innerText = "❓";

            card.onclick = () => flipMemoryCard(card);
            memoryGrid.appendChild(card);
        });
    };

    function flipMemoryCard(card) {
        if (flippedCards.length >= 2 || card.innerText !== "❓") return;
        playBeep(600, 'sine', 0.1);
        card.innerText = card.dataset.val;
        card.style.background = "#fff";
        flippedCards.push(card);

        if (flippedCards.length === 2) {
            setTimeout(checkMemoryMatch, 800);
        }
    }

    function checkMemoryMatch() {
        if (flippedCards[0].dataset.val === flippedCards[1].dataset.val) {
            playWinSound();
            flippedCards[0].style.background = "#a8ffb5";
            flippedCards[1].style.background = "#a8ffb5";
            matchesFound++;
            window.setEmotion('laughing');
            if (matchesFound === memoryEmojis.length) {
                gameStatus.innerText = "You found them all! 🎉";
            }
        } else {
            playBeep(300, 'sawtooth', 0.2);
            flippedCards[0].innerText = "❓";
            flippedCards[0].style.background = "#ddd";
            flippedCards[1].innerText = "❓";
            flippedCards[1].style.background = "#ddd";
            window.setEmotion('surprised');
        }
        flippedCards = [];
    }

    // ----- SIMON SAYS -----
    let simonSequence = [];
    let playerSequence = [];
    let simonLevel = 0;
    let simonPlaying = false;
    const simonScore = document.getElementById("simon-score");
    const simonBtns = document.querySelectorAll(".simon-btn");
    const simonSounds = [261.63, 329.63, 392.00, 523.25]; // C, E, G, C

    window.startSimonSays = function () {
        currentGame = "simon";
        gameMenu.style.display = "none";
        document.getElementById("simon-board").classList.remove("hidden");
        document.getElementById("simon-board").style.display = "flex";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";
        startSimonLevel(true);
    };

    window.startSimonLevel = function (reset = false) {
        if (reset) {
            simonSequence = [];
            simonLevel = 0;
        }
        simonLevel++;
        playerSequence = [];
        simonScore.innerText = `Level: ${simonLevel}`;
        gameStatus.innerText = "Watch carefully...";
        window.setEmotion('surprised');
        simonPlaying = false;

        simonSequence.push(Math.floor(Math.random() * 4));
        setTimeout(playSimonSequence, 1000);
    };

    function playSimonSequence() {
        let i = 0;
        let interval = setInterval(() => {
            lightUpSimon(simonSequence[i]);
            i++;
            if (i >= simonSequence.length) {
                clearInterval(interval);
                gameStatus.innerText = "Your turn!";
                window.setEmotion('happy');
                simonPlaying = true;
            }
        }, 800 - Math.min(simonLevel * 20, 400));
    }

    function lightUpSimon(index) {
        const btn = simonBtns[index];
        const oldBg = btn.style.background;
        playBeep(simonSounds[index], 'sine', 0.3);
        btn.style.filter = "brightness(2)";
        setTimeout(() => { btn.style.filter = "brightness(1)"; }, 300);
    }

    window.simonPlayerClick = function (index) {
        if (!simonPlaying || currentGame !== "simon") return;

        lightUpSimon(index);
        playerSequence.push(index);

        if (playerSequence[playerSequence.length - 1] !== simonSequence[playerSequence.length - 1]) {
            // Wrong
            playLoseSound();
            gameStatus.innerText = "Game Over! 💥";
            window.setEmotion('sad');
            simonPlaying = false;
            return;
        }

        if (playerSequence.length === simonSequence.length) {
            // Survived level
            simonPlaying = false;
            window.setEmotion('laughing');
            gameStatus.innerText = "Good job!";
            setTimeout(() => startSimonLevel(false), 1000);
        }
    };

    // ----- WORD GUESSER (Hangman Style) -----
    const wordDisplay = document.getElementById("word-display");
    const wordHint = document.getElementById("word-hint");
    const wordKeyboard = document.getElementById("word-keyboard");
    const wordList = [
        { word: "DOG", hint: "It barks and plays fetch" },
        { word: "CAT", hint: "It meows and purrs" },
        { word: "BIRD", hint: "It flies in the sky" },
        { word: "ROBOT", hint: "A machine that computes" },
        { word: "STAR", hint: "It twinkles at night" }
    ];
    let currentWord = "";
    let guessedLetters = [];

    window.startWordGuess = function () {
        currentGame = "word";
        gameMenu.style.display = "none";
        document.getElementById("word-board").classList.remove("hidden");
        document.getElementById("word-board").style.display = "flex";
        gameActions.classList.remove("hidden");
        gameActions.style.display = "flex";
        startWordGuessLevel();
    };

    window.startWordGuessLevel = function () {
        let randomObj = wordList[Math.floor(Math.random() * wordList.length)];
        currentWord = randomObj.word;
        wordHint.innerText = `Hint: ${randomObj.hint}`;
        guessedLetters = [];
        gameStatus.innerText = "Guess the Word!";
        window.setEmotion('happy');
        updateWordDisplay();
        renderKeyboard();
    };

    function updateWordDisplay() {
        let displayStr = "";
        let won = true;
        for (let char of currentWord) {
            if (guessedLetters.includes(char)) {
                displayStr += char + " ";
            } else {
                displayStr += "_ ";
                won = false;
            }
        }
        wordDisplay.innerText = displayStr.trim();

        if (won) {
            gameStatus.innerText = "You got it! 🎉";
            window.setEmotion('laughing');
            playWinSound();
            setTimeout(startWordGuessLevel, 2500);
        }
    }

    function renderKeyboard() {
        wordKeyboard.innerHTML = "";
        const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        for (let l of letters) {
            let btn = document.createElement("button");
            btn.innerText = l;
            btn.style.padding = "10px 15px";
            btn.style.fontSize = "18px";
            btn.style.borderRadius = "8px";
            btn.style.border = "none";
            btn.style.background = "#fff";
            btn.style.color = "#333";
            btn.style.cursor = "pointer";

            btn.onclick = () => {
                if (guessedLetters.includes(l)) return;
                guessedLetters.push(l);
                btn.style.pointerEvents = "none";

                if (currentWord.includes(l)) {
                    playBeep(800, 'sine', 0.1);
                    btn.style.background = "#a8ffb5";
                    window.setEmotion('surprised');
                } else {
                    playBeep(300, 'sawtooth', 0.1);
                    btn.style.background = "#ffb5b5";
                    window.setEmotion('sad');
                }
                updateWordDisplay();
            };
            wordKeyboard.appendChild(btn);
        }
    }

    // ==========================================
    // THEMES LOGIC
    // ==========================================
    const themesModal = document.getElementById("themes-modal");

    window.openThemesMode = function () {
        if (!themesModal) return;
        themesModal.classList.remove("hidden");
        themesModal.style.position = "absolute";
        themesModal.style.top = "0";
        themesModal.style.left = "0";
        themesModal.style.width = "100%";
        themesModal.style.height = "100%";
        themesModal.style.display = "flex";
        themesModal.style.justifyContent = "center";
        themesModal.style.alignItems = "center";
        themesModal.style.background = "rgba(0,0,0,0.6)";
        themesModal.style.zIndex = "40";
        window.setEmotion('happy');
    };

    window.closeThemesMode = function () {
        if (!themesModal) return;
        themesModal.classList.add("hidden");
        themesModal.style.display = "none";
    };

    window.setAppTheme = function (themeName) {
        document.body.classList.remove('theme-blue', 'theme-pink', 'theme-green', 'theme-dark', 'theme-gold', 'theme-purple');

        if (themeName !== 'pink') {
            document.body.classList.add('theme-' + themeName);
        }

        localStorage.setItem('lumi_theme', themeName);
        closeThemesMode();
    };

    // Load saved theme on startup
    const savedTheme = localStorage.getItem('lumi_theme');
    if (savedTheme) {
        setAppTheme(savedTheme);
    }

    // ==========================================
    // AUTO BATTERY MONITOR
    // ==========================================
    if ('getBattery' in navigator) {
        navigator.getBattery().then(function (battery) {
            function updateBatteryStatus() {
                // If battery under 15% and not charging
                if (battery.level <= 0.15 && !battery.charging) {
                    if (currentEmotion !== 'battery') {
                        window.setEmotion('battery');
                    }
                } else if (currentEmotion === 'battery' && (battery.level > 0.15 || battery.charging)) {
                    window.setEmotion('happy');
                }
            }
            updateBatteryStatus();
            battery.addEventListener('levelchange', updateBatteryStatus);
            battery.addEventListener('chargingchange', updateBatteryStatus);
        });
    }

});
