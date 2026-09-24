# Gửi mã mở tủ cho người nhận — SMS & email

Hợp đồng kênh thông báo cho người **chưa có tài khoản Lock.R**. Liên quan: gap
[F2-G03](../02-flows/flow-2-locker-send.md), câu hỏi Q2 trong [STATUS](../STATUS.md).

## 1. Vấn đề

Trước đây mã mở tủ chỉ tới được người nhận **đã có tài khoản**: `OrderService.notifyParcelReadyForReceiver`
tra số điện thoại trong user-service, trùng một tài khoản thì đẩy thông báo trong app.
Không trùng ⇒ **không gửi gì**, người gửi phải tự copy mã chuyển tay. Vì phần lớn
người nhận không phải khách Lock.R, đây là điểm hỏng thường gặp nhất của luồng gửi hàng.

## 2. Kênh mới

`notification-service` nhận thêm một endpoint nội bộ:

```
POST /internal/notifications/guest
```

```json
{
  "phone": "0901234567",
  "email": "an@example.com",
  "subject": "Mã mở tủ Lock.R cho đơn ORD-20260915-K3F9QZ",
  "smsMessage": "Lock.R: Ban co kien hang ORD-… tai Tu Le Loi (1 Le Loi, Q1). Ma mo tu: 482913. Han lay: 09:00:00 16/09/2026.",
  "emailBody": "…"
}
```

- `phone` và `email` **đều tuỳ chọn** nhưng phải có ít nhất một.
- `emailBody` trống ⇒ dùng `smsMessage`.
- `email` sai định dạng ⇒ `400 VALIDATION_ERROR`.

Trả về:

```json
{ "smsSent": true, "emailSent": false, "smsChannelAvailable": true, "emailChannelAvailable": false }
```

`*Sent` = lần gửi này có đi hay không. `*ChannelAvailable` = kênh **có được cấu hình**
hay không — hai thứ khác nhau, để phân biệt "gửi hỏng" với "chưa bật bao giờ".

`/internal/**` bị gateway chặn ra ngoài. Nếu không, ai cũng nhắn tin được dưới tên Lock.R.

## 3. Nhà cung cấp

| Kênh | Bản chạy thật | Khi thiếu cấu hình |
|---|---|---|
| SMS | **Twilio** Messages API, gọi thẳng HTTP | Bản chỉ ghi log, `isReal() = false` |
| Email | **SMTP dùng chung với auth-service** (đang gửi OTP đăng nhập) | Bản chỉ ghi log |

Thiếu khoá thì service **vẫn khởi động** — máy lập trình và CI không cần khoá thật.

Số điện thoại được chuẩn hoá sang E.164 nên `0901234567`, `090 123-4567`, `84901234567`
và `+84901234567` đều ra `+84901234567`. Số đã có dấu `+` giữ nguyên để không phá số nước ngoài.

> ⚠️ **Tài khoản Twilio dùng thử** chỉ gửi được tới số đã xác minh trong console và
> chèn thêm một dòng quảng cáo vào tin. Nâng lên tài khoản trả phí là gửi được mọi
> số, **không phải sửa dòng code nào**.

## 4. Bảo mật

- **Log không bao giờ ghi nội dung tin nhắn** — tin chứa mã mở tủ, ai đọc được log là
  mở được tủ người khác. Đây đúng là rủi ro [SEC-07](../STATUS.md) đang có với OTP email.
- Số điện thoại và email ghi dạng che bớt: `090****567`, `a***@example.com`.
- Khoá nhà cung cấp là **secret**, chỉ nạp qua biến môi trường. Tài liệu chỉ ghi **tên** biến.

## 5. Biến môi trường

Đặt trên VM (`docker-compose.yml` đã khai báo sẵn với mặc định rỗng):

| Biến | Ý nghĩa |
|---|---|
| `APP_SMS_TWILIO_ACCOUNT_SID` | Account SID trong Twilio console |
| `APP_SMS_TWILIO_AUTH_TOKEN` | Auth Token |
| `APP_SMS_TWILIO_FROM_NUMBER` | Số gửi Twilio cấp, dạng E.164 |
| `SPRING_MAIL_HOST` | Bắt buộc — trống là kênh email tắt, `emailChannelAvailable=false` |
| `SPRING_MAIL_*` còn lại, `APP_MAIL_FROM` | Giống khối `auth-service` đã có |

Khác với SMS, khối `notification-service` trong compose để **trống** cả `SPRING_MAIL_HOST` và
`SPRING_MAIL_USERNAME`. Trước đây hai biến này mặc định `localhost` / `noreply@laundry.test`,
mà compose không chạy mail catcher nào, nên `emailChannelAvailable` luôn báo `true` kể cả khi
máy chủ chưa hề cấu hình SMTP — đúng thứ trường này sinh ra để phân biệt.

Thiếu **bất kỳ** giá trị nào trong ba biến Twilio ⇒ rơi về bản ghi log.

## 6. Quy tắc bật/tắt (admin cấu hình)

Bật/tắt kênh là quy tắc nghiệp vụ nên nằm trên `/admin/settings` theo
[ADR-0005](../adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md), nhóm **Thông báo cho người nhận**:

| Key | Mặc định | Ý nghĩa |
|---|---|---|
| `app.order.receiver-notify-sms` | `true` | Nhắn mã tới số điện thoại người nhận |
| `app.order.receiver-notify-email` | `true` | Gửi mã tới email người nhận |

Bật mà máy chủ chưa nạp khoá thì vẫn không gửi được — admin bật là **cho phép**, không phải **bảo đảm**.

## 7. Luồng khi người gửi bỏ hàng

`PUT /api/orders/{id}/confirm` ⇒ đơn sang `STORING`, phát PIN nhận hàng, rồi thử **cả ba**
đường (không dừng ở đường đầu thành công — mã không tới nơi là hỏng cả lượt nhận hàng):

1. thông báo trong app, nếu số điện thoại trùng một tài khoản;
2. SMS tới số người gửi đã nhập;
3. email, nếu người gửi có nhập.

Sau đó báo lại cho **người gửi**: gửi được thì *"Pickup code sent to the receiver"*, không
kênh nào tới nơi thì *"We could not reach the receiver — please share the PIN with them yourself"*.
Người gửi chỉ chủ động chuyển mã nếu biết là cần.

Tin nhắn kèm **tên và địa chỉ tủ** (tra qua `/internal/lockers/batch`; tra hỏng thì rơi về
`tủ #id`) và hạn lấy hàng **đổi sang giờ Việt Nam** — container chạy UTC.

## 8. Trường mới trên đơn

`POST /api/orders/send` nhận thêm `receiverEmail` (tuỳ chọn, kiểm định dạng email).
Cột `orders.receiver_email` cho phép NULL (migration `V12__receiver_email.sql`) nên
đơn cũ và client cũ không bị ảnh hưởng.

`OrderResponse` **chưa** trả thông tin người nhận — phần này vẫn nằm trong gap F2-G03.

## 9. Việc chưa làm

- `OrderResponse` trả thông tin người nhận cho app.
- Gửi lại mã khi người nhận báo không nhận được.
- Uỷ quyền lấy hộ (`delegate`) hiện vẫn chỉ báo chủ đơn, chưa dùng kênh này.
- Đổi nhà cung cấp SMS: thêm một bản cài `SmsSender` và một nhánh trong `SmsChannelConfig`,
  không phải sửa nghiệp vụ.
