# ADR-0010: Chữ server tự soạn được dịch sang tiếng Anh ở tầng response, theo bảng câu Việt → Anh

| | |
|---|---|
| **Trạng thái** | Proposed |
| **Ngày** | 2026-11-02 |
| **Người quyết định** | binhtntse182370 |
| **Liên quan** | mobile [#112](https://github.com/LockR-Tech/mobile/pull/112), [#113](https://github.com/LockR-Tech/mobile/pull/113) (app có tiếng Anh) · backend [#126](https://github.com/LockR-Tech/backend/pull/126), mobile [#114](https://github.com/LockR-Tech/mobile/pull/114) |

## Bối cảnh

App khách và màn KTV tủ đã có tiếng Anh. Chữ do server soạn vẫn là tiếng Việt viết thẳng trong code Java, nên khách chọn tiếng Anh vẫn thấy tiếng Việt ở:

- câu báo lỗi trong toast,
- tiêu đề và nội dung thông báo (danh sách, realtime, push FCM),
- ghi chú mốc đơn và nhật ký xử lý sự cố của KTV.

Có khoảng 1.100 câu như vậy. Nhiều câu ghép giá trị động, ví dụ `"Đơn " + code + " đã hoàn tất"`. Thông báo đã lưu trong DB bằng tiếng Việt.

App còn dò một số câu server bằng chữ tiếng Việt: tag `[ĐIỀU CHUYỂN Ô]`, cụm "sang ô #5" ở màn đơn khách và màn KTV, "đã tồn tại" khi đăng ký.

## Các phương án đã cân nhắc

| Phương án | Ưu | Nhược |
|---|---|---|
| Message bundle (`messages_en.properties`) và đổi từng chỗ ném lỗi sang mã khoá | Chuẩn Spring | Phải sửa khoảng 1.100 chỗ trong 11 service. Thông báo đã lưu trong DB vẫn tiếng Việt. Không dịch được push |
| Bảng dịch đặt trong app | Không phải deploy backend | Bảng nằm xa code sinh câu nên dễ lệch. Phải sửa mọi chỗ hiển thị. Push hiện ngoài app vẫn tiếng Việt |
| **Bảng câu Việt → Anh trong `common-lib`, dịch JSON lúc ghi response khi app gửi `X-App-Language: en`** | Không phải sửa code sinh câu. Dịch được cả dữ liệu đã lưu. Bảng nằm cạnh code, có script kiểm câu thiếu | Khớp theo nguyên câu nên câu mới phải được thêm vào bảng. Câu do người gõ (ghi chú KTV, phản hồi) vẫn giữ nguyên |

## Quyết định

- Bảng dịch đặt ở `backend/common-lib/src/main/resources/i18n/server-text-en.json`. Khoá là câu tiếng Việt đúng như trong code, `{}` thay cho phần ghép động; giá trị là câu tiếng Anh (`{0}` `{1}` khi cần đổi thứ tự).
- `ServerText` (`backend/common-lib/…/common/i18n/ServerText.java`) dịch theo thứ tự:
  1. khớp nguyên câu;
  2. khớp mẫu câu có `{}`, và phần ghép động có tiếng Việt cũng được dịch tiếp;
  3. tách theo dòng hoặc câu rồi dịch từng phần;
  4. thay các mảnh câu ghép bằng `StringBuilder` (mảnh bắt đầu hoặc kết thúc bằng khoảng trắng).

  Mẫu có quá ít chữ cố định (`"Tủ {}"`) chỉ dùng cho phần ghép bên trong câu khác, để tên tủ do admin đặt không bị đổi.
- `EnglishResponseAdvice` (`ResponseBodyAdvice` trong `common-lib`, mọi service quét gói `common`) chỉ chạy khi request có `X-App-Language: en`. Nó dựng cây JSON của body (cả body lỗi từ `GlobalExceptionHandler`) rồi dịch mọi giá trị chuỗi. Tin RabbitMQ, lời gọi giữa các service và WebSocket không đi qua advice này, nên dữ liệu lưu trong DB không đổi.
- Chỉ app mobile gửi header này (`AppLanguageInterceptor`). Web admin và kiosk không gửi nên không đổi gì. Không dùng `Accept-Language` vì trình duyệt tự gửi header đó theo ngôn ngữ máy.
- Push FCM: `fcm_tokens.language` (notification **V3**) lưu theo header lúc app đăng ký token. App đổi ngôn ngữ thì đăng ký lại token. Máy chọn `en` nhận tiêu đề và nội dung đã dịch, cả trong `data`. Tin `/user/queue/notifications` dịch theo token đăng ký gần nhất của người đó.
- Không dịch thư email/SMS, prompt và tài liệu của trợ lý, mô tả cài đặt admin. Trợ lý (Claude) đã tự trả lời theo ngôn ngữ của câu hỏi.

## Hệ quả

- **Tích cực:**
  - Khách dùng tiếng Anh thấy lỗi, thông báo, push và ghi chú mốc đơn bằng tiếng Anh, kể cả thông báo cũ.
  - Người dùng tiếng Việt và web admin không bị ảnh hưởng gì.
- **Tiêu cực / đánh đổi chấp nhận:**
  - Thêm hoặc sửa câu tiếng Việt ở server mà không thêm vào bảng thì câu đó hiện tiếng Việt cho khách dùng tiếng Anh. Kiểm bằng `python -I backend/scripts/i18n/server_text_missing.py`, script trả mã thoát 1 khi còn câu thiếu.
  - Chữ người gõ không được dịch: ghi chú và lý do của KTV/admin, phản hồi đánh giá, tên tủ.
  - Response tiếng Anh tốn thêm một lượt dựng cây JSON.
  - Code app dò câu server phải hiểu cả hai ngôn ngữ (`mobile/lib/core/utils/server_note_keys.dart`).
- **Việc phải làm theo sau:**
  - Nếu cần thì gắn script kiểm câu thiếu vào CI.
  - Thư email/SMS gửi theo ngôn ngữ người nhận (cần lưu ngôn ngữ trên hồ sơ người dùng).
