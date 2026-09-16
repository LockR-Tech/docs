# STATUS — Lock.R

> **Nguồn sự thật duy nhất về tiến độ dự án.** Người và agent đọc file này **đầu tiên**, cập nhật nó **cuối cùng** trong mỗi phiên làm việc. Giao thức: [AGENTS.md](AGENTS.md).

| | |
|---|---|
| **Cập nhật lần cuối** | 2026-09-16 |
| **Người cập nhật** | Claude Code — merge toàn bộ nhánh vào `main`; backend chờ deploy vì hết quota Actions |
| **Tổng tiến độ 4 luồng** | **42,5 %** |

## 0. Mốc code đã rà soát

Mọi con số bên dưới đúng với các commit này. Trước khi tin STATUS, kiểm tra xem code đã đi xa hơn chưa (xem [AGENTS.md § Kiểm tra độ tươi](AGENTS.md#1-bắt-đầu-phiên)).

| Repo | Commit đã rà soát | Nhánh |
|---|---|---|
| [backend](https://github.com/LockR-Tech/backend) | `705c556` | `main` |
| [frontend](https://github.com/LockR-Tech/frontend) | `e1b9a73` | `main` |
| [mobile](https://github.com/LockR-Tech/mobile) | `5890184` | `main` |
| [iot](https://github.com/LockR-Tech/iot) | `927b057` | `main` |
| [legal](https://github.com/LockR-Tech/legal) | `87ad342` | `main` |

## 1. Tiến độ theo luồng

| Luồng | Tiến độ | Một dòng tình trạng | Chi tiết |
|---|---:|---|---|
| **L1** Giao hàng drone → PIN → nhận hàng | **60 %** | Chạy trọn vẹn **chỉ ở chế độ DEMO** (bộ giả lập đẩy chặng bay). Ở STANDARD đơn kẹt tại LAUNCHING, drone kẹt IN_FLIGHT. | [flow-1](02-flows/flow-1-drone-delivery.md) |
| **L2** Thuê tủ gửi hàng → chuyển mã → người nhận lấy | **65 %** | Tạo đơn, giữ ô, mở tủ bằng mã chạy được. Nhận bằng mã ở kiosk **không hoàn tất đơn**; không gửi mã cho người nhận chưa có tài khoản; app có bug xác nhận sai id. | [flow-2](02-flows/flow-2-locker-send.md) |
| **L3** Vai trò · quản lý drone · bảo trì | **45 %** | Có 4 vai trò và màn hình riêng, nhưng **lỗ hổng phân quyền nghiêm trọng**; ticket và tài sản lệch trạng thái; không tự phát hiện hỏng từ IoT. | [flow-3](02-flows/flow-3-roles-maintenance.md) |
| **L4** RAG hỏi đáp tài liệu nội bộ | **0 %** | Chưa có dòng code nào. Đã có kiến trúc đề xuất và danh sách tài liệu nguồn. | [flow-4](02-flows/flow-4-rag-assistant.md) |

**Cách tính:** mỗi luồng có checklist 8–10 hạng mục; DONE = 1 · PARTIAL = 0,5 · MISSING = 0. % luồng = tổng điểm / số hạng mục. Tổng dự án = trung bình cộng 4 luồng (trọng số bằng nhau): (60 + 65 + 45 + 0) / 4 = **42,5 %**. Chỉ được đổi % khi đổi checklist trong file luồng, kèm bằng chứng `file:line`.

## 2. 🔴 Rủi ro chặn production — xử lý trước mọi tính năng

| ID | Rủi ro | Vị trí | Hậu quả |
|---|---|---|---|
| **SEC-01** | JWT secret production là **giá trị mặc định hardcode** | `backend/docker-compose.yml:66,120` (compose không đọc `.env` cho biến này) | Ai biết chuỗi mặc định giả được token ADMIN. **Code đã vá** ([backend #10](https://github.com/LockR-Tech/backend/pull/10)): compose đọc `.env` và dừng khi thiếu. Secret đã đặt trên VM (16/09), code đã merge vào `main`. **Chưa đóng** cho tới khi DEPLOY — lần deploy đó làm mọi người dùng bị đăng xuất. |
| **SEC-02** | Tự nâng quyền ADMIN | `PUT /api/users/{id}` nhận `roles` từ mọi JWT — `user-service/…/UserController.java:36`, `UserProfileService.java:150-151` | Khách hàng bất kỳ tự thành ADMIN, vào được web quản trị. |
| **SEC-03** | Đổi trạng thái đơn / thanh toán không kiểm soát | `PATCH /api/orders/{id}/status` (`OrderController.java:75`), `POST …/checkout` (`:115`), `PATCH /api/payments/{id}/status` + CASH tự hoàn tất (`PaymentService.java:152`) | Hoàn tất/huỷ đơn người khác, giải phóng ô đang có hàng, tự đánh dấu đã thanh toán. |
| **SEC-04** | MQTT dùng broker **công khai**, không xác thực, không TLS | `iot-service/…/application.yml:77` → `tcp://broker.hivemq.com:1883` | Ai cũng publish được lệnh mở tủ vào topic `cabinet/{id}/command/open`. |
| **SEC-05** | Lộ PIN qua IDOR | `GET /api/notifications/user/{userId}` (`NotificationController.java:105`), `GET /api/orders/{id}` trả `pinCode`, `GET /api/orders/pin/{pin}` dò PIN | Lấy PIN mở tủ của người khác. |
| **SEC-06** | Báo hỏng/giả trạng thái IoT tuỳ ý | `POST /api/boxes/{id}/fault` mọi ô, `POST /api/iot/device-status` · `/box-status` mọi JWT | Khoá ô hàng loạt, giả thiết bị online/offline. |
| **SEC-07** | OTP email ghi log dạng rõ | `auth-service/…/EmailOtpService.java:99` | Ai đọc log là đăng nhập được. **Code đã vá** ([backend #10](https://github.com/LockR-Tech/backend/pull/10)): bỏ mã khỏi log, email ghi dạng che bớt. Đã merge vào `main`; đóng khi deploy. |
| **SEC-08** | Token Cloudflare (quyền Edit Workers) từng bị dán vào lịch sử chat khi nạp secret | GitHub secrets `CLOUDFLARE_API_TOKEN` của `frontend`, `mobile` | Ai có lịch sử chat deploy đè được admin web, landing, mobile web. Tạo token mới → nạp lại → xoá token cũ. |

## 3. Đang làm

> 📌 **Bàn giao đầy đủ: [handoff/2026-09-16-trang-thai-day-du-va-viec-con-lai.md](handoff/2026-09-16-trang-thai-day-du-va-viec-con-lai.md)** — đọc file đó trước nếu bạn vừa vào dự án hoặc đổi máy.

**Không còn việc nào đang code dở.** Mọi nhánh đã merge vào `main`. Hai nút thắt là thao tác vận hành, không phải lập trình:

| Nút thắt | Trạng thái | Ai làm |
|---|---|---|
| **GitHub Actions hết quota** (2.000/2.000 phút, gói Free, reset ~2026-10-01) | Mọi CI và deploy đỏ sau 2–5 giây. Nguyên nhân gốc đã sửa ở `999d48f`, nhưng phải chờ reset hoặc nâng spending limit | Chủ dự án |
| **backend `main` đi trước production 4 commit** | `main` `569d323` · production `980f4fd`. Deploy được ngay khi Actions sống lại; lần deploy đó **làm mọi người dùng bị đăng xuất** (đổi JWT secret) | Chủ dự án |

| Khoá còn thiếu trên VM | Thiếu thì sao |
|---|---|
| `CLOUDINARY_URL` | API ảnh trả 503 — ảnh phiếu sự cố, avatar, ảnh cửa hàng không upload được |
| `APP_SMS_TWILIO_FROM_NUMBER` | Có SID + Auth Token rồi, thiếu số gửi ⇒ SMS chỉ ghi log |
| `SPRING_MAIL_*` · `FIREBASE_CREDENTIALS_JSON` | Chưa kiểm chứng; thiếu thì mất kênh email và push |

Cách lấy và nạp: [cau-hinh-dich-vu-ngoai.md](04-engineering/cau-hinh-dich-vu-ngoai.md).

## 4. Việc tiếp theo — theo thứ tự ưu tiên

1. **Gỡ nút thắt Actions** rồi **deploy backend** — SEC-01 và SEC-07 đã vá trong code trên `main` nhưng chỉ đóng khi deploy xong. _(rất gấp)_
2. **Nạp khoá còn thiếu trên VM** (Cloudinary, số Twilio, SMTP, Firebase) — [runbook](04-engineering/cau-hinh-dich-vu-ngoai.md).
3. **SEC-02 · SEC-03 · SEC-05 · SEC-06** Khoá API theo chủ sở hữu + vai trò ở service, không chỉ ở gateway — [F3-G01](02-flows/flow-3-roles-maintenance.md).
4. **SEC-04** Broker MQTT riêng có xác thực + TLS trong `docker-compose.yml`.
5. **F2-G11** Sửa 3 bug mobile chặn demo luồng 2 (id payment/order, nút mở tủ, locker id truyền như store id). _(nhỏ)_
6. **F2-G01 = F1-G05** Hoàn tất đơn phía server khi người nhận mở ô bằng mã ở kiosk. _(dùng chung cho L1 và L2)_
7. **F1-G01 · F1-G02** Tiến trình bay thật cho STANDARD + sửa guard mission (accept lại khi đang bay, 1 drone 2 đơn).
8. **F3-G02 · F3-G03** Nhất quán ticket ↔ tài sản; IoT tự báo offline/hỏng.
9. **F4-G01 → F4-G04** Khởi động RAG: pgvector, `assistant-service`, ingest, ask API.

## 5. Đã xong gần đây

| Ngày | Việc | Liên kết |
|---|---|---|
| 2026-09-16 | **Vá SEC-01 và SEC-07 bằng code**: JWT secret ra `.env` (cả 3 service xác thực JWT — notification-service trước đó chưa hề được truyền biến), bỏ mã OTP khỏi log. Khởi tạo Firebase để push thật sự gửi. Giảm tiêu thụ Actions của repo backend. **Đã merge, chờ deploy.** | [backend #10](https://github.com/LockR-Tech/backend/pull/10) · [#11](https://github.com/LockR-Tech/backend/pull/11) |
| 2026-09-16 | **F2-G03**: gửi mã mở tủ cho người nhận chưa có tài khoản qua SMS (Twilio) và email (SMTP dùng chung auth-service); app nhập email người nhận, hiện lịch sử trạng thái và địa điểm tủ trong chi tiết đơn. **Đã merge, chờ deploy.** | [backend #9](https://github.com/LockR-Tech/backend/pull/9) · [mobile #6](https://github.com/LockR-Tech/mobile/pull/6) · [hợp đồng](01-overview/receiver-pickup-code.md) |
| 2026-09-16 | **F2-G08 (phần web)**: `/admin/orders`, `/admin/payments`, `/admin/revenue` dùng dữ liệu thật đồng bộ với app khách — đủ trường, enum đúng bộ backend sinh ra, thời gian `HH:mm:ss dd/MM/yyyy` giờ Việt Nam. Bỏ toàn bộ dữ liệu giả và delta ghi cứng. Merge `43e5d00`, deploy Cloudflare **xanh**. Chưa thử với token ADMIN thật ⇒ xem mục 2 của bàn giao. | [frontend #7](https://github.com/LockR-Tech/frontend/pull/7) · [hợp đồng API](01-overview/admin-reporting-api.md) · [bàn giao](handoff/2026-09-16-bao-cao-admin-web-va-mobile-con-lai.md) |
| 2026-09-16 | API báo cáo admin phía backend: tìm kiếm/chi tiết đơn, tìm kiếm/chi tiết/hoàn tiền/ví/thống kê thanh toán, 8 endpoint doanh thu theo tiền thực thu. Merge `c66a510`, `980f4fd`, đã lên production. | [backend #7](https://github.com/LockR-Tech/backend/pull/7) · [#8](https://github.com/LockR-Tech/backend/pull/8) |
| 2026-09-16 | Quy tắc nghiệp vụ cấu hình trên admin (ADR-0005): `system_settings` cho 7 service, trang `/admin/settings`, mobile đọc giá/giờ/mốc nạp từ server. | [ADR-0005](adr/0005-quy-tac-nghiep-vu-cau-hinh-tren-admin.md) · [hợp đồng](01-overview/business-settings.md) |
| 2026-09-13 | Chuyển 5 repo sang org `LockR-Tech` (snapshot sạch), nguồn deploy chính thức là org; tắt workflow deploy ở repo cá nhân cũ | [ADR-0003](adr/0003-snapshot-sach-khi-chuyen-org.md) |
| 2026-09-13 | Tạo repo `docs`, chuẩn GitHub Flow + Conventional Commits, rà soát 4 luồng, 5 sơ đồ A4 | [ADR-0001](adr/0001-github-flow-main-la-production.md) · [ADR-0002](adr/0002-docs-as-code-repo-trung-tam.md) |

## 6. Blocker & câu hỏi mở

| # | Nội dung | Cần ai quyết |
|---|---|---|
| Q1 | Org gói **Free** + repo private ⇒ **không bật được branch protection / rulesets**. Luật GitHub Flow hiện chỉ thực thi bằng quy ước + PR template. Nâng GitHub Team để bắt buộc review trước khi merge? | Chủ dự án |
| Q2 | ~~Nhà cung cấp SMS cho F2-G03~~ — chốt **Twilio** (bản dùng thử, đủ để demo; chỉ gửi được tới số đã xác minh trong console). **Còn chờ**: nạp `APP_SMS_TWILIO_*` lên VM, và quyết có nâng lên tài khoản trả phí trước khi chạy thật không. LLM + embedding cho L4 (cần hỗ trợ tiếng Việt) vẫn chưa chọn. | Chủ dự án |
| Q3 | Drone thật giao tiếp qua MAVLink hay MQTT? Quyết định kiến trúc cho F1-G01 | Nhóm drone |
