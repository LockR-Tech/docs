# L4 — Trợ lý RAG hỏi đáp tài liệu nội bộ

| Tiến độ | Rà soát | Sơ đồ |
|---|---|---|
| **0 %** (0 / 8) | 2026-09-13 · toàn bộ 5 repo — tìm theo rag, embedding, vector, pgvector, spring-ai, openai, anthropic, gemini, ollama, llm, chatbot… | [Kiến trúc](../diagrams/pdf/architecture.pdf) (khối `assistant-service` nét đứt) |

## 1. Mục tiêu nghiệp vụ

Nạp tài liệu nội bộ (hướng dẫn sử dụng, quy trình vận hành, chính sách, FAQ) để người dùng đặt câu hỏi bằng tiếng Việt và nhận câu trả lời **dựa trên tài liệu, có trích nguồn**. Câu hỏi ngoài phạm vi phải được từ chối. Tài liệu vận hành chỉ hiện cho vai trò nhân viên. ADMIN quản lý kho tài liệu.

## 2. Checklist

| # | Hạng mục | Bằng chứng | Verdict |
|---|---|---|---|
| F4.01 | Nạp tài liệu (PDF/DOCX/MD) | Không có parser nào trong `pom.xml`/`pubspec.yaml`/`package.json`/`pyproject.toml`; upload hiện chỉ có ảnh | MISSING |
| F4.02 | Chia đoạn + embedding + vector store | Không có; Postgres là `postgres:16-alpine` không có pgvector (`backend/docker-compose.yml:3`) | MISSING |
| F4.03 | Truy xuất + LLM trả lời có trích nguồn | Không có SDK LLM nào | MISSING |
| F4.04 | API hỏi đáp qua gateway | Không có route `/api/assistant` (`api-gateway/…/application.yml:21-127`) | MISSING |
| F4.05 | Giao diện hỏi đáp (mobile/web) | "Trợ giúp" mobile chỉ là bottom sheet liên hệ (`mobile/lib/features/profile/presentation/pages/profile_page.dart:547,643-680`) | MISSING |
| F4.06 | ADMIN quản lý kho tài liệu | Không có | MISSING |
| F4.07 | Phân quyền tài liệu theo vai trò + lịch sử hội thoại | Không có (có thể tái dùng header `X-User-Roles` của gateway) | MISSING |
| F4.08 | Guardrail + bộ đánh giá | Không có | MISSING |

**Điểm:** 0 / 8 = **0 %**.

Dương tính giả đã loại: "embedding" của Flutter Android, gói `vector_math`, FAQ tĩnh trên landing page, "Trợ giúp" là thông tin liên hệ, `drone_position_socket_service.dart` là telemetry.

## 3. Hạ tầng tái dùng được

- **PostgreSQL 16** ⇒ đổi image sang `pgvector/pgvector:pg16` (cùng major, giữ nguyên volume) và `CREATE EXTENSION vector` trong DB mới `assistant_db`.
- **Flyway** đã dùng ở mọi service ⇒ schema + extension đi bằng migration.
- **Gateway + Eureka + `X-User-Id`/`X-User-Roles`** ⇒ lọc tài liệu theo vai trò không cần auth riêng.
- **RabbitMQ** ⇒ hàng đợi `assistant.reindex` cho index bất đồng bộ.
- **STOMP `/ws`** ở notification-service ⇒ stream câu trả lời (tuỳ chọn).
- **Spring Boot 3.5 / Java 21** ⇒ Spring AI 1.x khớp (pgvector store, chat model, Tika reader).

## 4. Kiến trúc đề xuất

**`assistant-service`** — module Spring Boot mới trong `backend/`, cùng ngôn ngữ, gateway, Eureka, Flyway, Docker và pipeline deploy. Không cần sidecar Python.

```
Nạp:   Admin web → /api/admin/knowledge/documents → assistant-service
         → lưu file, kb_document(PENDING) → RabbitMQ → Tika/Markdown reader
         → TokenTextSplitter (~600 token, chồng lấn) → EmbeddingModel → kb_chunk(vector) → READY
Hỏi:   Mobile/Web → /api/assistant/ask (JWT → X-User-Roles)
         → similaritySearch(topK=5, ngưỡng 0.7, lọc allowed_roles)
         → dưới ngưỡng: từ chối "tài liệu chưa đề cập"
         → trên ngưỡng: ChatClient (chỉ trả lời từ ngữ cảnh, tiếng Việt, trích [n]) → lưu hội thoại → trả lời + nguồn
```

