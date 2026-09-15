# Quy tắc nghiệp vụ cấu hình trên admin

> Quyết định: [ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md). Đây là **hợp đồng API** cho backend, admin web (trang `/admin/settings`) và mobile. Danh sách key đầy đủ của từng scope luôn lấy từ API (`GET /api/admin/settings/{scope}`) — bảng ở mục 4 là bản tóm tắt tại thời điểm viết.

## 1. Cách hoạt động

- Mỗi service khai báo quy tắc của mình trong một `SettingsCatalog` (key, nhóm, nhãn, mô tả, kiểu, mặc định, min/max, đơn vị, giá trị cho phép, công khai).
- Giá trị admin sửa lưu ở bảng `system_settings` trong schema của service; mọi lần sửa ghi `system_setting_audits`.
- Đọc: **DB → property/biến môi trường cùng tên key → mặc định catalog**. Cache 30 giây; instance nhận lệnh sửa làm mới ngay. DB lỗi ⇒ giữ giá trị cũ, nghiệp vụ không dừng.
- Lưu theo lô: một giá trị sai ⇒ không giá trị nào được ghi.
- Service bật tính năng bằng `app.settings.scope: <scope>`.

## 2. API

Mọi phản hồi bọc `ApiResponse { success, code, message, data, errors }`.

| Method · Path | Quyền | Body | `data` |
|---|---|---|---|
| `GET /api/admin/settings/{scope}` | ADMIN | — | `SettingView[]` |
| `PUT /api/admin/settings/{scope}` | ADMIN | `{ "values": { "<key>": <giá trị> } }` | `SettingView[]` (toàn bộ, đã làm mới) |
| `DELETE /api/admin/settings/{scope}/{key}` | ADMIN | — | `SettingView[]` (key vừa khôi phục mặc định) |
| `GET /api/admin/settings/{scope}/audits?key=&limit=100` | ADMIN | — | `SettingAuditView[]` mới nhất trước |
| `GET /api/settings/{scope}/public` | Không cần đăng nhập | — | `{ "<key>": giá trị đã ép kiểu }` chỉ quy tắc công khai |

`scope` ∈ `order`, `locker`, `payment`, `iot`, `auth`, `loyalty`, `store` (gateway định tuyến tới service tương ứng).

**SettingView**

```json
{ "scope": "order", "key": "app.order.send-base-fee", "group": "Giá & phí", "label": "Phí gửi hàng qua tủ",
  "description": "Giá mỗi đơn gửi hàng (SEND). Áp dụng cho đơn tạo sau khi lưu.",
  "type": "INTEGER", "value": "15000", "defaultValue": "15000", "overridden": false,
  "min": "0", "max": "100000000", "unit": "VND", "allowedValues": [], "publicValue": true,
  "updatedByUserId": null, "updatedAt": null }
```

| `type` | Dạng `value` | Ví dụ PUT |
|---|---|---|
| `INTEGER` | `"15000"` | `15000` hoặc `"15000"` |
| `DECIMAL` | `"12.5"` | `12.5` |
| `BOOLEAN` | `"true"` / `"false"` | `true` |
| `STRING` | chuỗi, có thể rỗng; `allowedValues` khác rỗng ⇒ phải thuộc danh sách | `"CASH,WALLET"` |
| `INTEGER_LIST` | `"2,4,8"` | `[2, 4, 8]` hoặc `"2,4,8"` |

**SettingAuditView**: `{ id, key, oldValue, newValue, actorUserId, changedAt }` — `newValue = null` nghĩa là khôi phục mặc định.

**Lỗi**: `400 SETTING_INVALID` (message nêu nhãn + key + lý do), `400 SETTINGS_EMPTY`, `404 SETTING_UNKNOWN`.

**Thời gian**: `updatedAt`, `changedAt` là `LocalDateTime` không kèm múi giờ, theo **UTC** (container chạy UTC). Client hiển thị `HH:mm:ss dd/MM/yyyy` giờ Việt Nam.

## 3. Quy ước client

- Admin web dựng giao diện hoàn toàn từ `SettingView` — không hardcode key; xác nhận danh sách thay đổi (cũ → mới) trước khi lưu.
- Mobile đọc `/api/settings/{scope}/public`, cache, và **giữ giá trị mặc định cũ khi API lỗi**. Giá hiển thị trên app chỉ để xem; server luôn tự tính tiền.

## 4. Quy tắc theo scope (tóm tắt)

| Scope | Nhóm | Quy tắc |
|---|---|---|
| order | Giá & phí | Phí gửi hàng, phí drone, giá thuê ô STANDARD/XL mỗi giờ, phí lưu trữ mỗi món, phí quá hạn mỗi giờ, trần phí quá hạn (VND và %) |
| order | Thời hạn & tự động hoá | Hạn lấy hàng gửi, hạn lấy hàng drone, tự huỷ đơn chưa bỏ hàng, nhả ô quá hạn (0 = tắt), khoảng cách nhắc quá hạn |
| order | Thuê tủ | Giờ thuê tối thiểu/tối đa/mặc định, nút chọn nhanh, gia hạn mặc định/tối đa |
| order | Thanh toán · Drone | Bắt buộc thanh toán trước khi bỏ hàng; drone DEMO bật/tắt, user được dùng, thời gian mỗi chặng; pin tối thiểu nhận đơn; khối lượng kiện mặc định |
| locker | Bảo trì & SLA | SLA, số phiếu trễ bị chặn nhận việc, bậc phạt cảnh báo/hạn chế/đình chỉ, bắt buộc ảnh nghiệm thu, giới hạn ảnh mỗi lần/mỗi phiếu |
| locker | Ô tủ · Drone | Giữ ô RESERVED, kích thước ô hiển thị cho app; pin thấp chặn cất cánh |
| payment | Nạp ví · Phương thức | Nạp tối thiểu/tối đa/mặc định, mốc nạp nhanh; phương thức bật; tiền mặt tự hoàn tất |
| iot | Mở tủ & chống dò mã | Số lần sai trước khi khoá, thời gian khoá, thời gian chờ tủ phản hồi, thời gian cửa mở |
| auth | Xác thực | Hạn OTP, độ dài OTP, hạn token tạm (đăng ký, 2FA admin) |
| loyalty | Hạng & phần thưởng | Điểm lên Silver/Gold/Platinum, số tem đổi thưởng, điểm đổi thưởng, số tem mỗi lần |
| store | Tìm cửa hàng | Bán kính tìm mặc định |

Không cấu hình trên admin: tập trạng thái cho phép hành động, bí mật/TTL JWT, cron và timeout kỹ thuật, giới hạn nhà cung cấp — xem ADR-0005.
