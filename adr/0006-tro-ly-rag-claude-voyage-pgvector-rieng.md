# ADR-0006: Trợ lý hỏi đáp dùng Claude + Voyage AI, kho vector là container pgvector riêng

| | |
|---|---|
| **Trạng thái** | Accepted |
| **Ngày** | 2026-09-21 |
| **Người quyết định** | Chủ dự án (chốt khi duyệt kế hoạch luồng 2–5, 2026-09-21) |
| **Liên quan** | [L4 — trợ lý RAG](../02-flows/flow-4-rag-assistant.md), F4-G01 → F4-G09, [STATUS Q2](../STATUS.md#6-blocker--câu-hỏi-mở), [backend #23](https://github.com/LockR-Tech/backend/pull/23) |

## Bối cảnh

Luồng L4 cần trả lời câu hỏi tiếng Việt **chỉ dựa trên tài liệu của Lock.R, có trích nguồn**, từ chối câu ngoài phạm vi, và không để khách đọc được tài liệu vận hành nội bộ. Trước 2026-09-21 chưa có dòng code nào; STATUS Q2 để ngỏ việc chọn LLM + embedding.

Ràng buộc:
- VM production 8 GB đã dùng khoảng 6,3 GB + 4 GB swap, chạy 11 service Spring Boot. Không có GPU ⇒ không tự chạy model.
- Postgres chính là `postgres:16-alpine`, không có pgvector. Đổi image của DB chính đụng tới dữ liệu 10 service.
- `main` = production; mọi thay đổi schema qua Flyway; deploy chờ đủ app đăng ký Eureka rồi mới tính là xong.
- Cần trích dẫn đáng tin (người dùng thấy câu nguồn), không muốn tự dựng cơ chế trích dẫn bằng prompt.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| **Claude + Voyage AI (embedding riêng)** | Claude có **Citations** gốc trên document block ⇒ trích đúng câu nguồn, không phải parse "[n]"; SDK Java chính thức; Voyage là nhà cung cấp embedding Anthropic khuyến nghị, đa ngôn ngữ (có tiếng Việt), chọn được số chiều | Hai nhà cung cấp, hai khoá API; mất mạng ra ngoài ⇒ trợ lý không trả lời |
| Spring AI + một nhà cung cấp cho cả chat lẫn embedding | Ít khoá hơn; một thư viện trừu tượng | Trừu tượng che mất tính năng Citations; thêm tầng phụ thuộc lớn cho một service nhỏ |
| Tự chạy model mở (Ollama) trên VM | Không tốn phí API, dữ liệu không ra ngoài | VM không đủ RAM/CPU; chất lượng tiếng Việt và độ bám tài liệu kém hơn |
| **pgvector trong container riêng** | Không đụng Postgres chính; xoá/khôi phục độc lập; không cần ADR đổi image DB chính | Thêm một container (~100–150 MB RAM) |
| Đổi image Postgres chính sang `pgvector/pgvector:pg16` | Một DB cho tất cả | Rủi ro cho dữ liệu 10 service; phải thử trên bản sao volume production trước |
| Vector DB chuyên dụng (Qdrant…) | Tính năng tìm kiếm phong phú | Thêm công nghệ mới, thêm RAM; quy mô vài nghìn đoạn không cần |

## Quyết định

- Sinh câu trả lời bằng **Claude** qua Anthropic Java SDK; model đổi bằng `ASSISTANT_CHAT_MODEL` (mặc định `claude-haiku-4-5`). Mỗi đoạn truy xuất gửi thành một document block bật Citations.
- Nhúng bằng **Voyage AI** `voyage-4`, **1024 chiều** (cột `vector(1024)`). Đổi model phải giữ 1024 chiều, hoặc viết migration đổi cột rồi đánh chỉ mục lại toàn bộ.
- Kho vector là **container `assistant-db` = `pgvector/pgvector:pg16`** riêng, chỉ `assistant-service` dùng; Postgres chính giữ nguyên.
- Truy xuất dưới ngưỡng liên quan ⇒ trả lời "tài liệu chưa đề cập" **không gọi LLM**. Tài liệu gắn vai trò được đọc, lọc theo `X-User-Roles` của gateway.
- Thiếu khoá API ⇒ service vẫn khởi động (deploy không bị rollback), API hỏi đáp trả 503.

## Hệ quả

- Tích cực: không rủi ro cho dữ liệu hiện có; trích dẫn đáng tin; câu ngoài phạm vi không tốn phí LLM; admin chỉnh ngưỡng/giới hạn trên web (ADR-0005).
- Tiêu cực / đánh đổi chấp nhận: chi phí API theo lượt hỏi (khống chế bằng giới hạn câu/giờ mỗi người); nội dung câu hỏi và đoạn tài liệu được gửi tới Anthropic và Voyage — không nạp dữ liệu cá nhân vào kho tri thức; thêm khoảng 450 MB RAM trên VM.
- Việc phải làm theo sau: nạp `ANTHROPIC_API_KEY`, `EMBEDDING_API_KEY`, `ASSISTANT_DB_PASSWORD` vào `.env` VM ([runbook](../04-engineering/cau-hinh-dich-vu-ngoai.md)); chạy `scripts/seed-knowledge.sh`; chạy bộ đánh giá rồi hiệu chỉnh ngưỡng; cân nhắc cập nhật chính sách quyền riêng tư nếu mở trợ lý cho khách.
