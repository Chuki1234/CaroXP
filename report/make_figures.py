"""Vẽ các hình cho báo cáo từ experiments/results.json và engine thật."""
import json
import sys
from math import inf
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'experiments'))
from caro import engine  # noqa: E402
from caro.engine import EMPTY, HUMAN, SECOND, evaluate  # noqa: E402
import benchmark as B  # noqa: E402

IMG = Path(__file__).resolve().parent / 'img'
IMG.mkdir(exist_ok=True)
R = json.loads((ROOT / 'experiments' / 'results.json').read_text(encoding='utf-8'))
BLUE, ORANGE, INK, MUTED, GRID = '#2a78d6', '#eb6834', '#1f1f1e', '#6b6a64', '#e4e3df'
plt.rcParams.update({'font.family': 'Arial Unicode MS', 'font.size': 11, 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED})


def p1(m):
    return f'({m[0]+1},{m[1]+1})'


def clean(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


# ------------------------------------------------------------ Hình: số node
def fig_nodes():
    e1 = R['e1_minimax_vs_ab']
    depths = [1, 2, 3, 4]
    mm = [sum(r['minimax_nodes'] for r in e1 if r['depth'] == d) / 3 for d in depths]
    ab = [sum(r['ab_nodes'] for r in e1 if r['depth'] == d) / 3 for d in depths]
    fig, ax = plt.subplots(figsize=(7.2, 4))
    w = 0.36
    x = range(len(depths))
    b1 = ax.bar([i - w/2 - 0.01 for i in x], mm, w, color=ORANGE, label='Minimax thuần')
    b2 = ax.bar([i + w/2 + 0.01 for i in x], ab, w, color=BLUE, label='Minimax + Alpha-Beta')
    ax.set_yscale('log')
    ax.set_xticks(list(x), [f'Độ sâu {d}' for d in depths])
    ax.set_ylabel('Số node duyệt (thang log, TB 3 thế cờ)')
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height()*1.12, f'{b.get_height():,.0f}'.replace(',', '.'),
                    ha='center', fontsize=9, color=INK)
    ax.legend(frameon=False, loc='upper left')
    clean(ax)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_nodes.png', dpi=200)
    plt.close(fig)


def fig_ordering():
    e2 = [r for r in R['e2_move_ordering'] if r['depth'] == 4]
    names = [r['position'].split(' (')[0] for r in e2]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    w = 0.36
    x = range(len(e2))
    b1 = ax.bar([i - w/2 - 0.01 for i in x], [r['shuffled_nodes_mean'] for r in e2], w, color=ORANGE, label='Thứ tự ngẫu nhiên (TB 5 seed)')
    b2 = ax.bar([i + w/2 + 0.01 for i in x], [r['ordered_nodes'] for r in e2], w, color=BLUE, label='Sắp xếp theo heuristic')
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 25, f'{b.get_height():,.0f}'.replace(',', '.'), ha='center', fontsize=9)
    ax.set_xticks(list(x), names)
    ax.set_ylabel('Số node (Alpha-Beta, độ sâu 4)')
    ax.legend(frameon=False)
    clean(ax)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_ordering.png', dpi=200)
    plt.close(fig)


# ------------------------------------------------------------ Hình: cây trò chơi
def trace_tree():
    """Cây độ sâu 2 thật trên thế P3: gốc MAX (O) 3 nước, mỗi nút MIN (X) 3 nước, lá = evaluate."""
    board = [r[:] for r in B.build_positions()['P3 chiến thuật (12 quân)']]
    root = {'kind': 'MAX', 'children': []}
    alpha = -inf
    for (r, c) in engine._ordered(board, SECOND, 3)[:3]:
        board[r][c] = SECOND
        node = {'kind': 'MIN', 'move': ('O', (r, c)), 'children': [], 'alpha_in': alpha}
        beta = inf
        replies = engine._ordered(board, HUMAN, 3)[:3]
        for i, (rr, cc) in enumerate(replies):
            board[rr][cc] = HUMAN
            v = evaluate(board)
            board[rr][cc] = EMPTY
            node['children'].append({'move': ('X', (rr, cc)), 'value': v})
            beta = min(beta, v)
            if alpha >= beta:
                node['pruned'] = [('X', m) for m in replies[i+1:]]
                break
        node['value'] = beta
        board[r][c] = EMPTY
        root['children'].append(node)
        alpha = max(alpha, beta)
    root['value'] = alpha
    return root


