# Caro XP — hướng thiết kế

Áp dụng quy trình của skill awesome-design-md. Bộ tham chiếu không có Windows XP; sử dụng ngôn ngữ giao diện XP theo yêu cầu, không sao chép logo hoặc hình nền thương hiệu.

- Cửa sổ desktop mở thẳng vào màn hình chọn chế độ cỡ nhỏ, không có nền desktop hay taskbar giả; khung XP có khoảng đệm để thấy trọn viền bo góc.
- Cửa sổ: thanh tiêu đề gradient xanh, viền nổi, nền xám kem `#ece9d8`, nút beveled.
- Chữ: Tahoma với fallback hệ thống; cỡ chữ và mật độ theo ứng dụng desktop cổ điển.
- Trang đầu: chọn PVP/PVE trực tiếp và xem luật chi tiết. Cấu hình Claude nằm trong file `.env` trên máy, ngoài giao diện.
- Ván đấu: cửa sổ native nới rộng, dialog modal 756px; bàn 15×15 bên trái, thông tin người chơi và lượt bên phải. Trở về menu thì cửa sổ thu về kích thước ban đầu; khi mở luật chi tiết, cửa sổ tự tăng chiều cao theo nội dung. Dưới 740px chuyển thông tin xuống dưới bàn.
- X đỏ, O xanh, nước cuối vàng, chuỗi thắng xanh lá; nội dung chữ/nhãn hỗ trợ nhận biết ngoài màu sắc.
- Bàn phím: ô bàn cờ có nhãn hàng/cột, phím mũi tên và Enter; modal giữ focus, có nút đóng.
- Giảm chuyển động khi hệ thống bật prefers-reduced-motion.
- Không tải font, hình hay thư viện frontend từ bên ngoài. Minimax offline chạy ngay khi mở game.

Đã kiểm tra trực quan trong pywebview trên macOS; các nền tảng desktop khác cần kiểm tra khi đóng gói.
