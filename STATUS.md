# STATUS — Lock.R

> **Nguồn sự thật duy nhất về tiến độ dự án.** Người và agent đọc file này **đầu tiên**, cập nhật nó **cuối cùng** trong mỗi phiên làm việc. Giao thức: [AGENTS.md](AGENTS.md).

| | |
|---|---|
| **Cập nhật lần cuối** | 2026-09-25 |
| **Người cập nhật** | BaoHuy-Dev — thêm tài liệu phần cứng `03-hardware/`, rà repo iot tới `454c49a`; số % các luồng chưa tính lại |
| **Tổng tiến độ 4 luồng** | **67,2 %** |

## 0. Mốc code đã rà soát

Mọi con số bên dưới đúng với các commit này. Trước khi tin STATUS, kiểm tra xem code đã đi xa hơn chưa (xem [AGENTS.md § Kiểm tra độ tươi](AGENTS.md#1-bắt-đầu-phiên)).

| Repo | Commit đã rà soát | Nhánh |
|---|---|---|
| [backend](https://github.com/LockR-Tech/backend) | `684dcf5` | `main` |
| [frontend](https://github.com/LockR-Tech/frontend) | `612912d` | `main` |
| [mobile](https://github.com/LockR-Tech/mobile) | `5890184` | `main` |
| [iot](https://github.com/LockR-Tech/iot) | `454c49a` | `main` |
| [legal](https://github.com/LockR-Tech/legal) | `87ad342` | `main` |

## 1. Tiến độ theo luồng

| Luồng | Tiến độ | Một dòng tình trạng | Chi tiết |
|---|---:|---|---|
| **L1** Giao hàng drone → PIN → nhận hàng | **60 %** | Chạy trọn vẹn **chỉ ở chế độ DEMO** (bộ giả lập đẩy chặng bay). Ở STANDARD đơn kẹt tại LAUNCHING, drone kẹt IN_FLIGHT. | [flow-1](02-flows/flow-1-drone-delivery.md) |
| **L2** Thuê tủ gửi hàng → chuyển mã → người nhận lấy (gồm thuê ô theo giờ) | **70 %** | Gửi hàng và thuê ô chạy trọn: trả tiền thật → mở ô → xác nhận bỏ hàng (app hoặc kiosk) → người nhận lấy bằng mã hoàn tất đơn; thuê ô mở lại nhiều lần, kết thúc tại kiosk. Còn: phí quá hạn chưa thu, người nhận có tài khoản chưa thấy đơn gửi tới mình, payload MQTT với Pi. | [flow-2](02-flows/flow-2-locker-send.md) |
| **L3** Vai trò · quản lý drone · bảo trì | **45 %** | Phần **KTV tủ** đã đủ; **ADMIN quản lý drone** đã sửa route đổi trạng thái/pin và guard drone đang có nhiệm vụ. Còn **lỗ hổng phân quyền** (SEC-02/03/05/06), IoT chưa tự báo hỏng, telemetry/ticket drone. | [flow-3](02-flows/flow-3-roles-maintenance.md) |
| **L4** RAG hỏi đáp tài liệu nội bộ | **94 %** | `assistant-service` (Claude + Voyage, pgvector riêng): nạp tài liệu, hỏi đáp có trích nguồn, lọc theo vai trò, từ chối ngoài phạm vi, trang Kho tri thức, màn hình trợ lý. Còn: nạp khoá API, chạy bộ đánh giá và hiệu chỉnh ngưỡng. | [flow-4](02-flows/flow-4-rag-assistant.md) |

**Cách tính:** mỗi luồng có checklist 8–10 hạng mục; DONE = 1 · PARTIAL = 0,5 · MISSING = 0. % luồng = tổng điểm / số hạng mục. Tổng dự án = trung bình cộng 4 luồng (trọng số bằng nhau): (60 + 70 + 45 + 93,75) / 4 = **67,2 %**. Chỉ được đổi % khi đổi checklist trong file luồng, kèm bằng chứng `file:line`.

> Chủ dự án đánh số theo nghiệp vụ: *luồng 2* = gửi hàng, *luồng 3* = thuê ô (cả hai nằm trong L2), *luồng 4* = vận hành–bảo trì (L3), *luồng 5* = trợ lý RAG (L4).

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
> Cần bản **ngắn** (vướng mắc + việc còn lại, 1 trang): [handoff/2026-09-16-tom-tat-viec-con-lai.md](handoff/2026-09-16-tom-tat-viec-con-lai.md).

| Việc | Gap | Người/nhánh | Trạng thái |
|---|---|---|---|
| Khóa vòng đời điều phối drone: `IDLE → RESERVED → IN_FLIGHT`, guard cất cánh/hủy và không ghi đè FAULT | **F1-G02** | Codex · backend `codex/drone-demo-3s`, mobile `codex/drone-maintenance-dialog-fix` | Đã code và qua test cục bộ; **chưa merge/deploy** |
| L4 trợ lý RAG lên chạy thật: nạp khoá, seed tài liệu, chạy bộ đánh giá, chỉnh ngưỡng | F4-G09 | Chủ dự án | Code đã deploy; chờ `ANTHROPIC_API_KEY`, `EMBEDDING_API_KEY` trên VM ([runbook § 11b](04-engineering/cau-hinh-dich-vu-ngoai.md)) rồi chạy `backend/scripts/seed-knowledge.sh` |
| Kiểm dữ liệu production bị lỗi thuê ô trước backend #20: đơn RENTAL bị COMPLETED sớm từ 2026-09-17, đơn INITIALIZED chưa trả tiền (giờ bị chặn mở ô), đơn thuê STORING quá hạn | F2-G01 | Chủ dự án | Chưa chạy truy vấn |
| Lắp tủ vật lý theo sơ đồ nhà cung cấp: Pi ↔ USB-RS485 ↔ Arduino ↔ relay/khoá, kiosk chạy trên Pi | F2-G09 | Chủ dự án | Đang chuẩn bị phần cứng theo [03-hardware/controller-wiring-guide.md](03-hardware/controller-wiring-guide.md); firmware đã khớp sơ đồ (7 ngăn, iot#7); code còn nợ: `base: '/ui/'` cho kiosk, thống nhất payload lệnh mở (mục 7 của hướng dẫn) |

Các nút thắt vận hành hiện có:

| Nút thắt | Trạng thái | Ai làm |
|---|---|---|
| **GitHub Actions hết quota** (2.000/2.000 phút, gói Free, reset ~2026-10-01) | Mọi CI và deploy đỏ sau 2–5 giây. Nguyên nhân gốc đã sửa ở `999d48f`, nhưng phải chờ reset hoặc nâng spending limit | Chủ dự án |
| **Backend đã khớp production** ✅ | backend `569d323` deploy thành công 16/09 09:58 (không ai bị đăng xuất — giữ secret cũ). frontend `main` `b1686f5` vs đã deploy `a1ca345` — sau 1 commit · mobile `main` chưa build lại | Chủ dự án |

| Khoá còn thiếu trên VM | Thiếu thì sao |
|---|---|
| `APP_SMS_TWILIO_FROM_NUMBER` | Có SID + Auth Token rồi, thiếu số gửi ⇒ SMS chỉ ghi log |
| `SPRING_MAIL_*` · `FIREBASE_CREDENTIALS_JSON` | Chưa kiểm chứng; thiếu thì mất kênh email và push |

✅ **`CLOUDINARY_URL` đã nạp 16/09/2026** — cả bốn service (`user`, `order`, `locker`,
`store`) ghi `Cloudinary media storage enabled` lúc khởi động. Upload ảnh dùng được trên
production; không cần deploy lại web hay mobile vì client lấy `cloudName`/`uploadUrl` từ
chữ ký backend trả về.

Cách lấy và nạp: [cau-hinh-dich-vu-ngoai.md](04-engineering/cau-hinh-dich-vu-ngoai.md).

## 4. Việc tiếp theo — theo thứ tự ưu tiên

1. **Nghiệm thu trên production** luồng 2/3/4 vừa deploy (kịch bản ở kế hoạch: gửi hàng, thuê ô mở lại nhiều lần, KTV nhận–sửa–hoàn tất phiếu, kiểm tra định kỳ không đạt) và **kiểm dữ liệu** bị lỗi thuê ô trước backend #20 (§ 3). _(rất gấp)_
2. **Gỡ nút thắt Actions** rồi **deploy backend** — SEC-01 và SEC-07 đã vá trong code trên `main` nhưng chỉ đóng khi deploy xong. _(rất gấp)_
3. **Nạp khoá còn thiếu trên VM** (số Twilio, SMTP, Firebase) — [runbook](04-engineering/cau-hinh-dich-vu-ngoai.md). Cloudinary đã xong 16/09.
4. **SEC-02 · SEC-03 · SEC-05 · SEC-06** Khoá API theo chủ sở hữu + vai trò ở service, không chỉ ở gateway — [F3-G01](02-flows/flow-3-roles-maintenance.md).
5. **SEC-04** Broker MQTT riêng có xác thực + TLS trong `docker-compose.yml`.
6. **L4 lên production**: nạp `ANTHROPIC_API_KEY`, `EMBEDDING_API_KEY`, `ASSISTANT_DB_PASSWORD` trước lần deploy đầu có `assistant-service`; seed tài liệu; chạy bộ đánh giá (`POST /api/admin/knowledge/eval`) và chỉnh ngưỡng liên quan.
7. **F2-G05 · F2-G06** Thu phí quá hạn; người nhận có tài khoản thấy đơn gửi tới mình.
8. **F1-G01** Tiến trình bay thật cho STANDARD. F1-G02 đã code/test cục bộ, chờ review + merge + deploy.
9. **F3-G03** IoT tự báo offline/hỏng; phần drone còn lại của F3-G02/G07.

## 5. Đã xong gần đây

| Ngày | Việc | Liên kết |
|---|---|---|
| 2026-09-24 | **Đợt sửa lỗi UX + múi giờ, đã merge và deploy backend/frontend.** Gốc chung của 3 lỗi: backend trả `LocalDateTime` (chuỗi trần = UTC, container chạy UTC) nhưng mobile gọi `DateTime.parse(s).toLocal()` — `DateTime.parse` coi chuỗi trần là giờ máy nên `.toLocal()` vô nghĩa ⇒ mọi mốc hiện sớm 7 tiếng và **mọi hạn chót lùi 7 tiếng nên đơn vừa tạo đã "quá hạn"**; tách `core/utils/app_date_time.dart` dùng chung. Frontend còn vài chỗ `new Date(chuỗi)` cùng lỗi. **Mã giảm giá tự hết hạn**: `toDatetimeLocal` cắt thẳng chuỗi UTC vào ô `datetime-local` rồi lưu lại đổi VN→UTC lần nữa, mỗi lần admin sửa là mã lùi thêm 7 tiếng. **Gia hạn thuê tủ thu lại cả phần đã trả**: `extendRental`/`assessOvertime` cộng vào `totalPrice` rồi đặt `UNPAID`; thêm cột `paid_amount` (order `V14`) + `amountDue`, client thu phần còn thiếu. **Tạo user ở admin báo trùng mail sai**: không service nào kiểm trùng, auth lỗi thì xoá profile ⇒ tài khoản auth mồ côi chiếm email; thêm kiểm trùng + bắt buộc trường. **Số liệu Noti admin**: hook trả `stats: undefined` nên 6 thẻ luôn 0, `totalPages` cứng 1, 3 bộ lọc bị server bỏ qua. Thêm: nút quay lại thông báo (push dùng `context.go` xoá stack), mở được thông báo không có payload, chỉ đường tới tủ (thiếu `<queries>` nên `canLaunchUrl` false trên Android 11+), mã giao dịch + hình thức thanh toán trong chi tiết đơn, thông tin người nhận, lọc trạng thái ở KTV, lối đi tiếp khi kiểm tra định kỳ KHÔNG ĐẠT, thanh tiêu đề co khi cuộn (mới 4/25 màn), gỡ uỷ quyền lấy hộ. **Backend + frontend deploy xanh; mobile web deploy đỏ** do 7 test hỏng sẵn trên `main` chặn bước `flutter test` (235 pass / 7 fail, trùng con số trước và sau khi sửa). **% các luồng chưa tính lại** — chưa rà lại checklist. | mobile [#24](https://github.com/LockR-Tech/mobile/pull/24) [#25](https://github.com/LockR-Tech/mobile/pull/25) [#26](https://github.com/LockR-Tech/mobile/pull/26) · frontend [#19](https://github.com/LockR-Tech/frontend/pull/19) · backend [#26](https://github.com/LockR-Tech/backend/pull/26) · [runbook chạy cục bộ](04-engineering/chay-he-thong-cuc-bo.md) |
| 2026-09-21 | **ADMIN quản lý drone: sửa điều khiển trạng thái/pin qua route admin.** Backend thêm đường admin riêng cho đổi trạng thái và cập nhật pin, giữ phân công KTV hiện tại, ghi audit log, chặn sửa/ngừng drone khi đang `RESERVED`/`IN_FLIGHT`, và không cho ADMIN/DRONE_TECHNICIAN tự ép các trạng thái workflow-managed (`RESERVED`, `IN_FLIGHT`) từ màn vận hành. Frontend `/admin/drones` gọi đúng route admin cho trạng thái/pin và disable sửa/ngừng khi drone đang có nhiệm vụ. Test backend targeted pass 13/13 ở PR này; docs chưa tính các chỉnh sửa sau 2026-09-21 22:51. | backend [#24](https://github.com/LockR-Tech/backend/pull/24) · frontend [#17](https://github.com/LockR-Tech/frontend/pull/17) |
| 2026-09-21 | **Hoàn thiện L2 + phần KTV tủ của L3 + L4, đã merge.** Hotfix đơn thuê bị kết thúc khi mở lại ô (backend #20, deploy xanh). Gửi hàng/thuê ô: chặn mã đơn chưa trả và thuê quá hạn, xác nhận bỏ hàng cần đã mở ô, kiosk xác nhận bỏ hàng và kết thúc thuê bằng mã, app trả tiền thật (bỏ CASH) và chờ PAID. KTV tủ: KTV phụ trách tủ, định tuyến + thông báo phiếu, đóng phiếu trả tài sản, tủ bảo trì chặn đặt ô, kiểm tra định kỳ ĐẠT/KHÔNG ĐẠT, nhắc hạn 07:00. Trợ lý RAG: `assistant-service` + `assistant-db` (pgvector), trang Kho tri thức, màn hình trợ lý. Migration mới: `order_service` V13, `locker_service` V18, `assistant_db` V1. Backend #21–#23 deploy chung một lần (hai lần deploy trung gian bị huỷ ở bước build, chưa chạm VM). | backend [#20](https://github.com/LockR-Tech/backend/pull/20) [#21](https://github.com/LockR-Tech/backend/pull/21) [#22](https://github.com/LockR-Tech/backend/pull/22) [#23](https://github.com/LockR-Tech/backend/pull/23) · frontend [#15](https://github.com/LockR-Tech/frontend/pull/15) [#16](https://github.com/LockR-Tech/frontend/pull/16) · mobile [#18](https://github.com/LockR-Tech/mobile/pull/18)–[#21](https://github.com/LockR-Tech/mobile/pull/21) · iot [#5](https://github.com/LockR-Tech/iot/pull/5) · [ADR-0006](adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md) |
| 2026-09-16 | **Deploy backend `569d323` lên production** (09:58, nghiệm thu health/public/admin đạt): đóng SEC-07 (bỏ OTP khỏi log), khởi tạo Firebase, truyền JWT secret cho `notification-service`, gửi mã mở tủ cho người nhận. Giữ secret cũ trong `.env` nên **không ai bị đăng xuất**. Mở được nhờ chuyển 6 repo sang public → Actions miễn phí. **SEC-01 vẫn mở**: secret là chuỗi mặc định, giờ công khai theo repo. | [DEPLOY-LOG](https://github.com/LockR-Tech/backend/blob/main/infra/azure/DEPLOY-LOG.md) |
| 2026-09-16 | **Lưu ảnh chạy trên production**: nạp `CLOUDINARY_URL` + `MEDIA_FOLDER_ROOT` vào `.env` VM, khởi động lại `user`/`order`/`locker`/`store-service`; cả bốn xác nhận `Cloudinary media storage enabled`. Avatar, ảnh phiếu sự cố, ảnh cửa hàng, ảnh khuyến mãi hết trả 503. Không cần deploy lại web/mobile. | [runbook §4](04-engineering/cau-hinh-dich-vu-ngoai.md) · [ADR-0004](adr/0004-anh-luu-cloudinary-upload-truc-tiep.md) |
| 2026-09-16 | **Quản lý dịch vụ trên admin**: trang `/admin/services` dựng lại — mỗi dịch vụ (gửi hàng, thuê ô, drone) một thẻ với giá, quy tắc sửa được tại chỗ và hiệu quả trong kỳ. Trang cũ gọi `/api/admin/services` vốn trả 404 nên chưa bao giờ chạy. Kèm bỏ mã số nội bộ khỏi admin và app: hiện tên tủ, tên cửa hàng, số ô in trên tủ. **Đã merge, chờ deploy.** | [frontend #8](https://github.com/LockR-Tech/frontend/pull/8) · [mobile #7](https://github.com/LockR-Tech/mobile/pull/7) |
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
| Q2 | ~~Nhà cung cấp SMS cho F2-G03~~ — chốt **Twilio** (bản dùng thử, đủ để demo; chỉ gửi được tới số đã xác minh trong console). **Còn chờ**: nạp `APP_SMS_TWILIO_*` lên VM, và quyết có nâng lên tài khoản trả phí trước khi chạy thật không. ~~LLM + embedding cho L4~~ — chốt **Claude + Voyage AI**, kho vector container pgvector riêng ([ADR-0006](adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md)). | Chủ dự án |
| Q3 | Drone thật giao tiếp qua MAVLink hay MQTT? Quyết định kiến trúc cho F1-G01 | Nhóm drone |
