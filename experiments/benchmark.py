"""Thực nghiệm cho báo cáo: đo số node, thời gian và tỉ lệ thắng của AI Caro XP.

Chạy:  python3 experiments/benchmark.py [--games N] [--seed S]
Kết quả in ra màn hình và ghi vào experiments/results.json.
Script không sửa engine; chỉ gọi lại các hàm trong caro/engine.py.
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import sys
import time
from math import inf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from caro import engine  # noqa: E402
from caro.engine import EMPTY, HUMAN, SECOND, SIZE, WIN_SCORE, evaluate, is_win, nearby_moves, ranked_ai_moves  # noqa: E402

OUT = Path(__file__).resolve().parent / 'results.json'


# ---------------------------------------------------------------- helpers
def blank():
    return [[EMPTY] * SIZE for _ in range(SIZE)]


def swap(board):
    m = {HUMAN: SECOND, SECOND: HUMAN, EMPTY: EMPTY}
    return [[m[v] for v in row] for row in board]


def full(board):
    return all(v != EMPTY for row in board for v in row)


class Counter:
    def __init__(self):
        self.nodes = 0
        self.leaves = 0
        self.cutoffs = 0


def search(board, depth, player, alpha, beta, ply, c, prune=True, ordered=True, rng=None):
    """Bản sao của engine._minimax có đếm node; prune/ordered để so sánh."""
    c.nodes += 1
    if depth == 0:
        c.leaves += 1
        return evaluate(board)
    maximizing = player == SECOND
    moves = engine._ordered(board, player, 10 if depth > 1 else 8)
    if not ordered:
        moves = moves[:]
        rng.shuffle(moves)
    best = -inf if maximizing else inf
    for row, col in moves:
        board[row][col] = player
        if is_win(board, row, col, player):
            c.nodes += 1
            value = WIN_SCORE - ply if maximizing else -WIN_SCORE + ply
        else:
            value = search(board, depth - 1, HUMAN if maximizing else SECOND, alpha, beta, ply + 1, c, prune, ordered, rng)
        board[row][col] = EMPTY
        if maximizing:
            best, alpha = max(best, value), max(alpha, value)
        else:
            best, beta = min(best, value), min(beta, value)
        if prune and alpha >= beta:
            c.cutoffs += 1
            break
    return best


def root_search(board, depth, prune=True, ordered=True, seed=0):
    """Tìm nước cho O ở đúng một độ sâu cố định (không giới hạn thời gian)."""
    board = [r[:] for r in board]
    rng = random.Random(seed)
    c = Counter()
    t0 = time.perf_counter()
    cands = engine._ordered(board, SECOND, 16)
    if not ordered:
        rng.shuffle(cands)
    best, best_move = -inf, None
    alpha = -inf
    for row, col in cands:
        board[row][col] = SECOND
        c.nodes += 1
        if is_win(board, row, col, SECOND):
            value = WIN_SCORE
        elif depth == 1:
            c.leaves += 1
            value = evaluate(board)
        else:
            # Gốc chia sẻ alpha giữa các nhánh khi bật cắt tỉa.
            value = search(board, depth - 1, HUMAN, alpha if prune else -inf, inf, 1, c, prune, ordered, rng)
        board[row][col] = EMPTY
        if value > best:
            best, best_move = value, (row, col)
        alpha = max(alpha, best)
    return {'nodes': c.nodes, 'leaves': c.leaves, 'cutoffs': c.cutoffs,
            'ms': (time.perf_counter() - t0) * 1000, 'move': best_move, 'score': best}


# ---------------------------------------------------------------- players
def ai_move(board, player, max_depth=4, time_limit=1.5):
    view = board if player == SECOND else swap(board)
    res = ranked_ai_moves(view, count=1, time_limit=time_limit, max_depth=max_depth)
    return res[0][0], res[0][1]


def greedy_move(board, player):
    """Tham lam 1 lớp: chọn ô làm evaluate() tốt nhất cho mình."""
    best, move = -inf, None
    sign = 1 if player == SECOND else -1
    for r, c in nearby_moves(board):
        board[r][c] = player
        if is_win(board, r, c, player):
            board[r][c] = EMPTY
            return r, c
        v = sign * evaluate(board)
        board[r][c] = EMPTY
        if v > best:
            best, move = v, (r, c)
    return move


def random_move(board, player, rng):
    return rng.choice(nearby_moves(board, radius=1))


def play_game(p_x, p_o, starter, rng, opening=2):
    """p_x, p_o: callable(board, player) -> (r,c). Trả về ('X'|'O'|'draw', số nước, thời gian AI)."""
    board = blank()
    turn = starter
    moves = 0
    # Mở đầu ngẫu nhiên vài nước gần tâm để các ván không giống hệt nhau.
    for _ in range(opening):
        cells = [(r, c) for r in range(5, 10) for c in range(5, 10) if board[r][c] == EMPTY]
        r, c = rng.choice(cells)
        board[r][c] = turn
        turn = SECOND if turn == HUMAN else HUMAN
        moves += 1
    times = {HUMAN: [], SECOND: []}
    while True:
        player_fn = p_x if turn == HUMAN else p_o
        t0 = time.perf_counter()
        r, c = player_fn(board, turn)
        times[turn].append(time.perf_counter() - t0)
        board[r][c] = turn
        moves += 1
        if is_win(board, r, c, turn):
            return turn, moves, times
        if full(board):
            return 'draw', moves, times
        turn = SECOND if turn == HUMAN else HUMAN


def match(name, ai_fn, opp_fn, games, rng):
    """AI luôn được tính là bên 'AI'; đổi màu và người đi trước luân phiên."""
    w = d = l = 0
    lengths, ai_times = [], []
    for g in range(games):
        ai_is_o = g % 2 == 0
        starter = HUMAN if g % 4 < 2 else SECOND
        p_x, p_o = (opp_fn, ai_fn) if ai_is_o else (ai_fn, opp_fn)
        winner, n, times = play_game(p_x, p_o, starter, rng)
        ai_side = SECOND if ai_is_o else HUMAN
        ai_times += times[ai_side]
        lengths.append(n)
        if winner == 'draw':
            d += 1
        elif winner == ai_side:
            w += 1
        else:
            l += 1
        print(f'  [{name}] ván {g+1}/{games}: {"hòa" if winner == "draw" else ("AI thắng" if winner == ai_side else "AI thua")} sau {n} nước', flush=True)
    return {'name': name, 'games': games, 'win': w, 'draw': d, 'loss': l,
            'avg_moves': statistics.mean(lengths),
            'ai_avg_s': statistics.mean(ai_times), 'ai_max_s': max(ai_times)}


# ---------------------------------------------------------------- positions
def build_positions():
    """Ba thế cờ cố định: khai cuộc, trung cuộc, chiến thuật (O cần chặn/tấn công)."""
    p1 = blank()
    for r, c, v in [(7, 7, 'X'), (7, 8, 'O'), (8, 8, 'X'), (6, 6, 'O')]:
        p1[r][c] = v
    p2 = blank()
    for r, c, v in [(7, 7, 'X'), (7, 8, 'O'), (8, 8, 'X'), (6, 6, 'O'), (8, 7, 'X'), (9, 7, 'O'),
                    (8, 6, 'X'), (8, 9, 'O'), (6, 8, 'X'), (5, 9, 'O'), (9, 9, 'X'), (10, 10, 'O')]:
        p2[r][c] = v
    p3 = blank()
    for r, c, v in [(7, 5, 'X'), (7, 6, 'X'), (7, 7, 'X'), (6, 6, 'O'), (8, 8, 'O'), (5, 5, 'O'),
                    (6, 7, 'X'), (5, 8, 'O'), (8, 6, 'X'), (9, 9, 'O'), (4, 9, 'X'), (6, 9, 'O')]:
        p3[r][c] = v
    return {'P1 khai cuộc (4 quân)': p1, 'P2 trung cuộc (12 quân)': p2, 'P3 chiến thuật (12 quân)': p3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=12)
    ap.add_argument('--seed', type=int, default=2026)
    ap.add_argument('--skip-games', action='store_true')
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out: dict = {"env": {'python': platform.python_version(), 'machine': platform.machine(),
                   'system': f'{platform.system()} {platform.release()}', 'processor': platform.processor(),
                   'seed': args.seed}}

    print('== E1: Minimax thuần vs Alpha-Beta theo độ sâu ==')
    e1 = []
    for pname, pos in build_positions().items():
        for depth in (1, 2, 3, 4):
            mm = root_search(pos, depth, prune=False)
            ab = root_search(pos, depth, prune=True)
            row = {'position': pname, 'depth': depth,
                   'minimax_nodes': mm['nodes'], 'minimax_ms': round(mm['ms'], 1),
                   'ab_nodes': ab['nodes'], 'ab_ms': round(ab['ms'], 1), 'ab_cutoffs': ab['cutoffs'],
                   'same_move': mm['move'] == ab['move'], 'move': ab['move'],
                   'reduction_pct': round(100 * (1 - ab['nodes'] / mm['nodes']), 1)}
            e1.append(row)
            print(row, flush=True)
    out['e1_minimax_vs_ab'] = e1

    print('== E2: Ảnh hưởng của sắp xếp nước đi (Alpha-Beta, độ sâu 3 và 4) ==')
    e2 = []
    for pname, pos in build_positions().items():
        for depth in (3, 4):
            o = root_search(pos, depth, prune=True, ordered=True)
            shuffled = [root_search(pos, depth, prune=True, ordered=False, seed=s) for s in range(5)]
            row = {'position': pname, 'depth': depth, 'ordered_nodes': o['nodes'], 'ordered_ms': round(o['ms'], 1),
                   'shuffled_nodes_mean': round(statistics.mean(x['nodes'] for x in shuffled)),
                   'shuffled_ms_mean': round(statistics.mean(x['ms'] for x in shuffled), 1)}
            e2.append(row)
            print(row, flush=True)
    out['e2_move_ordering'] = e2

    print('== E3: Độ sâu đạt được trong 1,5 giây (ranked_ai_moves) ==')
    e3 = []
    for pname, pos in build_positions().items():
        for md in (2, 3, 4):
            t0 = time.perf_counter()
            res = ranked_ai_moves(pos, count=3, max_depth=md)
            e3.append({'position': pname, 'max_depth': md, 'ms': round((time.perf_counter() - t0) * 1000, 1),
                       'best': res[0][:2], 'score': res[0][2]})
            print(e3[-1], flush=True)
    out['e3_time_by_depth'] = e3

    if not args.skip_games:
        print('== E4: Đấu với các đối thủ ==')
        n = args.games
        ai4 = lambda b, p: ai_move(b, p, 4)
        ai2 = lambda b, p: ai_move(b, p, 2)
        rnd = lambda b, p: random_move(b, p, rng)
        out['e4_matches'] = [
            match('AI(d=4) vs Ngẫu nhiên', ai4, rnd, n, rng),
            match('AI(d=4) vs Tham lam 1 lớp', ai4, greedy_move, n, rng),
            match('AI(d=2) vs Tham lam 1 lớp', ai2, greedy_move, n, rng),
            match('AI(d=4) vs AI(d=2)', ai4, ai2, n, rng),
        ]
        for m in out['e4_matches']:
            print(m)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Đã ghi', OUT)


if __name__ == '__main__':
    main()