def fig_tree(root):
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis('off')

    def box(x, y, text, fc, ec, tc=INK, w=12, h=6):
        ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle='round,pad=0.4,rounding_size=1.2', fc=fc, ec=ec, lw=1.4))
        ax.text(x, y, text, ha='center', va='center', fontsize=9, color=tc)

    box(50, 54, f'MAX (O)\nv = {root["value"]}', '#dbe8f8', BLUE, w=14)
    xs = [17, 50, 83]
    for i, node in enumerate(root['children']):
        x = xs[i]
        ax.plot([50, x], [50.5, 39.5], color=MUTED, lw=1)
        ax.text((50 + x) / 2 + (2 if i != 1 else 2.5), 45, f'O{p1(node["move"][1])}', fontsize=8.5, color=BLUE)
        a = node['alpha_in']
        label = f'MIN (X)\nv = {node["value"]}' + ('' if a == -inf else f'\nα = {a}')
        box(x, 35, label, '#fde4d8', ORANGE, w=13, h=8 if a != -inf else 6)
        kids = node['children'] + [{'move': m, 'pruned': True} for m in node.get('pruned', [])]
        n = len(kids)
        for j, k in enumerate(kids):
            cx = x + (j - (n - 1) / 2) * 10
            pruned = k.get('pruned')
            ax.plot([x, cx], [30.5 if a == -inf else 29.5, 17.5], color='#c9c8c2' if pruned else MUTED, lw=1,
                    ls='--' if pruned else '-')
            ax.text(cx, 21.5, f'X{p1(k["move"][1])}', fontsize=8, ha='center', color='#a2a19a' if pruned else INK,
                    bbox=dict(fc='white', ec='none', pad=0.5))
            if pruned:
                box(cx, 13, 'bị cắt', '#f4f3ef', '#c9c8c2', tc='#8a8982', w=8, h=5)
                ax.text(cx, 18.5, '✂', fontsize=12, ha='center', color=ORANGE)
            else:
                box(cx, 13, f'{k["value"]}', 'white', MUTED, w=8, h=5)
    ax.text(50, 3, 'Lá = evaluate(bàn cờ) sau 2 lớp. Nhánh nét đứt bị Alpha-Beta cắt vì giá trị MIN đã ≤ α (O đã có lựa chọn tốt hơn).',
            ha='center', fontsize=8.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_tree.png', dpi=200)
    plt.close(fig)


# ------------------------------------------------------------ Sơ đồ khối
def flow(path, steps, title_w=8.6, colors=None, horizontal=False, size=(9, 3)):
    fig, ax = plt.subplots(figsize=size)
    ax.axis('off')
    n = len(steps)
    if horizontal:
        ax.set_xlim(0, n * 20)
        ax.set_ylim(0, 20)
        for i, (t, fc, ec) in enumerate(steps):
            x = i * 20 + 10
            ax.add_patch(FancyBboxPatch((x - 8, 4), 16, 12, boxstyle='round,pad=0.3,rounding_size=1.5', fc=fc, ec=ec, lw=1.4))
            ax.text(x, 10, t, ha='center', va='center', fontsize=8.6, color=INK, wrap=True)
            if i < n - 1:
                ax.annotate('', xy=(x + 11.6, 10), xytext=(x + 8.4, 10), arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.4))
    fig.tight_layout()
    fig.savefig(IMG / path, dpi=200)
    plt.close(fig)


