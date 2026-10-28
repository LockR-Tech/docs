# Các luồng nghiệp vụ của LockR

Mô tả ngắn từng luồng theo bước: **ai** (vai trò, thiết bị) **làm gì** → **hệ thống / người kế tiếp nhận gì**.
Cập nhật 2026-10-13. Phần ghi *(mới)* (backend #61, mobile #56, iot #15) đã merge và chạy trên production; thanh toán chỉ còn chuyển khoản VietQR (SePay).

## Vai trò và thiết bị

| Vai trò | Dùng | Làm gì chính |
|---|---|---|
| **Khách** (CUSTOMER) | App mobile, kiosk tại tủ | Gửi hàng, thuê ô, đặt drone, ví, báo sự cố, hỏi trợ lý |
| **Người nhận** | Kiosk (không cần tài khoản), app nếu có tài khoản | Lấy hàng bằng mã PIN/QR |
| **KTV tủ** (LOCKER_TECHNICIAN) | App mobile | Xử lý sự cố ô/tủ, kiểm tra định kỳ, thiết bị IoT, thu hồi kiện drone rơi |
| **KTV drone** (DRONE_TECHNICIAN) | App mobile | Điều phối đơn drone, nạp hàng, phóng, đội bay, sự cố drone |
| **Admin** (ADMIN) | Web quản trị | Cấu hình, tài khoản, tủ/drone, duyệt hoàn tiền/rút tiền, theo dõi, kho tri thức |
| **Hệ thống** | Backend + Pi điều khiển tủ (MQTT) | Giữ ô, mở khoá, gửi thông báo, job định kỳ |

Trạng thái đơn hay gặp: `INITIALIZED` (vừa tạo) → `AWAITING_DISPATCH` (drone chờ đội bay) → `STORING` (hàng/đồ đang trong ô) → `COMPLETED`; nhánh phụ `CANCELED`, `EXPIRED`, `REFUND_PENDING` → `REFUNDED`.

---

## 1. Tài khoản và đăng nhập

**1a. Khách đăng ký / đăng nhập (app)**
1. **Khách** — đăng ký bằng họ tên, email, SĐT, mật khẩu (hoặc Google / SĐT + OTP Firebase / email + OTP; lần đầu đăng nhập SĐT app hỏi họ tên) → hệ thống tạo tài khoản CUSTOMER, cấp token.
2. **Khách** — đăng nhập → app vào trang chủ khách. KTV đăng nhập cùng màn → app tự vào trang KTV theo vai trò; admin → báo dùng web.
3. **Khách** — quên mật khẩu: nhận OTP qua email → đặt mật khẩu mới.

**1b. Admin đăng nhập (web)**
1. **Admin** — nhập email + mật khẩu → hệ thống gửi OTP 6 số qua email.
2. **Admin** — nhập OTP (tối đa 5 lần sai) → vào web quản trị.

**1c. Đăng nhập kiosk bằng QR** *(mới)*
1. **Khách** — tại kiosk chọn "Gửi đồ / Thuê tủ" → "Quét QR bằng app" → kiosk hiện mã QR (hết hạn sau 2 phút).
2. **Khách** — trên app bấm nút QR ở trang chủ, quét mã (hoặc nhập mã tay) → xác nhận "Đăng nhập kiosk?".
3. **Hệ thống** — kiosk nhận phiên đăng nhập, hiện tên khách, chuyển sang chọn ô. (Cách khác: OTP qua email ngay trên kiosk.)

**1d. Admin tạo nhân viên, khoá / xoá tài khoản**
1. **Admin** — "Thêm người dùng" với vai trò KTV tủ / KTV drone → KTV đăng nhập app được ngay.
2. **Admin** — gán KTV phụ trách tủ (sơ đồ tủ → "KTV phụ trách") hoặc drone → phiếu sự cố của tủ/drone đó gửi thẳng cho KTV này.
3. **Admin** — khoá tài khoản → người đó mất quyền trong khoảng 30 giây, không làm mới token được.
4. **Admin** — xoá người dùng → tài khoản đăng nhập bị vô hiệu, email/SĐT được nhả để đăng ký lại.

---

## 2. Gửi hàng qua tủ (SEND)

1. **Khách gửi** (app) — "Gửi hàng": chọn tủ, kích cỡ (hoặc chạm một ô trống trên sơ đồ tủ), nhập SĐT / tên / email người nhận, mã giảm giá → "Tạo đơn". **Hệ thống** giữ ô (`RESERVED`), quá hạn giữ thì tự nhả.
2. **Khách gửi** — trả bằng chuyển khoản VietQR/SePay (mã QR hiện ngay trên màn, hoặc "Thanh toán bằng app ngân hàng" điền sẵn) → webhook SePay xác nhận → đơn `PAID`. Chưa trả trong thời hạn → job tự huỷ, nhả ô.
3. **Khách gửi** — tới tủ: bấm "Mở ô để bỏ hàng" trên app *hoặc* nhập mã gửi ở kiosk → **tủ** mở ô → bỏ hàng, đóng cửa → "Đã bỏ hàng".
4. **Hệ thống** — ô `OCCUPIED`, đơn `STORING`; app người gửi hiện mã lấy hàng + nút "Chia sẻ mã cho người nhận" (Zalo/Messenger/SMS); email cho người nhận nếu có. Người nhận có tài khoản trùng SĐT thấy đơn ở tab **"Hàng chờ nhận"** kèm PIN *(mới)*.
5. **Người nhận** (kiosk) — "Mở tủ / Nhận đồ" → nhập PIN (hoặc mã QR) → tủ mở ô → lấy hàng.
6. **Hệ thống** — đơn `COMPLETED`, nhả ô; cộng điểm thưởng cho người gửi *(mới)*.

Ngoại lệ:
- **Quá hạn lấy** (hạn và thời gian ân hạn do admin cấu hình) → phải trả "phí quá giờ" trước khi mở ô; quá hạn lâu → job chuyển hàng ra kho, nhả ô.
- **Người gửi đổi mã PIN** nếu lộ mã *(mới)*.
- **Ủy quyền lấy hộ** → luồng 5.

---

## 3. Thuê ô giữ đồ (RENTAL) bằng app

1. **Khách** — "Thuê tủ": chọn tủ, loại ô (thường / vali XL), số giờ → "Thuê ngay" → hệ thống giữ ô.
2. **Khách** — thanh toán (như luồng 2) → "Mở ô để bỏ đồ" → tủ mở → bỏ đồ → "Bắt đầu kỳ thuê" → đơn `STORING`.
3. **Khách** — trong thời gian thuê: "Mở ô" lấy/bỏ thêm đồ (nhiều lần), "Gia hạn thuê" (trả thêm tiền).
4. **Khách** — "Kết thúc thuê & lấy đồ" → mở ô lần cuối → "Đã lấy đồ và đóng tủ" → đơn `COMPLETED`, nhả ô, cộng điểm *(mới)*.
5. **Quá giờ** — muốn mở ô phải trả phí quá giờ trước; quá hạn lâu → job chuyển đồ ra kho.

## 4. Thuê ô ngay tại kiosk

1. **Khách** (kiosk) — "Gửi đồ / Thuê tủ" → đăng nhập bằng email + OTP hoặc QR từ app (luồng 1c); chưa có tài khoản → "Đăng ký nhanh".
2. **Khách** — chọn ô trên sơ đồ → chọn số giờ, mã giảm giá → "Đặt tủ".
3. **Khách** — thanh toán chuyển khoản VietQR/SePay (kiosk tự hiện mã QR) → tủ tự mở ô → bỏ đồ → "Đã bỏ hàng xong".
4. **Khách** — lần sau nhập mã thuê ở kiosk → "Đóng cửa, tiếp tục thuê" hoặc "Lấy hết đồ & kết thúc thuê".

## 5. Ủy quyền lấy hộ *(mới)*

1. **Chủ đơn** (app) — đơn đang `STORING`: "Ủy quyền lấy hộ" → nhập SĐT, tên, ghi chú người lấy hộ.
2. **Hệ thống** — đổi mã PIN, gửi thông báo cho người được ủy quyền (nếu SĐT có tài khoản); người nhận gốc không còn dùng mã cũ.
3. **Người được ủy quyền** — xem đơn ở "Đơn ủy quyền" (có PIN khi sẵn sàng) → mở ô bằng mã tại kiosk hoặc "Mở tủ ủy quyền" trên app → lấy hàng → đơn hoàn tất.

---

## 6. Giao hàng bằng drone

1. **Khách** (app) — chạm ô DRONE ở tủ gửi → "Gửi hàng bằng Drone": chọn tủ nhận (có bãi đáp, còn ô drone, cách ≤ 5 km), loại hàng, mức khối lượng, giá trị khai báo, hàng dễ vỡ, người nhận, cam kết không hàng cấm → "Tạo đơn và thanh toán".
2. **Khách** — thanh toán → đơn `PAID`, chờ điều phối (`AWAITING_DISPATCH`). Chưa trả 30 phút → tự huỷ.
3. **Khách** — bỏ kiện vào ô drone ở tủ gửi → "Tôi đã bỏ kiện vào ô". Quá hạn chưa bỏ → tự huỷ + hoàn tiền.
4. **KTV drone** (app, tab Điều phối) — "Tiếp nhận": chọn drone rảnh, đủ pin ở tủ gửi → nhiệm vụ được tạo. Quá hạn không ai nhận → tự huỷ + hoàn tiền.
5. **KTV drone** — "Xác nhận nạp": cân kiện thực tế, mã niêm phong do hệ thống cấp, tick 3 mục kiểm tra.
   - Cân lệch quá 50 g so với khai báo → hệ thống tính lại phí → **khách** "Trả thêm phí chênh" hoặc "Không đồng ý" (huỷ, hoàn tiền, trả kiện).
6. **KTV drone** — "Phóng" (trong khung giờ bay, thời tiết dưới ngưỡng, không bị admin tạm dừng bay toàn hệ thống hay ở trạm cất cánh / tủ nhận).
7. **Hệ thống** — chặng bay: Đang cất cánh → Đã rời trạm → Đang bay → Sắp tới → Đã đến. Đơn **DEMO** tự chạy chặng; đơn **thật** đi theo telemetry của drone hoặc KTV xác nhận từng chặng. **Khách** theo dõi timeline + bản đồ.
8. **Hệ thống** — kiện vào ô drone ở tủ nhận → `READY_FOR_PICKUP`, gửi PIN cho người nhận (email / app).
9. **Người nhận** — mở ô bằng PIN tại kiosk → lấy hàng → **khách** xác nhận "Tôi đã lấy đồ — hoàn tất" trên app → đơn `COMPLETED`.

## 7. Huỷ / thất bại → hoàn tiền

1. Một trong các trường hợp:
   - **Khách** huỷ đơn drone khi còn chờ đội bay tiếp nhận.
   - **KTV drone** huỷ trước khi bay.
   - **KTV drone** báo chuyến bay thất bại sau khi phóng ⇒ drone chuyển `FAULT` + mở phiếu sự cố drone.
   - **Hệ thống** tự huỷ do quá hạn.
2. **Hệ thống** — đơn `REFUND_PENDING`, tạo yêu cầu hoàn tiền (về tài khoản ngân hàng khách đã lưu); kiện đã vào hệ thống thì chờ trả lại cho người gửi.
3. **Admin** (web, Thanh toán → Hoàn tiền) — chuyển khoản thủ công → "Duyệt & CK", đính kèm biên lai (hoặc "Từ chối" kèm lý do).
4. **Khách** — nhận thông báo, đơn `REFUNDED`.

Khách cũng có thể **tự gửi yêu cầu hoàn tiền** cho đơn đã thanh toán (kèm ảnh bằng chứng) ở màn "Hoàn tiền" → admin xử lý như bước 3.

## 8. Sự cố rơi kiện drone

1. **KTV drone** — thấy kiện rơi (camera / quan sát) → "Báo rơi kiện" + mô tả, ảnh → luồng giao dừng, hiện cảnh báo "Cần can thiệp tay / RTL thủ công".
2. **Admin** (web, Sự cố rơi kiện) — "Phân công" một **KTV tủ** đi thu hồi.
3. **KTV tủ** (tab Thu hồi kiện) — "Nhận nhiệm vụ" → chỉ đường tới vị trí rơi → tìm kiếm, chụp ảnh (kèm GPS) → "Gửi Admin xác minh".
4. **Admin** — "Xác minh kết quả" → tạo phương án (giao lại / bồi thường…).
5. **Khách** — thẻ "Sự cố rơi kiện" trên màn theo dõi: "Đồng ý" hoặc "Yêu cầu xem xét" (nếu chính sách cho phép).
6. **KTV tủ** — "Xác nhận bàn giao kiện về Hub"; **Admin** chốt bồi thường / đóng sự cố.

---

## 9. Báo sự cố ô / tủ → KTV tủ xử lý

1. **Khách** (app) — "Báo ô lỗi" trên đơn, hoặc "Báo sự cố" (chọn tủ, ô, tiêu đề, mô tả, ảnh) → "Gửi báo cáo".
2. **Hệ thống** — ô chuyển `FAULT`, mở phiếu sự cố (`OPEN`), gửi cho KTV phụ trách tủ (chưa có thì báo mọi KTV tủ); đặt hạn SLA.
3. **KTV tủ** (tab Sự cố) — "Nhận việc" → phiếu `IN_PROGRESS`, vào "Việc của tôi". Admin cũng có thể giao / đổi KTV.
4. **KTV tủ** — tới tủ xử lý, ghi nhật ký + ảnh tiến độ. Nếu ô còn hàng của khách, chọn một cách:
   - **Điều chuyển sang ô trống mới** → khách nhận PIN ô mới.
   - **Bàn giao trực tiếp** → phải nhập PIN/QR của khách *(mới)*.
   - **Niêm phong đưa về Hub** → nhập mã niêm phong.
   - **Sửa tại chỗ.**
   - **Khoá ô bảo trì.**
5. **KTV tủ** — "Nghiệm thu & Hoàn tất" (bắt buộc ảnh sau sửa) → phiếu `RESOLVED`, ô trả về trạng thái trước khi hỏng.
6. **Khách** — xem tiến độ ở "Báo cáo của tôi" → chấm sao, nhận xét.
7. **Admin** — theo dõi phiếu, SLA, xếp hạng KTV trên web.

Phụ:
- **KTV gia hạn SLA** chỉ khi đang giữ phiếu: tối đa 2 lần × 24 giờ, admin chỉnh được, bắt buộc lý do *(mới)*.
- **KTV "Trả lại phiếu"** về hàng chờ, kèm lý do *(mới)*.
- **Trễ SLA nhiều lần** → bị hạn chế nhận việc.

## 10. Kiểm tra định kỳ

1. **Admin** (web, Bảo trì → Lịch) — tạo lịch kiểm tra tủ hoặc drone, chu kỳ, checklist, giao KTV.
2. **Hệ thống** — tới hạn → thông báo KTV được giao.
3. **KTV** (tab Định kỳ) — "Kiểm tra": từng mục Đạt / Không đạt, ảnh → gửi.
4. **Hệ thống** — có mục không đạt → tự mở phiếu sự cố giao cho KTV đó (drone không đạt → drone `FAULT`); lịch dời sang kỳ sau.

## 11. Mở tủ khẩn cấp (KTV tủ)

1. **KTV tủ** — chọn ô → "Mở tủ khẩn cấp (Master)" → chọn lý do, ghi chú, ảnh (khi mở từ phiếu) *(mới: bắt buộc lý do)*.
2. **Hệ thống** — gửi lệnh mở tới Pi của tủ, ghi nhật ký MASTER kèm lý do → app báo đúng kết quả: đã mở / quá thời gian / lỗi / kẹt chốt.
3. **Hệ thống** — mở thất bại do kẹt chốt → tự đánh dấu ô hỏng + mở phiếu *(mới)*.

## 12. Thiết bị IoT của tủ

1. **Admin** (web, sơ đồ tủ) — gán Pi (theo MAC) cho tủ → gửi sơ đồ ô xuống Pi.
2. **Pi** — gửi tín hiệu định kỳ → hệ thống tính tủ trực tuyến / mất kết nối (tủ mất kết nối thì app khách không cho đặt ô).
3. **KTV tủ** (tab Thiết bị IoT) — xem thiết bị tủ mình phụ trách, lần cuối thấy; "Khởi động lại thiết bị" → Pi khởi động lại tiến trình điều khiển *(mới)*; đánh dấu thiết bị lỗi.

## 13. Đội bay drone

1. **Admin** (web, Drone) — thêm drone, gán trạm (tủ), KTV phụ trách, ngừng hoạt động.
2. **KTV drone** (tab Đội bay) — "Nhận xử lý" drone → đổi trạng thái: Sẵn sàng / Đang sạc / Bảo trì / Lỗi (bắt buộc lý do → mở phiếu drone); cập nhật pin; ghi nhật ký bảo trì.
3. **Hệ thống** — không cho về Sẵn sàng khi còn phiếu mở; drone đang bay không đặt Lỗi trực tiếp (phải báo chuyến bay thất bại) *(mới)*.
4. **KTV drone** (tab Sự cố) — nhận phiếu drone → xử lý → nghiệm thu (ảnh sau sửa) → drone trở lại phục vụ.

---

## 14. Ví

**Nạp tiền**
1. **Khách** — "Nạp ví": chọn số tiền, chuyển khoản VietQR/SePay → chuyển khoản / thanh toán.
2. **Hệ thống** — nhận xác nhận từ cổng thanh toán (webhook) → cộng ví. App chỉ báo "thành công" khi thấy tiền đã vào *(mới)*.

**Rút tiền**
1. **Khách** — "Rút tiền": ngân hàng, số tài khoản, tên, số tiền (≥ 10.000đ) → ví bị trừ ngay, yêu cầu "Chờ duyệt".
2. **Admin** — chuyển khoản thủ công → "Duyệt", hoặc "Từ chối" (tiền hoàn lại ví).
3. **Khách** — xem trạng thái ở "Yêu cầu rút tiền" *(mới)*.

## 15. Khuyến mãi, voucher, điểm thưởng

1. **Admin** — tạo khuyến mãi: mã, % hoặc số tiền, thời gian, giới hạn lượt.
2. **Khách** — xem "Ưu đãi", "Lưu" voucher → khi thanh toán chọn mã (khuyến mãi đang chạy hoặc voucher đã lưu) → giảm giá.
3. **Hệ thống** — đơn hoàn tất đã thanh toán → cộng điểm (mặc định 1 điểm / 1.000đ) *(mới)*; khách xem điểm, hạng (Đồng → Bạch kim), lịch sử ở "Điểm thưởng".

## 16. Đánh giá và phản hồi

1. **Khách** — đơn hoàn tất: chấm sao + nhận xét, hoặc gửi khiếu nại *(mới trên app)*.
2. **Admin** (web, Phản hồi) — xem đánh giá, "Gửi phản hồi" (khách nhận thông báo), "Đánh dấu đã xử lý"; xem thống kê theo ngày/tuần/tháng, NPS.

## 17. Trợ lý AI hỏi đáp (RAG)

1. **Admin** (web, Kho tri thức) — tải tài liệu PDF/DOCX/MD, chọn vai trò được xem → hệ thống chia đoạn, tạo embedding.
2. **Khách / KTV** (app, Trợ lý AI) — đặt câu hỏi → trả lời kèm nguồn trích dẫn, chỉ từ tài liệu vai trò đó được xem; ngoài phạm vi → từ chối.
3. **Admin** — xem hội thoại, đánh giá, chạy bộ đánh giá truy xuất.

## 18. Thông báo

1. **Hệ thống** — sự kiện (đơn đổi trạng thái, mã lấy hàng, phiếu được giao, lịch tới hạn, hoàn tiền, phản hồi…) → gửi push + lưu thông báo trong app.
2. **Người dùng** — bấm thông báo → app mở đúng màn theo vai trò (đơn, phiếu, lịch, theo dõi drone) *(mới)*; xoá một / xoá tất cả *(mới)*.
3. **Admin** — gửi thông báo / broadcast tới người dùng.

## 19. Cấu hình và job định kỳ (admin)

1. **Admin** (web, Cấu hình nghiệp vụ) — giá dịch vụ, phương thức thanh toán, hạn lấy / thời gian ân hạn, giới hạn drone (tầm bay, khung giờ, tạm dừng bay), số lần gia hạn SLA… → áp dụng ngay.
   - **Admin** (web, **Thời tiết & bay** `/admin/flight-control`) — xem thời tiết từng trạm, tạm dừng bay toàn hệ thống hoặc **từng trạm** (lý do, ghi chú, giờ tự mở lại), chỉnh ngưỡng thời tiết (gió, gió giật, tầm nhìn, lượng mưa, mưa/dông, khoảng dự báo), xem **lịch sử chặn bay** (đơn nào bị chặn vì thời tiết hoặc lệnh dừng, ở bước nào, lúc nào) và nhật ký dừng trạm. *(mới)*
2. **Hệ thống** (job định kỳ, admin có thể "Chạy ngay") — tự huỷ đơn chưa thanh toán, nhắc lấy hàng, chuyển hàng quá hạn ra kho / nhả ô, đối soát ô.
3. **Admin** — dashboard: doanh thu, đơn theo trạng thái, giờ cao điểm, tăng trưởng người dùng, top địa điểm.
