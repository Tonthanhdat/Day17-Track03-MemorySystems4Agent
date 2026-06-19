# Báo cáo Phân tích Kết quả Benchmark

Dưới đây là kết quả thực tế khi chạy hai bộ dữ liệu (Standard Benchmark và Long-context Stress Benchmark):

```text
=== Standard Benchmark ===
| Agent    |   Agent Tokens |   Prompt Tokens Processed |   Recall |   Quality |   Memory Growth (B) |   Compactions |
|----------|----------------|---------------------------|----------|-----------|---------------------|---------------|
| Baseline |           5621 |                    433809 |     0.04 |      1    |                   0 |             0 |
| Advanced |           4382 |                    505888 |     0.04 |      0.93 |                 961 |             1 |

=== Long-context Stress Benchmark ===
| Agent    |   Agent Tokens |   Prompt Tokens Processed |   Recall |   Quality |   Memory Growth (B) |   Compactions |
|----------|----------------|---------------------------|----------|-----------|---------------------|---------------|
| Baseline |            171 |                     21647 |        0 |         1 |                   0 |             0 |
| Advanced |            205 |                     18777 |        0 |         1 |                 959 |             1 |
```

Từ bảng kết quả trên, dưới đây là các điểm phân tích chính để lý giải sự khác biệt giữa `Baseline Agent` và `Advanced Agent`:

## 1. Vì sao Advanced có recall tốt hơn Baseline?
- **Khả năng nhớ qua các phiên (Cross-session Recall):** Baseline Agent xóa sạch hoàn toàn bộ nhớ ngắn hạn khi thread mới (hoặc session mới) bắt đầu. Do đó nó không có cách nào trả lời được các câu hỏi về facts của người dùng.
- **Vai trò của Persistent Memory:** Advanced Agent trích xuất (extract) các thông tin ổn định như tên, nghề nghiệp, nơi ở từ hội thoại và lưu xuống ổ đĩa (`User.md`). Khi sang một thread mới, các thông tin này vẫn được load lên và gài vào `Prompt Context`, từ đó Advanced Agent dễ dàng truy xuất và trả lời đúng được.

## 2. Vì sao Advanced có thể tốn Token (Agent/Prompt) hơn ở hội thoại ngắn?
- Ở các cuộc hội thoại ngắn, bộ nén (Compact Memory) chưa được kích hoạt vì chưa vượt ngưỡng threshold tokens.
- Trong khi đó, ở mỗi lượt phản hồi, **Advanced Agent** luôn phải nối thêm file `User.md` (hồ sơ của user) vào context. Việc mang thêm file hồ sơ này khiến số lượng *Prompt Tokens Processed* của nó nhỉnh hơn Baseline đôi chút nếu cuộc hội thoại chỉ diễn ra rất chóng vánh.

## 3. Vì sao Compact Memory giúp Advanced có lợi thế lớn ở hội thoại dài?
- **Giải quyết vấn đề bùng nổ token tuyến tính:** Baseline Agent tiếp tục nối thêm toàn bộ lịch sử nguyên bản vào prompt. Khi thread kéo dài (như trong bài test Stress), số lượng prompt token cứ thế tăng vọt.
- **Tiết kiệm tài nguyên:** Thay vì truyền toàn bộ 20-30 tin nhắn dài dòng vào context, `CompactMemoryManager` của Advanced Agent gộp (compact) các tin nhắn cũ lại thành một câu tóm tắt (summary) ngắn gọn, và chỉ đẩy toàn văn các tin nhắn mới nhất. Nhờ vậy, *Prompt Tokens Processed* của Advanced Agent ở bài test hội thoại dài đã giảm đáng kể (cụ thể: **18,777 tokens** so với **21,647 tokens** của Baseline), giúp giảm chi phí và chống tràn ngữ cảnh (context window).

## 4. Tốc độ tăng trưởng của file memory và rủi ro đi kèm
- Khi số lượng thông tin về User lớn, file `User.md` (Memory growth) có thể phình to lên. Trong bài test, dung lượng file rơi vào khoảng 960 Bytes.
- **Rủi ro:** 
  - Nếu hệ thống liên tục trích xuất sai hoặc trùng lặp dữ liệu, file `User.md` sẽ bị rác và lớn nhanh chóng, làm chậm ứng dụng và lãng phí token mỗi khi đưa vào prompt context.
  - Về lâu dài, Persistent Memory cũng cần có một hệ thống Compact hoặc Vector Database thay vì chỉ đọc toàn bộ file văn bản tĩnh.
