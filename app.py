"""
Chess Engine Web Server
Run with: python app.py
Then open http://localhost:5000
"""

import json
import uuid
from flask import Flask, request, jsonify, send_from_directory
from chess_engine import (
    Board, board_to_dict, move_from_uci, move_to_uci,
    apply_move, legal_moves, get_ai_move, get_legal_moves_for_square,
    is_checkmate, is_stalemate, is_insufficient_material, is_in_check,
    WHITE, BLACK, sq
)

app = Flask(__name__, static_folder='static')

# In-memory game sessions
games = {}


def new_game_state(mode='pvai', player_color='white', difficulty=3):
    board = Board()
    return {
        'board': board,
        'mode': mode,  # 'pvp' or 'pvai'
        'player_color': WHITE if player_color == 'white' else BLACK,
        'difficulty': difficulty,
        'history': [],  # list of (uci, fen-like snapshot)
        'captured': {'white': [], 'black': []},
    }


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    data = request.get_json(force=True)
    mode = data.get('mode', 'pvai')
    player_color = data.get('player_color', 'white')
    difficulty = int(data.get('difficulty', 3))
    game_id = str(uuid.uuid4())[:8]
    games[game_id] = new_game_state(mode, player_color, difficulty)
    state = games[game_id]
    bd = board_to_dict(state['board'])
    return jsonify({
        'game_id': game_id,
        'board': bd,
        'mode': mode,
        'player_color': player_color,
        'difficulty': difficulty
    })


@app.route('/api/move', methods=['POST'])
def make_move():
    data = request.get_json(force=True)
    game_id = data.get('game_id')
    uci = data.get('move')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    state = games[game_id]
    board = state['board']

    if is_checkmate(board) or is_stalemate(board) or is_insufficient_material(board):
        return jsonify({'error': 'Game is over'}), 400

    # Parse and validate move
    try:
        move = move_from_uci(uci)
    except Exception:
        return jsonify({'error': 'Invalid move format'}), 400

    legal = legal_moves(board)
    if move not in legal:
        return jsonify({'error': 'Illegal move'}), 400

    # Track capture
    frm, to, promo = move
    if not board.is_empty(to):
        piece_char = _piece_char(board, to)
        color_key = 'white' if board.colors[to] == WHITE else 'black'
        state['captured'][color_key].append(piece_char)

    # Apply player move
    state['history'].append(uci)
    state['board'] = apply_move(board, move)
    board = state['board']

    response = {
        'board': board_to_dict(board),
        'move': uci,
        'captured': state['captured'],
        'history': state['history'],
        'ai_move': None
    }

    # If PvAI and game not over and it's AI's turn
    if (state['mode'] == 'pvai' and
        not is_checkmate(board) and not is_stalemate(board) and
        not is_insufficient_material(board) and
        board.turn != state['player_color']):

        ai_move = get_ai_move(board, depth=state['difficulty'])
        if ai_move:
            frm2, to2, _ = ai_move
            if not board.is_empty(to2):
                piece_char = _piece_char(board, to2)
                color_key = 'white' if board.colors[to2] == WHITE else 'black'
                state['captured'][color_key].append(piece_char)
            ai_uci = move_to_uci(ai_move)
            state['history'].append(ai_uci)
            state['board'] = apply_move(board, ai_move)
            response['ai_move'] = ai_uci
            response['board'] = board_to_dict(state['board'])
            response['captured'] = state['captured']
            response['history'] = state['history']

    return jsonify(response)


@app.route('/api/legal_moves', methods=['POST'])
def get_legal():
    data = request.get_json(force=True)
    game_id = data.get('game_id')
    square = data.get('square')  # index 0-63

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    state = games[game_id]
    moves = get_legal_moves_for_square(state['board'], square)
    return jsonify({'moves': moves})


@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    """Trigger AI move (used when human plays as black)."""
    data = request.get_json(force=True)
    game_id = data.get('game_id')
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    state = games[game_id]
    board = state['board']
    if is_checkmate(board) or is_stalemate(board) or is_insufficient_material(board):
        return jsonify({'error': 'Game over'}), 400
    move = get_ai_move(board, depth=state['difficulty'])
    if not move:
        return jsonify({'error': 'No moves'}), 400
    frm, to, _ = move
    if not board.is_empty(to):
        piece_char = _piece_char(board, to)
        color_key = 'white' if board.colors[to] == WHITE else 'black'
        state['captured'][color_key].append(piece_char)
    uci = move_to_uci(move)
    state['history'].append(uci)
    state['board'] = apply_move(board, move)
    return jsonify({
        'board': board_to_dict(state['board']),
        'move': uci,
        'captured': state['captured'],
        'history': state['history'],
    })


@app.route('/api/undo', methods=['POST'])
def undo():
    data = request.get_json(force=True)
    game_id = data.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    state = games[game_id]
    # Undo 2 moves (player + AI) or 1 (pvp)
    undo_count = 2 if state['mode'] == 'pvai' and len(state['history']) >= 2 else 1
    if len(state['history']) < undo_count:
        return jsonify({'error': 'Nothing to undo'}), 400

    # Replay from scratch
    history = state['history'][:-undo_count]
    board = Board()
    for uci in history:
        move = move_from_uci(uci)
        board = apply_move(board, move)
    state['board'] = board
    state['history'] = history
    state['captured'] = {'white': [], 'black': []}

    return jsonify({
        'board': board_to_dict(state['board']),
        'history': state['history'],
        'captured': state['captured']
    })


def _piece_char(board, s):
    names = {1:'p',2:'n',3:'b',4:'r',5:'q',6:'k'}
    ch = names.get(board.pieces[s], '?')
    return ch.upper() if board.colors[s] == WHITE else ch


if __name__ == '__main__':
    import os
    os.makedirs('static', exist_ok=True)
    print("♟  Chess Engine Server starting at http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
