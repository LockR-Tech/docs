# Review 2 (SWP490) – FA26SE002 (nhóm GFA26SE32)

| Đường dẫn | Nội dung |
|---|---|
| `bieu-mau/` | Hướng dẫn chuẩn bị Review 2 (PDF) và 4 biểu mẫu của môn: BM01 Design Brief, BM02 Self Review Report, BM03 Record of Changes, BM04 Review 2 Commitment |
| `FA26SE002_Registration_v2.0.docx` / `.pdf` | Phiếu đăng ký bản 2.0 = phiếu ký 17/08/2026 (`../FA26SE002_DRONE_DELIVERY_AND_SMART_LOCKER_MANAGEME_ducdnm2.docx`, không sửa) bỏ phần nghiên cứu, bỏ AI tóm tắt báo cáo, thêm Module 3 báo cáo sự cố trước bảo trì, NFR theo Design Brief §7, ghi đúng cách nhận hàng (PIN ở kiosk; Bluetooth hoặc quét QR tủ trên app) |
| `SWP490_FA26SE002_R2_DesignBrief.docx` / `.pdf` | BM01 – Design Brief |
| `SWP490_FA26SE002_R2_RecordOfChanges.docx` / `.pdf` | BM03 – Record of Changes của phiếu đăng ký (bản 1.0 → 2.0), nộp chung với phiếu trong `..._R2_Registration.pdf` |
| `SWP490_FA26SE002_R2_SelfReview.docx` / `.pdf` | BM02 – kết quả gốc của prompt chuẩn (Claude Code, Claude Opus 5.5, 08/11/2026) + Team response |
| `SWP490_FA26SE002_R2_Commitment.docx` / `.pdf` | BM04 – bản nháp trước buổi review (0.1); hoàn thiện trong 3 ngày làm việc sau Review 2 |
| `build_registration.py`, `build_brief.py`, `build_bm02.py`, `build_bm03.py`, `build_bm04.py` | Dựng từng biểu mẫu từ `bieu-mau/` — nội dung nằm ở các danh sách đầu file |
| `merge_registration.py` | Ghép phiếu 2.0 và BM03 thành `SWP490_FA26SE002_R2_Registration.pdf` (file nộp) |
| `formfill.py` | Hàm dùng chung: điền bảng, tô vàng chỗ chờ nhóm, xoá hướng dẫn xám |
| `to_pdf.ps1` | Xuất PDF bằng Word, in trang bắt đầu của từng mục (BM01 mục 0–8 tối đa 4 trang) |

## Dựng lại

```powershell
cd review-2
foreach ($f in 'build_registration','build_brief','build_bm02','build_bm03','build_bm04') { uv run --no-project --with python-docx python "$f.py" }
foreach ($n in 'FA26SE002_Registration_v2.0','SWP490_FA26SE002_R2_DesignBrief','SWP490_FA26SE002_R2_SelfReview','SWP490_FA26SE002_R2_RecordOfChanges','SWP490_FA26SE002_R2_Commitment') {
  powershell -ExecutionPolicy Bypass -File to_pdf.ps1 -Docx "$PWD\$n.docx" -Pdf "$PWD\$n.pdf" }
uv run --no-project --with pymupdf python merge_registration.py   # phiếu 2.0 + BM03 -> SWP490_FA26SE002_R2_Registration.pdf
```

Sửa nội dung trong các `build_*.py` rồi chạy lại, không sửa tay file `.docx` (lần dựng sau sẽ ghi đè).
BM04 đọc tính năng, NFR, workflow, kịch bản demo từ `build_brief.py` và việc phải sửa từ `build_bm02.py`,
nên chỉ cần sửa một chỗ.

**BM02:** `FINDINGS` và `TOP5` là kết quả gốc của AI — không sửa, không xoá dòng (hướng dẫn mục 05).
Chỉ nhóm điền / sửa `RESPONSE` (Fixed kèm link commit, Kept kèm lý do, Planned kèm người và hạn).

## Còn phải làm (tô vàng trong file)

- Phiếu chỉ sửa 4 nhóm (BM03 No. 1–6); các điểm lệch khác giữa phiếu và hệ thống ghi ở BM02 (SR-07, SR-28: Kept).
  BM03 No. 6: nhóm xác nhận lý do (tô vàng).
- BM02: nhóm duyệt cột Team response; gắn tag `review-2` trên cả 5 repo và chạy lại prompt nếu code đổi sau 08/11.
- BM04: số test tự động, thành viên hỗ trợ, ngày Review 2, tên giảng viên phản biện, ngày Defense 1.1;
  phần kết quả và chữ ký do giảng viên điền.

## Cách chia việc

- 4 workflow theo các luồng nhóm demo (chốt 09/11/2026): WF-01 giao hàng bằng drone, lấy hàng tận nhà (Vi);
  WF-02 thuê ô / gửi hàng qua tủ (Huy); WF-03 báo sự cố ô (Bình); WF-04 bảo trì tủ và drone (Nhã).
  "Thống kê, báo cáo" là tính năng F-20 (không đủ điều kiện workflow: chỉ admin xem số liệu, không đổi trạng thái),
  demo cuối DS-01a và DS-02a.
- Chủ sở hữu tính năng, module (BM01 §8, BM04) theo người viết phần lớn code trên `origin/main` (git blame,
  08–09/11/2026); riêng F-14, F-18, F-19 giao Nhã theo WF-04 (code lịch bảo trì phần lớn của Huy và Bình).
- 127 test = 20 tính năng × 3 + 4 workflow + 57 chuyển trạng thái (Order 9, Box 15, Stage 18, Drone 11, Ticket 4,
  đếm trên sơ đồ `docs/rp3/srs-assets/drawio`) + 6 NFR. Test chuyển trạng thái được chia để mỗi người khoảng 32 test
  (`STATE_TESTS` trong `build_bm04.py`); `build_bm04.py` dừng nếu tổng theo workflow, theo người và Phụ lục A3 lệch nhau.
