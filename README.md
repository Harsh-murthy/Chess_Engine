# ♟ Chess Engine

A fully functional chess engine built from scratch in Python with a Flask web server and a browser-based UI. No external chess libraries — every rule, move, and AI decision is implemented from the ground up.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Features

- **Complete chess rules** — castling, en passant, pawn promotion, check, checkmate, stalemate, and insufficient material draws
- **AI opponent** — Minimax with alpha-beta pruning and positional piece-square tables
- **4 difficulty levels** — Easy through Expert (search depth 1–4)
- **Play vs Computer or Two Players** on the same machine
- **Move history** — full game log with UCI notation
- **Captured pieces** tracker
- **Undo move** — steps back one full turn (player + AI)
- **Dark wood UI** — clean browser-based interface, no installation needed for players

---

## Project Structure

```
chess-engine/
├── app.py              # Flask web server & REST API
├── chess_engine.py     # Chess engine (rules, AI, move generation)
├── requirements.txt    # Python dependencies
├── Procfile            # For deployment on Render / Railway
└── static/
    └── index.html      # Frontend UI (HTML + CSS + JS, single file)
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/chess-engine.git
cd chess-engine

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## How to Play

1. Choose **vs Computer** or **Two Players**
2. If playing vs Computer, select your colour and difficulty
3. Click a piece to select it — legal moves are highlighted
4. Click a destination square to move
5. Pawn reaching the last rank opens a **promotion dialog**
6. Use **Undo Move** to take back your last move
7. Use **New Game** to start over

---

## API Endpoints

The Flask server exposes a simple REST API:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/new_game` | Start a new game session |
| POST | `/api/move` | Make a move (UCI format e.g. `e2e4`) |
| POST | `/api/legal_moves` | Get legal moves for a square |
| POST | `/api/ai_move` | Trigger the AI to make a move |
| POST | `/api/undo` | Undo the last move |

### Example request — make a move

```bash
curl -X POST http://localhost:5000/api/move \
  -H "Content-Type: application/json" \
  -d '{"game_id": "abc12345", "move": "e2e4"}'
```

---

## How the AI Works

The engine uses **Minimax search with Alpha-Beta pruning**:

- Evaluates positions using material count + positional piece-square tables
- Alpha-beta pruning cuts branches that can't affect the result, making deeper search practical
- Move ordering (captures first) improves pruning efficiency
- Depth scales with difficulty: Easy=1, Medium=2, Hard=3, Expert=4

---

## Deploying for Free

### Render (recommended)
1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Set start command to `python app.py`
4. Deploy — you get a free public URL

### Railway
1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your repo — it auto-detects Flask
3. Deploy

Make sure your `app.py` reads the port from the environment (already configured):
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

---

## Built With

- **Python** — chess engine logic and web server
- **Flask** — lightweight REST API
- **HTML / CSS / JavaScript** — single-file frontend, no frameworks
- **Unicode chess symbols** — ♔♕♖♗♘♙ rendered natively in the browser

---

## License

MIT — free to use, modify, and distribute.
