"""Exact-five Caro rules and time-bounded, threat-aware alpha-beta search."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from math import inf
from secrets import choice
from time import monotonic

SIZE = 15
WIN_LENGTH = 5
EMPTY, HUMAN, SECOND = '.', 'X', 'O'
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))
WIN_SCORE = 10_000_000


def winning_line(board, row, col, player):
    if player not in (HUMAN, SECOND) or board[row][col] != player:
        return []
    for dr, dc in DIRECTIONS:
        line = [(row, col)]
        for sign in (-1, 1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < SIZE and 0 <= c < SIZE and board[r][c] == player:
                line.append((r, c))
                r, c = r + sign * dr, c + sign * dc
        if len(line) == WIN_LENGTH:
            return sorted(line)
    return []


def is_win(board, row, col, player):
    return bool(winning_line(board, row, col, player))


@dataclass
class Game:
    mode: str
    board: list[list[str]] = field(default_factory=lambda: [[EMPTY] * SIZE for _ in range(SIZE)])
    turn: str = field(default_factory=lambda: choice((HUMAN, SECOND)))
    starter: str = field(init=False)
    winner: str | None = None
    moves: int = 0
    last_move: tuple[int, int] | None = None
    win_cells: list = field(default_factory=list)
    api_key: str = field(default='', repr=False)
    provider: str = 'openai'
    base_url: str = ''
    model: str = ''
    ai_note: str = ''

    def __post_init__(self):
        self.starter = self.turn

    @property
    def done(self):
        return self.winner is not None

    @property
    def llm_enabled(self):
        return bool(self.base_url and self.model)

    def play(self, row, col):
        if self.done:
            raise ValueError('Ván đấu đã kết thúc.')
        if type(row) is not int or type(col) is not int or not (0 <= row < SIZE and 0 <= col < SIZE):
            raise ValueError('Nước đi nằm ngoài bàn cờ.')
        if self.board[row][col] != EMPTY:
            raise ValueError('Ô này đã được đánh.')
        player = self.turn
        self.board[row][col] = player
        self.moves += 1
        self.last_move = (row, col)
        self.win_cells = winning_line(self.board, row, col, player)
        if self.win_cells:
            self.winner = player
        elif self.moves == SIZE * SIZE:
            self.winner = 'draw'
        else:
            self.turn = SECOND if player == HUMAN else HUMAN

    def public(self):
        return {key: getattr(self, key) for key in (
            'mode', 'board', 'turn', 'starter', 'winner', 'moves', 'last_move', 'win_cells', 'ai_note'
        )} | {'llm_enabled': self.llm_enabled, 'provider': self.provider}


def nearby_moves(board, radius=2):
    occupied = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] != EMPTY]
    if not occupied:
        return [(7, 7)]
    found = set()
    for row, col in occupied:
        for r in range(max(0, row-radius), min(SIZE, row+radius+1)):
            for c in range(max(0, col-radius), min(SIZE, col+radius+1)):
                if board[r][c] == EMPTY:
                    found.add((r, c))
    return sorted(found, key=lambda p: (abs(p[0]-7) + abs(p[1]-7), p))


# Every complete row, column and diagonal; cache line evaluations across nodes.
LINES = []
for dr, dc in DIRECTIONS:
    for r in range(SIZE):
        for c in range(SIZE):
            if 0 <= r-dr < SIZE and 0 <= c-dc < SIZE:
                continue
            line = []
            rr, cc = r, c
            while 0 <= rr < SIZE and 0 <= cc < SIZE:
                line.append((rr, cc))
                rr, cc = rr+dr, cc+dc
            if len(line) >= 5:
                LINES.append(line)
CELL_LINES = {(r, c): [line for line in LINES if (r, c) in line] for r in range(SIZE) for c in range(SIZE)}


@lru_cache(maxsize=65536)
def _line_score(text, player):
    opponent = HUMAN if player == SECOND else SECOND
    score = 0
    for start in range(len(text)-4):
        window = text[start:start+5]
        if opponent in window:
            continue
        # A five-window extended by the same colour cannot make exact five.
        if (start > 0 and text[start-1] == player) or (start+5 < len(text) and text[start+5] == player):
            continue
        own = window.count(player)
        score += (0, 2, 30, 550, 18000, WIN_SCORE)[own]
    return score


def evaluate(board):
    value = 0
    for line in LINES:
        text = ''.join(board[r][c] for r, c in line)
        value += _line_score(text, SECOND) - _line_score(text, HUMAN)
    return value


def _potential(board, row, col, player):
    value = 0
    for line in CELL_LINES[row, col]:
        text = ''.join(board[r][c] for r, c in line)
        value += _line_score(text, player)
    return value


def _ordered(board, player, limit, deadline=inf):
    opponent = HUMAN if player == SECOND else SECOND
    ranked, wins, blocks = [], [], []
    for row, col in nearby_moves(board):
        if monotonic() >= deadline:
            raise TimeoutError
        try:
            board[row][col] = player
            if is_win(board, row, col, player):
                wins.append((row, col))
            attack = _potential(board, row, col, player)
            board[row][col] = opponent
            if is_win(board, row, col, opponent):
                blocks.append((row, col))
            defense = _potential(board, row, col, opponent)
        finally:
            board[row][col] = EMPTY
        ranked.append((attack + defense * 1.1, row, col))
    # Never discard a forced win or a mandatory block due to branch limits.
    if wins:
        return wins
    if blocks:
        return blocks
    ranked.sort(key=lambda p: -p[0])
    return [(r, c) for _, r, c in ranked[:limit]]


def _minimax(board, depth, player, alpha, beta, deadline, ply):
    if monotonic() >= deadline:
        raise TimeoutError
    if depth == 0:
        return evaluate(board)
    maximizing = player == SECOND
    moves = _ordered(board, player, 10 if depth > 1 else 8, deadline)
    if not moves:
        return 0
    best = -inf if maximizing else inf
    for row, col in moves:
        try:
            board[row][col] = player
            if is_win(board, row, col, player):
                value = WIN_SCORE-ply if maximizing else -WIN_SCORE+ply
            else:
                value = _minimax(board, depth-1, HUMAN if maximizing else SECOND, alpha, beta, deadline, ply+1)
        finally:
            board[row][col] = EMPTY
        if maximizing:
            best, alpha = max(best, value), max(alpha, value)
        else:
            best, beta = min(best, value), min(beta, value)
        if alpha >= beta:
            break
    return int(best)


def ranked_ai_moves(board, count=5, time_limit=1.5, max_depth=4):
    """Rank O moves. Only completed iterative-deepening rounds are published.

    Tactical win/block checks precede the timed search. The caller's board is
    never mutated, including when a search times out.
    """
    board = [row[:] for row in board]
    candidates = _ordered(board, SECOND, 16)
    if not candidates:
        return []
    results = []
    for row, col in candidates:
        board[row][col] = SECOND
        if is_win(board, row, col, SECOND):
            return [(row, col, WIN_SCORE)]
        score = evaluate(board)
        board[row][col] = EMPTY
        results.append((row, col, score))
    if len(results) == 1:
        return results
    results.sort(key=lambda p: -p[2])
    deadline = monotonic() + time_limit
    for depth in range(2, max_depth+1):
        complete = []
        try:
            for row, col, _ in results:
                try:
                    board[row][col] = SECOND
                    score = _minimax(board, depth-1, HUMAN, -inf, inf, deadline, 1)
                finally:
                    board[row][col] = EMPTY
                complete.append((row, col, score))
        except TimeoutError:
            break
        results = sorted(complete, key=lambda p: -p[2])
        if abs(results[0][2]) >= WIN_SCORE - 100:
            break
    return results[:count]
