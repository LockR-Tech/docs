# STATUS — Lock.R

> **Nguồn sự thật duy nhất về tiến độ dự án.** Người và agent đọc file này **đầu tiên**, cập nhật nó **cuối cùng** trong mỗi phiên làm việc. Giao thức: [AGENTS.md](AGENTS.md).

| | |
|---|---|
| **Cập nhật lần cuối** | 2026-09-13 |
| **Người cập nhật** | BaoHuy-Dev — rà soát toàn bộ code 4 luồng (5 agent song song, đối chiếu `file:line`) |
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
| **SEC-01** | JWT secret production là **giá trị mặc định hardcode** | `backend/docker-compose.yml:66,120` (compose không đọc `.env` cho biến này) | Ai biết chuỗi mặc định giả được token ADMIN. Sửa xong phải xoay secret ⇒ mọi người dùng bị đăng xuất. |
| **SEC-02** | Tự nâng quyền ADMIN | `PUT /api/users/{id}` nhận `roles` từ mọi JWT — `user-service/…/UserController.java:36`, `UserProfileService.java:150-151` | Khách hàng bất kỳ tự thành ADMIN, vào được web quản trị. |
| **SEC-03** | Đổi trạng thái đơn / thanh toán không kiểm soát | `PATCH /api/orders/{id}/status` (`OrderController.java:75`), `POST …/checkout` (`:115`), `PATCH /api/payments/{id}/status` + CASH tự hoàn tất (`PaymentService.java:152`) | Hoàn tất/huỷ đơn người khác, giải phóng ô đang có hàng, tự đánh dấu đã thanh toán. |
| **SEC-04** | MQTT dùng broker **công khai**, không xác thực, không TLS | `iot-service/…/application.yml:77` → `tcp://broker.hivemq.com:1883` | Ai cũng publish được lệnh mở tủ vào topic `cabinet/{id}/command/open`. |
| **SEC-05** | Lộ PIN qua IDOR | `GET /api/notifications/user/{userId}` (`NotificationController.java:105`), `GET /api/orders/{id}` trả `pinCode`, `GET /api/orders/pin/{pin}` dò PIN | Lấy PIN mở tủ của người khác. |
| **SEC-06** | Báo hỏng/giả trạng thái IoT tuỳ ý | `POST /api/boxes/{id}/fault` mọi ô, `POST /api/iot/device-status` · `/box-status` mọi JWT | Khoá ô hàng loạt, giả thiết bị online/offline. |
| **SEC-07** | OTP email ghi log dạng rõ | `auth-service/…/EmailOtpService.java:99` | Ai đọc log là đăng nhập được. |
| **SEC-08** | Token Cloudflare (quyền Edit Workers) từng bị dán vào lịch sử chat khi nạp secret | GitHub secrets `CLOUDFLARE_API_TOKEN` của `frontend`, `mobile` | Ai có lịch sử chat deploy đè được admin web, landing, mobile web. Tạo token mới → nạp lại → xoá token cũ. |

## 3. Đang làm

| Việc | ID | Người / agent | Nhánh | PR | Bắt đầu |
|---|---|---|---|---|---|
| Lưu ảnh thật trên Cloudinary: ảnh phiếu sự cố (báo → xác nhận hiện trường → quá trình → nghiệm thu), avatar, ảnh cửa hàng, khuyến mãi | ADR-0004 · F3.08 | Claude Code (theo yêu cầu chủ dự án) | `feat/media-cloudinary-photos` (backend, frontend, mobile, docs) | docs #2 ✅ · backend #4 ✅ #3 ✅ · frontend #4 ⏳ · mobile #4 ⏳ — **tiếp tục theo [bàn giao](handoff/2026-09-15-luu-anh-cloudinary.md)** | 2026-09-15 |

## 4. Việc tiếp theo — theo thứ tự ưu tiên

1. **SEC-01** Đưa JWT secret ra biến môi trường, sinh secret mới trên VM, xoay khoá. _(nhỏ, rất gấp)_
2. **SEC-02 · SEC-03 · SEC-05 · SEC-06** Khoá API theo chủ sở hữu + vai trò ở service, không chỉ ở gateway — [F3-G01](02-flows/flow-3-roles-maintenance.md).
3. **SEC-04** Broker MQTT riêng có xác thực + TLS trong `docker-compose.yml`.
4. **F2-G11** Sửa 3 bug mobile chặn demo luồng 2 (id payment/order, nút mở tủ, locker id truyền như store id). _(nhỏ)_
5. **F2-G01 = F1-G05** Hoàn tất đơn phía server khi người nhận mở ô bằng mã ở kiosk. _(dùng chung cho L1 và L2)_
6. **F2-G03** Kênh gửi mã cho người nhận chưa có tài khoản (SMS/email).
7. **F1-G01 · F1-G02** Tiến trình bay thật cho STANDARD + sửa guard mission (accept lại khi đang bay, 1 drone 2 đơn).
8. **F3-G02 · F3-G03** Nhất quán ticket ↔ tài sản; IoT tự báo offline/hỏng.
9. **F4-G01 → F4-G04** Khởi động RAG: pgvector, `assistant-service`, ingest, ask API.

## 5. Đã xong gần đây

| Ngày | Việc | Liên kết |
|---|---|---|
| 2026-09-13 | Chuyển 5 repo sang org `LockR-Tech` (snapshot sạch), nguồn deploy chính thức là org; tắt workflow deploy ở repo cá nhân cũ | [ADR-0003](adr/0003-snapshot-sach-khi-chuyen-org.md) |
| 2026-09-13 | Tạo repo `docs`, chuẩn GitHub Flow + Conventional Commits, rà soát 4 luồng, 5 sơ đồ A4 | [ADR-0001](adr/0001-github-flow-main-la-production.md) · [ADR-0002](adr/0002-docs-as-code-repo-trung-tam.md) |

## 6. Blocker & câu hỏi mở

| # | Nội dung | Cần ai quyết |
|---|---|---|
| Q1 | Org gói **Free** + repo private ⇒ **không bật được branch protection / rulesets**. Luật GitHub Flow hiện chỉ thực thi bằng quy ước + PR template. Nâng GitHub Team để bắt buộc review trước khi merge? | Chủ dự án |
| Q2 | Nhà cung cấp SMS cho F2-G03, và LLM + embedding cho L4 (cần hỗ trợ tiếng Việt) | Chủ dự án |
| Q3 | Drone thật giao tiếp qua MAVLink hay MQTT? Quyết định kiến trúc cho F1-G01 | Nhóm drone |
