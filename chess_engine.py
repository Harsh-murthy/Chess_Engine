"""
Chess Engine - Complete implementation from scratch
Supports: full legal move generation, castling, en passant, promotion,
          check/checkmate/stalemate detection, and AI with minimax + alpha-beta pruning
"""

# Piece constants
EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 0, 1

# Piece values for evaluation
PIECE_VALUES = {PAWN: 100, KNIGHT: 320, BISHOP: 330, ROOK: 500, QUEEN: 900, KING: 20000}

# Positional tables (from white's perspective)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]
KING_MID_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

PIECE_TABLES = {
    PAWN: PAWN_TABLE, KNIGHT: KNIGHT_TABLE, BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE, QUEEN: QUEEN_TABLE, KING: KING_MID_TABLE
}


def sq(row, col):
    return row * 8 + col

def row_of(s): return s // 8
def col_of(s): return s % 8

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


class Board:
    def __init__(self):
        self.pieces = [EMPTY] * 64
        self.colors = [None] * 64
        self.turn = WHITE
        self.castling = {WHITE: {'K': True, 'Q': True}, BLACK: {'K': True, 'Q': True}}
        self.en_passant = None  # square index where en passant capture is possible
        self.halfmove_clock = 0
        self.fullmove = 1
        self._setup()

    def _setup(self):
        back_row = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for col, piece in enumerate(back_row):
            self.place(7, col, piece, WHITE)
            self.place(0, col, piece, BLACK)
        for col in range(8):
            self.place(6, col, PAWN, WHITE)
            self.place(1, col, PAWN, BLACK)

    def place(self, r, c, piece, color):
        s = sq(r, c)
        self.pieces[s] = piece
        self.colors[s] = color

    def get(self, s):
        return self.pieces[s], self.colors[s]

    def is_empty(self, s):
        return self.pieces[s] == EMPTY

    def copy(self):
        b = Board.__new__(Board)
        b.pieces = self.pieces[:]
        b.colors = self.colors[:]
        b.turn = self.turn
        b.castling = {WHITE: dict(self.castling[WHITE]), BLACK: dict(self.castling[BLACK])}
        b.en_passant = self.en_passant
        b.halfmove_clock = self.halfmove_clock
        b.fullmove = self.fullmove
        return b

    def to_fen_board(self):
        rows = []
        for r in range(8):
            row = ''
            empty = 0
            for c in range(8):
                s = sq(r, c)
                if self.pieces[s] == EMPTY:
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    names = {PAWN:'p',KNIGHT:'n',BISHOP:'b',ROOK:'r',QUEEN:'q',KING:'k'}
                    ch = names[self.pieces[s]]
                    row += ch.upper() if self.colors[s] == WHITE else ch
            if empty:
                row += str(empty)
            rows.append(row)
        return '/'.join(rows)


def _sliding_moves(board, s, directions):
    moves = []
    r, c = row_of(s), col_of(s)
    color = board.colors[s]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            ns = sq(nr, nc)
            if board.is_empty(ns):
                moves.append((s, ns, None))
            else:
                if board.colors[ns] != color:
                    moves.append((s, ns, None))
                break
            nr += dr
            nc += dc
    return moves


def _pawn_moves(board, s):
    moves = []
    r, c = row_of(s), col_of(s)
    color = board.colors[s]
    direction = -1 if color == WHITE else 1
    start_row = 6 if color == WHITE else 1
    promo_row = 0 if color == WHITE else 7

    # Forward
    nr = r + direction
    if in_bounds(nr, c) and board.is_empty(sq(nr, c)):
        if nr == promo_row:
            for p in [QUEEN, ROOK, BISHOP, KNIGHT]:
                moves.append((s, sq(nr, c), p))
        else:
            moves.append((s, sq(nr, c), None))
            # Double push
            if r == start_row and board.is_empty(sq(nr + direction, c)):
                moves.append((s, sq(nr + direction, c), None))

    # Captures
    for dc in [-1, 1]:
        nc = c + dc
        if not in_bounds(nr, nc):
            continue
        ns = sq(nr, nc)
        if not board.is_empty(ns) and board.colors[ns] != color:
            if nr == promo_row:
                for p in [QUEEN, ROOK, BISHOP, KNIGHT]:
                    moves.append((s, ns, p))
            else:
                moves.append((s, ns, None))
        # En passant
        if board.en_passant == ns:
            moves.append((s, ns, None))

    return moves


