# ADR-0004: Lưu ảnh trên Cloudinary, client upload trực tiếp bằng chữ ký của server

| | |
|---|---|
| **Trạng thái** | Proposed |
| **Ngày** | 2026-09-15 |
| **Người quyết định** | Chủ dự án (chờ duyệt) |
| **Liên quan** | [media-storage](../01-overview/media-storage.md), F3.08, F3-G02 |

## Bối cảnh

Tính năng có ảnh đều **chưa lưu ảnh thật**:

- Phiếu sự cố: admin web hiển thị ảnh Unsplash mẫu (`frontend/fe/src/pages/Admin/maintenance/maintenancePhotos.ts` — `SAMPLE_PHOTOS_BY_REPORT`); app KTV chỉ ghi **tên file** vào ghi chú nhật ký (`mobile/…/technician_home_page.dart` `_RepairLogSheet._add`, `_ResolveVerificationSheet._submit`); trang báo lỗi cũ chèn URL Unsplash cứng vào mô tả (`mobile/…/maintenance_remote_datasource.dart:41`).
- Ảnh đại diện: app gửi multipart tới `PUT /api/user/avatar` nhưng backend chỉ nhận JSON `{imageUrl}` ⇒ không lưu được. `UserSummary` không có `imageUrl`.
- Ảnh cửa hàng / khuyến mãi: chỉ là cột URL, không có đường upload; nút "Đổi ảnh" trên web không có xử lý.

Ràng buộc: VM production 8 GB chạy 11 service Spring Boot, Nginx `client_max_body_size 20m`; không có object storage; ảnh điện thoại 3–8 MB; cần xác minh ảnh nghiệm thu thật sự do KTV được giao chụp.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| A. Multipart qua gateway → service → lưu đĩa VM | Không phụ thuộc bên ngoài | Tốn RAM/băng thông VM, mất ảnh khi đổi VM, không có CDN/resize, phải tự backup |
| B. Multipart qua gateway → service → đẩy tiếp lên Cloudinary/S3 | Server kiểm soát file | Byte ảnh vẫn đi qua VM 2 lần, upload chậm trên 4G, giữ luồng lâu trên pool 3 kết nối |
| C. **Signed direct upload lên Cloudinary** + server xác minh chữ ký phản hồi | Byte ảnh không chạm VM; CDN + resize/thumbnail sẵn (`f_auto,q_auto`); không thêm service mới; không cần SDK (ký SHA-1 bằng JDK) | Phụ thuộc Cloudinary (gói Free 25 credit/tháng); ảnh mồ côi nếu client upload rồi không gắn |
| D. S3/Cloudflare R2 presigned URL | Rẻ khi lớn, đã dùng Cloudflare | Tự làm thumbnail/resize; xác minh sau upload cần gọi HEAD; thêm cấu hình bucket/CORS |

## Quyết định

Chọn **C**.

- `user-service` cấp chữ ký tại `POST /api/media/upload-signatures` với `public_id = <root>/<purpose>/u<userId>/<uuid>`; client upload thẳng tới `api.cloudinary.com`.
- API nghiệp vụ nhận `MediaUpload` (`publicId`, `version`, `signature` do Cloudinary trả). Service xác minh `sha1(public_id&version + api_secret)` và tiền tố `u<X-User-Id>` ⇒ không nhận ảnh của người khác, không nhận URL tuỳ ý. URL do server dựng.
- Code dùng chung ở `common-lib` (`common.media.CloudinaryMediaStorage`), cấu hình bằng một biến `CLOUDINARY_URL` ở user/order/locker/store-service.
- Ảnh phiếu sự cố lưu bảng mới `locker_schema.report_attachments` với `stage` REPORT / INSPECTION / PROGRESS / RESOLUTION.

## Hệ quả

- Tích cực: có bằng chứng ảnh thật cho toàn bộ vòng đời phiếu (khách báo → KTV xác nhận hiện trường → quá trình → nghiệm thu); avatar/ảnh cửa hàng/khuyến mãi upload được; VM không tốn thêm tài nguyên.
- Tiêu cực / đánh đổi chấp nhận: phụ thuộc nhà cung cấp; ảnh mồ côi khi client bỏ dở (dọn tay trên Console); gói Free giới hạn dung lượng — client phải nén (≤ 1920 px).
- Việc phải làm theo sau: tạo tài khoản Cloudinary, đặt `CLOUDINARY_URL` + `MEDIA_FOLDER_ROOT=lockr-prod` trong `.env` VM **trước** khi merge; bật `APP_MAINTENANCE_REQUIRE_RESOLUTION_PHOTO=true` sau khi app mobile mới phát hành; cân nhắc job dọn ảnh mồ côi nếu dung lượng tăng.
- Đổi nhà cung cấp sau này: chỉ thay `CloudinaryMediaStorage` và client upload; bảng `report_attachments` giữ nguyên (cột `public_id`/`secure_url`).
