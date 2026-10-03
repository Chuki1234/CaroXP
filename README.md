# Caro XP

Game caro 15×15, backend Python và frontend HTML/CSS/JavaScript, mở trong cửa sổ desktop bằng pywebview. Khi khởi chạy, cửa sổ chọn chế độ có kích thước khoảng 700×660; khi vào ván, cửa sổ nới rộng để hiện bàn 15×15 và thu lại khi về menu. Mở “Luật chơi chi tiết” sẽ tự tăng chiều cao cửa sổ để đọc hết nội dung, rồi thu lại khi gập luật. Có PVP cùng máy và PVE với Minimax; LLM là kết nối tùy chọn, chưa cần API key để chơi.

## Chạy ứng dụng desktop

Yêu cầu Python 3.10+. Trong thư mục dự án:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python desktop.py
```

Trên macOS, sau khi cài xong có thể nhấp đúp **Caro XP.command**. Môi trường `.venv` đã được tạo và cài thư viện trên máy hiện tại.

Trên Windows, dùng `.venv\Scripts\python` thay cho `.venv/bin/python`; cần WebView2 Runtime. Linux cần một backend GUI, ví dụ cài `pywebview[qt]`. Xem [hướng dẫn cài đặt pywebview](https://pywebview.flowrl.com/guide/installation.html).

Launcher tự mở server trên một cổng trống ở `127.0.0.1`; đóng cửa sổ sẽ dừng server. Giao diện chỉ có cửa sổ Caro XP, không có nền desktop hay taskbar giả. Nếu muốn kiểm tra bằng trình duyệt:

```bash
python3 app.py
```

Mở http://127.0.0.1:8000. Đổi cổng bằng `CARO_PORT=8080 python3 app.py`. Không cần thư viện ngoài để chạy bản trình duyệt hoặc kiểm thử backend.

## Luật chơi

- PVP: hai người thay phiên trên cùng máy. PVE: người cầm X, máy cầm O.
- Mỗi ván đều bốc ngẫu nhiên bên đi trước, kể cả máy.
- **Đúng 5 quân liên tiếp** ngang, dọc hoặc chéo là thắng, không xét chặn hai đầu.
- Nối thành chuỗi **6 quân trở lên không thắng** theo hướng đó. Nếu đồng thời tạo đúng 5 theo hướng khác thì vẫn thắng.
- Bàn đầy 225 ô mà không có chuỗi thắng thì hòa. Nước cuối tạo chuỗi thắng được tính thắng trước khi xét hòa.
- Nhấp chuột để đặt quân; hỗ trợ phím mũi tên và Enter. Ô vàng là nước vừa đánh, ô xanh là chuỗi thắng. Kết quả ván cờ hiển thị trên bảng trạng thái.

## AI và LLM

AI ưu tiên thắng ngay, rồi chặn nước thắng ngay của người chơi. Sau đó tìm kiếm Minimax cắt tỉa alpha–beta, tăng dần độ sâu đến tối đa 4 lượt và giới hạn khoảng 1,5 giây cho phần tìm kiếm. Kiểm tra chiến thuật và xếp hạng ban đầu nằm ngoài khoảng thời gian này. Chỉ xét các ô trống gần quân đã đặt (bán kính 2), giới hạn số nhánh và đánh giá các mẫu trên hàng, cột, đường chéo. Do đó đây là AI tìm kiếm có giới hạn, **không có bảo đảm bất bại**.

Luồng kết hợp: **Minimax xếp hạng → LLM chọn giữa các ứng viên có cùng điểm tốt nhất → Python kiểm tra → đặt quân**. Nếu chỉ có một nước tốt nhất thì bỏ qua lời gọi LLM. Khi chưa cấu hình, mất kết nối, quá 12 giây chờ phản hồi, JSON sai hoặc nước không thuộc nhóm cho phép, AI dùng nước tốt nhất của Minimax. Không giả lập phản hồi LLM khi chưa kết nối.

### Cấu hình Claude Anthropic trên máy

Ứng dụng tự đọc file [`.env`](.env) trong thư mục dự án khi khởi động. File này nằm trong `.gitignore`, nên API key không được đưa vào Git. File `.env.example` là mẫu có thể sao chép lại.

1. Mở `.env` bằng trình soạn thảo văn bản.
2. Điền key vào dòng `ANTHROPIC_API_KEY=...`.
3. Giữ `CARO_LLM_PROVIDER=anthropic`. Để trống `CARO_LLM_MODEL` để dùng model mặc định, hoặc điền ID model Claude mà tài khoản của bạn được phép dùng.
4. Đóng và mở lại Caro XP, rồi chọn PVE. Khi không có key, AI vẫn chơi offline bằng Minimax.

Backend gọi [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create) bằng header `x-api-key` và `anthropic-version`. Model mặc định là `claude-haiku-4-5-20251001`, theo [danh sách model Anthropic](https://platform.claude.com/docs/en/models/overview). Chỉ backend Python đọc key; API trạng thái không trả về key. Key không được lưu trong HTML/JavaScript hay localStorage.

Biến môi trường của hệ điều hành có cùng tên được ưu tiên hơn giá trị trong `.env`. Backend vẫn hỗ trợ `CARO_LLM_PROVIDER=openai` cùng `CARO_LLM_BASE_URL`, `CARO_LLM_MODEL`, `CARO_LLM_API_KEY` cho API tương thích OpenAI. Cấu hình được đọc khi khởi động, nên cần mở lại app sau khi sửa file. Khi Anthropic báo key sai, thiếu quyền, model không tồn tại hoặc giới hạn lượt gọi, game thông báo lý do và dùng Minimax. Chưa có kiểm thử bằng key thật.

Ván đấu giữ trong bộ nhớ, tối đa 128 ván; đóng ứng dụng sẽ mất dữ liệu này. LLM chỉ được gọi trong ván PVE khi có nhiều ứng viên cùng điểm Minimax tốt nhất.

## Kiểm thử

```bash
python3 -m unittest discover -s tests -v
```

Bao gồm luật đúng 5/chặn hai đầu/chuỗi 6, hòa với bàn đầy thực tế, thắng ở ô cuối, random lượt đầu, các tình huống AI thắng/chặn/tạo hai mối đe dọa, hết thời gian tìm kiếm, kiểm tra lựa chọn LLM, fallback, nước trùng và API HTTP thực. Kiểm thử HTTP cần quyền mở cổng localhost. Các kiểm thử LLM dùng phản hồi giả lập; chưa kiểm chứng chất lượng với model thật.

## Cấu trúc

- `desktop.py`: cửa sổ desktop và vòng đời server.
- `app.py`: API, khóa theo ván, kiểm tra lượt/phiên bản bàn cờ, điều phối AI.
- `caro/engine.py`: luật chính xác 5 và thuật toán Minimax.
- `caro/llm.py`: adapter LLM và kiểm tra tọa độ.
- `web/`: giao diện XP, dialog ván đấu, cài đặt và thao tác bàn phím.
- `tests/test_game.py`: kiểm thử luật, AI, adapter và API.
- `DESIGN.md`: các quyết định giao diện.

Ứng dụng phục vụ chơi local, chưa có phòng online, lưu lịch sử lâu dài hay gói cài đặt độc lập kèm Python.
