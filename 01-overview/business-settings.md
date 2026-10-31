# Quy tắc nghiệp vụ cấu hình trên admin

> Quyết định: [ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md). Đây là **hợp đồng API** cho backend, admin web (trang `/admin/settings` và `/admin/services`) và mobile. Danh sách key đầy đủ của từng scope luôn lấy từ API (`GET /api/admin/settings/{scope}`) — bảng ở mục 4 là bản tóm tắt tại thời điểm viết.

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
  "min": "0", "max": "100000000", "unit": "VND", "allowedValues": [], "allowedItems": [], "publicValue": true,
  "updatedByUserId": null, "updatedAt": null }
```

| `type` | Dạng `value` | Ví dụ PUT |
|---|---|---|
| `INTEGER` | `"15000"` | `15000` hoặc `"15000"` |
| `DECIMAL` | `"12.5"` | `12.5` |
| `BOOLEAN` | `"true"` / `"false"` | `true` |
| `STRING` | chuỗi, có thể rỗng; `allowedValues` khác rỗng ⇒ phải thuộc danh sách; `allowedItems` khác rỗng (backend #65) ⇒ danh sách cách nhau bởi dấu phẩy, **mỗi phần tử** phải thuộc `allowedItems` (sai ⇒ `SETTING_INVALID`; giá trị đã lưu còn phần tử nay không hỗ trợ thì khi đọc bỏ phần tử đó) | `"CASH,WALLET"` |
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
| order | Giá & phí | Phí gửi hàng, phí drone cơ bản và phụ phí mỗi nấc khối lượng, giá thuê ô STANDARD/XL mỗi giờ, phí lưu trữ mỗi món, phí quá hạn mỗi giờ, trần phí quá hạn (VND và %) |
| order | Thời hạn & tự động hoá | Hạn lấy hàng gửi, hạn lấy hàng drone, tự huỷ đơn chưa bỏ hàng, nhả ô quá hạn (0 = tắt), khoảng cách nhắc quá hạn |
| order | Thuê tủ | Giờ thuê tối thiểu/tối đa/mặc định, nút chọn nhanh, gia hạn mặc định/tối đa, phí ở quá giờ thuê theo % giá thuê loại ô (`app.order.rental-overtime-rate-percent`, mặc định 100 %, tối thiểu 100 % — ở quá giờ không rẻ hơn gia hạn; trần phí quá hạn chỉ áp cho đơn gửi hàng) |
| order | Thanh toán · Drone | Bắt buộc thanh toán trước khi bỏ hàng; drone DEMO bật/tắt, user được dùng, thời gian mỗi chặng; pin tối thiểu nhận đơn; khối lượng kiện mặc định, tải tối đa, khối lượng cơ bản, nấc khối lượng, các mức khách chọn, sai số cân cho phép |
| locker | Bảo trì & SLA | SLA, số phiếu trễ bị chặn nhận việc, bậc phạt cảnh báo/hạn chế/đình chỉ, bắt buộc ảnh nghiệm thu, giới hạn ảnh mỗi lần/mỗi phiếu |
| locker | Ô tủ · Drone | Giữ ô RESERVED, kích thước ô hiển thị cho app; pin thấp chặn cất cánh |
| payment | Nạp ví · Phương thức | Nạp tối thiểu/tối đa/mặc định, mốc nạp nhanh (app khách không còn đọc từ 2026-10-31 — ví đã gỡ khỏi app); phương thức bật (`app.payment.enabled-methods`: chỉ nhận `CASH`, `WALLET`, `SEPAY`, mặc định `SEPAY` từ backend #65); tiền mặt tự hoàn tất |
| payment | Giả lập thanh toán (test) | Hiện nút "Giả lập thanh toán" trên màn VietQR của app và kiosk (`app.payment.simulation-enabled`, mặc định **tắt**) và danh sách user id được dùng (`app.payment.simulation-allowed-user-ids`, trống = mọi tài khoản). Bấm ⇒ `POST /api/payments/simulate` ghi nhận như webhook SePay (đủ hoặc một phần, mô tả `[Giả lập]`, mã giao dịch `SIMULATED-…`) — **chỉ bật khi test**, giao dịch giả lập vẫn tính như thật |
| iot | Mở tủ & chống dò mã | Số lần sai trước khi khoá, thời gian khoá, thời gian chờ tủ phản hồi, thời gian cửa mở |
| auth | Xác thực | Hạn OTP, độ dài OTP, hạn token tạm (đăng ký, 2FA admin) |
| order | Mã giảm giá | Số mã giảm giá tối đa mỗi đơn (`app.order.max-vouchers-per-order`, mặc định 1, 0 = tạm ngưng mã; > 1 thì chỉ mã "dùng kèm được" mới cộng dồn). Mã có thể gắn một tủ (`promotions.locker_id`) hoặc toàn hệ thống; đơn drone xét theo tủ gửi. Mã có **giá đổi bằng điểm** (`promotions.points_cost` > 0, nhập ở form khuyến mãi) là voucher đổi điểm: không hiện ở trang Ưu đãi, khách đổi trong "Ưu đãi của tôi" → tab Đổi điểm (`POST /api/promotions/{id}/exchange`), chỉ người đang giữ voucher (đã đổi, chưa dùng) áp được mã; dùng xong mới đổi lại được |
| loyalty | Hạng & phần thưởng | Điểm lên Silver/Gold/Platinum (so với **tổng điểm đã tích** `lifetime_points`, tiêu điểm hay đổi voucher không tụt hạng; mặc định 50.000 / 200.000 / 500.000), số tem đổi thưởng, điểm đổi thưởng, số tem mỗi lần; số đồng cho 1 điểm khi tích (`app.loyalty.vnd-per-point`, mặc định **10 đ** = tích 10 % số tiền, tích khi đơn hoàn tất trên tiền khách thật sự trả) |
| loyalty | Dùng điểm thanh toán | Bật/tắt (`app.loyalty.redeem-enabled`), giá trị 1 điểm khi dùng (`app.loyalty.redeem-vnd-per-point`, mặc định **1 đ**), % tối đa của đơn sau mã giảm giá (`app.loyalty.redeem-max-percent`, mặc định 50), số điểm tối thiểu mỗi lần (`app.loyalty.redeem-min-points`, mặc định 1.000). Điểm trả lại khi đơn huỷ/hoàn tiền. Từ loyalty V5 (2026-10-24) **1 điểm = 1 đ**: migration nhân mọi số điểm cũ và mốc hạng với 100 (giá trị tiền khách đang có giữ nguyên); app hiện điểm được cộng ở chi tiết đơn dạng `+700đ (10%)` |
| store | Tìm cửa hàng | Bán kính tìm mặc định |

Không cấu hình trên admin: tập trạng thái cho phép hành động, bí mật/TTL JWT, cron và timeout kỹ thuật, giới hạn nhà cung cấp — xem ADR-0005.

## 7. Trang `/admin/services` — quản lý dịch vụ

Lock.R bán **ba dịch vụ**, và chúng **không phải bản ghi trong cơ sở dữ liệu**: mỗi dịch
vụ là một loại đơn (`OrderType`) mà giá và quy tắc nằm ở scope `order` của bảng này.

| Dịch vụ | `OrderType` | Key giá chính |
|---|---|---|
| Gửi hàng qua tủ | `SEND` | `app.order.send-base-fee` |
| Thuê ô theo giờ | `RENTAL` | `app.order.rental-rate-standard` |
| Giao hàng bằng drone | `DRONE_DELIVERY` | `app.order.drone-delivery-fee` |

Vì vậy trang `/admin/services` **sửa quy tắc và xem hiệu quả**, không thêm/xoá dịch vụ.
Nó chỉ dùng hai API đã có, không có endpoint riêng:

- `GET`/`PUT /api/admin/settings/order` — giá và quy tắc (chính hợp đồng này);
- `GET /api/admin/revenue/by-service` — doanh thu, số đơn, tỉ trọng theo kỳ
  ([hợp đồng báo cáo](admin-reporting-api.md) § 3.4).

> ⚠️ `GET /api/admin/services` **không tồn tại** (404, gateway không có route). Trang cũ
> gọi endpoint đó nên chưa bao giờ hiển thị được gì — tàn dư từ thời sản phẩm còn là
> dịch vụ giặt ủi. Đừng dựng lại theo hướng đó.

Web chọn và xếp nhóm key theo dịch vụ ở `frontend/fe/src/pages/Admin/services/service-catalog.ts`;
tên key chép từ `OrderSettingsCatalog.java`. Backend đổi tên key thì trang chỉ mất dòng
tương ứng, không vỡ — vì metadata vẫn lấy từ API.
