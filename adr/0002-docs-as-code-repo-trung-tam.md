# ADR-0002: Tài liệu dạng code trong một repo trung tâm

| | |
|---|---|
| **Trạng thái** | Accepted |
| **Ngày** | 2026-09-13 |
| **Người quyết định** | BaoHuy-Dev (chủ dự án) |
| **Liên quan** | [documentation-rules](../04-engineering/documentation-rules.md), [AGENTS.md](../AGENTS.md) |

## Bối cảnh

- Tài liệu cũ nằm rải rác trong từng repo code (`docs/`, hàng chục file `*_GUIDE.md`, `*_REPORT.md`, `AGENTS.md`, `CLAUDE.md`), trùng lặp và **nhiều chỗ nói sai so với code** (ví dụ README từng liệt kê 14 service trong khi chỉ có 12).
- Nhóm dùng nhiều AI agent. Mỗi agent mở một repo code riêng lẻ và cần biết ngay tiến độ chung, luật làm việc, việc tiếp theo.
- Hệ thống trải trên 5 repo; một luồng nghiệp vụ (ví dụ giao hàng drone) đi qua backend + mobile + web + iot ⇒ không repo code nào là "chủ" của tài liệu luồng.
- Chủ dự án yêu cầu sơ đồ in được, đúng một trang A4.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| **Repo `docs` trung tâm + `AGENTS.md` con trỏ trong mỗi repo code** | Một nguồn sự thật cho tiến độ liên-repo; review tài liệu như code; agent mở repo nào cũng được dẫn tới | Phải giữ kỷ luật mở PR ở hai repo |
| Tài liệu trong từng repo code | Gần code | Tiến độ liên-repo không có chỗ; trùng lặp; đã từng thất bại |
| Wiki GitHub / Notion / Google Docs | Soạn dễ | Không review qua PR, không version cùng code, agent khó đọc, dễ lệch |

## Quyết định

- Repo **`LockR-Tech/docs`** là nguồn sự thật cho tiến độ (`STATUS.md`), luồng nghiệp vụ, sơ đồ, luật kỹ thuật và ADR.
- Mỗi repo code có `AGENTS.md` ngắn (+ `CLAUDE.md` import nó) **chỉ** trỏ tới repo docs và nêu lệnh riêng của repo — ngoại lệ duy nhất cho quy ước "repo code không chứa file `.md`".
- Sơ đồ viết bằng **Mermaid**, xuất **PDF đúng 1 trang A4** bằng Chrome headless; CI kiểm tra số trang.
- Tiến độ đo bằng checklist có bằng chứng `file:line`, không đo bằng cảm nhận.

## Hệ quả

- Tích cực: agent và người mới có một điểm vào; tiến độ kiểm chứng được; sơ đồ luôn render lại được từ nguồn.
- Đánh đổi: thay đổi code kéo theo PR docs; PDF là file nhị phân được commit (chấp nhận để xem trực tiếp trên GitHub và in).
- Việc theo sau: thêm `AGENTS.md`, `CLAUDE.md`, PR template vào 5 repo code.
