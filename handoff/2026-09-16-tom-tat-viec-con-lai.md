# Tóm tắt việc còn lại và vướng mắc — 16/09/2026 (cập nhật chiều)

Bản ngắn để tiếp tục nhanh trên máy khác. Chi tiết đầy đủ:
[trạng thái đầy đủ](2026-09-16-trang-thai-day-du-va-viec-con-lai.md).

## 1. Vướng mắc

| # | Vướng mắc | Trạng thái | Gỡ thế nào |
|---|---|---|---|
| 1 | **Quota GitHub Actions** | ✅ **ĐÃ GỠ** — chuyển cả 6 repo sang **public**, Actions miễn phí không giới hạn | — |
| 2 | **Deploy backend** | ✅ **XONG** — deploy 569d323 thành công 09:58 (health 200 · public 200 · admin 401). Không ai bị đăng xuất | — |
| 3 | 🔴 **JWT + QR secret production đang công khai** | **MỞ** — hệ quả của việc backend public. Secret vẫn là chuỗi mặc định, ai đọc `docker-compose.yml` cũng ký được token ADMIN và mã QR mở tủ cho hệ thống thật | Chạy lệnh xoay secret trên VM (runbook §3/§5) — độc lập với deploy, sẽ đăng xuất mọi người |
| 4 | **Thiếu khoá dịch vụ ngoài trên VM** | MỞ — SMS, email, push chưa gửi được | Chủ dự án lấy khoá — xem §3 |

> ⚠️ Đánh đổi đã chọn: public để có Actions miễn phí, **chấp nhận secret công khai**. SEC-01
> chưa đóng. Phải xoay secret trước khi có người dùng thật.

## 2. Việc còn lại, theo thứ tự ưu tiên

1. **Xoay JWT + QR secret trên VM** (SEC-01) — giờ là rủi ro sống vì repo đã public. Lệnh sẵn trong runbook, chạy bằng Azure Run Command, không cần Actions. Sẽ đăng xuất mọi người. _(rất gấp)_
2. **Nạp khoá còn thiếu trên VM** — Twilio, SMTP, Firebase. Không cần Actions. [runbook](../04-engineering/cau-hinh-dich-vu-ngoai.md)
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

## 4. Trạng thái repo

Cả 6 repo (`backend`, `frontend`, `mobile`, `docs`, `iot`, `legal`) đã **public**.

| Repo | `main` | Đang chạy thật |
|---|---|---|
| backend | `569d323` | `569d323` ✅ khớp production |
| frontend | `b1686f5` | `a1ca345` — sau **1 commit**, deploy được (Actions đã free) |
| mobile | `b39d198` | chưa build lại |
| docs | cập nhật liên tục | — |

## 5. Đã xong — đừng làm lại

- **Deploy backend** ✅ 16/09 09:58 — `569d323` lên production, nghiệm thu health/public/admin đạt.
  Đóng SEC-07 (bỏ OTP khỏi log), khởi tạo Firebase, truyền JWT secret cho `notification-service`
  (sửa nghi vấn realtime STOMP). **SEC-01 vẫn mở** — secret là chuỗi mặc định, đang công khai.
- **Chuyển 6 repo sang public** ✅ 16/09 — gỡ nút thắt quota Actions.
- **Lưu ảnh Cloudinary** ✅ 16/09 — 4 service xác nhận `Cloudinary media storage enabled`.
  Không cần deploy lại web hay mobile.
- Báo cáo admin, trang quản lý dịch vụ, bỏ `#id` khỏi admin + app, gửi mã mở tủ cho người
  nhận qua SMS/email: **đã merge và deploy** lên production 16/09.
- Mobile chạy được trên máy ảo. Bẫy đã gỡ: máy có Java 25 mà Android Gradle Plugin không
  hỗ trợ, báo lỗi khó hiểu `* What went wrong: 25.0.2`. Sửa bằng
  `flutter config --jdk-dir=C:\src\jdk-21`.
