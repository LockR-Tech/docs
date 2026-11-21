# ADR-0011: Hướng dẫn lần đầu trên màn hình — nội dung tĩnh ở frontend, trạng thái ở user-service, lớp khoanh tự viết

| | |
|---|---|
| **Trạng thái** | Proposed — đang làm theo đợt (F3-G13) |
| **Ngày** | 2026-11-21 |
| **Người quyết định** | HuyNQB |
| **Liên quan** | [flow-3 F3-G13](../02-flows/flow-3-roles-maintenance.md#6-gap-để-đạt-100-) · backend `feat/f3-g13-onboarding-backend` |

## Bối cảnh

Cần hướng dẫn lần đầu đăng nhập ngay trên màn hình (onboarding tour) cho cả web admin và app mobile: hộp chào, lớp làm tối nền có khoanh từng phần tử, chia theo nhóm chức năng và vai trò, có phiên bản để báo "Có hướng dẫn mới", và trang Hướng dẫn sử dụng (HDSD) dựng từ cùng nội dung.

Ràng buộc trong repo:

- Web admin (React 19) chỉ dành cho ADMIN. Khách và KTV dùng app Flutter, chạy trên Android và trên web (`app.locker-drone.tech`). Hai nền tảng gần như không có màn hình chung.
- Merge backend là deploy lại cả stack (khoảng 20 phút, có gián đoạn). Merge frontend deploy Cloudflare khoảng 2 phút, không gián đoạn.
- App Android cài từ file APK, không tự cập nhật nội dung nếu nội dung nằm trong app.
- Web có vi/en/ja, app có vi/en.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| Nội dung tour (nhóm, bước, chữ) lưu ở backend, phục vụ qua API | Lọc vai trò ở server | Sửa một câu hướng dẫn phải deploy backend, mất kết nối vài phút |
| Nội dung viết trong từng app | Không cần mạng | Hai bản lệch nhau; app Android phải phát hành lại khi sửa chữ |
| **Nội dung tĩnh ở frontend (`fe/public/onboarding/`), app mobile tải lúc chạy và có bản kèm trong app; server chỉ lưu trạng thái** | Một nguồn cho cả hai; sửa chữ chỉ deploy frontend; app không cần phát hành lại | Cần header CORS cho bản Flutter web; repo mobile phải đồng bộ bản kèm để chạy test |
| Thư viện tour (react-joyride, driver.js, showcaseview, tutorial_coach_mark) | Có sẵn | Không thư viện nào chạy cho cả React và Flutter; joyride vướng React 19 và không có phím mũi tên; driver.js không chờ đổi trang; thư viện Flutter khoanh trong một route, không mở ngăn kéo |
| **Lớp khoanh tự viết ở mỗi nền tảng, logic dùng chung kiểm bằng cùng bộ fixture** | Làm đúng yêu cầu đổi trang, bước "có thể không xuất hiện", ngăn kéo, phím tắt | Phải tự viết và tự test khoảng vài trăm dòng mỗi bên |

## Quyết định

1. **Trạng thái** ở user-service, bảng `user_onboarding_state` (Flyway V9): `auto_show`, `seen_groups` (JSONB mã nhóm → phiên bản đã xem), `updated_at`. Ba endpoint `GET /api/user/onboarding`, `PUT /api/user/onboarding/auto-show`, `POST /api/user/onboarding/seen`, chỉ thao tác trên người đăng nhập (`X-User-Id`). "Bỏ qua" một lần lưu ở phía máy khách theo phiên, không lưu server.
2. **Nội dung** ở `frontend/fe/public/onboarding/`: `tours.json` (nhóm: mã, phiên bản, vai trò, bước; bước: id, neo, trang cần mở, phía đặt ô chú thích, cờ "có thể không xuất hiện", nền tảng) và `locales/{vi,en,ja}.json` (chữ). App mobile tải từ `https://admin.locker-drone.tech/onboarding/…`, dùng bản kèm `assets/onboarding/` khi lỗi mạng và để chạy test.
3. **Lớp khoanh tự viết**: web dùng React portal + `@floating-ui/react-dom` để đặt ô chú thích; neo là thuộc tính `data-tour`. Mobile dùng `OverlayEntry` + `CustomPainter`; neo là widget `TourAnchor`, gắn thêm `Semantics(identifier: 'tour:<id>')` để script chụp ảnh tìm được trên bản Flutter web.
4. **Tăng phiên bản nhóm** mỗi khi sửa nội dung nhóm. Người đã xem chỉ được hỏi lại các nhóm mới hoặc vừa tăng phiên bản.

## Hệ quả

- Sửa màn hình hay nút phải sửa hướng dẫn cùng lúc: gắn/sửa neo, khai nhóm, đủ chữ mọi ngôn ngữ, tăng phiên bản, chụp lại ảnh HDSD. Ghi trong `AGENTS.md` của frontend và mobile. Test quét neo và chữ sẽ đỏ nếu quên.
- Một nhóm của nền tảng khác (ví dụ nhóm KTV khi admin đang ở web) chỉ xem được ở trang HDSD, không khoanh được vì phần tử không có trên nền tảng đó.
