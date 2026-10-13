# L4 — Trợ lý RAG hỏi đáp tài liệu nội bộ

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **100 %** (8 / 8) | 2026-10-10 · backend [#23](https://github.com/LockR-Tech/backend/pull/23), [#50](https://github.com/LockR-Tech/backend/pull/50) · frontend [#16](https://github.com/LockR-Tech/frontend/pull/16), [#35](https://github.com/LockR-Tech/frontend/pull/35) · mobile [#21](https://github.com/LockR-Tech/mobile/pull/21) — chạy thật trên production từ 2026-10-07 | [Kiến trúc](../diagrams/pdf/architecture.pdf) (khối `assistant`) |

Viết tắt: `AS` = `backend/assistant-service/src/main/java/com/huynqb/laundrylocker/assistant`. Quyết định công nghệ: [ADR-0006](../adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md).

## 1. Mục tiêu nghiệp vụ

Nạp tài liệu nội bộ (hướng dẫn sử dụng, quy trình vận hành, chính sách) để người dùng đặt câu hỏi bằng tiếng Việt và nhận câu trả lời **dựa trên tài liệu, có trích nguồn**. Câu hỏi ngoài phạm vi phải được từ chối. Tài liệu vận hành chỉ hiện cho vai trò nhân viên. ADMIN quản lý kho tài liệu.

## 2. Checklist

| # | Hạng mục | Bằng chứng | Verdict | Còn thiếu |
|---|---|---|---|---|
| F4.01 | Nạp tài liệu (PDF/DOCX/MD) | `POST /api/admin/knowledge/documents` (multipart, ≤ 20 MB, MD/TXT/HTML/PDF/DOCX) `AS/controller/KnowledgeAdminController.java:36`; đọc tài liệu `AS/knowledge/DocumentParser.java:72` (DOCX bằng zip + StAX, tắt DTD `:167`); seed `backend/scripts/seed-knowledge.sh` | **DONE** | — |
| F4.02 | Chia đoạn + embedding + vector store | Đoạn ~2000 ký tự, chồng lấn 200 `AS/knowledge/TextChunker.java:13-14`; job nền PENDING → INDEXING → READY/FAILED `AS/knowledge/KnowledgeIndexer.java:51`; Voyage `voyage-4` 1024 chiều `AS/provider/VoyageEmbeddingProvider.java:64,94`; `vector(1024)` + HNSW cosine `assistant-service/src/main/resources/db/migration/V1__assistant_schema.sql:37,42`; container `pgvector/pgvector:pg16` `backend/docker-compose.yml:390-391` | **DONE** | — |
| F4.03 | Truy xuất + LLM trả lời có trích nguồn | Top-k theo cosine `AS/knowledge/ChunkRepository.java:41`; Claude, mỗi đoạn một document block bật Citations `AS/provider/ClaudeAnswerGenerator.java:99,122`; stop_reason refusal ⇒ từ chối lịch sự `:80` | **DONE** | — |
| F4.04 | API hỏi đáp qua gateway | `POST /api/assistant/ask` `AS/controller/AssistantController.java:27`; route `backend/api-gateway/src/main/resources/application.yml:79` (`/api/assistant/**` cần JWT, `/api/admin/knowledge/**` chỉ ADMIN) | **DONE** | — |
| F4.05 | Giao diện hỏi đáp (mobile/web) | App: route `/assistant`, `/assistant/history` `mobile/lib/core/routing/app_router.dart:104-105`; màn hỏi đáp `mobile/lib/features/assistant/presentation/pages/assistant_chat_page.dart:18`, nguồn trích dẫn `…/widgets/assistant_sources.dart:9`; lối vào "Trợ giúp" `mobile/lib/features/profile/presentation/pages/profile_page.dart:447`, nút trên trang KTV tủ/KTV drone; request hỏi chờ riêng 120 s | **DONE** | Web admin chỉ xem lại hội thoại, không có ô hỏi |
| F4.06 | ADMIN quản lý kho tài liệu | API `AS/controller/KnowledgeAdminController.java`; web `/admin/knowledge` `frontend/fe/src/routes/routes-config.tsx:371`, trang `frontend/fe/src/pages/Admin/knowledge/index.tsx:33` (tài liệu, hội thoại, đánh giá), API slice `frontend/fe/src/stores/apis/admin/knowledge.ts`; xem nội dung tài liệu — file gốc `GET …/documents/{id}/file` và các đoạn đã đánh chỉ mục `GET …/documents/{id}/chunks` (backend #50), giao diện `frontend/fe/src/pages/Admin/knowledge/DocumentDetailSheet.tsx` (frontend #35); cấu hình trợ lý là tab `assistant` ở `/admin/settings` | **DONE** | — |
| F4.07 | Phân quyền tài liệu theo vai trò + lịch sử hội thoại | Lọc `allowed_roles && vai trò người hỏi` `AS/knowledge/ChunkRepository.java:51` (ADMIN đọc tất cả); hội thoại + tin nhắn + citations `AS/chat/AssistantService.java:70` | **DONE** | — |
| F4.08 | Guardrail + bộ đánh giá | Dưới ngưỡng ⇒ "tài liệu chưa đề cập", không gọi LLM `AS/chat/AssistantService.java:38,114`; giới hạn câu/giờ `:85`; ngưỡng/top-k/giới hạn chỉnh trên admin `AS/settings/AssistantSettingsCatalog.java:29`; 27 câu đánh giá `backend/scripts/knowledge/eval-cases.json`, `POST /api/admin/knowledge/eval` `AS/eval/EvalService.java:107`. **Đã chạy trên production 2026-10-07** (10 tài liệu, 89 đoạn): ngưỡng 35 % đạt 27/27 — trúng tài liệu 22/22 (điểm thấp nhất 0,407), từ chối đúng 5/5 (điểm cao nhất 0,345); giữ 35 % | **DONE** | — |
| F4.09 | Trả lời theo **đơn hàng thật** của người hỏi | Nhận câu hỏi về đơn (không phân biệt dấu, mã `ORD-…`, câu nối tiếp) `AS/query/OrderIntent.java`; tải đơn đã tạo + đơn người khác gửi cho người hỏi qua order-service với `X-User-Id` từ gateway, tên tủ/ô qua locker-service `AS/orders/OrderContextService.java`; tài liệu "Đơn hàng của bạn" không chứa PIN/QR/mã lấy hàng, email, ghi chú, SĐT chỉ 3 số cuối `AS/orders/OrderDocumentFormatter.java`; có tài liệu đơn thì không chặn ở ngưỡng truy xuất `AS/chat/AssistantService.java`; bật/tắt `app.assistant.order-context-enabled` ([backend #68](https://github.com/LockR-Tech/backend/pull/68)) | **DONE** | Dữ liệu đơn gửi tới Anthropic khi trả lời — ghi vào chính sách quyền riêng tư (F4-G10) |
| F4.10 | Hiểu tiếng Việt **không dấu** | Nhận câu không dấu `AS/query/VietnameseText.java`; thêm dấu bằng một lần gọi Claude, chỉ nhận khi chỉ khác dấu và giữ nguyên số/mã `AS/provider/ClaudeDiacriticsRestorer.java`, dùng cho truy xuất + nhận ý định + trả lời, bộ đánh giá dùng cùng bước `AS/query/QuestionPreparer.java`; 4 câu không dấu trong `eval-cases.json`; bật/tắt `app.assistant.restore-diacritics` (backend #68) | **DONE** | — |

**Điểm:** DONE 8 × 1 = 8 / 8 = **100 %**.

## 3. Luồng chạy

```
Nạp:   Admin web → POST /api/admin/knowledge/documents (file + vai trò được đọc)
         → kb_documents(PENDING) → job nền (mỗi 5 s) nhận tài liệu → đọc MD/TXT/HTML/PDF/DOCX
         → chia đoạn theo mục (~2000 ký tự, chồng lấn 200) → Voyage embed (input_type=document)
         → kb_chunks(vector 1024) → READY   (thiếu EMBEDDING_API_KEY ⇒ chờ ở PENDING)
Hỏi:   App/Web → POST /api/assistant/ask (JWT → X-User-Id, X-User-Roles)
         → quá số câu/giờ ⇒ 429
         → embed câu hỏi (kèm câu hỏi trước nếu đang trong hội thoại) → top-k theo cosine, lọc vai trò
         → không đoạn nào ≥ ngưỡng ⇒ "Tài liệu hiện có chưa đề cập…" (refused, KHÔNG gọi LLM)
         → có ⇒ Claude (document block + Citations, lịch sử N lượt) → lưu hội thoại → trả lời + nguồn
```

Bảng (Flyway V1, DB `assistant_db` ở container riêng): `kb_documents(allowed_roles text[], checksum unique, content bytea, status…)` · `kb_chunks(embedding vector(1024), HNSW cosine)` · `assistant_conversations` · `assistant_messages(citations jsonb, refused, top_score, model, tokens)` · `eval_cases` · `system_settings` (scope `assistant`).

Thiếu `ANTHROPIC_API_KEY`/`EMBEDDING_API_KEY` ⇒ service vẫn khởi động, `GET /api/assistant/status` trả `configured=false` (kèm `embeddingConfigured`, `chatConfigured`), hỏi đáp trả 503. Nạp khoá: [runbook § 11b](../04-engineering/cau-hinh-dich-vu-ngoai.md).

Tìm kiếm dùng mọi đoạn đang có, không lọc theo trạng thái tài liệu: đánh chỉ mục lại thay đoạn trong một transaction nên tài liệu đang chờ/đang đánh chỉ mục lại (hoặc lỗi khi đánh lại) vẫn trả lời bằng đoạn cũ.

## 4. Tài liệu nạp ban đầu (`backend/scripts/seed-knowledge.sh`)

**Hạn mức Voyage:** tài khoản chưa gắn phương thức thanh toán chỉ được 3 request + 10K token/phút; từ backend #68 bộ nhúng chia lô theo số ký tự và chờ rồi thử lại khi 429 nên tài liệu dài vẫn nạp được (chậm). Gắn phương thức thanh toán ở dashboard Voyage để bỏ giới hạn.

**Nạp lại 2026-10-13** trên production (11 tài liệu): bản mới của hướng dẫn khách hàng (đăng nhập SĐT, chỉ chuyển khoản VietQR/SePay + mở app ngân hàng, chia sẻ mã lấy hàng, yêu cầu hoàn tiền), tài liệu luồng L1–L4, quy trình KTV, phát hành; thêm tài liệu tóm tắt luồng nghiệp vụ. Tài liệu không đổi nội dung bị máy chủ chặn trùng (`DOCUMENT_DUPLICATE`) và giữ nguyên. Bộ đánh giá thay bằng `eval-cases.json` mới.

| Tài liệu | Vai trò được đọc | Nguồn |
|---|---|---|
| Hướng dẫn sử dụng Lock.R cho khách hàng | Tất cả | `backend/scripts/knowledge/huong-dan-khach-hang.md` — viết theo hành vi đã code của L2 (gửi hàng, thuê ô, thanh toán, báo hỏng) |
| Chính sách quyền riêng tư · Hướng dẫn xóa dữ liệu người dùng | Tất cả | `legal/privacy-policy.html`, `legal/data-deletion.html` |
| Điều khoản dịch vụ | Tất cả | `mobile/assets/markdown/terms_of_service.md` |
| Quy trình vận hành và bảo trì tủ cho kỹ thuật viên | LOCKER_TECHNICIAN · ADMIN | `backend/scripts/knowledge/huong-dan-ktv-tu.md` |
| Tóm tắt các luồng nghiệp vụ Lock.R (từng bước ai làm gì) | LOCKER_TECHNICIAN · DRONE_TECHNICIAN · ADMIN | `docs/01-overview/tom-tat-luong-nghiep-vu.md` |
| Các luồng nghiệp vụ L1–L4 | LOCKER_TECHNICIAN · DRONE_TECHNICIAN · ADMIN | `docs/02-flows/*.md` |
| Quy trình phát hành và triển khai | ADMIN | `docs/04-engineering/release-deploy.md` |

**Không nạp** FAQ của landing page (`frontend/landingPage/…/FAQSection.tsx`, `lockr/LockrFAQSection.tsx`): có gói giá (miễn phí 3 lượt/tháng, 499.000đ/tháng), cam kết bảo hiểm/đền bù và mô tả bảo mật không khớp sản phẩm thật — trợ lý sẽ nói sai với khách. Sửa nội dung FAQ trước nếu muốn nạp.

## 5. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| ~~F4-G01 → F4-G08~~ | Hạ tầng pgvector, `assistant-service`, nạp tài liệu, hỏi đáp, gateway, seed, trang Kho tri thức, màn hình trợ lý — **đã làm** (backend #23, frontend #16, mobile #21) | — | F4.01 → F4.07 |
| ~~F4-G09~~ | **Đã làm 2026-10-07:** nạp khoá Anthropic + Voyage trên VM, seed 10 tài liệu + 27 câu, chạy bộ đánh giá: 27/27 ở ngưỡng 35 % (giữ nguyên — xem F4.08). Lưu ý vận hành: khoá Voyage chưa gắn thẻ ⇒ 3 request/phút, 10K token/phút (nạp nhiều tài liệu liền nhau sẽ lỗi 429 — đánh chỉ mục lại từng tài liệu, cách nhau ~1 phút); `seed-knowledge.sh` chạy trong Git Bash trên Windows làm hỏng dấu tiêu đề (curl nhận tham số qua code page ANSI) | — | F4.08 |
| **F4-G10** | Nội dung: sửa FAQ landing page cho khớp sản phẩm rồi nạp; cập nhật chính sách quyền riêng tư nêu việc câu hỏi — và dữ liệu đơn của người hỏi khi hỏi về đơn (F4.09) — được gửi tới Anthropic/Voyage | `frontend/landingPage/…`, `legal/privacy-policy.html` | — |
