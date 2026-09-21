# Lock.R — Tổng quan sản phẩm

## Lock.R là gì

Hệ thống **tủ khoá thông minh kết hợp giao hàng bằng drone**. Người dùng thuê ô tủ để gửi/giữ hàng và chuyển mã cho người nhận, hoặc đặt drone chở hàng tới một tủ có bãi đáp. Mỗi tủ là một cụm ô điều khiển bằng Raspberry Pi + Arduino, có màn hình kiosk để nhập mã. Nhân viên kỹ thuật và đội drone vận hành, bảo trì qua ứng dụng di động; quản trị viên dùng web.

Tên miền production: `locker-drone.tech` (landing) · `admin.locker-drone.tech` (quản trị) · `api.locker-drone.tech` (API).

## Người dùng & vai trò

| Vai trò | Ai | Kênh | Việc chính |
|---|---|---|---|
| `CUSTOMER` | Người gửi, người thuê, người nhận có tài khoản | App mobile, mobile web, kiosk | Tìm tủ, thuê/gửi hàng, thanh toán, theo dõi drone, nhận hàng, báo hỏng |
| Người nhận không tài khoản | Người được gửi mã | Kiosk tại tủ | Nhập PIN / quét QR để lấy hàng |
| `LOCKER_TECHNICIAN` | Kỹ thuật viên tủ | App mobile | Xử lý ô hỏng, ticket, vệ sinh, mở cưỡng bức, lịch bảo trì, thiết bị IoT |
| `DRONE_TECHNICIAN` | Kỹ thuật viên drone (đội bay) | App mobile | Quản lý đội drone, nhận – nạp – phóng – huỷ đơn drone |
| `ADMIN` | Quản trị | Web (2FA) | Người dùng & vai trò, cửa hàng, tủ, drone, đơn, thanh toán, ví, khuyến mãi, thông báo |

## Bốn luồng nghiệp vụ chính

| | Luồng | Mô tả mục tiêu | Tài liệu |
|---|---|---|---|
| **L1** | Giao hàng bằng drone | Đặt đơn → thanh toán → điều phối → nạp hàng → bay (theo dõi) → hạ cánh gửi vào ô DRONE → cấp PIN → người nhận lấy | [flow-1](../02-flows/flow-1-drone-delivery.md) |
| **L2** | Thuê tủ gửi hàng | Người gửi giữ ô, trả tiền, bỏ hàng, nhập người nhận → hệ thống gửi mã + thông tin đơn → người nhận nhập mã ở tủ lấy hàng | [flow-2](../02-flows/flow-2-locker-send.md) |
| **L3** | Vai trò & bảo trì | Phân quyền theo vai trò, quản lý đội drone, trạng thái theo vai trò, tài sản hỏng tự chuyển bảo trì → ticket → sửa → hoạt động lại | [flow-3](../02-flows/flow-3-roles-maintenance.md) |
| **L4** | Trợ lý RAG | Nạp tài liệu nội bộ để người dùng hỏi đáp, trả lời có trích nguồn, phân quyền tài liệu theo vai trò | [flow-4](../02-flows/flow-4-rag-assistant.md) |

Tiến độ hiện tại của từng luồng: [STATUS.md](../STATUS.md).

## Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| **Tủ** (locker, cabinet) | Một cụm ô tại một địa điểm, gắn với một cửa hàng (store) |
| **Ô** (box, cell) | Ngăn chứa hàng. Loại `STANDARD`, `XL`, `DRONE` (ô nhận hàng từ drone, cạnh bãi đáp) |
| **Bãi đáp** (landing pad) | Vị trí drone hạ cánh tại tủ, có mã ArUco; trạng thái OK / FAULT / MAINTENANCE |
| **Đơn** (order) | Loại `SEND` (gửi cho người khác), `RENTAL` (thuê ô theo giờ), `STORAGE`, `DRONE_DELIVERY` |
| **PIN / QR** | Mã 6 số / token `LLQR.*` để mở ô; PIN gửi hàng và PIN nhận hàng là hai mã khác nhau |
| **Uỷ quyền** (delegate) | Chủ đơn cấp PIN mới cho người khác lấy hàng |
| **Mission** | Một chuyến bay của drone gắn với một đơn drone |
| **deliveryStage** | Chặng giao hàng drone mà khách nhìn thấy (AWAITING_DISPATCH … READY_FOR_PICKUP) |
| **fulfillmentMode** | `DEMO` (bộ giả lập đẩy chặng bay) hoặc `STANDARD` (cần dữ liệu drone thật) |
| **Ticket** (locker report) | Phiếu báo hỏng: OPEN → IN_PROGRESS → RESOLVED |
| **Claim** | Kỹ thuật viên/đội drone nhận trách nhiệm một ticket hoặc một drone trước khi thao tác |
| **Kiosk** | Màn hình React chạy tại tủ, gọi thẳng API backend |
| **Gap** | Việc còn thiếu để một luồng đạt 100 %, mã `F<n>-G<nn>` |
