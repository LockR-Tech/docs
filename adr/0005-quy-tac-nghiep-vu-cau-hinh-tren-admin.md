# ADR-0005: Quy tắc nghiệp vụ cấu hình trên admin, mỗi service tự sở hữu

| | |
|---|---|
| **Trạng thái** | Proposed |
| **Ngày** | 2026-09-15 |
| **Người quyết định** | Chủ dự án (chờ duyệt) |
| **Liên quan** | [business-settings](../01-overview/business-settings.md), ADR-0004 |

## Bối cảnh

Chủ dự án yêu cầu: **toàn bộ business rule phải cấu hình trên admin thay vì hardcode**. Rà soát code (2026-09-15, backend `0e55abc`) cho thấy:

- Không có bảng cấu hình, API settings hay cache nào.
- Quy tắc nằm rải rác ở ba dạng: `@Value("${app.order.*:mặc định}")` (không key nào có trong `application.yml` ⇒ mặc định trong Java là giá trị thật), hằng số `static final`, số viết cứng.
  - order-service: phí gửi 15.000, giá thuê 5.000/10.000 mỗi giờ, phí quá hạn 500/giờ, trần 50.000 và 50%, hạn lấy hàng 48h, tự huỷ 24h, drone giao 24h, pin 20%, phí lưu trữ mỗi món 5.000.
  - locker-service: SLA 4h, KTV trễ ≥ 3 phiếu bị chặn nhận việc, bậc phạt 1/3/5, pin drone 20%, giữ ô 24h.
  - Các service khác: khoá mã sau 5 lần sai / 15 phút (iot); OTP 300s (auth); nạp tối thiểu 1.000 (payment); hạng thành viên 500/2.000/5.000 (loyalty); bán kính tìm 10km (store).
- App mobile cũng hardcode giá (15.000đ, 5.000đ/giờ…), mốc nạp tiền, giới hạn ảnh.
- Muốn đổi bất kỳ giá trị nào phải sửa code và deploy (~20 phút gián đoạn backend).

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| A. Service cấu hình trung tâm mới | Một nơi quản lý | Thêm container trên VM 8 GB; mọi service phụ thuộc runtime vào nó; thêm điểm hỏng |
| B. Một service (ví dụ user-service) lưu hết, service khác gọi Feign + cache | Không thêm container | Service sở hữu quy tắc không kiểm được kiểu/giới hạn của chính nó; phụ thuộc chéo |
| C. Spring Cloud Config / biến môi trường | Có sẵn hệ sinh thái | Admin không sửa được trên web; vẫn phải restart |
| D. **Mỗi service sở hữu bảng `system_settings` + module dùng chung ở common-lib** | Không thêm container, không gọi chéo trên luồng nghiệp vụ; service tự kiểm kiểu/min/max; biến môi trường cũ vẫn là mặc định | Admin web gọi 7 endpoint (1 mỗi scope); cache 30s ⇒ thay đổi có hiệu lực chậm tối đa 30s trên instance khác |

## Quyết định

Chọn **D**.

- `common-lib` `common.settings`: `SettingsCatalog` (service khai báo quy tắc), `BusinessSettings` (đọc có kiểu, cache 30s, kiểm tra, audit), `JdbcSettingsStore`, `BusinessSettingsController`. Chỉ bật khi service đặt `app.settings.scope`.
- Thứ tự ưu tiên khi đọc: **giá trị admin trong DB → property/biến môi trường cùng tên key → mặc định trong catalog**. Key giữ nguyên tên property cũ.
- API: `/api/admin/settings/{scope}` (ADMIN), `/api/settings/{scope}/public` (không cần đăng nhập, chỉ quy tắc đánh dấu công khai cho app hiển thị giá/giới hạn).
- Server **luôn tự tính giá** theo cấu hình; giá client gửi lên bị bỏ qua.

**Không đưa lên admin (cố ý):**

- Tập trạng thái cho phép từng hành động: đây là máy trạng thái, sửa tuỳ ý sẽ phá dữ liệu.
- Bí mật và TTL JWT: thuộc bảo mật, đổi qua biến môi trường.
- Chu kỳ cron, timeout Feign/MQTT kỹ thuật, giới hạn của nhà cung cấp (Cloudinary 10MB).
- Công thức khuyến mãi: đã quản lý bằng CRUD khuyến mãi.

## Hệ quả

- **Tích cực:**
  - Đổi giá, phí, thời hạn, ngưỡng không cần deploy.
  - Có lịch sử ai đổi gì lúc nào (`system_setting_audits`).
  - App hiển thị đúng giá server áp dụng.
  - Chặn được lỗ hổng khách tự đặt `totalPrice` khi tạo đơn.
- **Tiêu cực / đánh đổi chấp nhận:**
  - Mỗi service thêm một migration.
  - Thay đổi lan tới instance khác sau tối đa 30s.
  - Admin nhập sai trong giới hạn min/max vẫn có hiệu lực ngay ⇒ trang admin phải xác nhận trước khi lưu.
- **Việc phải làm theo sau:**
  - Ràng buộc chéo giữa các quy tắc: bậc phạt warning ≤ restricted ≤ suspended; `app.locker.reserved-ttl-hours` ≥ `app.order.auto-cancel-hours`.
  - Phân quyền chi tiết hơn ADMIN nếu cần.
