♟️ AI Chess Trainer: A custom-built, multi-threaded Python chess engine designed for sparring, analysis, and tactical improvement. This application bridges the gap between competitive chess play and deep-learning performance analysis.

🧩 Core Architecture: The application is built using a Modular Tab-Based UI implemented in CustomTkinter. It utilizes Python-Chess for move validation and engine interfacing, while managing AI difficulty through a custom-built, adaptive, and performance-based Elo algorithm.


🚀 Key Features1. The Arena (Competitive Mode)Adaptive AI Trainer: The bot dynamically scales its decision-making depth based on your calculated Elo rating. 2-Move Premove Queue: Seamlessly input moves during the AI's turn to maintain high-speed blitz performance.Tactical Material Tracking: Real-time material differential calculation with automated captured-piece visualization.IP Anti-Tamper System: Integrated immutable security signatures to ensure code integrity during runtime. 2. The Sandbox (Sparring & Testing Mode)Dedicated Editor: A completely isolated environment for testing specific board states, opening traps, or endgame scenarios.FEN Injection: Import/Export Board states using standard Forsyth-Edwards Notation (FEN).Live Engine Evaluation: A continuous background Stockfish process provides real-time position evaluation (e.g., +1.5, -2.3) as you build your custom board.Engine Selectivity: Toggle between your Adaptive Trainer or a raw, high-depth Stockfish (3200+ Elo) for true sparring. 3. The Lab (Analytical Dashboard)Dynamic Elo Calculation: Moving away from flat point gains, the application uses a professional K-Factor-based Elo formula that weights performance against the relative strength of the opponent.Tactical Blind Spot Scanner: A sophisticated background engine that parses your saved match_history.json to identify consistent blunder patterns. 4. The ArchiveJSON History Cache: A lightweight, persistent database that records every match move-by-move.Full Replay Engine: Navigate through previous matches with complete move-stack traversal (Step forward/backward) to analyze mistakes.


🛠️ Technical Implementation: Multi-threading: To ensure the GUI never freezes during intensive engine calculations, the AI move logic, Blind Spot Scanner, and Evaluation loops all run on independent background threads. Coordinate Mapping: A custom math-inversion layer allows the board to map pixel-coordinates to the chess. Board array perfectly, whether you are playing as White or Black.

The Math Behind The AI: Expected Score: Calculated as $E_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}$.Performance Variance: Rating updates utilize a $K$-factor of 32 for developing players to reward rapid improvement.

⚙️ Installation & Setup: Clone the repository: Bashgit clone https://github.com/anthony-mishriky/AI-Chess-Trainer.git

Install Dependencies: Bash pip install -r requirements.txt
Engine Binary: This repository does not include the Stockfish binary due to file size limits.
Download the latest version from the Official Stockfish Website.
Place the stockfish.exe inside an engine_bin/ folder at the root directory.
Launch: Bashpython main.py

⚖️ Attribution Author: Anthony Mishriky
Contact: anthonymishrikyprivate@gmail.com
LinkedIn: www.linkedin.com/in/anthony-mishriky
