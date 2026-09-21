# L4 — Trợ lý RAG hỏi đáp tài liệu nội bộ

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **94 %** (7,5 / 8) | 2026-09-21 · backend [#23](https://github.com/LockR-Tech/backend/pull/23) · frontend [#16](https://github.com/LockR-Tech/frontend/pull/16) · mobile [#21](https://github.com/LockR-Tech/mobile/pull/21) (đã merge 2026-09-21) | [Kiến trúc](../diagrams/pdf/architecture.pdf) (khối `assistant`) |

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
| F4.06 | ADMIN quản lý kho tài liệu | API `AS/controller/KnowledgeAdminController.java`; web `/admin/knowledge` `frontend/fe/src/routes/routes-config.tsx:371`, trang `frontend/fe/src/pages/Admin/knowledge/index.tsx:33` (tài liệu, hội thoại, đánh giá), API slice `frontend/fe/src/stores/apis/admin/knowledge.ts`; cấu hình trợ lý là tab `assistant` ở `/admin/settings` | **DONE** | — |
| F4.07 | Phân quyền tài liệu theo vai trò + lịch sử hội thoại | Lọc `allowed_roles && vai trò người hỏi` `AS/knowledge/ChunkRepository.java:51` (ADMIN đọc tất cả); hội thoại + tin nhắn + citations `AS/chat/AssistantService.java:70` | **DONE** | — |
| F4.08 | Guardrail + bộ đánh giá | Dưới ngưỡng ⇒ "tài liệu chưa đề cập", không gọi LLM `AS/chat/AssistantService.java:38,114`; giới hạn câu/giờ `:85`; ngưỡng/top-k/giới hạn chỉnh trên admin `AS/settings/AssistantSettingsCatalog.java:29`; 27 câu đánh giá `backend/scripts/knowledge/eval-cases.json`, `POST /api/admin/knowledge/eval` `AS/eval/EvalService.java:107` | PARTIAL | Chưa chạy bộ đánh giá với khoá thật ⇒ ngưỡng mặc định 35 % chưa hiệu chỉnh |

**Điểm:** DONE 7 × 1 + PARTIAL 1 × 0,5 = 7,5 / 8 = **94 %**.

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

| Tài liệu | Vai trò được đọc | Nguồn |
|---|---|---|
| Hướng dẫn sử dụng Lock.R cho khách hàng | Tất cả | `backend/scripts/knowledge/huong-dan-khach-hang.md` — viết theo hành vi đã code của L2 (gửi hàng, thuê ô, thanh toán, báo hỏng) |
| Chính sách quyền riêng tư · Hướng dẫn xóa dữ liệu người dùng | Tất cả | `legal/privacy-policy.html`, `legal/data-deletion.html` |
| Điều khoản dịch vụ | Tất cả | `mobile/assets/markdown/terms_of_service.md` |
| Quy trình vận hành và bảo trì tủ cho kỹ thuật viên | LOCKER_TECHNICIAN · ADMIN | `backend/scripts/knowledge/huong-dan-ktv-tu.md` |
| Các luồng nghiệp vụ L1–L4 | LOCKER_TECHNICIAN · DRONE_TECHNICIAN · ADMIN | `docs/02-flows/*.md` |
| Quy trình phát hành và triển khai | ADMIN | `docs/04-engineering/release-deploy.md` |

**Không nạp** FAQ của landing page (`frontend/landingPage/…/FAQSection.tsx`, `lockr/LockrFAQSection.tsx`): có gói giá (miễn phí 3 lượt/tháng, 499.000đ/tháng), cam kết bảo hiểm/đền bù và mô tả bảo mật không khớp sản phẩm thật — trợ lý sẽ nói sai với khách. Sửa nội dung FAQ trước nếu muốn nạp.

## 5. Gap để đạt 100 %

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| ~~F4-G01 → F4-G08~~ | Hạ tầng pgvector, `assistant-service`, nạp tài liệu, hỏi đáp, gateway, seed, trang Kho tri thức, màn hình trợ lý — **đã làm** (backend #23, frontend #16, mobile #21) | — | F4.01 → F4.07 |
| **F4-G09** | Bộ đánh giá **đã có** (27 câu, endpoint, test Testcontainers pgvector). Còn: nạp khoá API trên VM, chạy `POST /api/admin/knowledge/eval` trên dữ liệu thật, chỉnh `app.assistant.min-score-percent` tới khi trúng tài liệu ≥ 90 % và từ chối đúng các câu ngoài phạm vi | `/admin/settings` scope `assistant` | F4.08 |
| **F4-G10** | Nội dung: sửa FAQ landing page cho khớp sản phẩm rồi nạp; cập nhật chính sách quyền riêng tư nêu việc câu hỏi được gửi tới Anthropic/Voyage | `frontend/landingPage/…`, `legal/privacy-policy.html` | — |
