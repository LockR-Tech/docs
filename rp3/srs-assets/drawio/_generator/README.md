# Sơ đồ SRS (draw.io) — script sinh lại

Các file `.drawio` / `.png` trong thư mục cha được sinh bằng các script này. Mở `.drawio` bằng draw.io để sửa tay;
muốn sinh lại từ code thì chạy script tương ứng (Python 3.11+, chạy trong thư mục này).

| Script | Sinh ra |
|---|---|
| `gen_context.py` | `01-context-diagram` |
| `gen_usecase.py` | `02-use-case-diagram` |
| `gen_screens_bus.py` | `03a`–`03d` screen flow (customer, locker technician, drone technician, admin web) |
| `gen_cerd_portrait.py 20` | `04-conceptual-erd` |
| `gen_lerd_portrait.py` | `05a`–`05d` logical ERD theo nghiệp vụ |
| `gen_lerd_overview.py 40 8` | `05-logical-erd-overview` (mọi bảng, mọi cột; chạy vài phút) |
| `gen_state_machines.py` | `06-1-state-machine-order` (Order theo status, rẽ nhánh Rental / Drone Delivery) + `06-2-state-machine-drone-delivery-order` (đơn drone chi tiết, khổ ngang) — bản dùng cho SRS · bản cũ: `06-state-machine-order` · `06a`–`06p` state machine diagram của thực thể chính (đủ mọi trạng thái, kể cả hủy / hết hạn / lỗi; tự kiểm 1 start, 1 end, không vòng lặp, mọi trạng thái đi qua được) |
| `gen_activity.py [tên]` | `06a`–`06g` activity diagram UML, swimlane nằm ngang (luồng trái → phải, màu: xanh dương bước thường, xanh lá tủ/drone/thông báo, cam nhánh huỷ/lỗi): gửi hàng, thuê ô, giao drone, hỏi trợ lý AI, quản lý kho tri thức, KTV xử lý phiếu sự cố, kiểm tra định kỳ (mọi service, tủ, drone gộp thành làn **System**; thanh toán SePay nằm trong System) |

- Dữ liệu bảng: `parse_entities.py` đọc JPA entity trong repo `backend` (đặt cạnh repo `docs`) → `entities.json`;
  bảng của assistant-service khai báo trong `erd_data.py`. `fk_nullability.py` → `fk_notnull.json` (FK có NOT NULL
  hay không, quyết định ký hiệu `|` / `o|` ở phía bảng cha).
- Mọi script đều tự kiểm tra trước khi xuất: không đường nào cắt nhau, không đi xuyên qua ô/bảng.
- Xuất PNG cần Chrome (đổi đường dẫn bằng biến môi trường `CHROME`) và file viewer của draw.io đặt tại
  `_generator/viewer-static.min.js` (tải từ `https://viewer.diagrams.net/js/viewer-static.min.js`; không commit).
