# Tóm tắt việc còn lại và vướng mắc — 16/09/2026

Bản ngắn để tiếp tục nhanh trên máy khác. Chi tiết đầy đủ:
[trạng thái đầy đủ](2026-09-16-trang-thai-day-du-va-viec-con-lai.md).

## 1. Vướng mắc đang chặn

| # | Vướng mắc | Hệ quả | Gỡ thế nào |
|---|---|---|---|
| 1 | **GitHub Actions hết quota** — 2.000/2.000 phút, gói Free, reset ~01/10/2026 | Mọi CI và deploy đỏ sau 2–5 giây, không kèm log | Chờ reset, hoặc nâng spending limit ở Settings → Billing |
| 2 | **Ba repo đều đi trước production** | Code đã merge nhưng chưa chạy thật | Deploy sau khi gỡ (1) |
| 3 | **Thiếu khoá dịch vụ ngoài trên VM** | SMS, email, push chưa gửi được | Chủ dự án lấy khoá — xem §3 |

> ⚠️ Deploy backend **làm mọi người dùng bị đăng xuất** vì đổi JWT secret. Báo nhóm trước.

## 2. Việc còn lại, theo thứ tự ưu tiên

1. **Deploy backend** — đóng SEC-01 (JWT secret mặc định nằm trong repo) và SEC-07 (OTP ghi ra log). Code đã ở `main`, chỉ chờ quota. _(rất gấp)_
2. **Nạp khoá còn thiếu trên VM** — Twilio, SMTP, Firebase. Không cần Actions, làm được ngay. [runbook](../04-engineering/cau-hinh-dich-vu-ngoai.md)
3. **Kiểm chứng nghi vấn realtime** — compose đang chạy không truyền `APP_SECURITY_JWT_SECRET` cho `notification-service`, trong khi gateway và auth-service dùng giá trị trong `.env`. Nếu đúng thì STOMP **đang hỏng sẵn**, không phải chờ deploy mới hỏng. Chưa ai kiểm.
4. **SEC-08** Xoay token Cloudflare (từng bị dán vào lịch sử chat): tạo mới → nạp lại cả `frontend` và `mobile` → xoá token cũ.
5. **SEC-02 · SEC-03 · SEC-05 · SEC-06** Khoá API theo chủ sở hữu + vai trò ở từng service, không chỉ ở gateway.
6. **SEC-04** Broker MQTT riêng có xác thực + TLS (hiện dùng broker công khai — ai cũng gửi lệnh mở tủ được).
7. **Thử 3 trang báo cáo admin bằng token ADMIN thật** — dựng xong nhưng chưa ai đăng nhập kiểm tra.
8. **F2-G11 · F2-G01 · F1-G01 · F1-G02 · F3-G02 · F3-G03** — mô tả ở [STATUS.md §4](../STATUS.md).
9. **Hai PR cũ chưa xử lý**, không thuộc các phiên gần đây: [backend#1](https://github.com/LockR-Tech/backend/pull/1) và [docs#1](https://github.com/LockR-Tech/docs/pull/1) (nhắc tới mã `SEC-09` chưa có trong STATUS). Cần người hiểu bối cảnh xem lại.

## 3. Cần chủ dự án cung cấp

| Việc | Lấy ở đâu | Còn thiếu |
|---|---|---|
| **Twilio** | Console → Phone Numbers → Buy a number | Số gửi, Verified Caller ID cho số nhận, bật Geo Permissions cho Việt Nam. Account SID và Auth Token đã có. |
| **SMTP** | [Brevo](https://www.brevo.com) — 300 email/ngày miễn phí | SMTP login, master password, sender đã verify |
| **Firebase** | Console → Service accounts → Generate new private key | File JSON |

Cách nạp: [cau-hinh-dich-vu-ngoai.md](../04-engineering/cau-hinh-dich-vu-ngoai.md). Nạp bằng
Azure Run Command, **không cần SSH** — khoá SSH cá nhân hiện không vào được VM.

## 4. Repo so với production

| Repo | `main` | Đang chạy thật |
|---|---|---|
| backend | `569d323` | `980f4fd` — sau **4 commit** |
| frontend | `b1686f5` | `a1ca345` — sau **1 commit** |
| mobile | `b39d198` | chưa build lại |
| docs | `c0691ad` | — |

## 5. Đã xong — đừng làm lại

- **Lưu ảnh Cloudinary** ✅ 16/09 — 4 service xác nhận `Cloudinary media storage enabled`.
  Không cần deploy lại web hay mobile.
- Báo cáo admin, trang quản lý dịch vụ, bỏ `#id` khỏi admin + app, gửi mã mở tủ cho người
  nhận qua SMS/email: **đã merge**, chờ deploy.
- Mobile chạy được trên máy ảo. Bẫy đã gỡ: máy có Java 25 mà Android Gradle Plugin không
  hỗ trợ, báo lỗi khó hiểu `* What went wrong: 25.0.2`. Sửa bằng
  `flutter config --jdk-dir=C:\src\jdk-21`.
