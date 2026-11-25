"""Build the English DOCX report (Group03_CaroMinimax_Report.docx).

Numbers are read from experiments/results.json and report/img/tree.json so the
report, slides and program always agree. Figures come from report/img/en.
"""
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IMG = HERE / 'img'
R = json.loads((ROOT / 'experiments' / 'results.json').read_text(encoding='utf-8'))
TTT = json.loads((ROOT / 'experiments' / 'tictactoe.json').read_text(encoding='utf-8'))
TREE = json.loads((IMG / 'tree.json').read_text(encoding='utf-8'))
OUT = HERE / 'Group03_CaroMinimax_Report.docx'
IMG_EN = IMG / 'en'

NAVY = RGBColor(0x1F, 0x4E, 0x79)
FONT = 'Times New Roman'

doc = Document()
fig_no = [0]
tab_no = [0]
FIGS, TABS = [], []


# ------------------------------------------------------------------ styles
def setup():
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    # Same page setup as the Hoa Sen report template: A4, top/bottom 2 cm, left 3 cm, right 2 cm.
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.0)
    sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(2.0)
    sec.header_distance = sec.footer_distance = Cm(1.27)
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(13)
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    pf = st.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
    # Template headings: Times New Roman 13 pt, bold, black, numbered "1.", "1.1.", "1.1.1.".
    for name, before in (('Heading 1', 6), ('Heading 2', 3), ('Heading 3', 3)):
        h = doc.styles[name]
        h.font.name = FONT
        h.font.size = Pt(13)
        h.font.bold = True
        h.font.italic = False
        h.font.color.rgb = RGBColor(0, 0, 0)
        h.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
        h.element.rPr.rFonts.set(qn('w:ascii'), FONT)
        h.element.rPr.rFonts.set(qn('w:hAnsi'), FONT)
        h.paragraph_format.space_before = Pt(before)
        h.paragraph_format.space_after = Pt(3)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.line_spacing = 1.5
    doc.styles['Heading 2'].paragraph_format.left_indent = Cm(0.635)
    doc.styles['Heading 3'].paragraph_format.left_indent = Cm(1.27)


def run_fmt(run, bold=False, italic=False, size=None, color=None, mono=False):
    run.bold, run.italic = bold, italic
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    if mono:
        run.font.name = 'Consolas'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
    return run