def _knight_moves(board, s):
    moves = []
    r, c = row_of(s), col_of(s)
    color = board.colors[s]
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            ns = sq(nr, nc)
            if board.is_empty(ns) or board.colors[ns] != color:
                moves.append((s, ns, None))
    return moves


def _king_moves(board, s):
    moves = []
    r, c = row_of(s), col_of(s)
    color = board.colors[s]
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                ns = sq(nr, nc)
                if board.is_empty(ns) or board.colors[ns] != color:
                    moves.append((s, ns, None))
    return moves


def _pseudo_moves(board, color):
    moves = []
    for s in range(64):
        if board.pieces[s] == EMPTY or board.colors[s] != color:
            continue
        p = board.pieces[s]
        if p == PAWN:
            moves.extend(_pawn_moves(board, s))
        elif p == KNIGHT:
            moves.extend(_knight_moves(board, s))
        elif p == BISHOP:
            moves.extend(_sliding_moves(board, s, [(-1,-1),(-1,1),(1,-1),(1,1)]))
        elif p == ROOK:
            moves.extend(_sliding_moves(board, s, [(-1,0),(1,0),(0,-1),(0,1)]))
        elif p == QUEEN:
            moves.extend(_sliding_moves(board, s, [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]))
        elif p == KING:
            moves.extend(_king_moves(board, s))
    return moves


def is_attacked(board, s, by_color):
    """Is square s attacked by by_color?"""
    # Temporarily assign a dummy piece at s to check attacks
    # Check pawns
    r, c = row_of(s), col_of(s)
    pawn_dir = 1 if by_color == WHITE else -1
    for dc in [-1, 1]:
        nr, nc = r + pawn_dir, c + dc
        if in_bounds(nr, nc):
            ns = sq(nr, nc)
            if board.pieces[ns] == PAWN and board.colors[ns] == by_color:
                return True
    # Knights
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            ns = sq(nr, nc)
            if board.pieces[ns] == KNIGHT and board.colors[ns] == by_color:
                return True
    # Sliding: bishops/queens on diagonals
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            ns = sq(nr, nc)
            if not board.is_empty(ns):
                if board.colors[ns] == by_color and board.pieces[ns] in (BISHOP, QUEEN):
                    return True
                break
            nr += dr; nc += dc
    # Sliding: rooks/queens on ranks/files
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            ns = sq(nr, nc)
            if not board.is_empty(ns):
                if board.colors[ns] == by_color and board.pieces[ns] in (ROOK, QUEEN):
                    return True
                break
            nr += dr; nc += dc
    # King
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                ns = sq(nr, nc)
                if board.pieces[ns] == KING and board.colors[ns] == by_color:
                    return True
    return False


def find_king(board, color):
    for s in range(64):
        if board.pieces[s] == KING and board.colors[s] == color:
            return s
    return -1


