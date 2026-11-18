"""Minimax for the 3×3 board (three in a row wins).

The whole 3×3 game tree is tiny, so "hard" searches it to the end and never
loses. "easy" and "medium" stop after 1 and 2 plies: easy only sees its own
immediate win, medium also blocks an immediate loss but can be beaten with a
fork. Moves with equal value are chosen at random so games vary.
"""
from __future__ import annotations

from functools import lru_cache
from secrets import choice

EMPTY, HUMAN, SECOND = '.', 'X', 'O'
LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
# Search depth per difficulty level; 9 plies covers every possible game.
DEPTHS = {'easy': 1, 'medium': 2, 'hard': 9}
WIN = 10


def winner(cells):
    for a, b, c in LINES:
        if cells[a] != EMPTY and cells[a] == cells[b] == cells[c]:
            return cells[a]
    return 'draw' if EMPTY not in cells else None


@lru_cache(maxsize=None)
def _value(cells, player, depth, ply):
    """Score for O (maximizer): +WIN-ply if O wins, -WIN+ply if X wins, 0 otherwise."""
    result = winner(cells)
    if result == SECOND:
        return WIN - ply
    if result == HUMAN:
        return -WIN + ply
    if result == 'draw' or depth == 0:
        return 0
    nxt = HUMAN if player == SECOND else SECOND
    scores = [_value(cells[:i] + player + cells[i+1:], nxt, depth-1, ply+1)
              for i, mark in enumerate(cells) if mark == EMPTY]
    return max(scores) if player == SECOND else min(scores)


def scored_moves(board, level='hard'):
    """Return [(row, col, score)] for every empty cell, from O's point of view."""
    depth = DEPTHS[level]
    cells = ''.join(''.join(row) for row in board)
    if len(cells) != 9 or winner(cells):
        return []
    return [(i // 3, i % 3, _value(cells[:i] + SECOND + cells[i+1:], HUMAN, depth-1, 1))
            for i, mark in enumerate(cells) if mark == EMPTY]


def best_move(board, level='hard'):
    """Pick one of O's best moves at the given level, or None if the game is over."""
    moves = scored_moves(board, level)
    if not moves:
        return None
    top = max(score for _, _, score in moves)
    row, col, _ = choice([m for m in moves if m[2] == top])
    return row, col
