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

- Dữ liệu bảng: `parse_entities.py` đọc JPA entity trong repo `backend` (đặt cạnh repo `docs`) → `entities.json`;
  bảng của assistant-service khai báo trong `erd_data.py`. `fk_nullability.py` → `fk_notnull.json` (FK có NOT NULL
  hay không, quyết định ký hiệu `|` / `o|` ở phía bảng cha).
- Mọi script đều tự kiểm tra trước khi xuất: không đường nào cắt nhau, không đi xuyên qua ô/bảng.
- Xuất PNG cần Chrome (đổi đường dẫn bằng biến môi trường `CHROME`) và file viewer của draw.io đặt tại
  `_generator/viewer-static.min.js` (tải từ `https://viewer.diagrams.net/js/viewer-static.min.js`; không commit).