def apply_move(board, move):
    """Apply move to a copy of the board and return it."""
    b = board.copy()
    frm, to, promo = move
    piece = b.pieces[frm]
    color = b.colors[frm]
    enemy = BLACK if color == WHITE else WHITE

    b.halfmove_clock += 1
    old_ep = b.en_passant
    b.en_passant = None

    # En passant capture
    if piece == PAWN and to == old_ep:
        cap_row = row_of(to) + (1 if color == WHITE else -1)
        b.pieces[sq(cap_row, col_of(to))] = EMPTY
        b.colors[sq(cap_row, col_of(to))] = None
        b.halfmove_clock = 0

    # Regular capture
    if not b.is_empty(to):
        b.halfmove_clock = 0

    # Move piece
    b.pieces[to] = piece
    b.colors[to] = color
    b.pieces[frm] = EMPTY
    b.colors[frm] = None

    # Promotion
    if promo:
        b.pieces[to] = promo

    # Pawn double push -> set en passant
    if piece == PAWN:
        b.halfmove_clock = 0
        if abs(row_of(to) - row_of(frm)) == 2:
            ep_row = (row_of(frm) + row_of(to)) // 2
            b.en_passant = sq(ep_row, col_of(frm))

    # Castling move
    if piece == KING:
        b.castling[color]['K'] = False
        b.castling[color]['Q'] = False
        # Kingside
        if col_of(to) - col_of(frm) == 2:
            rook_row = row_of(frm)
            b.pieces[sq(rook_row, 5)] = ROOK
            b.colors[sq(rook_row, 5)] = color
            b.pieces[sq(rook_row, 7)] = EMPTY
            b.colors[sq(rook_row, 7)] = None
        # Queenside
        elif col_of(frm) - col_of(to) == 2:
            rook_row = row_of(frm)
            b.pieces[sq(rook_row, 3)] = ROOK
            b.colors[sq(rook_row, 3)] = color
            b.pieces[sq(rook_row, 0)] = EMPTY
            b.colors[sq(rook_row, 0)] = None

    # Rook moves invalidate castling
    if piece == ROOK:
        back_row = 7 if color == WHITE else 0
        if frm == sq(back_row, 7): b.castling[color]['K'] = False
        if frm == sq(back_row, 0): b.castling[color]['Q'] = False

    # If enemy rook captured
    enemy_back = 7 if enemy == WHITE else 0
    if to == sq(enemy_back, 7): b.castling[enemy]['K'] = False
    if to == sq(enemy_back, 0): b.castling[enemy]['Q'] = False

    b.turn = enemy
    if color == BLACK:
        b.fullmove += 1

    return b


def _castling_moves(board):
    moves = []
    color = board.turn
    back_row = 7 if color == WHITE else 0
    enemy = BLACK if color == WHITE else WHITE
    king_sq = sq(back_row, 4)

    if board.pieces[king_sq] != KING or board.colors[king_sq] != color:
        return moves
    if is_attacked(board, king_sq, enemy):
        return moves

    # Kingside
    if board.castling[color]['K']:
        if (board.is_empty(sq(back_row, 5)) and
            board.is_empty(sq(back_row, 6)) and
            not is_attacked(board, sq(back_row, 5), enemy) and
            not is_attacked(board, sq(back_row, 6), enemy)):
            moves.append((king_sq, sq(back_row, 6), None))

    # Queenside
    if board.castling[color]['Q']:
        if (board.is_empty(sq(back_row, 3)) and
            board.is_empty(sq(back_row, 2)) and
            board.is_empty(sq(back_row, 1)) and
            not is_attacked(board, sq(back_row, 3), enemy) and
            not is_attacked(board, sq(back_row, 2), enemy)):
            moves.append((king_sq, sq(back_row, 2), None))

    return moves


def legal_moves(board):
    color = board.turn
    enemy = BLACK if color == WHITE else WHITE
    pseudo = _pseudo_moves(board, color)
    pseudo.extend(_castling_moves(board))
    legal = []
    for move in pseudo:
        b2 = apply_move(board, move)
        ks = find_king(b2, color)
        if ks != -1 and not is_attacked(b2, ks, enemy):
            legal.append(move)
    return legal


def is_in_check(board, color):
    ks = find_king(board, color)
    enemy = BLACK if color == WHITE else WHITE
    return is_attacked(board, ks, enemy)


def is_checkmate(board):
    return is_in_check(board, board.turn) and len(legal_moves(board)) == 0


def is_stalemate(board):
    return not is_in_check(board, board.turn) and len(legal_moves(board)) == 0


