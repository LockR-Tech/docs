# Luật tài liệu — docs-as-code

Quyết định: [ADR-0002](../adr/0002-docs-as-code-repo-trung-tam.md). Tóm tắt thao tác cho agent: [AGENTS.md § 3](../AGENTS.md#3-kết-thúc-phiên--definition-of-done).

## 1. Nguyên tắc

1. **Một nguồn sự thật cho mỗi loại thông tin** — không chép cùng nội dung ra hai nơi.

   | Thông tin | Nguồn sự thật duy nhất |
   |---|---|
   | Tiến độ, việc đang làm, ưu tiên, rủi ro | `STATUS.md` |
   | Checklist, % và gap của một luồng | `02-flows/flow-N-*.md` |
   | Trạng thái và chuyển trạng thái | `diagrams/src/*.mmd` (sơ đồ + bảng `@row`) |
   | Service, port, route, queue, secret (tên) | `01-overview/architecture.md` |
   | Quy trình Git, commit, deploy | `04-engineering/*.md` |
   | Lý do một quyết định | `adr/NNNN-*.md` |
   | Lịch sử thay đổi tài liệu | `CHANGELOG.md` |

2. **Code thắng tài liệu.** Thấy lệch ⇒ sửa tài liệu ngay trong PR đang làm, hoặc mở PR `docs` riêng.
3. **Có bằng chứng.** Mọi khẳng định về hành vi hệ thống kèm `repo/đường/dẫn:dòng`.
4. **Tài liệu đi cùng code.** PR code thay đổi hành vi mà thiếu cập nhật tài liệu = PR chưa xong.
5. **Ngày tuyệt đối.** Viết `2026-09-13`, không viết "hôm qua", "tuần sau".

## 2. Thay đổi nào ⇒ sửa tài liệu nào

| Thay đổi trong code | STATUS | flow-N | diagrams | architecture | engineering | ADR | CHANGELOG |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Bắt đầu / xong một gap | ✅ | ✅ | | | | | ✅ |
| Thêm/bỏ trạng thái hoặc chuyển trạng thái | ✅ | ✅ | ✅ | | | | ✅ |
| Endpoint công khai mới / đổi phân quyền | ✅ | ✅ | | ✅ | | | ✅ |
| Service, queue, topic MQTT, biến môi trường, secret mới | | | ✅ nếu đổi thành phần | ✅ | ✅ nếu đổi deploy | cân nhắc | ✅ |
| Phát hiện / vá lỗ hổng | ✅ § 2 | ✅ | | | | | ✅ |
| Đổi quy trình Git/deploy/review | | | | | ✅ | ✅ | ✅ |
| Chọn công nghệ / nhà cung cấp mới | ✅ § 6 | | | ✅ | | ✅ | ✅ |
| Sửa lỗi nhỏ không đổi hành vi được mô tả | — ghi "không ảnh hưởng tài liệu" trong PR | | | | | | |

## 3. PR code và PR docs

- Nhánh docs dùng **cùng tên** với nhánh code: `feat/f2-g01-kiosk-pickup-complete` ở cả hai repo.
- PR code ghi link PR docs; PR docs ghi link PR code.
- **Merge PR code trước**, xác nhận deploy ổn, rồi merge PR docs — để STATUS không báo "xong" cho việc chưa lên production.
- `AGENTS.md` trong repo code chỉ là **con trỏ** tới repo này. Không ghi tiến độ, checklist hay quyết định vào đó — dù thay đổi nhỏ.

## 4. Sơ đồ

- Nguồn: `diagrams/src/<tên>.mmd` (Mermaid). Kết quả: `diagrams/pdf/<tên>.pdf`. **Commit cả hai.**
- **Mỗi sơ đồ đúng 1 trang A4** (dọc hoặc ngang). Script `npm run diagrams` in PDF và **fail** nếu > 1 trang hoặc chữ bị thu nhỏ dưới 40 %.
- CI `diagrams.yml` render lại mọi sơ đồ trên mỗi PR đụng tới `diagrams/` hoặc `scripts/`.
- Metadata ở đầu file `.mmd`:

  ```text
  %% @title       Tiêu đề trang
  %% @subtitle    Nguồn code + ngày rà soát
  %% @orientation portrait | landscape
  %% @legend      <span class="sw ok"></span>Chú thích màu     (lặp được)
  %% @row         T1 | A → B | kích hoạt | ai | điều kiện       (lặp được)
  %% @note        Ghi chú cuối trang                           (lặp được)
  ```

  Mã đầu dòng `@row`: `~` = CHƯA code (xám, nghiêng) · `!` = chỉ DEMO (vàng) · `x` = lỗ hổng (đỏ).
- Quy ước màu: xanh = chạy thật · vàng = chỉ DEMO/sandbox · đỏ = lỗi hoặc rủi ro · xám nét đứt = cần có nhưng chưa code · xanh dương = trạng thái kết thúc.
- Trên sơ đồ trạng thái, mũi tên chỉ ghi **mã chuyển** (T1, O3…); chi tiết nằm trong bảng `@row` để sơ đồ không rối.
- Quá chật một trang ⇒ tách thành hai sơ đồ, không thu nhỏ chữ.

## 5. Văn phong

- Tiếng Việt có dấu. Tên kỹ thuật (class, endpoint, enum, biến) giữ nguyên tiếng Anh trong `code`.
- Câu ngắn, bảng thay cho đoạn văn khi liệt kê. Người đọc là thành viên mới hoặc agent mở dự án lần đầu.
- Không đưa secret, dữ liệu cá nhân, tài khoản thật vào tài liệu.
- File mới: chữ thường, kebab-case, tiếng Anh không dấu (`flow-2-locker-send.md`).

## 6. ADR — khi nào viết

Viết ADR khi quyết định **khó đảo ngược** hoặc **ảnh hưởng nhiều repo/người**: chọn công nghệ, đổi quy trình, đổi hợp đồng giữa các thành phần, chấp nhận một rủi ro. Mẫu: [adr/0000-template.md](../adr/0000-template.md). ADR đã `Accepted` không sửa nội dung — muốn đổi thì viết ADR mới `Supersedes ADR-NNNN`.