def P(text='', indent=True, align='justify', bold=False, italic=False, size=None, after=None, before=None, keep=False):
    """Paragraph; supports simple **bold** markup."""
    p = doc.add_paragraph()
    p.alignment = {'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                   'left': WD_ALIGN_PARAGRAPH.LEFT, 'right': WD_ALIGN_PARAGRAPH.RIGHT}[align]
    if indent:
        p.paragraph_format.first_line_indent = Cm(1.27)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    if before is not None:
        p.paragraph_format.space_before = Pt(before)
    if keep:
        p.paragraph_format.keep_with_next = True
    parts = text.split('**')
    for i, part in enumerate(parts):
        if part:
            run_fmt(p.add_run(part), bold=bold or i % 2 == 1, italic=italic, size=size)
    return p


def BUL(items, numbered=False):
    """Template-style list: "-" (or "1.") hanging at 0.635 cm, text at 1.27 cm."""
    for n, it in enumerate(items, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.left_indent = Cm(1.27)
        pf.first_line_indent = Cm(-0.635)
        pf.tab_stops.add_tab_stop(Cm(1.27))
        p.add_run(f'{n}.\t' if numbered else '-\t')
        parts = it.split('**')
        for i, part in enumerate(parts):
            if part:
                run_fmt(p.add_run(part), bold=i % 2 == 1)
    doc.paragraphs[-1].paragraph_format.space_after = Pt(6)


def H(level, text, new_page=False):
    h = doc.add_heading(text, level=level)
    if new_page:
        h.paragraph_format.page_break_before = True
    return h


def FM(text, toc=True):
    """Front/back-matter title: upper case, centred, bold 13 pt, on a new page (template style)."""
    h = doc.add_heading(text, level=1) if toc else doc.add_paragraph()
    if not toc:
        run_fmt(h.add_run(text), bold=True)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.paragraph_format.page_break_before = True
    h.paragraph_format.space_after = Pt(6)
    return h


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_fill)
    tcPr.append(shd)


def caption(kind, text):
    if kind == 'Figure':
        fig_no[0] += 1
        label = f'Figure {fig_no[0]} - {text}'
        FIGS.append(label)
    else:
        tab_no[0] += 1
        label = f'Table {tab_no[0]} - {text}'
        TABS.append(label)
    # Template caption: centred, italic, 9 pt, single spacing, 10 pt after.
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(10)
    if kind == 'Table':
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(10)
    run_fmt(p.add_run(label), italic=True, size=9)
    return fig_no[0] if kind == 'Figure' else tab_no[0]


def TABLE(header, rows, widths=None, title=None, size=11, align_center_cols=()):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ''
        para = c.paragraphs[0]
        para.paragraph_format.first_line_indent = Cm(0)
        para.paragraph_format.line_spacing = 1.1
        para.paragraph_format.space_after = Pt(1)
        run_fmt(para.add_run(str(h)), bold=True, size=size, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(c, '1F4E79')
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            c = cells[i]
            c.text = ''
            para = c.paragraphs[0]
            para.paragraph_format.first_line_indent = Cm(0)
            para.paragraph_format.line_spacing = 1.1
            para.paragraph_format.space_after = Pt(1)
            if i in align_center_cols:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            parts = str(v).split('**')
            for k, part in enumerate(parts):
                if part:
                    run_fmt(para.add_run(part), bold=k % 2 == 1, size=size)
            if ri % 2 == 1:
                shade(c, 'EEF4FB')
    if widths:
        t.autofit = False
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    if title:
        caption('Table', title)  # caption goes BELOW the table
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def FIG(path, text, width=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    src = IMG_EN / path if (IMG_EN / path).exists() else IMG / path
    p.add_run().add_picture(str(src), width=Cm(width))
    return caption('Figure', text)


def CODE(lines):
    t = doc.add_table(rows=1, cols=1)
    t.style = 'Table Grid'
    c = t.rows[0].cells[0]
    shade(c, 'F4F6F8')
    c.text = ''
    first = True
    for line in lines:
        para = c.paragraphs[0] if first else c.add_paragraph()
        first = False
        para.paragraph_format.first_line_indent = Cm(0)
        para.paragraph_format.line_spacing = 1.0
        para.paragraph_format.space_after = Pt(0)
        run_fmt(para.add_run(line if line else ' '), size=9.5, mono=True)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def field(paragraph, instr):
    r = paragraph.add_run()
    a = OxmlElement('w:fldChar'); a.set(qn('w:fldCharType'), 'begin')
    b = OxmlElement('w:instrText'); b.set(qn('xml:space'), 'preserve'); b.text = instr
    c = OxmlElement('w:fldChar'); c.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t'); t.text = '1'
    d = OxmlElement('w:fldChar'); d.set(qn('w:fldCharType'), 'end')
    r._r.append(a); r._r.append(b); r._r.append(c); r._r.append(t); r._r.append(d)


def p1(m):
    return f'({m[0]+1}, {m[1]+1})'


def num(x, d=0):
    return f'{x:,.{d}f}'


# ------------------------------------------------------------------ data
e1 = R['e1_minimax_vs_ab']
e2 = R['e2_move_ordering']
e3 = R['e3_time_by_depth']
e4 = R['e4_matches']


def avg(key, depth):
    rows = [r for r in e1 if r['depth'] == depth]
    return sum(r[key] for r in rows) / len(rows)


d4_red = 100 * (1 - avg('ab_nodes', 4) / avg('minimax_nodes', 4))
d4_speed = avg('minimax_ms', 4) / avg('ab_ms', 4)
ord4 = [r for r in e2 if r['depth'] == 4]
ord_red = 100 * (1 - sum(r['ordered_nodes'] for r in ord4) / sum(r['shuffled_nodes_mean'] for r in ord4))
total_games = sum(m['games'] for m in e4)



# ================================================================== COVER
def no_borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement(f'w:{side}'); e.set(qn('w:val'), 'nil'); b.append(e)
    tblPr.append(b)


def cover_page(title_size, rows, first, members=None):
    """One cover page laid out like the Hoa Sen template (outer cover and inner cover)."""
    # Header exactly as on the Hoa Sen cover: three bold lines (20 pt) and a short rule, no logo.
    for t in ('BỘ GIÁO DỤC VÀ ĐÀO TẠO', 'TRƯỜNG ĐẠI HỌC HOA SEN', 'KHOA CÔNG NGHỆ THÔNG TIN'):
        p = P(t, indent=False, align='center', bold=True, size=20)
        p.paragraph_format.line_spacing = 1.15
        if not first and t.startswith('BỘ'):
            p.paragraph_format.page_break_before = True
    p = P('_' * 18, indent=False, align='center', size=20)
    p.paragraph_format.line_spacing = 1.0
    P('', after=48)
    for t, b in (('FINAL PROJECT REPORT', True), ('TIC-TAC-TOE GAME WITH MINIMAX', True),
                 ('ADVANCED AI METHODS AND TOOLS – SEMESTER I, ACADEMIC YEAR 2026 - 2027', False)):
        P(t, indent=False, align='center', bold=b, size=title_size)
    P('', after=36)
    if members:
        # Inner cover: members only, as a table with gridlines (No. | Student ID | Full name).
        t = doc.add_table(rows=1, cols=3)
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        data = [('No.', 'Student ID', 'Full name')] + [(str(i), sid, name) for i, (sid, name) in enumerate(members, 1)]
        for ri, row in enumerate(data):
            cells = t.rows[0].cells if ri == 0 else t.add_row().cells
            for ci, txt in enumerate(row):
                c = cells[ci]
                c.text = ''
                para = c.paragraphs[0]
                para.paragraph_format.first_line_indent = Cm(0)
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 2 and ri else WD_ALIGN_PARAGRAPH.CENTER
                run_fmt(para.add_run(txt), bold=(ri == 0))
        for row in t.rows:
            for c, w in zip(row.cells, (1.6, 4.0, 8.0)):
                c.width = Cm(w)
    else:
        t = doc.add_table(rows=0, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(t)
        for a, b in rows:
            cells = t.add_row().cells
            for c, txt, bold in ((cells[0], a, True), (cells[1], ': ' + b, False)):
                c.text = ''
                para = c.paragraphs[0]
                para.paragraph_format.first_line_indent = Cm(0)
                run_fmt(para.add_run(txt), bold=bold)
            cells[0].width, cells[1].width = Cm(4.0), Cm(10.5)
    P('', after=48)
    P('Ho Chi Minh City, November 2026', indent=False, align='center', italic=True)


def cover():
    cover_page(13, [('Topic', '5 – Tic-Tac-Toe with Minimax'), ('Course', 'Advanced AI Methods and Tools'),
                    ('Class', '1027'), ('Group', '03'), ('Major', 'Information Technology'),
                    ('Lecturer', 'Phan Hồng Trung')], first=True)
    cover_page(15, None, first=False, members=[('22206393', 'Nguyễn Tấn Lộc'), ('22207197', 'Lưu Tiến Sang'),
                                               ('22207381', 'Hoàng Quốc Cường'), ('22205787', 'Mai Hữu Chí')])


# ================================================================== FRONT MATTER
def front():
    FM('ABSTRACT')
    P('This project addresses Topic 5, “Tic-Tac-Toe Game with Minimax”: a person plays against the computer, the state is '
      'the board, the transition function places X or O, and Minimax chooses the move. Because the 3×3 game tree can be '
      'searched completely in a fraction of a second, the group kept the same model and extended it to 15×15 Caro with the '
      'exact-five rule, where Minimax needs a four-ply depth limit and an evaluation function based on 5-cell windows; '
      'Alpha-Beta pruning, heuristic move ordering and iterative deepening with a 1.5-second limit are added only as '
      'optimisations that keep Minimax’s result. The product, '
      'Caro XP, consists of a Python engine and HTTP backend with a Windows XP-style desktop interface that offers '
      'player-versus-player and player-versus-computer modes. As an optimisation on three test positions, Alpha-Beta searched '
      f'{num(d4_red,1)}% fewer nodes than pure Minimax at depth 4 while always choosing the same move, and heuristic ordering '
      f'saved a further {num(ord_red,0)}%. In {total_games} automated games, the depth-4 AI won all 24 games against random and '
      'greedy opponents and 10 of 12 games against a depth-2 AI, using at most 0.84 seconds per move. On 3×3 Tic-Tac-Toe, '
      'full Minimax visits 549,946 nodes and confirms a draw under optimal play. All 38 unit tests pass.')

    FM('TABLE OF CONTENTS', toc=False)
    p = doc.add_paragraph()
    field(p, 'TOC \\o "1-3" \\h \\z \\u')

    FM('ACKNOWLEDGEMENTS')
    P('First of all, Group 03 would like to express our sincere gratitude to our lecturer, Mr. Phan Hồng Trung, who guided '
      'us throughout the course Advanced AI Methods and Tools. His lectures on adversarial search, Minimax and Alpha-Beta '
      'pruning gave us the foundation for this project, and his comments helped us shape the topic and the way we evaluated it.')
    P('We also thank the Faculty of Information Technology, Hoa Sen University, for providing the learning environment and '
      'the materials that made this work possible.')
    P('Finally, each member thanks the others for their equal effort in analysing the problem, writing the code, running the '
      'experiments and preparing this report and the slides. Although we have tried our best, the report may still contain '
      'shortcomings, and we look forward to receiving further feedback.')


def lists():
    FM('LIST OF FIGURES')
    for f in FIGS:
        P(f, indent=False)
    FM('LIST OF TABLES')
    for t in TABS:
        P(t, indent=False)
    FM('LIST OF ABBREVIATIONS')
    t = doc.add_table(rows=0, cols=2)
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for a, b in [('Abbreviation', 'Meaning'), ('AI', 'Artificial intelligence'), ('API', 'Application programming interface'),
                 ('avg', 'Average'), ('d', 'Search depth (plies)'), ('LLM', 'Large language model'),
                 ('PEAS', 'Performance, Environment, Actuators, Sensors'), ('PVE', 'Player versus environment (versus the computer)'),
                 ('PVP', 'Player versus player'), ('UI', 'User interface'), ('VCF', 'Victory by continuous fours')]:
        cells = t.add_row().cells
        for c, txt in zip(cells, (a, b)):
            c.text = ''
            para = c.paragraphs[0]
            para.paragraph_format.first_line_indent = Cm(0)
            run_fmt(para.add_run(txt), bold=(a == 'Abbreviation'))
        cells[0].width, cells[1].width = Cm(3.5), Cm(11.5)


def after_lists():
    FM('GROUP INFORMATION AND CONTRIBUTIONS')
    TABLE(['No.', 'Student ID', 'Full name', 'Role', 'Contribution'],
          [[1, '22206393', 'Nguyễn Tấn Lộc', 'Member', '100%'],
           [2, '22207197', 'Lưu Tiến Sang', 'Member', '100%'],
           [3, '22207381', 'Hoàng Quốc Cường', 'Member', '100%'],
           [4, '22205787', 'Mai Hữu Chí', 'Member', '100%']],
          widths=[1.3, 2.6, 5, 3.2, 3.2], title='Members of Group 03', align_center_cols=(0, 1, 4))
    P('All members took part in every stage of the project (problem analysis, implementation, experiments, report and slides) with equal contribution.')
    P('**Source code:** https://github.com/Chuki1234/CaroXP.git', indent=False)
    P('**Test environment:** Python 3.12.10, macOS (Darwin 27.0.0), Apple M4 Pro, 24 GB RAM.', indent=False)

    FM("LECTURER'S COMMENTS")
    for _ in range(14):
        P('.' * 120, indent=False, align='left').runs[0].font.size = Pt(11)
    p = P('Ho Chi Minh City, day …… month …… year ……', indent=False, align='right', before=12)
    for t in ('Lecturer', '(Signature)'):
        p = P(t, indent=False, align='center', bold=True)
        p.paragraph_format.left_indent = Cm(8.5)

    doc.add_section(WD_SECTION.NEW_PAGE)   # body: Arabic page numbers from 1
    FM('INTRODUCTION').paragraph_format.page_break_before = False
    P('Adversarial search is one of the central topics of the course Advanced AI Methods and Tools. To put it into practice, '
      'Group 03 chose Topic 5, “Tic-Tac-Toe Game with Minimax”: build a game in which a person plays against the computer, '
      'model the state as the board and the transition function as placing X or O, and let Minimax choose the best move.')
    P('Because the 3×3 board is solved almost instantly, the group extended the same model to 15×15 Caro, where search depth, '
      'pruning, move ordering, an evaluation function and a time limit all matter. This report presents the problem (Section 1), '
      'its formal model (Section 2), the algorithms (Section 3), the design of the Caro XP application (Section 4), the '
      'experiments (Section 5), a product demonstration (Section 6) and the conclusion (Section 7).')


# ================================================================== CHAPTER 1
def ch1():
    H(1, '1. Problem Introduction', new_page=True)
    H(2, '1.1. Background')
    P('Two-player, turn-based, perfect-information, zero-sum games are the classic setting for learning adversarial '
      'search. Tic-Tac-Toe is the introductory example: two players take turns placing X and O on a 3×3 grid, and whoever '
      'gets three in a row first wins. The Minimax algorithm assumes the opponent always plays optimally: the MAX player '
      'picks the move with the highest value, MIN picks the lowest, and values propagate from terminal states up to the root [1].')
    P('For 3×3 Tic-Tac-Toe there are only about 5,478 legal states and 255,168 distinct games, so Minimax searches the whole '
      'tree in a few milliseconds and proves that the game is a draw under correct play. The problem therefore hides the '
      'practical issues of adversarial search: the tree is too large, search must stop at a depth limit, an evaluation '
      'function is needed, and the answer must come within a time budget. The group kept the Tic-Tac-Toe model but scaled '
      'it up to 15×15 Caro (Gomoku), won by exactly five in a row. Caro is popular in Vietnam and belongs to the same '
      'm,n,k-game family as Tic-Tac-Toe: (m, n, k) = (3, 3, 3) versus (15, 15, 5).')
    TABLE(['Criterion', '3×3 Tic-Tac-Toe', '15×15 Caro XP'],
          [['Cells / win condition', '9 cells / 3 in a row', '225 cells / exactly 5 in a row'],
           ['Upper bound on states', '3⁹ = 19,683', '3²²⁵ ≈ 10¹⁰⁷'],
           ['Initial branching factor', '9', '225 (the AI limits it to 16)'],
           ['Full tree search?', 'Yes – Minimax gives the truly optimal move', 'No – needs a depth limit and heuristics'],
           ['Required techniques', 'Minimax', 'Minimax + Alpha-Beta + evaluation + move ordering + time limit']],
          widths=[4.2, 5, 6.5], title='Tic-Tac-Toe versus Caro – why the topic was extended')
    P('Table 2 shows that the modeling framework is the same (state = board, action = place a piece), but at 15×15 the '
      'state space is hundreds of orders of magnitude larger. That gap forces the group to apply the full set of techniques '
      'from the “Adversarial Search” chapter instead of only plain Minimax. To stay close to the original task, the group '
      'also implemented full Minimax for 3×3 Tic-Tac-Toe as a baseline experiment (Section 5.6) and made the 3×3 board playable '
      'in PVE mode (Section 4.4). The 3×3 part uses pure Minimax only; Alpha-Beta pruning belongs to the 15×15 extension and '
      'never changes the move that Minimax chooses.')

    H(2, '1.2. Objectives')
    BUL(['Model the game with PEAS and as an adversarial search problem: states, initial state, actions, transition '
         'function, terminal test and utility/evaluation function.',
         'Implement Minimax – full Minimax on 3×3 and depth-limited Minimax on 15×15 (with Alpha-Beta pruning only as an optimisation) – so the computer picks a good move within about 1.5 seconds per turn.',
         'Build a graphical interface where a person plays against the computer (PVE) or another person on the same machine (PVP).',
         'Measure and compare: nodes searched, move time by depth, the effect of move ordering, and win/draw/loss rates against '
         'opponents of different strength.'])

    H(2, '1.3. Scope, inputs and outputs')
    P('The scope is one 15×15 board played locally on one machine. The human always plays X and the computer plays O; the '
      'first player is drawn at random every game (the computer may start). A player wins with **exactly five in a row** '
      'horizontally, vertically or diagonally, with no rule about blocked ends; a line of six or more does not count as a '
      'win in that direction. If all 225 cells are filled without a winning line, the game is a draw.')
    BUL(['**AI input:** a 15×15 matrix of “.”, “X”, “O” and the current turn (always O when the AI is called).',
         '**AI output:** one legal (row, column) coordinate; optionally the ranked candidate list with Minimax scores.',
         '**System input:** mouse clicks or arrow keys + Enter in the interface; the output is the updated board, turn status, '
         'last move and the highlighted winning line.'])
    H(2, '1.4. Success criteria and limitations')
    TABLE(['Criterion', 'Target', 'Result (Chapter 5)'],
          [['Correct rules', 'All rule tests pass (exact five, line of six, draw, repeated move)', '38/38 tests pass'],
           ['Response time', 'Search ≤ 1.5 s per move', 'avg 0.25–0.33 s, max 0.84 s'],
           ['Pruning efficiency', 'Alpha-Beta clearly cuts nodes without changing the move', f'−{num(d4_red,1)}% at d = 4, same move in 12/12 position–depth pairs'],
           ['Playing strength', 'Beat random and greedy opponents', '24/24 games won'],
           ['Interaction', 'The player can play the AI through the interface', 'PVE/PVP, mouse + keyboard, 3 difficulty levels, 15×15 or 3×3 board in PVE']],
          widths=[3.5, 6.2, 6], title='Success criteria')
    P('Limitations: the AI is a depth-limited search (at most 4 plies) with a limited number of branches, so it is **not '
      'guaranteed to be unbeatable**. The LLM component was only tested with mocked responses, not with a real API key. The '
      'application has no online mode and no long-term game history.')


# ================================================================== CHAPTER 2
def ch2():
    H(1, '2. Problem Modeling')
    H(2, '2.1. PEAS model')
    TABLE(['Component', 'Description for the AI agent (playing O)'],
          [['Performance', 'Win the game (5 in a row before the opponent); prefer winning early and losing late '
            '(utility ± (10⁷ − plies)); always play a legal move; search time ≤ 1.5 s per move.'],
           ['Environment', '15×15 board, the opponent is the human playing X, exact-five rule, random first player.'],
           ['Actuators', 'Place one O on an empty cell via Game.play(row, col) in the /api/game/{id}/ai endpoint.'],
           ['Sensors', 'Read the whole board matrix, the current turn, the number of moves played (revision) and the last move.']],
          widths=[4.5, 11.2], title='PEAS model of the Caro-playing agent')
    H(2, '2.2. Environment classification')
    TABLE(['Property', 'Classification', 'Effect on the design'],
          [['Observability', 'Fully observable', 'The agent sees the whole board; no belief state is needed.'],
           ['Determinism', 'Deterministic', 'Each move yields exactly one next state; only the first player is random at the start.'],
           ['Episodic / sequential', 'Sequential', 'The current move affects all later moves → must look several plies ahead (Minimax).'],
           ['Static / dynamic', 'Static (turn-based)', 'The board does not change while the AI thinks, but a 1.5 s limit keeps play smooth.'],
           ['Discrete / continuous', 'Discrete', 'Finite cells and finite actions → represented by a character matrix.'],
           ['Number of agents', 'Multi-agent, competitive', 'Zero-sum: good for O is bad for X → MAX/MIN.'],
           ['Known rules?', 'Known', 'The transition model is coded directly; nothing has to be learned.']],
          widths=[3.4, 3.6, 8.7], title='Environment classification and design consequences')
    P('The three most important properties are full observability, determinism and two-player competition: they are exactly '
      'the conditions under which Minimax gives an optimal strategy in the game-theoretic sense. Sequential play over a very '
      'large space is why search must be cut off with a depth limit and an evaluation function.')

    H(2, '2.3. State representation')
    P('A state s is a triple (B, p, w), where B is a 15×15 matrix with each cell in {“.”, “X”, “O”}, p ∈ {X, O} is the player '
      'to move and w ∈ {None, X, O, draw} is the result. In the code the state is held by the Game class (caro/engine.py) with '
      'the fields board, turn, winner, moves, last_move and win_cells. During search the AI works on a copy of the board and '
      'places/removes pieces in place (make/unmake) so it never copies the matrix at each node.')
    BUL(['**Initial state:** B is empty (225 “.” cells), p is drawn at random with secrets.choice((X, O)), w = None, moves = 0.',
         '**Actions:** Actions(s) = {(r, c) | B[r][c] = “.”}, i.e. 225 − moves legal actions. During search the AI only considers '
         'empty cells within radius 2 of existing pieces (nearby_moves); on an empty board it only considers the centre (8, 8).',
         '**Terminal test:** after each move at (r, c), check the four directions through (r, c); if one direction has exactly 5 '
         'pieces of the same colour, the mover wins; otherwise, if moves = 225, it is a draw. A last move that completes a '
         'winning line counts as a win before the draw check.',
         '**Cost:** each move costs 1, but the game does not optimise path cost – it optimises utility at terminal states.'])
    P('Coordinates in this report use (row, column) numbered 1–15 as in the interface; in the code indices start at 0.', italic=True)

    H(2, '2.4. Transition function')
    P('The transition function Result(s, a) takes a state s = (B, p, None) and an action a = (r, c) with B[r][c] = “.”, and '
      'returns s′ = (B′, p′, w′) according to:')
    CODE(['Result((B, p, None), (r, c)):',
          '    B′ ← B;  B′[r][c] ← p                      # place the mover\'s piece',
          '    if ExactFive(B′, r, c, p):  w′ ← p          # exactly 5 through the new cell',
          '    else if piece count = 225:  w′ ← draw',
          '    else: w′ ← None;  p′ ← opponent of p        # switch turn',
          '    return (B′, p′, w′)'])
    P('Illegal actions (occupied cell, coordinate off the board, game already over) are rejected with a ValueError in '
      'Game.play and the API returns status 400. Table 6 shows a real sequence of transitions recorded from one game in the '
      'experiments, AI (O, d = 4) against the greedy opponent (X); the first two moves, X (8, 8) and O (6, 6), '
      'are the random opening placed by the experiment script, and the players choose every move after that. The Eval column is evaluate(B′) from O\'s point of view.')
    trace = [('S0', 'Empty board, X first', 'X → (8, 8)', 'S1: 1 piece, O to move', '—', 'No'),
             ('S1', '1 piece', 'O → (6, 6)', 'S2: 2 pieces, X to move', '0', 'No'),
             ('S2', '2 pieces', 'X → (7, 8)', 'S3: X has 2 in column 8', '−140', 'No'),
             ('S3', '3 pieces', 'O → (6, 8)', 'S4: O blocks the top of column 8', '56', 'No'),
             ('S4', '4 pieces', 'X → (10, 8)', 'S5: X extends column 8', '−496', 'No'),
             ('S5', '5 pieces', 'O → (11, 8)', 'S6: O blocks the bottom of column 8', '88', 'No'),
             ('S6', '6 pieces', 'X → (8, 7)', 'S7: X has 2 in row 8', '−152', 'No'),
             ('S7', '7 pieces', 'O → (6, 9)', 'S8: O has 3 in row 6 (6, 8, 9)', '998', 'No'),
             ('S8', '8 pieces', 'X → (8, 9)', 'S9: X has 3 in row 8', '−662', 'No'),
             ('S9', '9 pieces', 'O → (6, 7)', 'S10: O has an open four in row 6 (cols 6–9)', '34,318', 'No'),
             ('S10', '10 pieces', 'X → (8, 6)', 'S11: X has 4 in row 8 (cols 6–9)', '−136', 'No'),
             ('S11', '11 pieces', 'O → (6, 10)', 'S12: O has exactly 5 in row 6 (cols 6–10)', '9,963,894', 'Yes – O wins')]
    TABLE(['State', 'Description', 'Action', 'Next state', 'Eval', 'Terminal?'],
          [list(t) for t in trace], widths=[1.8, 2.4, 2.5, 5.2, 1.9, 2.0], size=10.5,
          title='Transitions of a real game (12 rows)', align_center_cols=(0, 4))
    P('Table 6 illustrates two points of the model. First, Eval hovers around 0 in the opening and then jumps when O gets an '
      'open four (S10, 34,318) – this score is designed to exceed any combination of threes. Second, at S11 both sides have '
      'four in a row; since it is O\'s turn, the rule “win first, block second” makes O play the fifth piece instead of '
      'blocking, and Eval jumps to WIN_SCORE (10⁷) minus X\'s points.')

    H(2, '2.5. Utility and evaluation functions')
    P('At terminal states, utility from O\'s point of view (the MAX player) is defined as:')
    CODE(['Utility(s) = +10,000,000 − ply   if O wins  (winning earlier is better)',
          '             −10,000,000 + ply   if X wins  (losing later is better)',
          '              0                  if draw'])
    P('Here ply is the number of plies from the root. Subtracting ply lets the AI tell a win in 1 move from a win in 3 moves. '
      'At non-terminal nodes that reach the depth limit, the AI uses the evaluation function evaluate(B) described in Section '
      '3.3: evaluate(B) = Σ_line [score_O(line) − score_X(line)], where line runs over every row, column and diagonal of length '
      '≥ 5 (72 lines in total).')


# ================================================================== CHAPTER 3
def ch3():
    H(1, '3. Methods and Algorithms')
    H(2, '3.1. Minimax')
    P('Minimax defines the value of a state recursively: at a MAX node (O to move) take the largest child value, at a MIN node '
      '(X to move) take the smallest, and at a terminal state take the Utility. With a depth limit d, nodes at depth d receive '
      'evaluate(B) instead of being expanded, an idea that goes back to Shannon\'s chess program [4], [1]. With branching factor b, the number of nodes is O(b^d). In Caro, even with b '
      'limited to 10, depth-4 Minimax already needs about 0.9–1.5×10⁴ nodes (Table 14), and each extra ply multiplies the node '
      'count by about 10.')
    H(2, '3.2. Speeding up Minimax: Alpha-Beta pruning')
    P('Alpha-Beta is not a separate algorithm and is not required by the topic; it is an optimisation of Minimax that the '
      'group uses only on the 15×15 board. It keeps two bounds: α is the best value MAX is guaranteed on the current path, β is the best value MIN is '
      'guaranteed. When α ≥ β at a node, the remaining children cannot affect the decision at the root, so they are skipped. '
      'The result at the root is **identical to Minimax**, only with fewer nodes. With perfect move ordering, the complexity '
      'drops from O(b^d) to O(b^(d/2)) [2] – which is why the group invested in move ordering (Section 3.4).')
    P('The pseudocode below corresponds to the _minimax function in caro/engine.py:')
    CODE(['function MINIMAX(B, depth, player, α, β, deadline, ply):',
          '    if now() ≥ deadline: raise Timeout',
          '    if depth = 0: return EVALUATE(B)',
          '    moves ← ORDERED(B, player, limit = 10 if depth > 1 else 8)',
          '    best ← −∞ if player = O (MAX), +∞ if player = X (MIN)',
          '    for (r, c) in moves:',
          '        B[r][c] ← player',
          '        if EXACT_FIVE(B, r, c, player): v ← ±(WIN_SCORE − ply)',
          '        else: v ← MINIMAX(B, depth−1, opponent, α, β, deadline, ply+1)',
          '        B[r][c] ← "."                                  # unmake',
          '        if MAX: best ← max(best, v); α ← max(α, v)',
          '        else:   best ← min(best, v); β ← min(β, v)',
          '        if α ≥ β: break                                # prune',
          '    return best'])
    H(3, '3.2.1. A game tree and its pruned branches')
    P('Figure 1 is a real game tree extracted from the engine on position P3 (described in Section 5.1): X has three in a row '
      'in row 8, columns 6–8, and it is O\'s turn. To keep the tree readable, each node keeps only the 3 best moves in the '
      'engine\'s ordering and the depth is 2 (O moves – X replies – evaluate).')
    FIG('fig_tree.png', 'Depth-2 game tree on position P3; Alpha-Beta prunes 3 of 9 leaves (leaf value = evaluate)', 16)
    ch = TREE['children']
    steps = []
    k = 1
    alpha = '−∞'
    for node in ch:
        om = p1(node['move'][1])
        for leaf in node['children']:
            steps.append([k, f'O{om} → X{p1(leaf["move"][1])}', alpha, num(leaf['value']), 'Leaf evaluated'])
            k += 1
        for pr in node.get('pruned', []):
            steps.append(['—', f'O{om} → X{p1(pr[1])}', alpha, '—', '**Pruned** (β ≤ α)'])
        alpha = num(max(TREE['value'], node['value'])) if alpha != '−∞' else num(node['value'])
    TABLE(['Step', 'Path', 'α at MIN node', 'Leaf value', 'Note'], steps,
          widths=[1.4, 5.2, 3, 2.6, 3.5], size=10.5, title='Alpha-Beta visiting order on the tree in Figure 1', align_center_cols=(0, 2, 3))
    P('The first branch, O(8, 9), blocks the right end of the three; its value is min(−2,034; −78; −72) = −2,034, so α at the '
      'root becomes −2,034. In the second branch, O(8, 5), the very first leaf X(8, 9) already gives −18,178 ≤ α: X can make '
      'four, so O will never choose this branch and the other two leaves are pruned. The third branch, O(8, 10), is also cut '
      'after two leaves. Result: only 6 of 9 leaves are evaluated and the root picks O(8, 9) – the same move the full engine '
      'picks at depth 4 in Table 14.')

    H(2, '3.3. Evaluation function based on 5-cell windows')
    P('The evaluate(B) function is designed around the exact-five rule. For every line (row, column, diagonal) of length ≥ 5, '
      'the program slides a window of length 5. A window only counts for player P if: (i) it contains no opponent piece, and '
      '(ii) the two cells just outside the window are not P\'s pieces – because extending it with the same colour would make '
      'a line of six, which cannot win through that window. The window\'s score depends on how many of P\'s pieces it holds '
      '(Table 8). Each line\'s result is cached (lru_cache with 65,536 entries) because the same character string appears at '
      'very many nodes.')
    FIG('fig_window.png', 'A 5-cell window sliding along a row: two windows score +550 for O, the window containing X is discarded', 14)
    TABLE(['Pieces in window', 'Score', 'Pattern', 'Why this weight'],
          [['0', '0', 'Empty window', 'Carries no information.'],
           ['1', '2', 'Single piece', 'Encourages playing near the centre, where there are more windows.'],
           ['2', '30', 'Two', '15× a single piece: two coordinated pieces are worth much more than scattered ones.'],
           ['3', '550', 'Three (open, ≥ 2 windows ≈ 1,100)', 'An open three forces a response; ~18× a two.'],
           ['4', '18,000', 'Four (open ≈ 36,000)', 'One move from winning; must exceed many threes so the AI never trades a four for a few threes.'],
           ['5', '10,000,000', 'Exactly 5 – win', 'Equal to WIN_SCORE, dominating every other total.']],
          widths=[3, 2.2, 4.4, 6.1], size=11, title='Pattern weights in the evaluation function', align_center_cols=(0, 1))
    P('The weights grow roughly geometrically (about 15–30× per level) so that one higher-level pattern always outweighs many '
      'lower-level ones combined. For example, an open three usually lies in two valid windows and scores about 1,100, while '
      'an open four “.OOOO.” lies in two 4-piece windows and scores about 36,000 – over 30× more, matching the fact that an '
      'open four is almost a certain win. The function returns O\'s score minus X\'s, so the same formula measures both '
      'attack and defence.')

    H(2, '3.4. Move generation and ordering')
    P('The function _ordered(B, player, limit) prepares the move list for each node in four steps:')
    BUL(['**Local filter:** keep only empty cells within radius 2 of existing pieces (nearby_moves). On a 15×15 board almost all '
         'good moves are near the action; the filter cuts the branching factor from hundreds to a few dozen.',
         '**Tactical priority:** if there is an immediate winning move, return only those moves; otherwise, if the opponent has '
         'an immediate win, return only the blocking cells. These lists are never cut by the branch limit.',
         '**Quick scoring:** for each cell, compute an attack score (placing our piece) and a defence score (assuming the '
         'opponent places there), and sort by attack + 1.1 × defence. The factor 1.1 makes the AI slightly prefer breaking the '
         'opponent\'s pattern when scores are tied.',
         '**Branch limit:** keep 16 candidates at the root, 10 at inner nodes and 8 at the last ply.'])
    P('Ordering has two effects: good moves are searched first, so Alpha-Beta prunes earlier (measured in Section 5.3), and the '
      'branch limit rarely drops the best move. In exchange, the branch limit is an approximation: a genuinely good move with a '
      'low static score can be missed.')

    H(2, '3.5. Iterative deepening, time limit and decision flow')
    P('The ranked_ai_moves function drives the whole computer turn (Figure 3). It takes 16 candidates, returns immediately if '
      'there is a winning move, then searches with increasing depth 2, 3, 4. Each round visits every root candidate; only '
      '**completed** rounds update the ranking. If the 1.5-second limit is hit mid-round, a TimeoutError is raised and the AI '
      'uses the result of the deepest finished round. If a round finds a forced win (|score| ≥ WIN_SCORE − 100), it stops '
      'early. The caller\'s board is never modified, even on timeout (covered by a dedicated test).')
    FIG('fig_ai_flow.png', 'Decision flow for one AI move', 16.5)
    P('The LLM component is an optional step after Minimax: only when two or more moves share the best score is that list sent '
      'to the LLM (Claude through the Anthropic Messages API [5], or an OpenAI-compatible API) along with a text board. Python re-checks the answer; if it is malformed, '
      'not in the list, takes more than 12 seconds or the network fails, the best Minimax move is used. The LLM therefore can '
      'never make the AI weaker than Minimax, and all algorithm analysis in this report holds without the LLM.')
    H(2, '3.6. Summary of design choices')
    TABLE(['Choice', 'Value', 'Reason'],
          [['Main algorithm', 'Minimax + Alpha-Beta', 'Deterministic, fully observable, two-player, zero-sum; Alpha-Beta keeps the same result.'],
           ['Maximum depth', '4 plies', 'Depth 4 finishes in ~0.1–0.4 s; an even depth avoids over-optimism (Section 5.4).'],
           ['Time limit', '1.5 s for the search', 'Keeps play smooth; iterative deepening always has a result ready.'],
           ['Candidate radius', '2 cells', 'Balances missing distant moves against the number of branches.'],
           ['Branches', '16 / 10 / 8', 'Caps the tree at 16×10×10×8 = 12,800 leaves at depth 4.'],
           ['Evaluation', '5-cell window, weights 2/30/550/18,000', 'Fits the exact-five rule; higher patterns dominate lower ones.']],
          widths=[3.4, 4.2, 8.1], size=11, title='Main design choices of the AI')


# ================================================================== CHAPTER 4
def ch4():
    H(1, '4. Design and Implementation')
    H(2, '4.1. System architecture')
    P('The system is split into three layers (Figure 4): the web interface only displays and sends input; the HTTP backend '
      'holds game state and validates moves; the engine contains the rules and the AI as pure Python functions with no UI '
      'dependency, so it can be tested and benchmarked on its own. The desktop window is pywebview wrapping the web page served '
      'on a random 127.0.0.1 port.')
    FIG('fig_arch.png', 'Module architecture of Caro XP', 16)
    TABLE(['Module', 'Lines', 'Main responsibility'],
          [['caro/engine.py', '258', 'Game class (state, Game.play, 15×15 or 3×3 board), exact-five check, evaluate, _ordered, _minimax, ranked_ai_moves.'],
           ['caro/tictactoe.py', '60', 'Minimax for the 3×3 board: Dễ 1 ply, Vừa 2 plies, Khó the whole game tree; ties broken at random.'],
           ['caro/llm.py', '60', 'Adapter for the Anthropic Messages API and OpenAI-compatible APIs; validates returned coordinates.'],
           ['app.py', '251', 'HTTP server (standard library), game API, per-game lock, turn and revision checks, AI/LLM coordination.'],
           ['desktop.py', '—', 'Opens the pywebview window (700×632) and manages the server lifecycle.'],
           ['web/ (HTML, CSS, JS)', '326 (JS)', 'Windows XP-style interface, PVE setup steps, 15×15 or 3×3 board, countdown, keyboard support, difficulty picker.'],
           ['tests/test_game.py', '421', '38 tests for rules, AI, the 3×3 board, the LLM adapter and the real HTTP API, including difficulty levels.'],
           ['experiments/benchmark.py', '—', 'Experiment script for Chapter 5 (nodes, time, automated matches).']],
          widths=[4.2, 1.8, 9.7], size=11, title='Main modules', align_center_cols=(1,))
    H(2, '4.2. Flow of one PVE turn')
    BUL(['The player clicks a cell (or uses arrow keys + Enter). app.js sends POST /api/game/{id}/move with {row, col, revision}.',
         'app.py takes the game\'s lock, compares revision with the current move count (mismatch → 409, so two requests cannot '
         'overwrite each other), checks it is X\'s turn and calls Game.play, which validates the move, places the piece, checks '
         'win/draw and switches turn.',
         'If the game is not over, the interface calls POST /api/game/{id}/ai. The backend calls play_ai → ranked_ai_moves → (optional LLM) → Game.play.',
         'The public state (board, turn, last move, winning line, AI note) is returned as JSON; the interface redraws the board, '
         'highlights the last move in yellow and the winning line in green.'], numbered=True)
    TABLE(['Method and path', 'Request body', 'Result'],
          [['POST /api/game', '{mode: "pvp" | "pve", level}', 'Creates a new game, draws the first player at random (201).'],
           ['POST /api/game/{id}/move', '{row, col, revision}', 'Human move; 400 if illegal, 409 if the revision is stale.'],
           ['POST /api/game/{id}/ai', '{revision, level}', 'The computer plays one move (PVE only, on O\'s turn).'],
           ['GET /api/game/{id}', '—', 'Re-syncs the game state.'],
           ['GET /api/config', '—', 'Reports whether an LLM is configured (never returns the key).']],
          widths=[5.2, 4.3, 6.2], size=11, title='Backend API')
    H(2, '4.3. Technologies')
    BUL(['**Python 3.10+** with the standard library (http.server, threading, functools.lru_cache, secrets) for the backend and '
         'AI – the browser version and the tests need no third-party packages.',
         '**pywebview 6** [6] to package the web interface as a desktop window (WebKit on macOS, WebView2 on Windows).',
         '**Plain HTML/CSS/JavaScript**, no fonts or libraries loaded from the Internet; Tahoma font in XP style.',
         '**unittest** for testing; **matplotlib** only for the report\'s charts.'])
    H(2, '4.4. Interface and adjustable parameters')
    P('The main screen lets the player choose “Play with a friend” (PVP) or “Challenge the computer” (PVE) and read the detailed '
      'rules. The game screen has a 15×15 board with row/column labels, a player panel, a turn indicator, an exact-five rule '
      'reminder and a note saying whether the AI is running Minimax offline or with an LLM. X is red, O is blue, the last move '
      'has a yellow background and the winning line a green one; every state also has text so nothing relies on colour alone.')
    TABLE(['Parameter', 'Default', 'Location', 'Effect'],
          [['max_depth', '4', 'ranked_ai_moves', 'Maximum depth; deeper is stronger but about 3–8× slower per ply.'],
           ['time_limit', '1.5 s', 'ranked_ai_moves', 'Search budget; on timeout the deepest finished round is used.'],
           ['radius', '2', 'nearby_moves', 'Range of candidate cells around existing pieces.'],
           ['Branch limits', '16 / 10 / 8', '_ordered, _minimax', 'Moves kept at the root / inner nodes / last ply.'],
           ['Defence factor', '1.1', '_ordered', 'Priority of blocking versus attacking when ordering.'],
           ['Game mode', 'PVP / PVE', 'Interface', 'Human vs human or human vs computer.'],
           ['Board size', '15×15', 'Interface (PVE setup, toolbar)', 'PVE only: 15×15 (exactly five) or 3×3 (three in a row, Minimax in caro/tictactoe.py, no LLM). Changing it starts a new game after confirmation.'],
           ['Difficulty level', 'Khó (hard)', 'Interface (game toolbar)', 'Sets max_depth and time_limit: Dễ 2 / 0.5 s, Vừa 3 / 1 s, Khó 4 / 1.5 s; can change during a game.'],
           ['LLM', 'Off', '.env file', 'Enable Claude/OpenAI-compatible to choose among tied moves.']],
          widths=[3.2, 2.4, 3.6, 6.5], size=11, title='Key system parameters')
    P('The finer algorithm parameters (radius, branch limits, defence factor) are set in the code and varied in the experiment '
      'script (for example running the AI at depth 2 and 4 in Section 5.5); in the interface the player changes the game mode, '
      'starts a new game and, in PVE, picks a difficulty level in the game toolbar: Dễ (easy, depth 2, 0.5 s), Vừa (medium, '
      'depth 3, 1 s) or Khó (hard, depth 4, 1.5 s – the default used in Chapter 5). The level can be changed during a game and '
      'applies from the AI\'s next move; the toolbar shows the depth and time of the current level.')
    P('PVE now starts with two setup steps – board size (15×15 or 3×3), then difficulty – and a confirmation dialog that '
      'summarises the opponent, board, win rule and level. A 3-2-1 countdown follows and only then reveals who moves first. On '
      'the 3×3 board the levels are plain search depths in caro/tictactoe.py: Dễ looks 1 ply ahead (it only sees its own '
      'immediate win), Vừa 2 plies (it also blocks an immediate loss but can be beaten with a fork) and Khó searches the whole '
      'game tree with the same utility as Section 5.6 (+10 − ply, −10 + ply, 0), so it never loses; the LLM is not used there. '
      'Starting a new game or changing the board mid-game asks for confirmation, and the interface waits about 1.1–1.6 s '
      'before showing each AI move so the player can follow it; this delay is not part of the search time measured in Chapter 5.')
    H(2, '4.5. Reliability and safety')
    BUL(['Each game has its own lock; requests with a stale revision are rejected (409), so a quick double click never places two pieces.',
         'The server only listens on 127.0.0.1, rejects foreign Origins and any Content-Type other than application/json, and limits request bodies to 16 KB.',
         'API keys are read only by the backend from .env (listed in .gitignore); they never appear in HTML/JS or API responses.',
         'At most the 128 most recent games are kept in memory to avoid unbounded growth.'])


# ================================================================== CHAPTER 5
def ch5():
    H(1, '5. Experiments and Evaluation')
    H(2, '5.1. Setup and environment')
    P('All numbers are produced by experiments/benchmark.py in the project repository [7] (seed = 2026) and stored in experiments/results.json. The script '
      'calls the engine\'s functions directly without modifying the engine. To count nodes and switch pruning off, it uses a '
      'copy of _minimax with a counter, the same move order, the same branch limits and the same evaluation function; the time '
      'limit is removed so comparisons run at exactly the requested depth. One difference from the application: the script '
      'shares α across the root moves, as standard Alpha-Beta does, while ranked_ai_moves searches every root move with a '
      'full window so that it can rank all of them. Time is measured with time.perf_counter on one '
      'machine, running sequentially.')
    TABLE(['Item', 'Value'],
          [['Hardware', 'Apple M4 Pro, 24 GB RAM'], ['Operating system', 'macOS (Darwin 27.0.0)'],
           ['Software', 'Python 3.12.10, standard library only'], ['Command', 'python3 experiments/benchmark.py --games 12'],
           ['Metrics', 'Nodes, cutoffs, time (ms), chosen move, win/draw/loss, moves per game']],
          widths=[4, 11.7], size=11, title='Experimental environment and configuration')
    P('Three test positions are fixed so results are reproducible: **P1 – opening** (4 pieces around the centre), **P2 – '
      'midgame** (12 interleaved pieces) and **P3 – tactical** (12 pieces, X has three in a row in row 8 and O must respond). '
      'In all three it is O\'s (the AI\'s) turn.')

    H(2, '5.2. Experiment 1 – Effect of pruning on Minimax (15×15 extension)')
    rows = []
    for r in e1:
        if r['depth'] >= 2:
            rows.append([r['position'].split(' ')[0], r['depth'], num(r['minimax_nodes']), num(r['ab_nodes']),
                         f"{num(r['reduction_pct'],1)}%", num(r['minimax_ms'], 1), num(r['ab_ms'], 1),
                         p1(r['move']) + (' ✓' if r['same_move'] else ' ✗')])
    TABLE(['Pos.', 'd', 'Minimax nodes', 'α-β nodes', 'Saved', 'Minimax ms', 'α-β ms', 'Move (same?)'], rows,
          widths=[1.6, 0.9, 2.3, 1.9, 1.7, 2.1, 1.7, 2.8], size=10.5,
          title='Nodes and time by depth (at d = 1 both use 16 nodes)', align_center_cols=(1, 4, 7))
    FIG('fig_nodes.png', 'Average nodes over the three positions by depth (log scale)', 14.5)
    P(f'The results show three things. (1) **Pruning does not change the decision**: in all 12 position–depth pairs Alpha-Beta '
      f'picks the same move as pure Minimax, as theory predicts. (2) **The saving grows with depth**: node reduction rises from '
      f'about 49–62% at d = 2 to 78–84% at d = 3 and {num(min(r["reduction_pct"] for r in e1 if r["depth"]==4),1)}–'
      f'{num(max(r["reduction_pct"] for r in e1 if r["depth"]==4),1)}% at d = 4. More plies mean more MIN/MAX nodes that can be '
      f'cut, and each cut high in the tree removes a whole subtree. (3) **Time drops less than nodes**: at d = 4 nodes drop about '
      f'{num(avg("minimax_nodes",4)/avg("ab_nodes",4),0)}× but time only about {num(d4_speed,1)}×, because every inner node still '
      f'calls _ordered to score all candidate cells – a cost that does not depend on pruning.')
    P('The pure Minimax node count on P1 matches the theoretical estimate: 16 + 16·10 + 16·10·10 + 16·10·10·8 = 14,576 versus '
      '14,592 measured (the 16-node difference is a counting artifact: the benchmark script counts each of the 16 root moves twice, so every node count in Table 14 includes the same extra 16). This confirms that the '
      'counter and the branch limits work as designed in Section 3.4.')

    H(2, '5.3. Experiment 2 – Effect of move ordering')
    rows = [[r['position'].split(' ')[0], r['depth'], num(r['ordered_nodes']), num(r['shuffled_nodes_mean']),
             f"{num(100*(1-r['ordered_nodes']/r['shuffled_nodes_mean']),1)}%", num(r['ordered_ms'], 1), num(r['shuffled_ms_mean'], 1)] for r in e2]
    TABLE(['Pos.', 'd', 'Nodes (ordered)', 'Nodes (random, avg of 5)', 'Saved', 'ms (ordered)', 'ms (random)'], rows,
          widths=[1.8, 0.9, 2.5, 3.4, 1.8, 2.5, 2.8], size=10.5, title='Alpha-Beta with heuristic ordering versus random ordering',
          align_center_cols=(1, 4))
    FIG('fig_ordering.png', 'Alpha-Beta nodes at depth 4: heuristic versus random ordering', 13.5)
    P(f'With the same (filtered and limited) move set and only the visiting order changed, the node count at d = 4 roughly '
      f'doubles or triples when moves are shuffled; across the three positions, ordering saves {num(ord_red,0)}% of nodes. The '
      f'tactical position P3 benefits most (about 66% fewer nodes) because the correct block there has an outstanding score: '
      f'searched first, it immediately sets α high enough to cut the remaining branches. In the opening P1, by contrast, moves '
      f'have similar scores, so order matters less. This is experimental evidence for the claim in Section 3.2 that “how strong '
      f'Alpha-Beta is depends on move ordering”.')

    H(2, '5.4. Experiment 3 – Time by maximum depth and the odd/even effect')
    rows = [[r['position'].split(' ')[0], r['max_depth'], num(r['ms'], 1), p1(r['best']), num(r['score'])] for r in e3]
    TABLE(['Pos.', 'max_depth', 'Time (ms)', 'Chosen move', 'Minimax score'], rows, widths=[2.4, 2.4, 3, 3, 3.2], size=10.5,
          title='Full ranked_ai_moves (iterative deepening) by maximum depth', align_center_cols=(1, 2, 3, 4))
    P('With the default configuration (max_depth = 4), a whole AI turn – the initial ranking plus rounds 2, 3 and 4 – takes '
      '355–432 ms, so depth 4 always finishes before the 1.5-second limit on the measured positions. Time grows about 3–8× per '
      'ply, so adding depth 5 would often exceed the limit and be cut off by iterative deepening.')
    P('Notably, scores at odd depth (3) are always positive while scores at even depths (2, 4) are zero or negative. At odd depth the '
      'last ply is O\'s move, so evaluation happens right after O creates a threat, before X can respond – an optimistic '
      'result for O. This is a form of the **horizon effect**. On P1, depth 3 even picks a different move (6, 7) than depths 2 '
      'and 4 (7, 8). The group therefore chose an even maximum depth (4) and only uses results of completed rounds.')

    H(2, '5.5. Experiment 4 – Playing strength in automated matches')
    P('Each pairing plays 12 games. The AI alternates between X and O and between moving first and second; two opening moves '
      'are placed at random in the central 5×5 area so games differ. Opponents: **Random** (picks an empty cell next to existing '
      'pieces), **Greedy 1-ply** (tries every nearby cell and picks the one with the best evaluate for itself, no look-ahead) and '
      'the AI itself at **depth 2**.')
    rows = [[m['name'].replace('Ngẫu nhiên', 'Random').replace('Tham lam 1 lớp', 'Greedy 1-ply'), m['games'], m['win'], m['draw'],
             m['loss'], f"{num(100*m['win']/m['games'],1)}%", num(m['avg_moves'], 1), num(m['ai_avg_s'], 3), num(m['ai_max_s'], 3)] for m in e4]
    TABLE(['Pairing', 'Games', 'Wins', 'Draws', 'Losses', 'Win rate', 'Moves/game', 'AI avg s/move', 'Max s/move'], rows,
          widths=[4.2, 1.1, 1.3, 1.1, 1.2, 1.9, 1.7, 1.9, 1.8], size=10, title='Automated match results (12 games per pairing)',
          align_center_cols=(1, 2, 3, 4, 5, 6, 7, 8))
    FIG('fig_matches.png', 'Wins and losses of the AI in each pairing (no draws)', 14)
    P('The depth-4 AI wins all 24 games against the two weak opponents, in only 11–13 moves per game on average: the greedy '
      'opponent evaluates statically, so it cannot see O preparing an open four two plies ahead (exactly as in the game of '
      'Table 6). The more important result is **d = 4 versus d = 2**: with the same evaluation function and the same rules, '
      'differing only in depth, the deeper AI wins 10/12 games and games are noticeably longer (27.7 moves). This shows that '
      'search depth directly improves move quality, at the cost of time per move rising from about 0.01 s to 0.33 s. The two '
      'losses at d = 4 show that the AI is not unbeatable. The group did not analyse these two games move by move; likely '
      'causes are a double threat built beyond the 4-ply horizon or the branch limit dropping the defensive move.')
    P('Note on reliability: 12 games per pairing is a small sample, so the rates should be read as trends; the greedy opponent '
      'and the AI are deterministic, so variety comes only from the two random opening moves and the side swaps.', italic=True)

    H(2, '5.6. Experiment 5 – Baseline on 3×3 Tic-Tac-Toe')
    mm, ab = TTT['minimax'], TTT['alphabeta']
    v = TTT['vs_random_200']
    P('To verify the original requirement of the topic, the group implemented Minimax for 3×3 Tic-Tac-Toe with the same model: '
      'the state is the 9-cell board, an action places X or O on an empty cell, and utility = +10 − ply if O wins, −10 + ply if '
      'X wins, 0 for a draw. Because the tree is small enough, Minimax searches all the way to terminal states, with no '
      'evaluation function or depth limit (script experiments/tictactoe.py).')
    TABLE(['Metric', 'Pure Minimax', 'Minimax + Alpha-Beta'],
          [['Root value (empty board, O first)', str(mm['value']) + ' (draw)', str(ab['value']) + ' (draw)'],
           ['Nodes searched', num(mm['nodes']), num(ab['nodes'])],
           ['Time', num(mm['ms'], 1) + ' ms', num(ab['ms'], 1) + ' ms'],
           ['Value of the 9 opening moves', 'All 0', 'All 0']],
          widths=[6.2, 4.5, 5], size=11, title='Minimax searching the full 3×3 Tic-Tac-Toe tree', align_center_cols=(1, 2))
    P(f'Pure Minimax visits {num(mm["nodes"])} nodes – the commonly cited size of the complete Tic-Tac-Toe game tree, confirming the implementation is correct. The root value is 0 and all nine opening moves have value 0, so '
      f'Tic-Tac-Toe is a draw under optimal play. Alpha-Beta gives the same value but saves '
      f'{num(100*(1-ab["nodes"]/mm["nodes"]),1)}% of nodes. In 200 games against a random opponent the optimal AI won {v["win"]}, '
      f'drew {v["draw"]} and lost {v["loss"]}; playing itself it draws. So on the 3×3 board Minimax truly “finds the optimal move” '
      f'and never loses – this is the reference point: in 15×15 Caro, the impossibility of searching the full tree is what forces '
      f'the AI to use a depth limit and an evaluation function and to give up the guarantee of never losing.')

    H(2, '5.7. Functional testing')
    TABLE(['Test group', 'Cases', 'Typical content', 'Result'],
          [['Game rules', '8', 'Exactly five in 4 directions, even blocked at both ends; a line of six does not win; five in one direction + six in another still wins; full-board draw; win on the last cell; illegal/repeated moves; random first player; hidden config.', 'Pass'],
           ['AI', '7', 'Win before block; block a four in 4 directions; block a broken four; never mistake six for a win; find a double four; no board change on timeout; empty/full board.', 'Pass'],
           ['LLM and fallback', '9', 'LLM error → Minimax; only tied moves are sent; malformed/missing/refused replies; no key sent to unknown hosts; auth errors.', 'Pass'],
           ['HTTP API', '9', 'Full game lifecycle over real HTTP; stale revision (409); AI does not move in PVP; difficulty levels set depth/time and reject unknown values; foreign Origin rejected; .env config.', 'Pass'],
           ['3×3 board', '5', 'Three in a row in every direction; full-board draw and bounds; Khó never loses against any sequence of replies; level behaviour (win, block, beaten by a fork); server allows 3×3 only in PVE and never calls the LLM.', 'Pass']],
          widths=[3.2, 1.4, 9.2, 1.9], size=10.5, title='Summary of the 38 unit tests (python3 -m unittest)', align_center_cols=(1, 3))
    H(2, '5.8. Limitations')
    BUL(['**Horizon effect:** threats that appear after the 4th ply are not seen; Experiment 3 shows the score changing sign with depth.',
         '**Branch limits are an approximation:** only 10 (or 8) moves are kept per node; a good move with a low static score can be dropped.',
         '**High cost per node:** evaluate scans 72 lines and _ordered scores every candidate cell; there is no transposition table '
         'yet, so positions reached by different move orders are recomputed.',
         '**Small experimental sample:** 48 games and 3 positions; not yet measured against strong players or dedicated Gomoku engines.',
         '**LLM not evaluated with a real API:** only tested with mocked responses.'])


# ================================================================== CHAPTER 6
def ch6():
    H(1, '6. Product Demonstration')
    P('This chapter shows the main screens in the order of a demo: choose a mode → start a game → watch the AI build a threat → end the game.')
    FIG('ui_menu.jpg', 'Mode selection screen: PVP “Play with a friend” and PVE “Challenge the computer”', 13)
    P('The first screen summarises the rules (15×15, exactly five, no blocked-end rule, random first player) and offers a '
      '“Detailed rules” section. The status bar shows “AI offline” when no LLM is configured – the AI still plays fully with Minimax. '
      'The interface text is in Vietnamese, as in the shipped application.')
    FIG('ui_open_four.jpg', 'A PVE game: the AI (O) moves first and builds an open four in column 8 after 7 moves', 13)
    P('In the game in Figure 9, the computer was drawn to move first and played the centre (8, 8). The player placed scattered '
      'X pieces; the AI kept extending column 8 and after 7 moves had four O pieces in a row from row 5 to row 8 with both ends '
      'open – a pattern the evaluation function scores at about 36,000. The yellow cell is the last move; the right panel shows '
      'the current turn and a rule reminder.')
    FIG('ui_ai_win.jpg', 'End of the game: the player blocks one end and the AI completes exactly five at the other', 13)
    P('When the player blocks the top end (4, 8), the AI plays (9, 8) to make exactly five. The winning line is highlighted in '
      'green, the status panel shows that the computer has won, and the board is locked until “New game” is chosen. This '
      'example shows visually why the weight of an open four must be very large: one block is not enough to save the game. '
      'Figure 11 shows the 3×3 board added to PVE: at Khó the AI searches the whole game tree, and in this game it wins with '
      'three O in the bottom row.')
    FIG('ui_3x3_end.jpg', 'The 3×3 board in PVE at Khó: the full-tree Minimax (O) wins with three in the bottom row', 13)
    H(2, '6.1. Live demo script')
    BUL(['Launch the app with python desktop.py (or Caro XP.command on macOS); introduce the mode selection screen.',
         'Choose PVE, pick the 15×15 board and a level (Dễ / Vừa / Khó), confirm, and watch the countdown reveal who moves first; play a few moves against the AI.',
         'Deliberately build a three/four to show the AI blocking immediately; then let the AI build an open four and finish the game.',
         'Switch to PVP to show the exact-five check (a line of six does not win).',
         'Go back to PVE, choose the 3×3 board at Khó and show that the full-tree Minimax never loses (the original Tic-Tac-Toe task).',
         'Fallback: the screenshots in this chapter and the browser version python3 app.py.'], numbered=True)


# ================================================================== CONCLUSION
def conclusion():
    H(1, '7. Conclusion and Future Work')
    H(2, '7.1. Achievement of objectives')
    P('The group modeled the game exactly as the topic requires – the state is the board, the transition function places X or '
      'O, and Minimax chooses the move – and extended it from 3×3 Tic-Tac-Toe to 15×15 Caro so that adversarial search '
      'techniques become genuinely necessary. Three main results:')
    BUL([f'**Pure Minimax solves 3×3 Tic-Tac-Toe (a draw, no losses in 200 games); as an optimisation for 15×15, Alpha-Beta cuts {num(d4_red,1)}% of nodes at depth 4** compared with pure Minimax on three positions, about '
         f'{num(d4_speed,1)}× faster and always choosing the same move; heuristic move ordering saves a further {num(ord_red,0)}% of nodes.',
         '**The AI is fast and plays well:** 0.25–0.33 s per move on average (max 0.84 s, under the 1.5 s limit); it wins 24/24 games '
         'against random and greedy opponents, and depth 4 beats depth 2 by 10/12.',
         '**A complete, rule-correct product:** a desktop interface where the player competes with the AI at three difficulty levels, a PVP mode, the exact-five '
         'rule, a playable 3×3 board and a safe optional LLM connection; 38/38 tests pass. In the original 3×3 Tic-Tac-Toe case, Minimax searches the '
         'whole tree, confirms the draw and the AI loses none of 200 games.'])
    H(2, '7.2. Limitations')
    P('The AI is not guaranteed to be unbeatable because of its depth and branch limits, and it suffers from the horizon effect; '
      'the LLM component has not been evaluated with a real API; and the '
      'number of experimental games is still small.')
    H(2, '7.3. Future work')
    BUL(['Add a transposition table with Zobrist hashing and the killer-move heuristic to reach depth 5–6 in the same time.',
         'Threat-space search (VCF) for sequences of fours and threes, to counter the horizon effect; Allis used threat-space search to solve Gomoku [3].',
         'A deeper difficulty level (depth 5–6) once the transposition table makes it fast enough, and a custom setting where players enter depth and time directly.',
         'More thorough evaluation: more games, stronger opponents, and separate measurements with the LLM enabled on a real API.',
         'Compare with Monte Carlo Tree Search on the same board and under the same time limit.'])


def references():
    FM('REFERENCES')
    refs = ['[1] S. Russell and P. Norvig, Artificial Intelligence: A Modern Approach, 4th ed. Hoboken, NJ: Pearson, 2020, ch. 5 “Adversarial Search and Games”.',
            '[2] D. E. Knuth and R. W. Moore, “An analysis of alpha-beta pruning,” Artificial Intelligence, vol. 6, no. 4, pp. 293–326, 1975.',
            '[3] L. V. Allis, “Searching for Solutions in Games and Artificial Intelligence,” Ph.D. dissertation, University of Limburg, Maastricht, 1994.',
            '[4] C. E. Shannon, “Programming a computer for playing chess,” Philosophical Magazine, vol. 41, no. 314, pp. 256–275, 1950.',
            '[5] Anthropic, “Messages API,” Claude Platform Docs. [Online]. Available: https://platform.claude.com/docs/en/api/messages/create',
            '[6] pywebview, “Installation guide.” [Online]. Available: https://pywebview.flowrl.com/guide/installation.html',
            '[7] Group 03, “Caro XP – source code,” GitHub. [Online]. Available: https://github.com/Chuki1234/CaroXP.git']
    for r in refs:
        p = P(r, indent=False, size=12)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)


def appendix():
    FM('APPENDIX')
    H(2, 'Appendix A. Installation and running')
    CODE(['# Requires Python 3.10+; in the project folder:',
          'python3 -m venv .venv',
          '.venv/bin/python -m pip install -r requirements.txt',
          '.venv/bin/python desktop.py          # desktop window',
          'python3 app.py                       # or the browser version: http://127.0.0.1:8000',
          'python3 -m unittest discover -s tests -v       # 38 tests',
          'python3 experiments/benchmark.py --games 12    # reproduce Chapter 5'])
    P('On Windows use .venv\\Scripts\\python; WebView2 Runtime is required. To enable the LLM, put ANTHROPIC_API_KEY in the .env '
      'file (optional).')
    H(2, 'Appendix B. Key code – scoring one line')
    CODE(['@lru_cache(maxsize=65536)',
          'def _line_score(text, player):',
          '    opponent = HUMAN if player == SECOND else SECOND',
          '    score = 0',
          '    for start in range(len(text) - 4):',
          '        window = text[start:start + 5]',
          '        if opponent in window: continue',
          '        # a window extended by the same colour can never be exactly five',
          '        if (start > 0 and text[start-1] == player) or \\',
          '           (start + 5 < len(text) and text[start+5] == player): continue',
          '        score += (0, 2, 30, 550, 18000, WIN_SCORE)[window.count(player)]',
          '    return score'])


# ================================================================== footer
def page_footer(sec, fmt=None, start=None, show=True):
    """Page number at the bottom right, Times New Roman 12 pt (as in the template)."""
    sectPr = sec._sectPr
    pg = sectPr.find(qn('w:pgNumType'))
    if pg is None:
        pg = OxmlElement('w:pgNumType'); sectPr.append(pg)
    if fmt:
        pg.set(qn('w:fmt'), fmt)
    if start:
        pg.set(qn('w:start'), str(start))
    sec.footer.is_linked_to_previous = False
    sec.header.is_linked_to_previous = False
    fp = sec.footer.paragraphs[0]
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fp.paragraph_format.first_line_indent = Cm(0)
    if show:
        field(fp, 'PAGE')
        for r in fp.runs:
            r.font.size = Pt(12)


def footer():
    s0, s1, s2 = doc.sections
    page_footer(s0, show=False)             # the two cover pages: no number
    page_footer(s1, fmt='upperRoman', start=1)
    page_footer(s2, fmt='decimal', start=1)


def build():
    setup()
    cover()
    doc.add_section(WD_SECTION.NEW_PAGE)   # front matter: Roman page numbers
    front()
    marker = doc.add_paragraph()
    after_lists()
    ch1(); ch2(); ch3(); ch4(); ch5(); ch6(); conclusion(); references(); appendix()
    start = len(doc.element.body) - 1
    lists()
    moved = list(doc.element.body)[start:-1] if doc.element.body[-1].tag.endswith('sectPr') else list(doc.element.body)[start:]
    for el in moved:
        marker._p.addprevious(el)
    marker._p.getparent().remove(marker._p)
    footer()
    doc.save(OUT)
    print('Saved', OUT, 'figures', fig_no[0], 'tables', tab_no[0])


if __name__ == '__main__':
    build()
