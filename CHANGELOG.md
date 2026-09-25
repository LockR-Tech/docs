# Changelog

Mỗi thay đổi ở repo docs thêm **một dòng** vào ngày tương ứng (mới nhất ở trên). Ghi mã gap/SEC/ADR nếu có.

## 2026-09-25

- F2-G09: firmware tủ khớp sơ đồ đấu nối ([iot#7](https://github.com/LockR-Tech/iot/pull/7)) — `LOCK_PINS` / `MAGNETIC_PINS` đủ 7 ngăn theo bản đồ ở [cabinet-wiring-spec § 5](03-hardware/cabinet-wiring-spec.md), `MAX_SLOTS` 6 → 7, `SLAVE_ID` 2 → 1 (Pi chỉ quét từ 1 tới `MAX_CABINETS`). Sửa kèm một lỗi tiềm ẩn: mảng trạng thái cảm biến khai cứng `[6]` trong khi mọi vòng lặp chạy tới `NUM_SLOTS` — nâng lên 7 mà giữ `[6]` là ghi tràn mảng; giờ khai `[NUM_SLOTS]`. `RELAY_ON` giữ `HIGH` và đánh dấu **chưa xác minh với module thật**. Hai tài liệu phần cứng cập nhật theo, mục 7 của hướng dẫn gạch việc 1.

- F2-G09: thêm thư mục [03-hardware/](03-hardware/) — [cabinet-wiring-spec.md](03-hardware/cabinet-wiring-spec.md) chép sơ đồ đấu nối của nhà cung cấp (nguồn 12 V, TB6600, relay 8 kênh, 7 khoá) và đối chiếu với firmware: code điều khiển tủ qua **Arduino trên RS485** (`locker_controller.ino`, `serial_manager.py`) chứ không phải Pi cắm thẳng GPIO như tài liệu gốc; firmware mới khai 3 ngăn, trần 6 (`MAX_SLOTS`), chưa có gì cho động cơ bước. [controller-wiring-guide.md](03-hardware/controller-wiring-guide.md): chọn Pi thay Jetson, danh sách chuẩn bị, thứ tự nối dây, bảng bring-up dùng các script sẵn có, kiosk trên Pi (ba bẫy đã kiểm trong code: build thiếu `base: '/ui/'`, kiosk nhận tủ qua `?lockerId=`, origin `localhost:8000` chưa trong CORS gateway), và danh sách việc còn nợ trong code. Rà `iot` tới `454c49a`; STATUS § 0 cập nhật mốc iot, § 3 nhận việc lắp tủ.

## 2026-09-24

- Thêm [04-engineering/chay-he-thong-cuc-bo.md](04-engineering/chay-he-thong-cuc-bo.md): lệnh dựng admin web / landing / kiosk / mobile / giả lập tủ trên máy cá nhân, cổng mặc định theo `vite.config` từng repo, và 5 cái bẫy đã gặp (giả lập ghi thật vào production qua broker công khai — SEC-04; `flutter run` mất kết nối khi app bị kill; `adb` ngoài PATH; cổng không được nhả sau Ctrl+C; bẫy toolchain máy SA-KT32). Ghi rõ `flutter run -d chrome` nổ ở màn đăng nhập vì `main.dart` bỏ qua `Firebase.initializeApp` khi `kIsWeb` còn `login_screen` vẫn dựng `FirebaseAuth.instance`. Thêm dòng tra cứu vào AGENTS.md.
- STATUS § 5: ghi đợt sửa lỗi 2026-09-23 đã merge (mobile #24–#26, frontend #19, backend #26). **Chưa tính lại %** vì chưa rà lại checklist từng luồng.

## 2026-09-22

- F3-G06: cập nhật STATUS và flow 3 theo phần ADMIN quản lý drone đã merge trước 2026-09-21 22:51 (backend #24, frontend #17): route admin đổi trạng thái/pin không cần claim, giữ phân công KTV, chặn sửa/ngừng drone đang `RESERVED`/`IN_FLIGHT`; chưa tính các chỉnh sửa sau mốc này.

## 2026-09-21

- L2 (gửi hàng + thuê ô, 65 → 70 %): F2.04 DONE; cập nhật F2.03, F2.08, F2.09 và mục "luồng chạy" theo backend #20/#21, mobile #19, iot #5 — đơn thuê không bị kết thúc khi mở lại, xác nhận bỏ hàng cần đã mở ô, chặn mã của đơn chưa trả/thuê quá hạn, kiosk xác nhận bỏ hàng và kết thúc thuê bằng mã, app bỏ CASH chờ PAID. F2-G01 xong; F2-G04, F2-G07, F2-G11 xong một phần.
- L3 (phần KTV tủ, % giữ 45): F3.07, F3.08, F3.10 thêm bằng chứng backend #22, frontend #15, mobile #20 — KTV phụ trách tủ, định tuyến + thông báo phiếu, đóng phiếu trả tài sản, kiểm tra định kỳ ĐẠT/KHÔNG ĐẠT, nhắc hạn; F3-G08 xong; F3-G02, F3-G04, F3-G07 xong một phần. Ma trận vai trò và vòng đời phiếu viết lại.
- L4 (trợ lý RAG, 0 → 94 %): file luồng viết lại theo backend #23, frontend #16, mobile #21. [ADR-0006](adr/0006-tro-ly-rag-claude-voyage-pgvector-rieng.md): Claude + Voyage AI, kho vector là container pgvector riêng (đóng STATUS Q2 phần LLM).
- `architecture.md`: thêm `assistant-service`, `assistant-db`, sự kiện `locker.report.routed/assigned`, `locker.schedule.due`, đường kiosk công khai mới, RBAC mới; bỏ hai dòng bảng lạc lên đầu file. Runbook dịch vụ ngoài thêm mục Anthropic/Voyage. Sơ đồ `order-status`, `locker-cell-status`, `architecture` cập nhật và render lại.

## 2026-09-20

- F1-G02: bổ sung trạng thái drone `RESERVED`, giữ drone bằng compare-and-set có khóa DB khi nhận đơn; kiểm tra lại pin/bãi đáp/reservation trước cất cánh; hủy nhả reservation; simulator không ghi đè FAULT. Cập nhật flow 1 và hai sơ đồ drone; ghi nhận chu kỳ DEMO 3 giây.

## 2026-09-16

- Bàn giao: phần mobile đã kiểm tra đầy đủ (analyze 259 = baseline, 154 test pass, build Android thành công) nên bỏ cảnh báo "chưa qua kiểm tra máy móc". Ghi chú môi trường thêm bẫy Java 25 làm `flutter run` chết với thông báo `25.0.2` mà `flutter doctor` không phát hiện được.

- STATUS và bàn giao: ghi rõ cả ba repo đều đang đi trước production (kèm commit từng bên), và đánh dấu `mobile #7` là thay đổi duy nhất chưa qua kiểm tra máy móc.

- Trang `/admin/services` dựng lại theo mô hình thật (ba loại đơn, quy tắc ở `system_settings`) thay cho trang cũ gọi endpoint không tồn tại; `business-settings.md` thêm mục 7 mô tả trang này và cảnh báo `GET /api/admin/services` trả 404. Giao diện admin và app bỏ mã số nội bộ, hiện tên tủ, tên cửa hàng và số ô in trên tủ.

- Thêm [bàn giao trạng thái đầy đủ](handoff/2026-09-16-trang-thai-day-du-va-viec-con-lai.md): mốc commit từng repo, nút thắt quota Actions, thứ tự việc còn lại, kết quả kiểm tra, nợ kỹ thuật, ghi chú môi trường. STATUS § 3 gọn lại còn hai nút thắt vận hành; § 4 đặt deploy backend lên đầu; § 5 nhận hai mốc mới; SEC-01 và SEC-07 ghi rõ đã merge, chờ deploy.

- SEC-01, SEC-07 và FCM: ghi nhận backend #10 đã vá bằng code — STATUS § 2 và § 4, `architecture.md` (JWT secret, hàng FCM push). Thêm [`04-engineering/cau-hinh-dich-vu-ngoai.md`](04-engineering/cau-hinh-dich-vu-ngoai.md): runbook nạp khoá cho từng dịch vụ ngoài (JWT, Cloudinary, Twilio, SMTP, Azure, Cloudflare, MQTT, VNPay/MoMo, Firebase) — nơi đặt, cách kiểm tra đã ăn chưa, thứ tự ưu tiên theo rủi ro, và việc phải làm khi khoá bị lộ. AGENTS và README thêm con trỏ.

- F2-G03: thêm hợp đồng [`01-overview/receiver-pickup-code.md`](01-overview/receiver-pickup-code.md) — kênh gửi mã mở tủ cho người nhận chưa có tài khoản (SMS Twilio + email dùng chung SMTP auth-service), quy tắc bật/tắt trên admin, biến môi trường; `architecture.md` cập nhật hàng Email và SMS. Flow 2 cập nhật F2.06 và F2-G03; STATUS Q2 chốt nhà cung cấp SMS là Twilio và nhận việc mới.

- STATUS: mốc cập nhật 2026-09-16; F2-G08 (phần web) chuyển từ § 3 sang § 5 sau khi merge `43e5d00` và deploy Cloudflare xanh; § 5 ghi thêm API báo cáo backend và ADR-0005 đã lên production.

- F2-G08 (phần web): 3 trang `/admin/orders`, `/admin/payments`, `/admin/revenue` chuyển sang dữ liệu thật theo [`01-overview/admin-reporting-api.md`](01-overview/admin-reporting-api.md); F2.09 bỏ "web thiếu EXPIRED" khỏi cột còn thiếu; F2-G08 ghi rõ phần enum web đã xong và phần legacy còn lại. Thêm [bàn giao 2026-09-16](handoff/2026-09-16-bao-cao-admin-web-va-mobile-con-lai.md).

## 2026-09-15

- Thêm ADR-0005 (Proposed) và hợp đồng [`01-overview/business-settings.md`](01-overview/business-settings.md): quy tắc nghiệp vụ cấu hình trên admin, mỗi service sở hữu bảng `system_settings`; STATUS § 3 nhận 2 việc (cấu hình nghiệp vụ, trang đơn hàng/thanh toán/doanh thu dữ liệu thật).

- Bàn giao lưu ảnh Cloudinary: ghi nhận đã merge + deploy backend #3, frontend #4, mobile #4; smoke test backend đỏ do race Eureka (không rollback); việc còn lại là cấu hình `CLOUDINARY_URL` trên VM.

- Thêm `handoff/2026-09-15-luu-anh-cloudinary.md`: trạng thái PR, việc còn lại theo thứ tự, ghi chú môi trường để người/AI khác tiếp tục việc lưu ảnh Cloudinary; STATUS § 3 trỏ tới file này.

- Thêm ADR-0004 (Proposed) và hợp đồng API [`01-overview/media-storage.md`](01-overview/media-storage.md): lưu ảnh trên Cloudinary bằng signed direct upload; cập nhật `architecture.md` (route `/api/media/**`, bảng `report_attachments`, biến `CLOUDINARY_URL`); STATUS § 3 nhận việc.

## 2026-09-13

- Khởi tạo repo `docs`: README, AGENTS/CLAUDE, STATUS, tổng quan sản phẩm, kiến trúc, luật Git/commit/deploy/tài liệu, ADR-0001…0003.
- Rà soát code 4 luồng tại backend `705c556`, frontend `e1b9a73`, mobile `5890184`, iot `927b057`: L1 60 %, L2 65 %, L3 45 %, L4 0 %.
- L2 hạ F2.04 từ DONE xuống PARTIAL sau khi xác minh bug `send_parcel_page.dart:377-382` (xác nhận bỏ hàng bằng id payment).
- Ghi nhận rủi ro SEC-01…SEC-08.
- Thêm 5 sơ đồ A4: kiến trúc, trạng thái đơn hàng, vòng đời giao hàng drone, trạng thái drone, trạng thái ô tủ; script `render-a4.mjs` + CI kiểm tra 1 trang.
