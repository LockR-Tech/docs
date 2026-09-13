# Changelog

Mỗi thay đổi ở repo docs thêm **một dòng** vào ngày tương ứng (mới nhất ở trên). Ghi mã gap/SEC/ADR nếu có.

## 2026-09-13

- STATUS: thêm SEC-09 (CVE trong image backend do Trivy phát hiện), Q4 (dependency-review/CodeQL cần GitHub Advanced Security trên repo private), ghi nhận PR #1 ở frontend/mobile/iot/legal.

- Khởi tạo repo `docs`: README, AGENTS/CLAUDE, STATUS, tổng quan sản phẩm, kiến trúc, luật Git/commit/deploy/tài liệu, ADR-0001…0003.
- Rà soát code 4 luồng tại backend `705c556`, frontend `e1b9a73`, mobile `5890184`, iot `927b057`: L1 60 %, L2 65 %, L3 45 %, L4 0 %.
- L2 hạ F2.04 từ DONE xuống PARTIAL sau khi xác minh bug `send_parcel_page.dart:377-382` (xác nhận bỏ hàng bằng id payment).
- Ghi nhận rủi ro SEC-01…SEC-08.
- Thêm 5 sơ đồ A4: kiến trúc, trạng thái đơn hàng, vòng đời giao hàng drone, trạng thái drone, trạng thái ô tủ; script `render-a4.mjs` + CI kiểm tra 1 trang.
