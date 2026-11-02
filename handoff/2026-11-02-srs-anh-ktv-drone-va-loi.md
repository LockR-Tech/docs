# 2026-11-02 — Chụp lại ảnh SRS app KTV drone và lỗi phát hiện

Người làm: binhtntse182370 (cùng Claude Code). Mốc code: mobile `main` @ `72e4ef2` (APK debug cài lúc 16:35), backend `main` @ `b23534e`.
Môi trường: production `https://api.locker-drone.tech`, emulator Android (1080×2400). Tài khoản: KTV drone `ktvdronedemo@gmail.com`, khách `truongnguyenthaibinh1050@gmail.com`, admin `binhtntse182370@fpt.edu.vn`.

## 1. Tóm tắt

| Việc | Kết quả | PR |
|---|---|---|
| Chụp lại toàn bộ chức năng app KTV drone cho SRS | 110 ảnh thay 54 ảnh cũ ở `rp3/srs-assets/mobile-drone-technician/` | PR docs này |
| Luồng giao drone thật trên production (2 đơn, khách trả tiền thật) | Chạy trọn từ lời mời lấy hàng → nạp → phóng → kiện vào tủ | — |
| 11 lỗi phát hiện | Đã sửa (§ 4) | [backend #128](https://github.com/LockR-Tech/backend/pull/128) · [mobile #116](https://github.com/LockR-Tech/mobile/pull/116) |

Lỗi tiền phụ thu cân lệch (#4 handoff 28/10) **đã hết**: hộp nạp hàng báo 3.000đ, khớp server.

## 2. Ảnh đã chụp

| Nhóm | File |
|---|---|
| Trang chủ / điều phối: thời tiết các tủ, trả kiện cho người gửi, bật/tắt nhận việc, sheet GPS ca trực | `d01*` |
| Đội bay: hành động drone, đổi trạng thái, cập nhật pin, nhật ký bảo trì, nhả phụ trách | `d02*` |
| Sự cố drone: lọc, sắp xếp, chi tiết, nhận việc, thêm bước, gia hạn SLA, trả phiếu, nghiệm thu có ảnh | `d03*` |
| Việc của tôi | `d04*` |
| Bảo trì định kỳ: danh sách, chi tiết, chỉ đường, checklist, hoàn thành | `d05*` |
| Lập kế hoạch bay: waypoint, sửa điểm, lệnh MAVLink, xuất `.waypoints`, menu, đổi tên, cài đặt, thư viện | `d06*` |
| Flight Data: chưa kết nối, hộp kết nối, chờ dữ liệu | `d07*` |
| Hồ sơ, đăng xuất, hết ca, avatar, trợ lý AI | `d08*`–`d12*` |
| Lấy hàng tận nhà: lời mời, từ chối, nhận, không lấy được, xác nhận đã lấy (mã + ảnh kiện), chỉ đường, giao không hoàn tất | `d13*` |
| Gán drone, thẻ đơn, chi tiết đơn, nạp hàng (cân lệch), huỷ trước khi bay, phóng, chi tiết nhiệm vụ, bản đồ đang bay, tiến trình, đã giao | `d14*`–`d20*` |

**Chưa chụp được:** bảng camera hành trình, hộp báo rơi kiện, hộp báo chuyến bay thất bại, chuyển chặng — giả lập bay quá nhanh (lỗi 9); "Đổi drone" — chỉ hiện khi đơn bị chặn bởi sự cố; Face Verify / Face Registration — đang tắt (`mobile/lib/core/config/feature_flags.dart:34` `faceRecognitionEnabled = false`) nhưng vẫn có trong sơ đồ `rp3/srs-assets/drawio/03c-screen-flow-mobile-drone-technician.png`.

Ảnh chưa che email/SĐT của tài khoản demo (giống bộ ảnh mobile cũ). Mục SRS 3.4 trong docx chưa chèn lại ảnh mới — tên file đã đổi.

## 3. Dữ liệu production đã thay đổi

| Thay đổi | Ghi chú |
|---|---|
| Đơn `ORD-20261102-1W39CS` (#152) và `ORD-20261102-5XV3CJ` (#153), mỗi đơn 8.000đ (khách trả thật) | Đang `READY_FOR_PICKUP` ở ô 1 và ô 2 tủ HCM-TD-02, người nhận `minhanh.tran@gmail.com` đã nhận mã qua email. **Còn giữ ô** — cần người nhận lấy hàng hoặc admin đóng |
| `ORD-20261029-58RD1J` | KTV xác nhận đã trả kiện cho người gửi |
| Phiếu `RPT-47` (kiểm tra DRONE-TEST sau rơi kiện) | Đã nghiệm thu; DRONE-TEST về `IDLE`; gia hạn SLA 1 lần |
| Lịch bảo trì định kỳ #19 cho LR-DRN-01, giao KTV `ktvdronedemo` | Tạo qua API admin, đã hoàn thành lần đầu, hạn kế tiếp 16/11 |
| LR-DRN-01 và DRONE-TEST | Nhận phụ trách để chụp rồi đã nhả; LR-DRN-01 thêm vài dòng nhật ký, pin đặt 100 % |
| KTV `ktvdronedemo` | Vẫn trong ca, vị trí FPT |

## 4. Lỗi phát hiện và cách sửa

| # | Lỗi | Sửa |
|---|---|---|
| 1 | Bấm "Từ chối" lời mời lấy hàng là từ chối ngay, KTV mất lời mời và không được mời lại đơn đó 10 phút | Hỏi lại trước khi từ chối — mobile #116 |
| 2 | KTV chưa phụ trách drone nào không nhận được drone từ app: tab Đội bay chỉ lọc drone của mình, nút "Nhận xử lý" chỉ hiện với drone chưa thuộc mình | Mục "Drone chưa có KTV phụ trách" — mobile #116 |
| 3 | Ô nhật ký trong sheet phiếu sự cố drone bị bàn phím che | Sheet co theo bàn phím — mobile #116 |
| 4 | Lý do lỗi drone / nhật ký hiện "Parcel drop incident DPI-…" | Server ghi tiếng Việt, migration locker **V33**, order **V38** đổi dữ liệu cũ — backend #128 |
| 5 | Nhật ký bảo trì drone hiện "KTV #800023" | API nhật ký trả `actorName` — backend #128 |
| 6 | Tên file xuất kế hoạch bay "K_ ho_ch bay m_i.waypoints" | Bỏ dấu trước khi lọc — mobile #116 |
| 7 | Tab Đội bay vẫn "Đang bay" khi server đã `IDLE` | Tải lại drone khi đơn đổi — mobile #116 |
| 8 | Hộp huỷ nhiệm vụ có "Hủy" cạnh "Xác nhận hủy" | Đổi thành "Quay lại" — mobile #116 |
| 9 | Giả lập DEMO bay 3 km trong ~20 s, KTV không kịp thao tác lúc bay | Mặc định 15 s/chặng — backend #128. Production đặt riêng 5000 ms ⇒ bấm "Khôi phục mặc định" sau deploy |
| 10 | Bấm "Hết ca" lúc app đang lấy GPS ngầm mở nhầm sheet GPS (nút bị khoá, cú chạm rơi xuống InkWell của thẻ) | Chặn cú chạm ở cụm nút — mobile #116 |
| 11 | `POST` vào API chỉ nhận `GET` trả 500 | 405 kèm `Allow`, đường dẫn lạ 404 — backend #128 |

## 5. Ghi chú kỹ thuật khi chụp

- Emulator đổi vị trí bằng `cmd location providers` (cần `appops set 2000 android:mock_location allow`); `adb emu geo fix` không tới thiết bị. Emulator 4 GB RAM bị đầy làm app ANR — `am kill-all` rồi mở lại.
- Gõ tiếng Việt: đặt clipboard trên Windows (emulator chia sẻ clipboard) rồi bấm chip clipboard trên dải gợi ý Gboard.
- Đặt đơn khách qua đúng API app gọi (`POST /api/orders/drone-deliveries`, `POST /api/payments/checkout`) để không phải đăng xuất KTV — đăng xuất KTV là kết thúc ca, lời mời không tới.
- Chụp lúc đang bay: chụp liên tục `adb exec-out screencap` mỗi ~0,6 s rồi chọn khung.
