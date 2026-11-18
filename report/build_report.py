"""Sinh báo cáo DOCX (Nhom03_CaroMinimax_BaoCao.docx) theo hướng dẫn của môn học.

Số liệu đọc trực tiếp từ experiments/results.json và report/img/tree.json để
báo cáo, slide và chương trình luôn khớp nhau.
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
OUT = HERE / 'Nhom03_CaroMinimax_BaoCao.docx'

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
    sec.left_margin, sec.right_margin = Cm(3.0), Cm(2.0)
    sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.2)
    st = doc.styles['Normal']
    st.font.name = FONT
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    pf = st.paragraph_format
    pf.line_spacing = 1.4
    pf.space_after = Pt(4)
    pf.space_before = Pt(0)
    for name, size, before in (('Heading 1', 16, 12), ('Heading 2', 14, 10), ('Heading 3', 13, 8)):
        h = doc.styles[name]
        h.font.name = FONT
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.italic = False
        h.font.color.rgb = NAVY
        h.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
        h.element.rPr.rFonts.set(qn('w:ascii'), FONT)
        h.element.rPr.rFonts.set(qn('w:hAnsi'), FONT)
        h.paragraph_format.space_before = Pt(before)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.line_spacing = 1.2


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
    """Đoạn văn; hỗ trợ **đậm** đơn giản trong text."""
    p = doc.add_paragraph()
    p.alignment = {'justify': WD_ALIGN_PARAGRAPH.JUSTIFY, 'center': WD_ALIGN_PARAGRAPH.CENTER,
                   'left': WD_ALIGN_PARAGRAPH.LEFT, 'right': WD_ALIGN_PARAGRAPH.RIGHT}[align]
    if indent:
        p.paragraph_format.first_line_indent = Cm(1)
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
    for it in items:
        p = doc.add_paragraph(style='List Number' if numbered else 'List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(2)
        parts = it.split('**')
        for i, part in enumerate(parts):
            if part:
                run_fmt(p.add_run(part), bold=i % 2 == 1)


def H(level, text):
    h = doc.add_heading(text, level=level)
    if level == 1:
        h.paragraph_format.page_break_before = True
    return h


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_fill)
    tcPr.append(shd)


def caption(kind, text):
    if kind == 'Hình':
        fig_no[0] += 1
        label = f'Hình {fig_no[0]}. {text}'
        FIGS.append(label)
    else:
        tab_no[0] += 1
        label = f'Bảng {tab_no[0]}. {text}'
        TABS.append(label)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    if kind == 'Bảng':
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
    run_fmt(p.add_run(label), italic=True, size=11.5)
    return fig_no[0] if kind == 'Hình' else tab_no[0]


def TABLE(header, rows, widths=None, title=None, size=11, align_center_cols=()):
    if title:
        caption('Bảng', title)
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
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def FIG(path, text, width=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(str(IMG / path), width=Cm(width))
    return caption('Hình', text)


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
    s = f'{x:,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


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


# ================================================================== BÌA
def cover():
    for t, s, b in [('TRƯỜNG ĐẠI HỌC HOA SEN', 14, True), ('KHOA CÔNG NGHỆ THÔNG TIN', 13, True)]:
        P(t, indent=False, align='center', bold=b, size=s, after=0)
    P('─────────────', indent=False, align='center', after=36)
    P('BÁO CÁO ĐỒ ÁN CUỐI KỲ', indent=False, align='center', bold=True, size=18, after=4)
    P('Môn học: Advanced AI Methods and Tools', indent=False, align='center', size=14, after=36)
    P('ĐỀ TÀI 5', indent=False, align='center', bold=True, size=14, after=4)
    p = P('GAME TIC-TAC-TOE VỚI MINIMAX', indent=False, align='center', bold=True, size=20, after=2)
    p.runs[0].font.color.rgb = NAVY
    P('Mở rộng thành Caro 15×15 “Caro XP”: Minimax, cắt tỉa Alpha-Beta và giao diện người chơi tương tác với AI',
      indent=False, align='center', italic=True, size=14, after=48)
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows = [('Giảng viên hướng dẫn:', 'Phan Hồng Trung'), ('Lớp:', '1027'), ('Nhóm:', '03'),
            ('Thành viên:', '22206393 – Nguyễn Tấn Lộc'), ('', '22207197 – Lưu Tiến Sang'),
            ('', '22207381 – Hoàng Quốc Cường'), ('', '22205787 – Mai Hữu Chí')]
    for a, b in rows:
        cells = t.add_row().cells
        for c, txt, bold in ((cells[0], a, True), (cells[1], b, False)):
            c.text = ''
            para = c.paragraphs[0]
            para.paragraph_format.first_line_indent = Cm(0)
            para.paragraph_format.space_after = Pt(2)
            run_fmt(para.add_run(txt), bold=bold, size=13)
        cells[0].width, cells[1].width = Cm(5.5), Cm(7.5)
    P('', after=60)
    P('TP. Hồ Chí Minh, tháng 11 năm 2026', indent=False, align='center', italic=True)


# ================================================================== TIỀN ĐỀ
def front():
    H(1, 'THÔNG TIN NHÓM VÀ PHÂN CÔNG')
    TABLE(['STT', 'MSSV', 'Họ và tên', 'Vai trò', 'Tỉ lệ đóng góp'],
          [[1, '22206393', 'Nguyễn Tấn Lộc', 'Thành viên', '100%'],
           [2, '22207197', 'Lưu Tiến Sang', 'Thành viên', '100%'],
           [3, '22207381', 'Hoàng Quốc Cường', 'Thành viên', '100%'],
           [4, '22205787', 'Mai Hữu Chí', 'Thành viên', '100%']],
          widths=[1.3, 2.6, 5, 3.2, 3.2], title='Danh sách thành viên Nhóm 03', align_center_cols=(0, 1, 4))
    P('Các thành viên cùng tham gia mọi giai đoạn của đồ án (phân tích bài toán, hiện thực, thực nghiệm, viết báo cáo và slide) với mức đóng góp như nhau.')
    P('**Mã nguồn:** https://github.com/Chuki1234/CaroXP.git', indent=False)
    P('**Môi trường chạy thử:** Python 3.12.10, macOS (Darwin 27.0.0), Apple M4 Pro, RAM 24 GB.', indent=False)

    H(1, 'TÓM TẮT')
    P('Đề tài yêu cầu xây dựng trò chơi Tic-Tac-Toe giữa người và máy, mô hình hóa trạng thái là bàn cờ, '
      'hàm chuyển trạng thái là việc đặt X hoặc O và dùng Minimax để chọn nước đi tối ưu. Vì Tic-Tac-Toe 3×3 '
      'quá nhỏ (cây trò chơi có thể duyệt hết trong tích tắc), nhóm mở rộng bài toán thành Caro 15×15 – một '
      'trò chơi cùng họ m,n,k (Tic-Tac-Toe là trường hợp (3,3,3), Caro là (15,15,5)). Ở kích thước này, '
      'Minimax thuần không thể duyệt hết nên nhóm kết hợp cắt tỉa Alpha-Beta, giới hạn độ sâu, sắp xếp nước đi '
      'theo heuristic, iterative deepening có giới hạn thời gian 1,5 giây và một hàm đánh giá dựa trên cửa sổ 5 ô.')
    P(f'Sản phẩm “Caro XP” gồm backend Python (luật “đúng 5 quân”, AI, API HTTP), giao diện HTML/CSS/JavaScript '
      f'phong cách Windows XP chạy trong cửa sổ desktop pywebview, có chế độ người–người và người–máy, và một kết nối '
      f'LLM tùy chọn chỉ được chọn giữa các nước Minimax đánh giá ngang nhau. Thực nghiệm trên ba thế cờ cho thấy '
      f'Alpha-Beta giảm trung bình {num(d4_red,1)}% số node ở độ sâu 4 so với Minimax thuần mà vẫn chọn cùng nước đi, '
      f'nhanh hơn khoảng {num(d4_speed,1)} lần; sắp xếp nước đi giảm thêm {num(ord_red,0)}% số node. Trong {total_games} ván '
      f'đấu tự động, AI độ sâu 4 thắng 24/24 ván trước đối thủ ngẫu nhiên và tham lam một lớp, thắng 10/12 ván trước '
      f'chính nó ở độ sâu 2, thời gian trung bình mỗi nước dưới 0,35 giây. Đối chứng trên Tic-Tac-Toe 3×3, Minimax duyệt hết '
      f'549.946 node và xác nhận ván hòa khi hai bên chơi tối ưu; Alpha-Beta chỉ cần 20.866 node. 32 kiểm thử đơn vị đều đạt.')
    P('**Từ khóa:** Minimax, Alpha-Beta, trò chơi đối kháng, Caro/Gomoku, hàm đánh giá, iterative deepening.', indent=False)

    H(1, 'MỤC LỤC')
    p = doc.add_paragraph()
    field(p, 'TOC \\o "1-3" \\h \\z \\u')


def lists():
    H(1, 'DANH MỤC HÌNH VÀ BẢNG')
    P('**Danh mục hình**', indent=False)
    for f in FIGS:
        P(f, indent=False, after=0, size=12)
    P('**Danh mục bảng**', indent=False, before=8)
    for t in TABS:
        P(t, indent=False, after=0, size=12)
    P('**Từ viết tắt:** AI – trí tuệ nhân tạo; PEAS – Performance, Environment, Actuators, Sensors; '
      'LLM – mô hình ngôn ngữ lớn; API – giao diện lập trình ứng dụng; TB – trung bình; d – độ sâu tìm kiếm.', indent=False, before=8)


# ================================================================== CHƯƠNG 1
def ch1():
    H(1, 'CHƯƠNG 1. GIỚI THIỆU BÀI TOÁN')
    H(2, '1.1. Bối cảnh')
    P('Trò chơi đối kháng hai người, có lượt, thông tin đầy đủ và tổng bằng không là môi trường kinh điển để học '
      'tìm kiếm có đối thủ (adversarial search). Tic-Tac-Toe là ví dụ nhập môn: hai người lần lượt đặt X và O trên '
      'lưới 3×3, ai có ba quân thẳng hàng trước thì thắng. Thuật toán Minimax giả định đối thủ luôn chơi tối ưu: '
      'người chơi MAX chọn nước làm giá trị lớn nhất, MIN chọn nước làm giá trị nhỏ nhất, và giá trị được lan truyền '
      'từ các trạng thái kết thúc lên gốc [1].')
    P('Với Tic-Tac-Toe 3×3, số trạng thái hợp lệ chỉ khoảng 5.478 và số ván khác nhau là 255.168, nên Minimax '
      'duyệt hết cây trong vài mili-giây và chứng minh được kết quả hòa khi cả hai chơi đúng. Bài toán vì thế '
      'không làm lộ ra các vấn đề thực tế của tìm kiếm đối kháng: cây quá lớn, phải dừng ở độ sâu giới hạn, phải '
      'có hàm đánh giá và phải trả lời trong thời gian cho phép. Nhóm giữ nguyên mô hình của Tic-Tac-Toe nhưng tăng '
      'kích thước lên Caro (Gomoku) 15×15, thắng khi có đúng năm quân liên tiếp. Đây là trò chơi phổ biến ở Việt Nam '
      'và cùng họ m,n,k-game với Tic-Tac-Toe: (m, n, k) = (3, 3, 3) so với (15, 15, 5).')
    TABLE(['Tiêu chí', 'Tic-Tac-Toe 3×3', 'Caro XP 15×15'],
          [['Số ô / điều kiện thắng', '9 ô / 3 liên tiếp', '225 ô / đúng 5 liên tiếp'],
           ['Cận trên số trạng thái', '3⁹ = 19.683', '3²²⁵ ≈ 10¹⁰⁷'],
           ['Hệ số rẽ nhánh ban đầu', '9', '225 (AI giới hạn còn 16)'],
           ['Duyệt hết cây?', 'Có – Minimax cho nước tối ưu tuyệt đối', 'Không – cần giới hạn độ sâu và heuristic'],
           ['Kỹ thuật cần thiết', 'Minimax', 'Minimax + Alpha-Beta + evaluation + sắp xếp nước + giới hạn thời gian']],
          widths=[4.2, 5, 6.5], title='So sánh Tic-Tac-Toe và Caro – lý do mở rộng đề tài')
    P('Bảng 2 cho thấy cùng một khung mô hình hóa (trạng thái là bàn cờ, hành động là đặt quân) nhưng ở kích thước '
      '15×15, không gian trạng thái lớn hơn hàng trăm bậc độ lớn. Chính khoảng cách đó buộc nhóm phải áp dụng đầy đủ '
      'các kỹ thuật của chương “Adversarial Search” thay vì chỉ cài Minimax nguyên bản. Để vẫn bám sát đề bài, nhóm cũng cài '
      'Minimax đầy đủ cho Tic-Tac-Toe 3×3 làm thí nghiệm đối chứng (mục 5.6).')

    H(2, '1.2. Mục tiêu')
    BUL(['Mô hình hóa trò chơi theo PEAS và theo định nghĩa bài toán tìm kiếm đối kháng: trạng thái, trạng thái đầu, '
         'hành động, hàm chuyển trạng thái, kiểm tra kết thúc và hàm utility/evaluation.',
         'Hiện thực Minimax có cắt tỉa Alpha-Beta để máy chọn nước đi tốt trong giới hạn khoảng 1,5 giây mỗi lượt.',
         'Xây dựng giao diện đồ họa cho phép người chơi đánh với máy (PVE) hoặc với người khác trên cùng máy (PVP).',
         'Đo đạc và so sánh: số node duyệt, thời gian chọn nước theo độ sâu, ảnh hưởng của sắp xếp nước đi và tỉ lệ '
         'thắng/hòa/thua trước các đối thủ có độ mạnh khác nhau.'])

    H(2, '1.3. Phạm vi, đầu vào và đầu ra')
    P('Phạm vi gồm một bàn 15×15 chơi cục bộ trên một máy. Người chơi luôn cầm X, máy cầm O; bên đi trước được bốc '
      'ngẫu nhiên mỗi ván (kể cả máy). Luật thắng là **đúng 5 quân liên tiếp** theo hàng, cột hoặc đường chéo, không xét '
      'chặn hai đầu; chuỗi từ 6 quân trở lên không được tính thắng theo hướng đó. Bàn đầy 225 ô mà không có chuỗi thắng '
      'thì hòa.')
    BUL(['**Đầu vào của AI:** ma trận 15×15 các ký hiệu “.”, “X”, “O” và lượt hiện tại (luôn là O khi gọi AI).',
         '**Đầu ra của AI:** một tọa độ (hàng, cột) hợp lệ; tùy chọn kèm danh sách ứng viên đã xếp hạng và điểm Minimax.',
         '**Đầu vào của hệ thống:** cú nhấp chuột hoặc phím mũi tên + Enter trên giao diện; đầu ra là bàn cờ cập nhật, '
         'trạng thái lượt, nước vừa đánh và chuỗi thắng được tô màu.'])
    H(2, '1.4. Tiêu chí thành công và giới hạn')
    TABLE(['Tiêu chí', 'Ngưỡng đặt ra', 'Kết quả (Chương 5)'],
          [['Đúng luật', 'Mọi kiểm thử luật đạt (đúng 5, chuỗi 6, hòa, nước trùng)', '32/32 kiểm thử đạt'],
           ['Thời gian phản hồi', 'Phần tìm kiếm ≤ 1,5 s/nước', 'TB 0,25–0,33 s, tối đa 0,84 s'],
           ['Hiệu quả cắt tỉa', 'Alpha-Beta giảm rõ số node, không đổi nước đi', f'Giảm {num(d4_red,1)}% ở d = 4, cùng nước 12/12 thế–độ sâu'],
           ['Chất lượng chơi', 'Thắng đối thủ ngẫu nhiên và tham lam', '24/24 ván thắng'],
           ['Tương tác', 'Người chơi đánh được với AI qua giao diện', 'Có PVE/PVP, chuột + bàn phím']],
          widths=[3.5, 6.2, 6], title='Tiêu chí thành công')
    P('Giới hạn: AI là tìm kiếm có giới hạn độ sâu (tối đa 4 lớp) và giới hạn số nhánh, nên **không bảo đảm bất bại**. '
      'Thành phần LLM chỉ được kiểm thử bằng phản hồi giả lập, chưa đánh giá với API key thật. Ứng dụng chưa có chế độ '
      'chơi trực tuyến hay lưu lịch sử lâu dài.')


# ================================================================== CHƯƠNG 2
def ch2():
    H(1, 'CHƯƠNG 2. MÔ HÌNH HÓA BÀI TOÁN')
    H(2, '2.1. Mô hình PEAS')
    TABLE(['Thành phần', 'Mô tả cho agent AI (quân O)'],
          [['Performance (độ đo)', 'Thắng ván (5 quân liên tiếp trước đối thủ); ưu tiên thắng sớm và thua muộn '
            '(utility ± (10⁷ − số lớp)); luôn đi nước hợp lệ; thời gian tìm kiếm ≤ 1,5 s mỗi nước.'],
           ['Environment (môi trường)', 'Bàn cờ 15×15, đối thủ là người chơi X, luật đúng 5 quân, bên đi trước ngẫu nhiên.'],
           ['Actuators (cơ cấu tác động)', 'Đặt một quân O vào ô trống qua lời gọi Game.play(row, col) trong API /api/game/{id}/ai.'],
           ['Sensors (cảm biến)', 'Đọc toàn bộ ma trận bàn cờ, lượt hiện tại, số nước đã đi (revision) và nước cuối cùng.']],
          widths=[4.5, 11.2], title='Mô hình PEAS của agent chơi Caro')
    H(2, '2.2. Phân loại môi trường')
    TABLE(['Thuộc tính', 'Phân loại', 'Ảnh hưởng đến thiết kế'],
          [['Khả năng quan sát', 'Quan sát đầy đủ', 'Agent thấy hết bàn cờ, không cần trạng thái niềm tin (belief state).'],
           ['Tính xác định', 'Xác định', 'Mỗi nước đi cho đúng một trạng thái kế tiếp; chỉ bên đi trước là ngẫu nhiên lúc mở ván.'],
           ['Tính tuần tự', 'Tuần tự', 'Nước hiện tại ảnh hưởng mọi nước sau → phải nhìn trước nhiều lớp (Minimax).'],
           ['Tĩnh / động', 'Tĩnh (theo lượt)', 'Bàn không đổi khi AI suy nghĩ, nhưng vẫn đặt hạn 1,5 s để giữ trải nghiệm.'],
           ['Rời rạc / liên tục', 'Rời rạc', 'Hữu hạn ô và hữu hạn hành động → biểu diễn bằng ma trận ký tự.'],
           ['Số agent', 'Đa tác nhân, cạnh tranh', 'Tổng bằng không: điểm tốt cho O là điểm xấu cho X → MAX/MIN.'],
           ['Biết luật?', 'Đã biết', 'Mô hình chuyển trạng thái được cài trực tiếp, không cần học.']],
          widths=[3.4, 3.6, 8.7], title='Phân loại môi trường và hệ quả thiết kế')
    P('Ba thuộc tính quan trọng nhất là quan sát đầy đủ, xác định và cạnh tranh hai người: chúng là đúng điều kiện '
      'để Minimax cho chiến lược tối ưu theo nghĩa lý thuyết trò chơi. Thuộc tính tuần tự với không gian rất lớn là lý '
      'do phải cắt ngắn tìm kiếm bằng độ sâu và hàm đánh giá.')

    H(2, '2.3. Biểu diễn trạng thái')
    P('Một trạng thái s là bộ ba (B, p, w), trong đó B là ma trận 15×15 với mỗi ô thuộc {“.”, “X”, “O”}, p ∈ {X, O} là '
      'người sắp đi và w ∈ {None, X, O, draw} là kết quả. Trong mã nguồn, trạng thái được giữ trong lớp Game '
      '(caro/engine.py) với các trường board, turn, winner, moves, last_move và win_cells. Khi tìm kiếm, AI làm việc '
      'trên một bản sao của board và đặt/gỡ quân tại chỗ (make/unmake) để không phải sao chép ma trận ở mỗi node.')
    BUL(['**Trạng thái ban đầu:** B rỗng (225 ô “.”), p được bốc ngẫu nhiên bằng secrets.choice((X, O)), w = None, moves = 0.',
         '**Hành động:** Actions(s) = {(r, c) | B[r][c] = “.”}, tức 225 − moves hành động hợp lệ. Khi tìm kiếm, AI chỉ xét '
         'các ô trống trong bán kính 2 quanh quân đã đặt (hàm nearby_moves); bàn rỗng thì chỉ xét ô trung tâm (8, 8).',
         '**Kiểm tra kết thúc:** sau mỗi nước tại (r, c), kiểm tra bốn hướng đi qua (r, c); nếu một hướng có đúng 5 quân '
         'cùng màu thì người vừa đi thắng; nếu không và moves = 225 thì hòa. Nước cuối tạo chuỗi thắng được tính thắng '
         'trước khi xét hòa.',
         '**Chi phí:** mỗi nước có chi phí 1, nhưng trò chơi không tối ưu chi phí đường đi mà tối ưu utility ở trạng thái kết thúc.'])
    P('Hệ tọa độ trong báo cáo dùng (hàng, cột) đánh số 1–15 như trên giao diện; trong mã nguồn chỉ số bắt đầu từ 0.', italic=True)

    H(2, '2.4. Hàm chuyển trạng thái (Transition Function)')
    P('Hàm chuyển Result(s, a) nhận trạng thái s = (B, p, None) và hành động a = (r, c) với B[r][c] = “.”, trả về '
      's′ = (B′, p′, w′) theo quy tắc:')
    CODE(['Result((B, p, None), (r, c)):',
          '    B′ ← B;  B′[r][c] ← p                      # đặt quân của người đang đi',
          '    nếu ExactFive(B′, r, c, p):  w′ ← p          # đúng 5 quân qua ô vừa đặt',
          '    ngược lại nếu số quân = 225:  w′ ← draw',
          '    ngược lại: w′ ← None;  p′ ← đối thủ của p    # đổi lượt',
          '    trả về (B′, p′, w′)'])
    P('Hành động không hợp lệ (ô đã có quân, tọa độ ngoài bàn, ván đã kết thúc) bị từ chối bằng ngoại lệ ValueError '
      'trong Game.play và API trả mã 400. Bảng 6 trình bày một chuỗi chuyển trạng thái thật, ghi lại từ một ván AI (O, d = 4) '
      'đấu với đối thủ tham lam (X) trong thực nghiệm; cột Eval là giá trị evaluate(B′) theo góc nhìn của O.')
    trace = [('S0', 'Bàn rỗng, X đi trước', 'X → (8, 8)', 'S1: 1 quân, lượt O', '—', 'Không'),
             ('S1', '1 quân', 'O → (6, 6)', 'S2: 2 quân, lượt X', '0', 'Không'),
             ('S2', '2 quân', 'X → (7, 8)', 'S3: X có 2 quân dọc cột 8', '−140', 'Không'),
             ('S3', '3 quân', 'O → (6, 8)', 'S4: O chặn đầu trên cột 8', '56', 'Không'),
             ('S4', '4 quân', 'X → (10, 8)', 'S5: X mở rộng cột 8', '−496', 'Không'),
             ('S5', '5 quân', 'O → (11, 8)', 'S6: O chặn đầu dưới cột 8', '88', 'Không'),
             ('S6', '6 quân', 'X → (8, 7)', 'S7: X có 2 quân hàng 8', '−152', 'Không'),
             ('S7', '7 quân', 'O → (6, 9)', 'S8: O có 3 quân hàng 6 (6,8,9)', '998', 'Không'),
             ('S8', '8 quân', 'X → (8, 9)', 'S9: X có 3 quân hàng 8', '−662', 'Không'),
             ('S9', '9 quân', 'O → (6, 7)', 'S10: O có 4 quân mở hàng 6 (cột 6–9)', '34.318', 'Không'),
             ('S10', '10 quân', 'X → (8, 6)', 'S11: X có 4 quân hàng 8 (cột 6–9)', '−136', 'Không'),
             ('S11', '11 quân', 'O → (6, 10)', 'S12: O đủ đúng 5 quân hàng 6 (cột 6–10)', '9.963.894', 'Có – O thắng')]
    TABLE(['Trạng thái', 'Mô tả', 'Hành động', 'Trạng thái kế tiếp', 'Eval', 'Kết thúc?'],
          [list(t) for t in trace], widths=[1.8, 2.4, 2.5, 5.2, 1.9, 2.0], size=10.5,
          title='Bảng chuyển trạng thái của một ván thật (12 dòng)', align_center_cols=(0, 4))
    P('Bảng 6 minh họa hai điểm của mô hình. Thứ nhất, Eval dao động quanh 0 trong khai cuộc rồi tăng vọt khi O có '
      'bốn quân mở (S10, 34.318) – mức điểm này được thiết kế để vượt mọi tổ hợp thế ba. Thứ hai, ở S11 cả hai bên '
      'đều có bốn quân; vì O tới lượt, quy tắc “thắng ngay trước, chặn sau” khiến O đặt quân thứ năm thay vì chặn, và '
      'Eval nhảy lên mức WIN_SCORE (10⁷) trừ các phần điểm của X.')

    H(2, '2.5. Hàm utility và hàm đánh giá')
    P('Tại trạng thái kết thúc, utility theo góc nhìn O (người chơi MAX) được định nghĩa:')
    CODE(['Utility(s) = +10.000.000 − ply   nếu O thắng  (thắng sớm tốt hơn)',
          '             −10.000.000 + ply   nếu X thắng  (thua muộn tốt hơn)',
          '              0                  nếu hòa'])
    P('Với ply là số lớp tính từ gốc. Phần trừ ply giúp AI phân biệt giữa thắng sau 1 nước và thắng sau 3 nước. Tại '
      'các node không kết thúc nhưng đã chạm giới hạn độ sâu, AI dùng hàm đánh giá evaluate(B) mô tả chi tiết ở mục 3.3: '
      'evaluate(B) = Σ_line [score_O(line) − score_X(line)], trong đó line chạy qua tất cả hàng, cột và đường chéo có '
      'độ dài ≥ 5 (tổng cộng 72 đường).')


# ================================================================== CHƯƠNG 3
def ch3():
    H(1, 'CHƯƠNG 3. PHƯƠNG PHÁP VÀ THUẬT TOÁN')
    H(2, '3.1. Minimax')
    P('Minimax định nghĩa giá trị của một trạng thái theo đệ quy: tại node MAX (lượt O) lấy giá trị lớn nhất của các '
      'con, tại node MIN (lượt X) lấy giá trị nhỏ nhất, tại trạng thái kết thúc lấy Utility. Với độ sâu giới hạn d, node '
      'ở độ sâu d được gán evaluate(B) thay vì đi tiếp [1]. Nếu hệ số rẽ nhánh là b, số node phải duyệt là O(b^d). Ở '
      'Caro, ngay cả khi giới hạn b = 10, Minimax độ sâu 4 đã cần khoảng 1,5×10⁴ node (Bảng 14), và mỗi lớp thêm '
      'nhân số node lên khoảng 10 lần.')
    H(2, '3.2. Cắt tỉa Alpha-Beta')
    P('Alpha-Beta duy trì hai cận: α là giá trị tốt nhất MAX chắc chắn đạt được trên đường đi hiện tại, β là giá trị tốt '
      'nhất MIN chắc chắn đạt được. Khi α ≥ β tại một node, các con còn lại không thể ảnh hưởng đến quyết định ở gốc nên '
      'bị bỏ qua. Kết quả ở gốc **giống hệt Minimax**, chỉ ít node hơn. Trong trường hợp thứ tự nước đi lý tưởng, độ phức '
      'tạp giảm từ O(b^d) xuống O(b^(d/2)) [2] – đây là lý do nhóm đầu tư vào sắp xếp nước đi (mục 3.4).')
    P('Mã giả bên dưới tương ứng với hàm _minimax trong caro/engine.py:')
    CODE(['function MINIMAX(B, depth, player, α, β, deadline, ply):',
          '    if now() ≥ deadline: raise Timeout',
          '    if depth = 0: return EVALUATE(B)',
          '    moves ← ORDERED(B, player, limit = 10 nếu depth > 1, ngược lại 8)',
          '    best ← −∞ nếu player = O (MAX), +∞ nếu player = X (MIN)',
          '    for (r, c) in moves:',
          '        B[r][c] ← player',
          '        if EXACT_FIVE(B, r, c, player): v ← ±(WIN_SCORE − ply)',
          '        else: v ← MINIMAX(B, depth−1, opponent, α, β, deadline, ply+1)',
          '        B[r][c] ← "."                                  # gỡ quân (unmake)',
          '        if MAX: best ← max(best, v); α ← max(α, v)',
          '        else:   best ← min(best, v); β ← min(β, v)',
          '        if α ≥ β: break                                # cắt tỉa',
          '    return best'])
    H(3, '3.2.1. Minh họa cây trò chơi và các nhánh bị cắt')
    P('Hình 1 là một cây trò chơi thật được trích từ engine trên thế cờ P3 (mô tả ở mục 5.1): X có ba quân '
      'liên tiếp ở hàng 8, cột 6–8, đến lượt O. Để cây đủ nhỏ để đọc, mỗi node chỉ giữ 3 nước tốt nhất theo thứ tự sắp xếp '
      'của engine và độ sâu là 2 (O đi – X đáp – đánh giá).')
    FIG('fig_tree.png', 'Cây trò chơi độ sâu 2 trên thế P3, Alpha-Beta cắt 3/9 lá (giá trị lá = evaluate)', 16)
    ch = TREE['children']
    steps = []
    k = 1
    alpha = '−∞'
    for node in ch:
        om = p1(node['move'][1])
        for leaf in node['children']:
            steps.append([k, f'O{om} → X{p1(leaf["move"][1])}', alpha, num(leaf['value']), 'Đánh giá lá'])
            k += 1
        for pr in node.get('pruned', []):
            steps.append(['—', f'O{om} → X{p1(pr[1])}', alpha, '—', '**Bị cắt** (β ≤ α)'])
        alpha = num(max(TREE['value'], node['value'])) if alpha != '−∞' else num(node['value'])
    TABLE(['Bước', 'Đường đi', 'α tại node MIN', 'Giá trị lá', 'Ghi chú'], steps,
          widths=[1.4, 5.2, 3, 2.6, 3.5], size=10.5, title='Thứ tự duyệt Alpha-Beta trên cây ở Hình 1', align_center_cols=(0, 2, 3))
    P(f'Nhánh đầu tiên O(8, 9) chặn đầu phải của thế ba; giá trị của nó là min(−2.034; −78; −72) = −2.034, nên α ở gốc '
      f'trở thành −2.034. Ở nhánh thứ hai O(8, 5), ngay lá đầu tiên X(8, 9) đã cho −18.178 ≤ α: X có thể tạo bốn quân, '
      f'nên O không bao giờ chọn nhánh này và hai lá còn lại bị cắt. Nhánh thứ ba O(8, 10) cũng bị cắt sau hai lá. Kết '
      f'quả: chỉ 6/9 lá được đánh giá, gốc chọn O(8, 9) – trùng với nước đi engine đầy đủ chọn ở độ sâu 4 trong Bảng 14.')

    H(2, '3.3. Hàm đánh giá theo cửa sổ 5 ô')
    P('Hàm evaluate(B) được thiết kế theo luật “đúng 5”. Với mỗi đường (hàng, cột, chéo) dài ≥ 5, chương trình trượt một '
      'cửa sổ độ dài 5. Một cửa sổ chỉ được tính cho người chơi P nếu: (i) không chứa quân đối thủ, và (ii) hai ô ngay ngoài '
      'cửa sổ không phải quân của P – vì nếu kéo dài thêm cùng màu thì sẽ thành chuỗi 6, không thể thắng bằng cửa sổ đó. '
      'Điểm của cửa sổ phụ thuộc số quân của P bên trong (Bảng 8). Kết quả từng đường được lưu bộ nhớ đệm (lru_cache 65.536 '
      'mục) vì cùng một chuỗi ký tự xuất hiện lặp lại ở rất nhiều node.')
    FIG('fig_window.png', 'Cửa sổ 5 ô trượt trên một hàng: hai cửa sổ tính +550 cho O, cửa sổ chứa X bị loại', 14)
    TABLE(['Số quân trong cửa sổ', 'Điểm', 'Thế cờ tương ứng', 'Lý do chọn trọng số'],
          [['0', '0', 'Cửa sổ trống', 'Không mang thông tin.'],
           ['1', '2', 'Quân lẻ', 'Khuyến khích đặt gần trung tâm, nơi có nhiều cửa sổ hơn.'],
           ['2', '30', 'Thế hai', 'Gấp 15 lần thế một: hai quân phối hợp đáng giá hơn nhiều quân rời.'],
           ['3', '550', 'Thế ba (mở có ≥ 2 cửa sổ ≈ 1.100)', 'Thế ba mở buộc đối thủ phản ứng; gấp ~18 lần thế hai.'],
           ['4', '18.000', 'Thế bốn (mở ≈ 36.000)', 'Còn 1 nước là thắng; phải lớn hơn tổng nhiều thế ba để AI không đổi thế bốn lấy vài thế ba.'],
           ['5', '10.000.000', 'Đúng 5 – thắng', 'Bằng WIN_SCORE, áp đảo mọi tổng điểm khác.']],
          widths=[3, 2.2, 4.4, 6.1], size=11, title='Trọng số các mẫu thế cờ trong hàm đánh giá', align_center_cols=(0, 1))
    P('Các trọng số tăng theo cấp số gần nhân (khoảng 15–30 lần mỗi bậc) để một thế cấp cao luôn quan trọng hơn nhiều thế '
      'cấp thấp cộng lại. Ví dụ, một thế ba mở thường nằm trong hai cửa sổ hợp lệ nên được khoảng 1.100 điểm, còn bốn '
      'quân mở “.OOOO.” nằm trong hai cửa sổ 4 quân nên được khoảng 36.000 – gấp hơn 30 lần, đúng với thực tế là thế bốn '
      'mở gần như thắng chắc. Hàm đánh giá trả về hiệu điểm O trừ X, nên cùng một công thức vừa đo tấn công vừa đo phòng thủ.')

    H(2, '3.4. Sinh và sắp xếp nước đi')
    P('Hàm _ordered(B, player, limit) chuẩn bị danh sách nước cho mỗi node theo bốn bước:')
    BUL(['**Lọc cục bộ:** chỉ lấy ô trống trong bán kính 2 quanh các quân đã có (nearby_moves). Trên bàn 15×15, hầu hết nước '
         'tốt đều nằm gần chiến trường; bộ lọc giảm hệ số rẽ nhánh từ hàng trăm xuống vài chục.',
         '**Ưu tiên chiến thuật:** nếu có nước thắng ngay thì chỉ trả về các nước đó; nếu không mà đối thủ có nước thắng ngay '
         'thì chỉ trả về các ô chặn. Hai danh sách này không bao giờ bị cắt bởi giới hạn số nhánh.',
         '**Chấm điểm nhanh:** với mỗi ô, tính điểm tiềm năng tấn công (đặt quân mình) và phòng thủ (giả sử đối thủ đặt), '
         'xếp theo attack + 1,1 × defense. Hệ số 1,1 làm AI hơi ưu tiên phá thế của đối thủ khi điểm ngang nhau.',
         '**Giới hạn nhánh:** giữ 16 ứng viên ở gốc, 10 ở các node trong và 8 ở lớp cuối.'])
    P('Việc sắp xếp có hai tác dụng: nước tốt được duyệt trước nên Alpha-Beta cắt sớm hơn (đo ở mục 5.3), và giới hạn số '
      'nhánh ít khi loại bỏ nước tốt nhất. Đổi lại, giới hạn nhánh là một xấp xỉ: nước thực sự tốt nhưng điểm tĩnh thấp '
      'có thể bị bỏ qua.')

    H(2, '3.5. Iterative deepening, giới hạn thời gian và luồng quyết định')
    P('Hàm ranked_ai_moves điều phối toàn bộ lượt của máy (Hình 3). Nó lấy 16 ứng viên, trả ngay nếu có nước thắng, rồi '
      'chạy tìm kiếm với độ sâu tăng dần 2, 3, 4. Mỗi vòng duyệt tất cả ứng viên ở gốc; chỉ những vòng **hoàn thành** mới '
      'được dùng để cập nhật thứ hạng. Nếu chạm hạn 1,5 giây giữa chừng, ngoại lệ TimeoutError được ném ra và AI dùng kết quả '
      'của vòng sâu nhất đã xong. Nếu một vòng tìm thấy thắng chắc (|điểm| ≥ WIN_SCORE − 100) thì dừng sớm. Bàn cờ của '
      'người gọi không bao giờ bị thay đổi, kể cả khi hết giờ (đã có kiểm thử riêng).')
    FIG('fig_ai_flow.png', 'Luồng quyết định một nước đi của AI', 16.5)
    P('Thành phần LLM là bước tùy chọn sau Minimax: chỉ khi có từ hai nước trở lên cùng điểm tốt nhất, danh sách đó mới được '
      'gửi cho LLM (Claude hoặc API tương thích OpenAI) kèm bàn cờ dạng văn bản. Python kiểm tra lại câu trả lời; nếu sai '
      'định dạng, ngoài danh sách, quá 12 giây hoặc lỗi mạng thì dùng nước tốt nhất của Minimax. Như vậy LLM không thể làm '
      'AI yếu hơn kết quả Minimax, và mọi phân tích thuật toán trong báo cáo đều đúng khi không có LLM.')
    H(2, '3.6. Tóm tắt lựa chọn thiết kế')
    TABLE(['Lựa chọn', 'Giá trị', 'Lý do'],
          [['Thuật toán chính', 'Minimax + Alpha-Beta', 'Môi trường xác định, quan sát đầy đủ, hai người, tổng bằng không; Alpha-Beta giữ nguyên kết quả.'],
           ['Độ sâu tối đa', '4 lớp', 'Độ sâu 4 hoàn tất trong ~0,1–0,4 s; độ sâu chẵn tránh lạc quan quá mức (mục 5.4).'],
           ['Giới hạn thời gian', '1,5 s cho phần tìm kiếm', 'Giữ trải nghiệm chơi mượt; iterative deepening luôn có kết quả để dùng.'],
           ['Bán kính ứng viên', '2 ô', 'Cân bằng giữa bỏ sót nước xa và số nhánh.'],
           ['Số nhánh', '16 / 10 / 8', 'Giới hạn tổng số node ≤ 16×10×10×8 = 12.800 lá ở độ sâu 4.'],
           ['Hàm đánh giá', 'Cửa sổ 5 ô, trọng số 2/30/550/18.000', 'Phù hợp luật đúng 5; thế cao áp đảo thế thấp.']],
          widths=[3.4, 4.2, 8.1], size=11, title='Các lựa chọn thiết kế chính của AI')


# ================================================================== CHƯƠNG 4
def ch4():
    H(1, 'CHƯƠNG 4. THIẾT KẾ VÀ HIỆN THỰC')
    H(2, '4.1. Kiến trúc hệ thống')
    P('Hệ thống tách thành ba lớp (Hình 4): giao diện web chỉ hiển thị và gửi thao tác; backend HTTP giữ trạng thái ván '
      'và kiểm tra hợp lệ; engine chứa luật và AI dưới dạng hàm thuần Python, không phụ thuộc giao diện nên kiểm thử và đo '
      'đạc được độc lập. Cửa sổ desktop là pywebview bọc trang web chạy trên một cổng ngẫu nhiên của 127.0.0.1.')
    FIG('fig_arch.png', 'Kiến trúc module của Caro XP', 16)
    TABLE(['Module', 'Số dòng', 'Trách nhiệm chính'],
          [['caro/engine.py', '242', 'Lớp Game (trạng thái, Game.play), kiểm tra đúng 5, evaluate, _ordered, _minimax, ranked_ai_moves.'],
           ['caro/llm.py', '60', 'Adapter Anthropic Messages API và API tương thích OpenAI; kiểm tra tọa độ trả về.'],
           ['app.py', '223', 'Server HTTP (thư viện chuẩn), API ván đấu, khóa theo ván, kiểm tra lượt và revision, điều phối AI/LLM.'],
           ['desktop.py', '—', 'Mở cửa sổ pywebview, quản lý vòng đời server, đổi kích thước cửa sổ theo màn hình.'],
           ['web/ (HTML, CSS, JS)', '136 (JS)', 'Giao diện phong cách Windows XP, bàn 15×15, bàn phím, thông báo trạng thái.'],
           ['tests/test_game.py', '333', '32 kiểm thử luật, AI, adapter LLM và API HTTP thật.'],
           ['experiments/benchmark.py', '—', 'Script thực nghiệm của Chương 5 (số node, thời gian, đấu tự động).']],
          widths=[4.2, 1.8, 9.7], size=11, title='Các module chính', align_center_cols=(1,))
    H(2, '4.2. Luồng xử lý một lượt PVE')
    BUL(['Người chơi nhấp ô (hoặc dùng phím mũi tên + Enter). app.js gửi POST /api/game/{id}/move với {row, col, revision}.',
         'app.py lấy khóa của ván, so sánh revision với số nước hiện tại (lệch → 409, tránh hai yêu cầu đè nhau), kiểm tra '
         'đúng lượt X rồi gọi Game.play. Game.play kiểm tra hợp lệ, đặt quân, xét thắng/hòa và đổi lượt.',
         'Nếu ván chưa kết thúc, giao diện gọi POST /api/game/{id}/ai. Backend gọi play_ai → ranked_ai_moves → (tùy chọn LLM) → Game.play.',
         'Trạng thái công khai (bàn cờ, lượt, nước cuối, chuỗi thắng, ghi chú AI) được trả về dạng JSON; giao diện vẽ lại bàn, '
         'tô vàng nước vừa đánh và tô xanh chuỗi thắng.'], numbered=True)
    TABLE(['Phương thức và đường dẫn', 'Dữ liệu gửi', 'Kết quả'],
          [['POST /api/game', '{mode: "pvp" | "pve"}', 'Tạo ván mới, bốc ngẫu nhiên bên đi trước (201).'],
           ['POST /api/game/{id}/move', '{row, col, revision}', 'Nước của người; 400 nếu sai luật, 409 nếu revision cũ.'],
           ['POST /api/game/{id}/ai', '{revision}', 'Máy đi một nước (chỉ trong PVE và đúng lượt O).'],
           ['GET /api/game/{id}', '—', 'Đồng bộ lại trạng thái ván.'],
           ['GET /api/config', '—', 'Cho biết LLM đã cấu hình hay chưa (không trả key).']],
          widths=[5.2, 4.3, 6.2], size=11, title='Các API của backend')
    H(2, '4.3. Công nghệ sử dụng')
    BUL(['**Python 3.10+** với thư viện chuẩn (http.server, threading, functools.lru_cache, secrets) cho backend và AI – chạy '
         'bản trình duyệt và kiểm thử không cần thư viện ngoài.',
         '**pywebview 6** để đóng gói giao diện web thành cửa sổ desktop (macOS dùng WebKit, Windows dùng WebView2).',
         '**HTML/CSS/JavaScript thuần**, không tải font hay thư viện từ Internet; font Tahoma theo phong cách XP.',
         '**unittest** cho kiểm thử; **matplotlib** chỉ dùng để vẽ biểu đồ cho báo cáo.'])
    H(2, '4.4. Giao diện và tham số có thể thay đổi')
    P('Màn hình chính cho chọn “Chơi cùng bạn bè” (PVP) hoặc “Đấu trí với máy” (PVE) và xem luật chi tiết. Màn hình ván đấu '
      'gồm bàn 15×15 có nhãn hàng/cột, bảng người chơi, chỉ báo lượt, nhắc luật đúng 5 và dòng ghi chú cho biết AI đang dùng '
      'Minimax offline hay có LLM. X màu đỏ, O màu xanh, nước cuối nền vàng, chuỗi thắng nền xanh lá; mọi trạng thái đều có '
      'chữ đi kèm để không phụ thuộc màu.')
    TABLE(['Tham số', 'Mặc định', 'Vị trí', 'Ảnh hưởng'],
          [['max_depth', '4', 'ranked_ai_moves', 'Độ sâu tối đa; tăng thì mạnh hơn nhưng chậm hơn khoảng 3–8 lần mỗi lớp.'],
           ['time_limit', '1,5 s', 'ranked_ai_moves', 'Hạn cho phần tìm kiếm; hết hạn dùng vòng sâu nhất đã xong.'],
           ['radius', '2', 'nearby_moves', 'Phạm vi ô ứng viên quanh quân đã đặt.'],
           ['Giới hạn nhánh', '16 / 10 / 8', '_ordered, _minimax', 'Số nước giữ lại ở gốc / node trong / lớp cuối.'],
           ['Hệ số phòng thủ', '1,1', '_ordered', 'Mức ưu tiên chặn so với tấn công khi sắp xếp.'],
           ['Chế độ chơi', 'PVP / PVE', 'Giao diện', 'Người–người hoặc người–máy.'],
           ['LLM', 'Tắt', 'File .env', 'Bật Claude/OpenAI-compatible để chọn giữa các nước đồng hạng.']],
          widths=[3.2, 2.4, 3.6, 6.5], size=11, title='Các tham số quan trọng của hệ thống')
    P('Các tham số thuật toán hiện được đặt trong mã nguồn và được thay đổi trong script thực nghiệm (ví dụ chạy AI ở độ sâu '
      '2 và 4 trong mục 5.5); giao diện hiện cho phép đổi chế độ chơi và bắt đầu ván mới. Việc đưa độ sâu/thời gian lên giao '
      'diện dưới dạng “mức độ khó” là hướng phát triển ở phần Kết luận.')
    H(2, '4.5. Độ tin cậy và an toàn')
    BUL(['Mỗi ván có khóa riêng; yêu cầu mang revision cũ bị từ chối (409) nên nhấp nhanh hai lần không làm đặt hai quân.',
         'Server chỉ lắng nghe 127.0.0.1, từ chối Origin lạ và Content-Type khác application/json, giới hạn thân yêu cầu 16 KB.',
         'API key chỉ được backend đọc từ .env (đã nằm trong .gitignore); không xuất hiện trong HTML/JS hay phản hồi API.',
         'Bộ nhớ giữ tối đa 128 ván gần nhất để tránh tăng bộ nhớ vô hạn.'])


# ================================================================== CHƯƠNG 5
def ch5():
    H(1, 'CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ')
    H(2, '5.1. Kịch bản và môi trường thực nghiệm')
    P('Toàn bộ số liệu được sinh bởi script experiments/benchmark.py (seed = 2026), kết quả lưu ở experiments/results.json. '
      'Script gọi trực tiếp các hàm của engine, không sửa engine. Để đếm node và tắt riêng cắt tỉa, script dùng một bản sao '
      'của _minimax có bộ đếm, cùng thứ tự nước, cùng giới hạn nhánh và cùng hàm đánh giá; cấu hình thời gian không giới hạn '
      'để so sánh ở đúng độ sâu yêu cầu. Thời gian đo bằng time.perf_counter trên cùng một máy, chạy tuần tự.')
    TABLE(['Hạng mục', 'Giá trị'],
          [['Phần cứng', 'Apple M4 Pro, RAM 24 GB'], ['Hệ điều hành', 'macOS (Darwin 27.0.0)'],
           ['Phần mềm', 'Python 3.12.10, chỉ thư viện chuẩn'], ['Lệnh chạy', 'python3 experiments/benchmark.py --games 12'],
           ['Chỉ số', 'Số node, số lần cắt, thời gian (ms), nước được chọn, thắng/hòa/thua, số nước mỗi ván']],
          widths=[4, 11.7], size=11, title='Môi trường và cấu hình thực nghiệm')
    P('Ba thế cờ thử nghiệm được cố định để kết quả lặp lại được: **P1 – khai cuộc** (4 quân quanh trung tâm), **P2 – trung '
      'cuộc** (12 quân đan xen) và **P3 – chiến thuật** (12 quân, X có thế ba liên tiếp ở hàng 8, O phải xử lý). Trong cả ba, '
      'đến lượt O (AI).')

    H(2, '5.2. Thí nghiệm 1 – Minimax thuần so với Alpha-Beta')
    rows = []
    for r in e1:
        if r['depth'] >= 2:
            rows.append([r['position'].split(' ')[0], r['depth'], num(r['minimax_nodes']), num(r['ab_nodes']),
                         f"{num(r['reduction_pct'],1)}%", num(r['minimax_ms'], 1), num(r['ab_ms'], 1),
                         p1(r['move']) + (' ✓' if r['same_move'] else ' ✗')])
    TABLE(['Thế', 'd', 'Node Minimax', 'Node α-β', 'Giảm', 'ms Minimax', 'ms α-β', 'Nước (cùng?)'], rows,
          widths=[1.6, 0.9, 2.3, 1.9, 1.7, 2.1, 1.7, 2.8], size=10.5,
          title='Số node và thời gian theo độ sâu (d = 1 hai bên bằng nhau: 16 node)', align_center_cols=(1, 4, 7))
    FIG('fig_nodes.png', 'Số node trung bình trên ba thế cờ theo độ sâu (thang logarit)', 14.5)
    P(f'Kết quả cho thấy ba điều. (1) **Cắt tỉa không làm đổi quyết định**: ở cả 12 cặp thế–độ sâu, Alpha-Beta chọn đúng nước '
      f'như Minimax thuần, phù hợp với lý thuyết. (2) **Hiệu quả tăng theo độ sâu**: mức giảm số node từ khoảng 49–62% ở d = 2 '
      f'lên 78–84% ở d = 3 và {num(min(r["reduction_pct"] for r in e1 if r["depth"]==4),1)}–{num(max(r["reduction_pct"] for r in e1 if r["depth"]==4),1)}% ở d = 4. '
      f'Lý do là càng nhiều lớp thì càng nhiều node MIN/MAX có cơ hội bị cắt, và mỗi lần cắt ở lớp cao loại bỏ cả một cây con. '
      f'(3) **Thời gian giảm ít hơn số node**: ở d = 4, số node giảm khoảng {num(avg("minimax_nodes",4)/avg("ab_nodes",4),0)} lần nhưng '
      f'thời gian chỉ giảm khoảng {num(d4_speed,1)} lần, vì mỗi node trong vẫn phải gọi _ordered để chấm điểm mọi ô ứng viên – '
      f'chi phí này không phụ thuộc việc có cắt hay không.')
    P(f'Số node Minimax thuần ở P1 khớp với ước lượng lý thuyết: 16 + 16·10 + 16·10·10 + 16·10·10·8 = 14.576, đo được 14.592 '
      f'(chênh 16 node do các nước thắng ngay được tính thêm). Điều này xác nhận bộ đếm và giới hạn nhánh hoạt động đúng như '
      f'thiết kế ở mục 3.4.')

    H(2, '5.3. Thí nghiệm 2 – Ảnh hưởng của thứ tự duyệt')
    rows = [[r['position'].split(' ')[0], r['depth'], num(r['ordered_nodes']), num(r['shuffled_nodes_mean']),
             f"{num(100*(1-r['ordered_nodes']/r['shuffled_nodes_mean']),1)}%", num(r['ordered_ms'], 1), num(r['shuffled_ms_mean'], 1)] for r in e2]
    TABLE(['Thế', 'd', 'Node (sắp xếp)', 'Node (ngẫu nhiên, TB 5)', 'Giảm', 'ms (sắp xếp)', 'ms (ngẫu nhiên)'], rows,
          widths=[1.8, 0.9, 2.5, 3.4, 1.8, 2.5, 2.8], size=10.5, title='Alpha-Beta với thứ tự heuristic và thứ tự ngẫu nhiên',
          align_center_cols=(1, 4))
    FIG('fig_ordering.png', 'Số node Alpha-Beta ở độ sâu 4: sắp xếp theo heuristic so với ngẫu nhiên', 13.5)
    P(f'Cùng một tập nước (đã lọc và giới hạn), chỉ đổi thứ tự duyệt, số node ở d = 4 tăng gần gấp đôi đến gấp ba khi xáo '
      f'trộn ngẫu nhiên; tính chung ba thế, sắp xếp giảm {num(ord_red,0)}% số node. Thế chiến thuật P3 hưởng lợi nhiều nhất '
      f'(giảm khoảng 66%) vì ở đó nước chặn đúng có điểm vượt trội: được duyệt đầu tiên, nó lập tức đặt α đủ cao để cắt các '
      f'nhánh còn lại. Ngược lại ở khai cuộc P1, các nước có điểm gần nhau nên thứ tự ít quyết định hơn. Đây là bằng chứng '
      f'thực nghiệm cho nhận định “Alpha-Beta mạnh đến đâu phụ thuộc vào thứ tự nước đi” ở mục 3.2.')

    H(2, '5.4. Thí nghiệm 3 – Thời gian theo độ sâu tối đa và hiệu ứng chẵn lẻ')
    rows = [[r['position'].split(' ')[0], r['max_depth'], num(r['ms'], 1), p1(r['best']), num(r['score'])] for r in e3]
    TABLE(['Thế', 'max_depth', 'Thời gian (ms)', 'Nước chọn', 'Điểm Minimax'], rows, widths=[2.4, 2.4, 3, 3, 3.2], size=10.5,
          title='Hàm ranked_ai_moves đầy đủ (iterative deepening) theo độ sâu tối đa', align_center_cols=(1, 2, 3, 4))
    P('Với cấu hình mặc định (max_depth = 4), toàn bộ lượt của AI – gồm xếp hạng ban đầu và các vòng 2, 3, 4 – mất 355–432 ms, '
      'tức luôn hoàn tất độ sâu 4 trước hạn 1,5 giây trên các thế đã đo. Thời gian tăng khoảng 3–8 lần mỗi lớp, nên thêm độ '
      'sâu 5 sẽ thường vượt hạn và bị cắt bởi iterative deepening.')
    P('Đáng chú ý là điểm ở độ sâu lẻ (3) luôn dương, còn ở độ sâu chẵn (2, 4) thì âm. Ở độ sâu lẻ, lớp cuối là nước của O nên '
      'đánh giá được thực hiện ngay sau khi O vừa tạo thế, chưa tính phản ứng của X – kết quả lạc quan cho O. Đây là một '
      'dạng **hiệu ứng chân trời (horizon effect)**. Ở P1, độ sâu 3 còn chọn nước khác (6, 7) so với độ sâu 2 và 4 (7, 8). Vì '
      'vậy nhóm chọn độ sâu tối đa chẵn (4) và chỉ công bố kết quả của vòng đã hoàn tất.')

    H(2, '5.5. Thí nghiệm 4 – Chất lượng chơi qua các ván đấu tự động')
    P('Mỗi cặp đấu 12 ván. AI luân phiên cầm X/O và luân phiên bên đi trước; hai nước mở đầu được đặt ngẫu nhiên trong vùng '
      '5×5 trung tâm để các ván khác nhau. Các đối thủ: **Ngẫu nhiên** (chọn ô trống kề quân đã có), **Tham lam 1 lớp** (thử mọi '
      'ô gần và chọn ô làm evaluate tốt nhất cho mình, không nhìn trước) và chính AI ở **độ sâu 2**.')
    rows = [[m['name'], m['games'], m['win'], m['draw'], m['loss'], f"{num(100*m['win']/m['games'],1)}%",
             num(m['avg_moves'], 1), num(m['ai_avg_s'], 3), num(m['ai_max_s'], 3)] for m in e4]
    TABLE(['Cặp đấu', 'Ván', 'Thắng', 'Hòa', 'Thua', 'Tỉ lệ thắng', 'Nước/ván', 'TB s/nước AI', 'Max s/nước'], rows,
          widths=[4.2, 1.1, 1.3, 1.1, 1.2, 1.9, 1.7, 1.9, 1.8], size=10, title='Kết quả đấu tự động (12 ván mỗi cặp)',
          align_center_cols=(1, 2, 3, 4, 5, 6, 7, 8))
    P('AI độ sâu 4 thắng toàn bộ 24 ván trước hai đối thủ yếu, trung bình chỉ 11–13 nước mỗi ván: đối thủ tham lam đánh giá '
      'tĩnh nên không thấy được việc O chuẩn bị thế bốn mở hai lớp sau (đúng như ván ở Bảng 6). Kết quả quan trọng hơn là '
      'cặp **d = 4 so với d = 2**: cùng hàm đánh giá, cùng luật, chỉ khác độ sâu, AI sâu hơn thắng 10/12 ván và ván đấu dài hơn '
      'rõ rệt (27,7 nước). Điều này cho thấy độ sâu tìm kiếm trực tiếp nâng chất lượng nước đi, đổi lại thời gian mỗi nước '
      'tăng từ khoảng 0,01 s lên 0,33 s. Hai ván thua của d = 4 cho thấy AI không bất bại: khi đối thủ tạo được thế đôi ngoài '
      'tầm nhìn 4 lớp hoặc bị giới hạn nhánh loại mất nước phòng thủ, AI có thể thua.')
    P('Lưu ý về độ tin cậy: 12 ván mỗi cặp là mẫu nhỏ, nên tỉ lệ nên được hiểu là xu hướng; đối thủ tham lam và AI là tất định '
      'nên sự đa dạng chỉ đến từ hai nước mở đầu ngẫu nhiên và việc đổi bên.', italic=True)

    H(2, '5.6. Thí nghiệm 5 – Đối chứng trên Tic-Tac-Toe 3×3')
    mm, ab = TTT['minimax'], TTT['alphabeta']
    v = TTT['vs_random_200']
    P('Để kiểm chứng đúng yêu cầu gốc của đề tài, nhóm cài Minimax cho Tic-Tac-Toe 3×3 theo cùng mô hình: trạng thái là bàn '
      'cờ 9 ô, hành động là đặt X hoặc O vào ô trống, utility = +10 − ply nếu O thắng, −10 + ply nếu X thắng, 0 nếu hòa. Vì '
      'cây đủ nhỏ, Minimax duyệt hết đến trạng thái kết thúc, không cần hàm đánh giá hay giới hạn độ sâu '
      '(script experiments/tictactoe.py).')
    TABLE(['Chỉ số', 'Minimax thuần', 'Minimax + Alpha-Beta'],
          [['Giá trị gốc (bàn rỗng, O đi trước)', str(mm['value']) + ' (hòa)', str(ab['value']) + ' (hòa)'],
           ['Số node duyệt', num(mm['nodes']), num(ab['nodes'])],
           ['Thời gian', num(mm['ms'], 1) + ' ms', num(ab['ms'], 1) + ' ms'],
           ['Giá trị của 9 nước mở đầu', 'Tất cả bằng 0', 'Tất cả bằng 0']],
          widths=[6.2, 4.5, 5], size=11, title='Minimax duyệt hết cây Tic-Tac-Toe 3×3', align_center_cols=(1, 2))
    P(f'Số node của Minimax thuần là {num(mm["nodes"])} – đúng bằng tổng số node của cây Tic-Tac-Toe đầy đủ được biết trong '
      f'tài liệu, xác nhận cài đặt đúng. Giá trị gốc bằng 0 và cả chín nước mở đầu đều có giá trị 0, tức Tic-Tac-Toe là '
      f'trò chơi hòa khi hai bên chơi tối ưu. Alpha-Beta cho cùng giá trị nhưng giảm '
      f'{num(100*(1-ab["nodes"]/mm["nodes"]),1)}% số node. Khi đấu 200 ván với đối thủ ngẫu nhiên, AI tối ưu thắng {v["win"]}, '
      f'hòa {v["draw"]}, thua {v["loss"]}; tự đấu với chính nó cho kết quả hòa. Như vậy ở bàn 3×3, Minimax đúng nghĩa '
      f'“tìm nước đi tối ưu” và không bao giờ thua – đây là chuẩn để so sánh: ở Caro 15×15, chính việc không thể duyệt hết '
      f'cây buộc AI phải dùng giới hạn độ sâu, hàm đánh giá và chấp nhận không bảo đảm bất bại.')

    H(2, '5.7. Kiểm thử chức năng')
    TABLE(['Nhóm kiểm thử', 'Số ca', 'Nội dung tiêu biểu', 'Kết quả'],
          [['Luật chơi', '8', 'Đúng 5 ở 4 hướng kể cả bị chặn hai đầu; chuỗi 6 không thắng; 5 hướng này + 6 hướng kia vẫn thắng; hòa bàn đầy; thắng ở ô cuối; nước sai/trùng; bốc lượt ngẫu nhiên; ẩn cấu hình.', 'Đạt'],
           ['AI', '7', 'Thắng trước chặn; chặn bốn ở 4 hướng; chặn bốn gãy; không nhầm chuỗi 6 là thắng; tìm thế đôi bốn; không sửa bàn khi hết giờ; bàn rỗng/đầy.', 'Đạt'],
           ['LLM và fallback', '9', 'Lỗi LLM → Minimax; chỉ gửi nước đồng hạng; phản hồi sai/thiếu/bị từ chối; không gửi key tới host lạ; lỗi xác thực.', 'Đạt'],
           ['API HTTP', '8', 'Vòng đời ván qua HTTP thật; revision cũ (409); AI không đi trong PVP; từ chối Origin lạ; cấu hình .env.', 'Đạt']],
          widths=[3.2, 1.4, 9.2, 1.9], size=10.5, title='Tổng hợp 32 kiểm thử đơn vị (python3 -m unittest)', align_center_cols=(1, 3))
    H(2, '5.8. Phân tích hạn chế')
    BUL(['**Hiệu ứng chân trời:** đe dọa xuất hiện sau lớp thứ 4 không được nhìn thấy; Thí nghiệm 3 cho thấy điểm thay đổi dấu theo độ sâu.',
         '**Giới hạn nhánh là xấp xỉ:** chỉ giữ 10 (hoặc 8) nước mỗi node; nước tốt có điểm tĩnh thấp có thể bị loại.',
         '**Chi phí mỗi node cao:** evaluate quét 72 đường và _ordered chấm điểm mọi ô ứng viên; chưa có bảng chuyển vị '
         '(transposition table) nên thế cờ lặp lại qua đường khác vẫn bị tính lại.',
         '**Mẫu thực nghiệm nhỏ:** 48 ván và 3 thế cờ; chưa đo trước người chơi mạnh hoặc engine Gomoku chuyên dụng.',
         '**LLM chưa được đánh giá với API thật:** chỉ có kiểm thử bằng phản hồi giả lập.'])


# ================================================================== CHƯƠNG 6
def ch6():
    H(1, 'CHƯƠNG 6. MINH HỌA SẢN PHẨM')
    P('Phần này trình bày các màn hình chính theo đúng trình tự một lượt demo: chọn chế độ → vào ván → quan sát AI tạo thế → kết thúc ván.')
    FIG('ui_menu.jpg', 'Màn hình chọn chế độ: PVP “Chơi cùng bạn bè” và PVE “Đấu trí với máy”', 13)
    P('Màn hình đầu tiên giới thiệu luật tóm tắt (15×15, đúng 5 quân, không xét chặn hai đầu, bốc ngẫu nhiên lượt đầu) và '
      'mục “Luật chơi chi tiết”. Thanh trạng thái cho biết “AI offline” khi chưa cấu hình LLM – AI vẫn chơi đầy đủ bằng Minimax.')
    FIG('ui_open_four.jpg', 'Ván PVE: AI (O) đi trước và tạo bốn quân mở ở cột 8 sau 7 nước', 13)
    P('Trong ván ở Hình 8, máy được bốc đi trước và đặt quân đầu ở trung tâm (8, 8). Người chơi đặt X rời rạc; AI liên tục '
      'mở rộng cột 8 và sau 7 nước đã có bốn quân O liên tiếp từ hàng 5 đến 8 với cả hai đầu trống – thế mà hàm đánh giá chấm '
      'khoảng 36.000 điểm. Ô nền vàng là nước vừa đánh; bảng bên phải hiển thị lượt hiện tại và nhắc luật.')
    FIG('ui_ai_win.jpg', 'Kết thúc ván: người chơi chặn một đầu, AI hoàn thành đúng 5 quân ở đầu còn lại', 13)
    P('Khi người chơi chặn đầu trên (4, 8), AI đặt quân ở (9, 8) để có đúng năm quân. Chuỗi thắng được tô xanh lá, bảng trạng '
      'thái ghi “Máy tính thắng!” và ván bị khóa cho đến khi chọn “Ván mới”. Ví dụ này minh họa trực quan vì sao trọng số của '
      'thế bốn mở phải rất lớn: một nước chặn không đủ để cứu ván.')
    H(2, '6.1. Kịch bản demo trực tiếp')
    BUL(['Mở ứng dụng bằng python desktop.py (hoặc Caro XP.command trên macOS); giới thiệu màn hình chọn chế độ.',
         'Chọn PVE, chỉ ra người đi trước được bốc ngẫu nhiên; đánh vài nước để AI phản hồi trong chưa tới một giây.',
         'Cố tình tạo thế ba/bốn để thấy AI chặn ngay; sau đó để AI tạo thế bốn mở và kết thúc ván.',
         'Chuyển sang PVP để cho thấy kiểm tra luật đúng 5 (chuỗi 6 không thắng).',
         'Phương án dự phòng: các ảnh trong chương này và chạy bản trình duyệt python3 app.py.'], numbered=True)


# ================================================================== KẾT LUẬN
def conclusion():
    H(1, 'KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN')
    H(2, 'Mức độ đạt mục tiêu')
    P('Nhóm đã mô hình hóa trò chơi theo đúng yêu cầu của đề tài – trạng thái là bàn cờ, hàm chuyển trạng thái là đặt X hoặc '
      'O, Minimax chọn nước đi – và mở rộng từ Tic-Tac-Toe 3×3 lên Caro 15×15 để các kỹ thuật tìm kiếm đối kháng thực sự cần '
      'thiết. Ba kết quả chính:')
    BUL([f'**Alpha-Beta giảm {num(d4_red,1)}% số node ở độ sâu 4** so với Minimax thuần trên ba thế cờ, nhanh hơn khoảng '
         f'{num(d4_speed,1)} lần và luôn chọn cùng nước đi; sắp xếp nước theo heuristic giảm thêm {num(ord_red,0)}% số node.',
         '**AI phản hồi nhanh và chơi tốt:** mỗi nước trung bình 0,25–0,33 s (tối đa 0,84 s, dưới hạn 1,5 s); thắng 24/24 ván trước '
         'đối thủ ngẫu nhiên và tham lam; độ sâu 4 thắng độ sâu 2 với tỉ số 10/12.',
         '**Sản phẩm hoàn chỉnh và đúng luật:** giao diện desktop cho người chơi tương tác với AI, chế độ PVP, luật đúng 5 quân, '
         'kết nối LLM tùy chọn an toàn; 32/32 kiểm thử đạt. Ở trường hợp gốc Tic-Tac-Toe 3×3, Minimax duyệt hết cây, '
         'xác nhận ván hòa và AI không thua ván nào trong 200 ván.'])
    H(2, 'Hạn chế')
    P('AI không bảo đảm bất bại do giới hạn độ sâu và số nhánh, chịu hiệu ứng chân trời; tham số độ khó chưa được đưa lên giao '
      'diện; thành phần LLM chưa được đánh giá với API thật; số ván thực nghiệm còn nhỏ.')
    H(2, 'Hướng phát triển')
    BUL(['Thêm bảng chuyển vị với Zobrist hashing và heuristic killer move để tăng độ sâu lên 5–6 trong cùng thời gian.',
         'Tìm kiếm chuỗi đe dọa (threat-space search / VCF) cho các thế bốn và ba liên tiếp, khắc phục hiệu ứng chân trời.',
         'Thêm lựa chọn “mức độ khó” trên giao diện (độ sâu 2/3/4, thời gian 0,5–3 s) để người chơi thay đổi tham số trực tiếp.',
         'Đánh giá hệ thống hơn: nhiều ván hơn, đối thủ mạnh hơn, đo riêng hiệu quả khi bật LLM với API thật.',
         'So sánh với Monte Carlo Tree Search trên cùng bàn cờ và cùng giới hạn thời gian.'])


def references():
    H(1, 'TÀI LIỆU THAM KHẢO')
    refs = ['[1] S. Russell and P. Norvig, Artificial Intelligence: A Modern Approach, 4th ed. Hoboken, NJ: Pearson, 2020, ch. 5 “Adversarial Search and Games”.',
            '[2] D. E. Knuth and R. W. Moore, “An analysis of alpha-beta pruning,” Artificial Intelligence, vol. 6, no. 4, pp. 293–326, 1975.',
            '[3] L. V. Allis, “Searching for Solutions in Games and Artificial Intelligence,” Ph.D. dissertation, University of Limburg, Maastricht, 1994.',
            '[4] C. E. Shannon, “Programming a computer for playing chess,” Philosophical Magazine, vol. 41, no. 314, pp. 256–275, 1950.',
            '[5] Anthropic, “Messages API,” Claude Platform Docs. [Online]. Available: https://platform.claude.com/docs/en/api/messages/create',
            '[6] pywebview, “Installation guide.” [Online]. Available: https://pywebview.flowrl.com/guide/installation.html',
            '[7] Nhóm 03, “Caro XP – mã nguồn,” GitHub. [Online]. Available: https://github.com/Chuki1234/CaroXP.git']
    for r in refs:
        p = P(r, indent=False, size=12)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.first_line_indent = Cm(-0.8)


def appendix():
    H(1, 'PHỤ LỤC')
    H(2, 'Phụ lục A. Hướng dẫn cài đặt và chạy')
    CODE(['# Yêu cầu Python 3.10+; trong thư mục dự án:',
          'python3 -m venv .venv',
          '.venv/bin/python -m pip install -r requirements.txt',
          '.venv/bin/python desktop.py          # cửa sổ desktop',
          'python3 app.py                       # hoặc bản trình duyệt: http://127.0.0.1:8000',
          'python3 -m unittest discover -s tests -v       # 32 kiểm thử',
          'python3 experiments/benchmark.py --games 12    # tái lập số liệu Chương 5'])
    P('Windows dùng .venv\\Scripts\\python và cần WebView2 Runtime. Bật LLM bằng cách điền ANTHROPIC_API_KEY vào file .env '
      '(không bắt buộc).')
    H(2, 'Phụ lục B. Đoạn mã then chốt – hàm đánh giá một đường')
    CODE(['@lru_cache(maxsize=65536)',
          'def _line_score(text, player):',
          '    opponent = HUMAN if player == SECOND else SECOND',
          '    score = 0',
          '    for start in range(len(text) - 4):',
          '        window = text[start:start + 5]',
          '        if opponent in window: continue',
          '        # cửa sổ bị kéo dài cùng màu thì không thể thành đúng 5',
          '        if (start > 0 and text[start-1] == player) or \\',
          '           (start + 5 < len(text) and text[start+5] == player): continue',
          '        score += (0, 2, 30, 550, 18000, WIN_SCORE)[window.count(player)]',
          '    return score'])


# ================================================================== footer
def footer():
    sec = doc.sections[0]
    sec.different_first_page_header_footer = True
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field(fp, 'PAGE')
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_fmt(hp.add_run('Nhóm 03 – Game Tic-Tac-Toe với Minimax (Caro XP)'), italic=True, size=10, color=RGBColor(0x6B, 0x6A, 0x64))


def build():
    setup()
    cover()
    front()
    # Danh mục hình/bảng cần số thứ tự: dựng nội dung trước rồi chèn danh mục.
    marker = doc.add_paragraph()
    ch1(); ch2(); ch3(); ch4(); ch5(); ch6(); conclusion(); references(); appendix()
    # Chèn danh mục trước chương 1 bằng cách dựng trong tài liệu tạm rồi di chuyển XML.
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
