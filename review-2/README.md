# Review 2 (SWP490)

| Đường dẫn | Nội dung |
|---|---|
| `bieu-mau/` | Hướng dẫn chuẩn bị Review 2 (PDF) và 4 biểu mẫu của môn: BM01 Design Brief, BM02 Self Review Report, BM03 Record of Changes, BM04 Review 2 Commitment |
| `SWP490_LockR_R2_DesignBrief.docx` / `.pdf` | Design Brief của Lock.R điền trên BM01 (bản nháp v1.0) |
| `build_brief.py` | Dựng Design Brief từ `bieu-mau/` — nội dung nằm ở các danh sách đầu file |
| `to_pdf.ps1` | Xuất PDF bằng Word, in trang bắt đầu của từng mục (mục 0–8 tối đa 4 trang) |

## Dựng lại

```powershell
cd review-2
uv run --no-project --with python-docx python build_brief.py
powershell -ExecutionPolicy Bypass -File to_pdf.ps1 -Docx "$PWD\SWP490_LockR_R2_DesignBrief.docx" -Pdf "$PWD\SWP490_LockR_R2_DesignBrief.pdf"
```

Sửa nội dung trong `build_brief.py` rồi chạy lại, không sửa tay file `.docx` (lần dựng sau sẽ ghi đè).

## Còn phải điền (tô vàng trong file)

- Mã đề tài và mục 1.1 Registration Changes (theo phiếu đăng ký, chi tiết ở BM03).
- G6 trong mục 5: các điểm High còn Kept / Planned của BM02.
- Tag `review-2` trên cả 5 repo lúc nộp.
