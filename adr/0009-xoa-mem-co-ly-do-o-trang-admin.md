# ADR-0009: Xoá ở trang admin là xoá mềm, bắt buộc có lý do

| | |
|---|---|
| **Trạng thái** | Accepted — theo yêu cầu chủ dự án ngày 2026-10-31 |
| **Ngày** | 2026-11-01 |
| **Người quyết định** | Chủ dự án |
| **Liên quan** | L3 · frontend [#83](https://github.com/LockR-Tech/frontend/pull/83) · nhánh backend `feat/admin-xoa-mem-co-ly-do` |

## Bối cảnh

Xoá tủ, ô tủ và người dùng ở web admin là xoá thật khỏi DB, không ghi lý do. Drone đã có cờ `active = false` nhưng cũng không có lý do. Sau khi xoá thì không còn biết ai xoá, vì sao, và không tra lại được bản ghi.

Xoá mềm vướng ràng buộc UNIQUE: mã tủ, mã drone, email và số điện thoại của bản ghi đã xoá vẫn chiếm chỗ nên không tạo lại được.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| Lọc tay `deleted_at` ở từng truy vấn | Bản ghi đã xoá vẫn đọc được qua JPA | Sót một chỗ là tủ đã xoá nhận đơn trở lại |
| **`@SQLRestriction("deleted_at IS NULL")` trên entity** | Mọi truy vấn JPA và API nội bộ cư xử như đã xoá thật, không phải sửa nơi gọi | Lịch sử chỉ còn hiện `#id` như khi xoá thật; đọc bản ghi đã xoá phải dùng SQL gốc |
| Chuyển bản ghi sang bảng lưu trữ | Bảng chính gọn | Thêm bảng cho từng loại, mất khoá ngoại với lịch sử |

## Quyết định

- Tủ, ô tủ và người dùng dùng `@SQLRestriction` cùng ba cột `deleted_at`, `deleted_by`, `deleted_reason` (`backend/locker-service/…/V32__soft_delete_with_reason.sql`, `backend/user-service/…/V7__soft_delete_with_reason.sql`).
- Drone giữ cờ `active = false` có sẵn, thêm ba cột trên; không dùng `@SQLRestriction` để phiếu sự cố và nhật ký cũ vẫn hiện được mã drone.
- UNIQUE đổi thành unique index một phần, chỉ áp dụng cho bản ghi chưa xoá, nên mã, email và số điện thoại dùng lại được.
- Lý do bắt buộc, tối đa 500 ký tự, kiểm ở server (`backend/common-lib/…/common/util/DeleteReason.java`).
- Admin xoá được admin khác, chỉ không tự xoá chính mình.
- Giữ nguyên các điều kiện chặn xoá cũ: tủ còn ô đang dùng hoặc còn drone, ô đang dùng, drone đang có nhiệm vụ.

## Hệ quả

- Tích cực: tra lại được ai xoá, khi nào, vì sao. Dịch vụ khác không phải đổi gì.
- Tiêu cực / đánh đổi chấp nhận:
  - Chưa có màn xem hay khôi phục bản ghi đã xoá; lý do chỉ xem được trong DB. Riêng người dùng có `GET /api/admin/users/deleted`.
  - Bản ghi đã xoá vẫn nằm trong DB nên không phù hợp khi khách yêu cầu xoá hẳn dữ liệu cá nhân; `auth_accounts` vẫn thu hồi đăng nhập và nhả định danh như trước, hồ sơ giữ nguyên email và số điện thoại.
  - Rollback code về bản trước V32/V7 làm bản ghi đã xoá hiện lại, vì code cũ không lọc `deleted_at`.
- Việc phải làm theo sau: địa điểm, khuyến mãi, thông báo, phiếu sự cố vẫn xoá thật, chưa đổi.