Bảng: `kb_document(id, title, source_path, mime, status, allowed_roles text[], checksum, …)` · `kb_chunk(id, document_id, ordinal, content, metadata jsonb, embedding vector(N))` + chỉ mục HNSW · `conversation` · `message(citations jsonb)` · `eval_case(question, expected_doc, must_refuse)`.

Nhà cung cấp LLM + embedding chọn qua cấu hình (embedding **phải hỗ trợ tiếng Việt**); khoá API để trong `.env` trên VM và GitHub secrets, không bao giờ trong repo. Chờ quyết định ở [STATUS Q2](../STATUS.md#6-blocker--câu-hỏi-mở).

## 5. Tài liệu nguồn để nạp ban đầu

| Nhóm | Vai trò được xem | Nguồn |
|---|---|---|
| Chính sách | Tất cả | `mobile/assets/markdown/terms_of_service.md`, `privacy_policy.md`; `legal/privacy-policy.html`, `data-deletion.html` |
| Hướng dẫn khách hàng | Tất cả | Hướng dẫn sử dụng + kịch bản theo vai trò (bản cũ trong repo mobile cá nhân `docs/manual-test/huong-dan/`, `kich-ban/00…05`) — cần chuyển vào repo này trước |
| Quy trình vận hành | TECHNICIAN · MAINTENANCE · ADMIN | Các file luồng trong `02-flows/`, sơ đồ trạng thái, [release-deploy](../04-engineering/release-deploy.md) |
| FAQ | Tất cả | Mảng FAQ tĩnh trong `frontend/landingPage/src/components/sections/FAQSection.tsx`, `lockr/LockrFAQSection.tsx` |

## 6. Gap để đạt 100 % — theo thứ tự làm

| ID | Việc | Ở đâu | Mục checklist |
|---|---|---|---|
| **F4-G01** | Đổi image Postgres sang `pgvector/pgvector:pg16`, thêm `assistant_db` — thử trên bản sao volume production trước | `backend/docker-compose.yml`, `docker/postgres/init-databases.sql` | F4.02 |
| **F4-G02** | Scaffold `assistant-service`: Eureka client, Flyway V1 schema, Spring AI BOM + pgvector + embedding + chat starter, cấu hình qua biến môi trường | `backend/assistant-service`, `backend/pom.xml` | F4.02 |
| **F4-G03** | API nạp tài liệu + reader + splitter + embedding + reindex bất đồng bộ qua RabbitMQ | `assistant-service` | F4.01, F4.02 |
| **F4-G04** | API hỏi: truy xuất lọc theo vai trò, từ chối dưới ngưỡng, prompt bám ngữ cảnh, trích nguồn, lưu + xem lịch sử hội thoại | `assistant-service` | F4.03, F4.07 |
| **F4-G05** | Route gateway (`/api/assistant/**`, `/api/admin/knowledge/**`), service trong compose, secret trên VM | `api-gateway/…/application.yml`, `docker-compose.yml`, `infra/azure` | F4.04 |
| **F4-G06** | Script seed: nạp hàng loạt tài liệu ở mục 5 kèm `allowed_roles` | `backend/scripts/` | F4.01 |
| **F4-G07** | Web admin trang Knowledge Base: upload, danh sách + trạng thái, xoá, reindex, chọn vai trò, xem hội thoại | `frontend/fe/src/pages/Admin/knowledge/` | F4.06 |
| **F4-G08** | Mobile màn hình trợ lý + xem nguồn; lối vào từ "Trợ giúp" và trang chủ TECHNICIAN/MAINTENANCE | `mobile/lib/features/assistant/`, `profile_page.dart` | F4.05 |
| **F4-G09** | Bộ đánh giá 20–40 câu hỏi tiếng Việt (có câu ngoài phạm vi) + endpoint eval + test (Testcontainers pgvector) | `assistant-service` | F4.08 |
