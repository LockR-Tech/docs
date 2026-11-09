# Review 2 (SEP490) – FA26SE002 (nhóm GFA26SE32)

| Đường dẫn | Nội dung |
|---|---|
| `bieu-mau/` | Hướng dẫn chuẩn bị Review 2 (PDF) và 4 biểu mẫu của môn: BM01 Design Brief, BM02 Self Review Report, BM03 Record of Changes, BM04 Review 2 Commitment |
| `FA26SE002_Registration_v2.0.docx` / `.pdf` | Phiếu đăng ký bản 2.0 = phiếu ký 17/08/2026 (`../FA26SE002_DRONE_DELIVERY_AND_SMART_LOCKER_MANAGEME_ducdnm2.docx`, không sửa) bỏ phần nghiên cứu, bỏ AI tóm tắt báo cáo, thêm Module 3 báo cáo sự cố trước bảo trì, thêm lắp đặt tủ ở Module 4, cập nhật Software & Hardware Products, NFR theo Design Brief §7, ghi đúng cách nhận hàng (PIN ở kiosk; Bluetooth hoặc quét QR tủ trên app) |
| `SEP490_FA26SE002_R2_DesignBrief.docx` / `.pdf` | BM01 – Design Brief |
| `SEP490_FA26SE002_R2_RecordOfChanges.docx` / `.pdf` | BM03 – Record of Changes của phiếu đăng ký (bản 1.0 → 2.0), nộp chung với phiếu trong `SEP490_FA26SE002_R2_Registration.pdf` |
| `SEP490_FA26SE002_R2_SelfReview.docx` / `.pdf` | BM02 – kết quả gốc của prompt chuẩn (Claude Code, Claude Opus 5.5) trên tag `review-2` + Team response |
| `SEP490_FA26SE002_R2_Commitment.docx` / `.pdf` | BM04 – bản nháp trước buổi review (0.1); hoàn thiện trong 3 ngày làm việc sau Review 2 |
| `build_registration.py`, `build_brief.py`, `build_bm02.py`, `build_bm03.py`, `build_bm04.py` | Dựng từng biểu mẫu từ `bieu-mau/` — nội dung nằm ở các danh sách đầu file |
| `merge_registration.py` | Ghép phiếu 2.0 và BM03 thành `SEP490_FA26SE002_R2_Registration.pdf` (file nộp) |
| `ci_test_map.py` | Đối chiếu 127 test case cam kết (BM04 §6) với test tự động đang chạy trong CI ở tag `review-2` (`Lớp#phương thức`, `None` = chưa tự động); BM04 đếm cột "Automated in CI" từ file này |
| `formfill.py` | Hàm dùng chung: điền bảng, đổi nhãn `SWP490` → `SEP490`, tô vàng chỗ chờ nhóm, xoá hướng dẫn xám |
| `to_pdf.ps1` | Xuất PDF bằng Word, in trang bắt đầu của từng mục (BM01 mục 0–8 tối đa 4 trang) |

## Dựng lại

```powershell
cd review-2
foreach ($f in 'build_registration','build_brief','build_bm02','build_bm03','build_bm04') { uv run --offline --no-project --with python-docx python "$f.py" }
foreach ($n in 'FA26SE002_Registration_v2.0','SEP490_FA26SE002_R2_DesignBrief','SEP490_FA26SE002_R2_SelfReview','SEP490_FA26SE002_R2_RecordOfChanges','SEP490_FA26SE002_R2_Commitment') {
  powershell -ExecutionPolicy Bypass -File to_pdf.ps1 -Docx "$PWD\$n.docx" -Pdf "$PWD\$n.pdf" }
uv run --offline --no-project --with pymupdf python merge_registration.py   # phiếu 2.0 + BM03 -> SEP490_FA26SE002_R2_Registration.pdf
```

Sửa nội dung trong các `build_*.py` rồi chạy lại, không sửa tay file `.docx` (lần dựng sau sẽ ghi đè).
BM04 đọc tính năng, NFR, workflow, kịch bản demo từ `build_brief.py` và việc phải sửa từ `build_bm02.py`,
nên chỉ cần sửa một chỗ.

**BM02:** `FINDINGS` và `TOP5` là kết quả gốc của AI — không sửa, không xoá dòng (hướng dẫn mục 05).
Chỉ nhóm điền / sửa `RESPONSE` (Fixed kèm link commit, Kept kèm lý do, Planned kèm người và hạn).

## Còn phải điền tại / sau buổi Review 2 (tô vàng trong BM04)

- BM04: các mục ghi nhận trong biên bản Review 2 — điền vào `MINUTES` trong `build_bm04.py` (mỗi mục: việc, người, hạn), sẽ thành RF-25…; ngày Defense 1.1 cụ thể khi có lịch (hiện ghi "Before Defense 1.1"); phần kết quả xác minh và chữ ký do giảng viên điền.
- Số test tự động trong CI (107/127) lấy từ `ci_test_map.py`; khi thêm test mới vào CI thì sửa mục `None` tương ứng rồi dựng lại BM04.

## Cách chia việc (cân bằng đều cho 4 thành viên)

- **4 workflow** theo các luồng nhóm demo (1 workflow / thành viên):
  - `WF-01` Giao hàng bằng drone, lấy hàng tận nhà (`Vi`)
  - `WF-02` Thuê ô / gửi hàng qua tủ (`Huy`)
  - `WF-03` Báo sự cố ô đến khi xử lý xong (`Bình`)
  - `WF-04` Bảo trì định kỳ tủ và drone (`Nhã`)
- **20 tính năng bắt buộc** chia đều **5 tính năng / thành viên**:
  - `Vi` (5): `F-10, F-11, F-12, F-17, F-20`
  - `Bình` (5): `F-02, F-03, F-04, F-06, F-13`
  - `Huy` (5): `F-01, F-05, F-07, F-09, F-16`
  - `Nhã` (5): `F-08, F-14, F-15, F-18, F-19`
- **8 kịch bản demo** chia đều **2 kịch bản (1 chính + 1 ngoại lệ) / thành viên**: `DS-01a/b` (`Vi`), `DS-02a/b` (`Huy`), `DS-03a/b` (`Bình`), `DS-04a/b` (`Nhã`).
- **127 test case chức năng** = 20 tính năng × 3 + 4 workflow + 57 chuyển trạng thái + 6 NFR, chia đều **32, 32, 32, 31 test / thành viên** (`Vi: 32, Bình: 32, Huy: 32, Nhã: 31`).
- **24 việc phải sửa (`Planned` trong BM02 → `RF-01..RF-24` trong BM04)** chia đều **6 việc / thành viên** (`Vi: 6, Bình: 6, Huy: 6, Nhã: 6`).