def is_insufficient_material(board):
    pieces = [(board.pieces[s], board.colors[s]) for s in range(64) if board.pieces[s] != EMPTY]
    if len(pieces) == 2:
        return True  # K vs K
    if len(pieces) == 3:
        types = [p for p, _ in pieces]
        if BISHOP in types or KNIGHT in types:
            return True
    return False


# ─── Evaluation ────────────────────────────────────────────────────────────────

def evaluate(board):
    if is_checkmate(board):
        return 100000 if board.turn == BLACK else -100000
    if is_stalemate(board) or is_insufficient_material(board):
        return 0

    score = 0
    for s in range(64):
        if board.pieces[s] == EMPTY:
            continue
        p, color = board.pieces[s], board.colors[s]
        val = PIECE_VALUES[p]
        table = PIECE_TABLES.get(p, None)
        if table:
            idx = s if color == BLACK else (56 - (s // 8) * 8 + s % 8)
            val += table[idx]
        score += val if color == WHITE else -val
    return score


def order_moves(board, moves):
    """Basic move ordering: captures first, then checks."""
    def score(m):
        _, to, promo = m
        s = 0
        if not board.is_empty(to):
            s += PIECE_VALUES.get(board.pieces[to], 0) * 10
        if promo:
            s += PIECE_VALUES.get(promo, 0)
        return -s
    return sorted(moves, key=score)


def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or is_checkmate(board) or is_stalemate(board) or is_insufficient_material(board):
        return evaluate(board), None

    moves = legal_moves(board)
    if not moves:
        return evaluate(board), None
    moves = order_moves(board, moves)

    best_move = moves[0]
    if maximizing:
        best_val = float('-inf')
        for m in moves:
            b2 = apply_move(board, m)
            val, _ = minimax(b2, depth - 1, alpha, beta, False)
            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = float('inf')
        for m in moves:
            b2 = apply_move(board, m)
            val, _ = minimax(b2, depth - 1, alpha, beta, True)
            if val < best_val:
                best_val = val
                best_move = m
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move


def get_ai_move(board, depth=3):
    maximizing = (board.turn == WHITE)
    _, move = minimax(board, depth, float('-inf'), float('inf'), maximizing)
    return move


# ─── Serialization helpers ─────────────────────────────────────────────────────

def board_to_dict(board):
    grid = []
    for r in range(8):
        row = []
        for c in range(8):
            s = sq(r, c)
            if board.pieces[s] == EMPTY:
                row.append(None)
            else:
                names = {PAWN:'p',KNIGHT:'n',BISHOP:'b',ROOK:'r',QUEEN:'q',KING:'k'}
                ch = names[board.pieces[s]]
                row.append(ch.upper() if board.colors[s] == WHITE else ch)
        grid.append(row)
    return {
        'grid': grid,
        'turn': 'white' if board.turn == WHITE else 'black',
        'in_check': is_in_check(board, board.turn),
        'checkmate': is_checkmate(board),
        'stalemate': is_stalemate(board),
        'insufficient': is_insufficient_material(board),
        'en_passant': board.en_passant,
        'castling': {
            'white': board.castling[WHITE],
            'black': board.castling[BLACK],
        }
    }


def move_from_uci(uci):
    """Parse a UCI move like 'e2e4' or 'e7e8q'."""
    files = 'abcdefgh'
    frm_c = files.index(uci[0])
    frm_r = 8 - int(uci[1])
    to_c = files.index(uci[2])
    to_r = 8 - int(uci[3])
    promo = None
    if len(uci) == 5:
        promo = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}[uci[4]]
    return (sq(frm_r, frm_c), sq(to_r, to_c), promo)


def move_to_uci(move):
    files = 'abcdefgh'
    frm, to, promo = move
    s = f"{files[col_of(frm)]}{8 - row_of(frm)}{files[col_of(to)]}{8 - row_of(to)}"
    if promo:
        s += {QUEEN:'q', ROOK:'r', BISHOP:'b', KNIGHT:'n'}[promo]
    return s


def get_legal_moves_for_square(board, s):
    moves = legal_moves(board)
    return [move_to_uci(m) for m in moves if m[0] == s]
