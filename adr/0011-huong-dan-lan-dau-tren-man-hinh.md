# ADR-0011: Hướng dẫn lần đầu trên màn hình — nội dung tĩnh ở frontend, trạng thái ở user-service, lớp khoanh tự viết

| | |
|---|---|
| **Trạng thái** | Accepted — đã lên production 2026-11-21 (F3-G13) |
| **Ngày** | 2026-11-21 |
| **Người quyết định** | HuyNQB |
| **Liên quan** | [flow-3 F3-G13](../02-flows/flow-3-roles-maintenance.md#6-gap-để-đạt-100-) · backend [#143](https://github.com/LockR-Tech/backend/pull/143) · mobile [#137](https://github.com/LockR-Tech/mobile/pull/137) [#138](https://github.com/LockR-Tech/mobile/pull/138) [#139](https://github.com/LockR-Tech/mobile/pull/139) · frontend [#107](https://github.com/LockR-Tech/frontend/pull/107) |

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
2. **Nội dung** ở `frontend/fe/public/onboarding/`: `tours.json` (nhóm: mã, phiên bản, vai trò, bước; bước: id, neo, trang cần mở, phía đặt ô chú thích, cờ "có thể không xuất hiện", nền tảng) và `locales/{vi,en}.json` (chữ; web admin chỉ bật vi/en nên ja chưa bắt buộc). App mobile tải từ `https://admin.locker-drone.tech/onboarding/…`, dùng bản kèm `assets/onboarding/` khi lỗi mạng và để chạy test.
3. **Lớp khoanh tự viết**: web dùng React portal + `@floating-ui/dom` để đặt ô chú thích; neo là thuộc tính `data-tour`. Mobile dùng `OverlayEntry` + `CustomPainter`; neo là widget `TourAnchor`, gắn thêm `Semantics(identifier: 'tour:<id>', explicitChildNodes: true)` để script chụp ảnh tìm được trên bản Flutter web (không có `explicitChildNodes` thì phần tử bấm được có chữ bị gộp và mất identifier).
4. **Tăng phiên bản nhóm** mỗi khi sửa nội dung nhóm. Người đã xem chỉ được hỏi lại các nhóm mới hoặc vừa tăng phiên bản.
5. **Ảnh HDSD** `hdsd/<nhóm>.png` + `.json` (toạ độ ô khoanh, số ↔ bước) chụp bằng `npm run hdsd:capture`, chỉ trên dev/demo: nhóm web chạy dev server với mọi `/api/**` bị chặn và trả dữ liệu giả; nhóm app chạy bản Flutter web cục bộ, đăng nhập tài khoản demo `@demo.lockr.test`, ảnh cắt ngay dưới ô khoanh cuối để không lộ dữ liệu khác. Test đỏ khi ảnh thiếu hoặc không khớp bước hiện tại.
6. **Phủ đủ mọi màn hình và tính năng** (bổ sung 2026-11-21): mỗi nhóm là một trạng thái màn hình (trang, tab, trang chi tiết, hộp thoại, menu), mọi bước của nhóm thấy được cùng lúc. Thêm vào nội dung:
   - `via` ở bước: neo cần bấm trước khi tìm phần tử (dòng đầu danh sách, tab, nút mở hộp thoại, mục menu). Trang chi tiết có tham số không dùng làm route; bước trỏ trang danh sách và nối `via` qua từng bước (menu "⋯" → "Xem chi tiết" → tab). Chỉ dùng cho thao tác mở/xem, không cho nút đổi dữ liệu. Lớp khoanh web bấm `via` bằng đủ chuỗi sự kiện chuột (menu, tab, Select của Radix mở bằng pointerdown/mousedown), và chặn cú bấm trong lớp hướng dẫn lọt tới Radix để menu, hộp thoại đang dẫn không tự đóng.
   - `manualOnly` ở nhóm: chỉ có ở trang HDSD (màn hình trước đăng nhập kèm `signedOut`, luồng cần đơn thật ở đúng trạng thái như thanh toán VietQR, bỏ hàng vào ô, drone đang bay). Nền tảng `kiosk` (màn hình cảm ứng tại tủ, repo iot) chỉ dùng trong nhóm `manualOnly`; neo kiosk không gắn vào mã iot mà khai ở `scripts/hdsd/kiosk-anchors.json` (neo → CSS selector), ảnh chụp bằng dev server `iot/ui` với mọi request bị chặn.
   - `intro` ở nhóm: chỉ các nhóm tổng quan (15 nhóm đầu) tự chạy khi đăng nhập lần đầu và báo "Có hướng dẫn mới"; nhóm chi tiết mở từ nút "Hướng dẫn" hoặc trang HDSD — tránh tour vài trăm bước.
   - Test bắt buộc "route nào cũng có hướng dẫn": mọi trang admin trong `routes-config.tsx` và mọi route trong `AppRouter` phải có bước trỏ tới (trang chi tiết: nhóm mở bằng `via` từ trang danh sách), hoặc nằm trong bảng ngoại lệ có lý do (màn chờ khởi động, tính năng đang tắt, route không còn chỗ mở tới, đích mã QR mở ô thật).

## Hệ quả

- Sửa màn hình hay nút phải sửa hướng dẫn cùng lúc: gắn/sửa neo, khai nhóm, đủ chữ mọi ngôn ngữ, tăng phiên bản, chụp lại ảnh HDSD. Ghi trong `AGENTS.md` của frontend và mobile. Test quét neo và chữ sẽ đỏ nếu quên.
- Một nhóm của nền tảng khác (ví dụ nhóm KTV khi admin đang ở web) chỉ xem được ở trang HDSD, không khoanh được vì phần tử không có trên nền tảng đó.
- Thêm trang hoặc route mới mà chưa có hướng dẫn ⇒ test đỏ; muốn bỏ qua phải ghi lý do vào bảng ngoại lệ trong `fe/tests/onboarding-content.test.mjs`.
- Nhóm `manualOnly` cần dữ liệu thật mà script chụp không tạo được (thanh toán VietQR, bỏ hàng vào ô, chuyển mã cho người nhận, kết quả thuê tủ, bản đồ drone đang bay) mang cờ `noImage`: trang HDSD chỉ có chữ kèm câu giải thích, script chụp bỏ qua và xoá ảnh cũ; test đỏ nếu nhóm `noImage` còn ảnh.
- Số nhóm tăng lên 288 (admin 153, khách 91, KTV tủ 29, KTV drone 15, tính cả nhóm chỉ có ở HDSD); mỗi người tối đa 142 nhóm chạy được, dưới giới hạn 300 nhóm "đã xem" của user-service.