def fig_arch():
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis('off')

    def blk(x, y, w, h, title, body, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.5', fc=fc, ec=ec, lw=1.4))
        ax.text(x + w/2, y + h - 2.6, title, ha='center', va='top', fontsize=10, weight='bold', color=INK)
        ax.text(x + w/2, y + h - 7.2, body, ha='center', va='top', fontsize=8.3, color=INK, linespacing=1.4)

    blk(1, 26, 26, 22, 'Giao diện (web/)', 'index.html · style.css · app.js\nBàn 15×15, chuột + bàn phím\nGửi nước đi qua fetch JSON', '#eef4fc', BLUE)
    blk(1, 2, 26, 20, 'desktop.py', 'Cửa sổ pywebview\nMở server cổng trống 127.0.0.1\nĐóng cửa sổ → dừng server', '#f4f3ef', MUTED)
    blk(37, 14, 26, 34, 'app.py (HTTP API)', 'POST /api/game\nPOST /api/game/{id}/move\nPOST /api/game/{id}/ai\nGET  /api/game/{id}\nKhóa theo ván, kiểm tra\nlượt + revision (409)\nTối đa 128 ván trong RAM', '#eef4fc', BLUE)
    blk(73, 26, 26, 22, 'caro/engine.py', 'Luật đúng 5 quân\nevaluate() theo cửa sổ 5\nMinimax + Alpha-Beta\nIterative deepening ≤ 4, 1,5 s', '#fdeee6', ORANGE)
    blk(73, 2, 26, 20, 'caro/llm.py (tùy chọn)', 'Claude / OpenAI-compatible\nChỉ chọn trong các nước\ncùng điểm tốt nhất\nLỗi → dùng Minimax', '#f4f3ef', MUTED)
    arrow = dict(arrowstyle='<->', color=MUTED, lw=1.4)
    ax.annotate('', xy=(37, 37), xytext=(27, 37), arrowprops=arrow)
    ax.text(32, 38.5, 'JSON', ha='center', fontsize=8, color=MUTED)
    ax.annotate('', xy=(73, 37), xytext=(63, 37), arrowprops=arrow)
    ax.annotate('', xy=(73, 12), xytext=(63, 20), arrowprops=arrow)
    ax.annotate('', xy=(14, 26), xytext=(14, 22), arrowprops=dict(arrowstyle='->', color=MUTED, lw=1.4))
    fig.tight_layout()
    fig.savefig(IMG / 'fig_arch.png', dpi=200)
    plt.close(fig)


def fig_ai_flow():
    steps = [('Sinh ứng viên\nô trống bán kính 2\n(nearby_moves)', '#eef4fc', BLUE),
             ('Kiểm tra chiến thuật\nthắng ngay → chặn ngay\n(_ordered)', '#eef4fc', BLUE),
             ('Xếp hạng 16 ứng viên\nbằng evaluate()', '#eef4fc', BLUE),
             ('Iterative deepening\nđộ sâu 2→4, Alpha-Beta\nhạn 1,5 s', '#fdeee6', ORANGE),
             ('Nhiều nước cùng điểm?\nLLM chọn (tùy chọn)\nPython kiểm tra lại', '#f4f3ef', MUTED),
             ('Đặt quân\nGame.play()', '#eef4fc', BLUE)]
    flow('fig_ai_flow.png', steps, horizontal=True, size=(11, 2.4))


def fig_window():
    """Minh họa cửa sổ 5 ô trượt trên một hàng."""
    row = '..OOO.X....'
    fig, ax = plt.subplots(figsize=(8, 2.2))
    ax.set_xlim(-0.5, len(row) + 0.5)
    ax.set_ylim(-1.6, 1.6)
    ax.axis('off')
    for i, ch in enumerate(row):
        ax.add_patch(Rectangle((i, 0), 1, 1, fc='white', ec=MUTED))
        if ch != '.':
            ax.text(i + 0.5, 0.5, ch, ha='center', va='center', fontsize=15, weight='bold', color=BLUE if ch == 'O' else '#c0392b')
        ax.text(i + 0.5, 1.2, str(i + 1), ha='center', fontsize=8, color=MUTED)
    spans = [(0, 'O×3 → +550', BLUE, -0.35), (1, 'O×3 → +550', BLUE, -0.75), (2, 'chứa X → 0', '#a2a19a', -1.15)]
    for s, lab, col, y in spans:
        ax.add_patch(Rectangle((s + 0.05, y), 4.9, 0.28, fc=col, alpha=0.25, ec=col))
        ax.text(s + 5.2, y + 0.14, f'cửa sổ {s+1}–{s+5}: {lab}', va='center', fontsize=8.5, color=INK)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_window.png', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    fig_nodes()
    fig_ordering()
    tree = trace_tree()
    (IMG / 'tree.json').write_text(json.dumps(tree, ensure_ascii=False, default=str, indent=1), encoding='utf-8')
    fig_tree(tree)
    fig_arch()
    fig_ai_flow()
    fig_window()
    print(json.dumps(tree, ensure_ascii=False, default=str))


def fig_matches():
    """Kết quả đấu tự động: thanh ngang chồng Thắng/Thua (không có hòa)."""
    e4 = R['e4_matches']
    names = [m['name'] for m in e4][::-1]
    wins = [m['win'] for m in e4][::-1]
    losses = [m['loss'] for m in e4][::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = range(len(names))
    ax.barh(list(y), wins, color=BLUE, label='AI thắng', height=0.55)
    ax.barh(list(y), losses, left=[w + 0.08 for w in wins], color=ORANGE, label='AI thua', height=0.55)
    for i, (w, l) in enumerate(zip(wins, losses)):
        ax.text(w / 2, i, f'{w}', ha='center', va='center', color='white', fontsize=11)
        ax.text(w + l + 0.35, i, f'{w}/{w + l}', va='center', fontsize=10, color=INK)
    ax.set_yticks(list(y), names)
    ax.set_xlim(0, 14)
    ax.set_xlabel('Số ván (12 ván mỗi cặp, không có ván hòa)')
    ax.legend(frameon=False, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_matches.png', dpi=200)
    plt.close(fig)


def fig_nodes_d4():
    e1 = [r for r in R['e1_minimax_vs_ab'] if r['depth'] == 4]
    names = [r['position'].split(' ')[0] for r in e1]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    w = 0.36
    x = range(len(e1))
    b1 = ax.bar([i - w/2 - 0.01 for i in x], [r['minimax_nodes'] for r in e1], w, color=ORANGE, label='Minimax thuần')
    b2 = ax.bar([i + w/2 + 0.01 for i in x], [r['ab_nodes'] for r in e1], w, color=BLUE, label='Minimax + Alpha-Beta')
    for bars, key in ((b1, 'minimax_ms'), (b2, 'ab_ms')):
        for b, r in zip(bars, e1):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 200,
                    f'{b.get_height():,.0f}'.replace(',', '.') + f'\n{r[key]:.0f} ms', ha='center', fontsize=8.5)
    ax.set_xticks(list(x), [f'{n} (giảm {r["reduction_pct"]}%)'.replace('.', ',') for n, r in zip(names, e1)])
    ax.set_ylabel('Số node ở độ sâu 4')
    ax.set_ylim(0, 17500)
    ax.legend(frameon=False)
    clean(ax)
    fig.tight_layout()
    fig.savefig(IMG / 'fig_nodes_d4.png', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    fig_matches()
    fig_nodes_d4()
