"""Thí nghiệm đối chứng: Minimax duyệt hết cây Tic-Tac-Toe 3×3 (trường hợp (3,3,3) của Caro).

Chạy: python3 experiments/tictactoe.py  → in kết quả và ghi experiments/tictactoe.json
"""
import json
import random
import time
from math import inf
from pathlib import Path

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def winner(b):
    for a, c, d in LINES:
        if b[a] != '.' and b[a] == b[c] == b[d]:
            return b[a]
    return 'draw' if '.' not in b else None


class C:
    nodes = 0


def minimax(b, player, ply, alpha=-inf, beta=inf, prune=False):
    """MAX = O. Utility = +10−ply (O thắng), −10+ply (X thắng), 0 (hòa)."""
    C.nodes += 1
    w = winner(b)
    if w == 'O':
        return 10 - ply
    if w == 'X':
        return -10 + ply
    if w == 'draw':
        return 0
    best = -inf if player == 'O' else inf
    for i in range(9):
        if b[i] != '.':
            continue
        b[i] = player
        v = minimax(b, 'X' if player == 'O' else 'O', ply + 1, alpha, beta, prune)
        b[i] = '.'
        if player == 'O':
            best, alpha = max(best, v), max(alpha, v)
        else:
            best, beta = min(best, v), min(beta, v)
        if prune and alpha >= beta:
            break
    return best


def best_move(b, player):
    moves = []
    for i in range(9):
        if b[i] == '.':
            b[i] = player
            v = minimax(b, 'X' if player == 'O' else 'O', 1, prune=True)
            b[i] = '.'
            moves.append((v if player == 'O' else -v, i))
    return max(moves)[1]


def main():
    out = {}
    for prune in (False, True):
        C.nodes = 0
        t0 = time.perf_counter()
        v = minimax(['.'] * 9, 'O', 0, prune=prune)
        out['alphabeta' if prune else 'minimax'] = {'value': v, 'nodes': C.nodes, 'ms': round((time.perf_counter() - t0) * 1000, 1)}
    # Giá trị từng nước mở đầu của O (O đi trước).
    first = []
    for i in range(9):
        b = ['.'] * 9
        b[i] = 'O'
        first.append(minimax(b, 'X', 1, prune=True))
    out['first_move_values'] = first
    # AI tối ưu đấu 200 ván với đối thủ ngẫu nhiên, luân phiên đi trước.
    rng = random.Random(2026)
    res = {'win': 0, 'draw': 0, 'loss': 0}
    for g in range(200):
        b = ['.'] * 9
        turn = 'O' if g % 2 == 0 else 'X'
        while winner(b) is None:
            if turn == 'O':
                i = best_move(b, 'O')
            else:
                i = rng.choice([k for k in range(9) if b[k] == '.'])
            b[i] = turn
            turn = 'X' if turn == 'O' else 'O'
        w = winner(b)
        res['win' if w == 'O' else 'draw' if w == 'draw' else 'loss'] += 1
    out['vs_random_200'] = res
    # AI tối ưu đấu với chính nó.
    b, turn = ['.'] * 9, 'O'
    while winner(b) is None:
        i = best_move(b, turn) if turn == 'O' else best_move(b, 'X')
        b[i] = turn
        turn = 'X' if turn == 'O' else 'O'
    out['self_play'] = winner(b)
    Path(__file__).with_name('tictactoe.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
