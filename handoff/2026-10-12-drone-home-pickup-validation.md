# Nghiệm thu lấy hàng tận nhà — 2026-10-12

Nhánh local: `feat/f1-g12-drone-home-pickup`. Chưa commit/merge/deploy.

## Kiểm chứng

- Mobile: `flutter test --reporter compact`, 321/321 test qua.
- Backend: `mvn -B clean test -Dcyclonedx.skip=true` trên toàn reactor, JDK 21: **BUILD SUCCESS**, 608 test qua, 0 thất bại, 0 lỗi, 0 bỏ qua (89 báo cáo XML). Docker/PostgreSQL/pgvector thật được bật cho test tích hợp.
- PostgreSQL order-service: 14 test giao không hoàn tất, 13 test lấy hàng tận nhà, 2 test migration/schema qua; không bị bỏ qua.
- Bản build JAR toàn backend: `mvn -B package -DskipTests -Dcyclonedx.skip=true` **BUILD SUCCESS trên 14 module**, tạo JAR của 12 service và common-lib. Không chạy lại test vì code không đổi. Kết thúc 21:26 ngày 2026-10-12 (UTC+7).
- Admin web: `npm test` qua 3/3 test quy tắc; lint riêng tất cả file trong đợt sửa 0 lỗi/0 cảnh báo. `npm run lint` toàn repo 0 lỗi, còn 70 cảnh báo ở code cũ. Đã xoá script cập nhật nhãn tạm; `git diff --check` sạch. `npm run build` (TypeScript + Vite production) thành công, còn cảnh báo chunk lớn hơn 500 kB. Chưa bấm thử toàn luồng trên trình duyệt với backend deploy.

## Admin web trong đợt sửa

Chi tiết `/admin/drone-orders` hiển thị lấy hàng tận nhà, địa chỉ/bản đồ, KTV, mốc nhận việc/lấy hàng, ghi chú, người gửi/người nhận và email; admin gán tay trước khi lấy kiện. Điều kiện UI dùng `homePickupRules.ts`, có test chống gán sau khi lấy hàng và chống đóng luồng rơi kiện bằng form giao không hoàn tất.

Đơn bị ảnh hưởng mở trực tiếp chi tiết phiếu/nhật ký; phiếu có các đơn liên quan và mở được đơn bằng `?orderId=`. Đơn giao không hoàn tất hiển thị lý do, phiếu và yêu cầu hoàn tiền thật; liên kết `/admin/payments?tab=refunds&orderId=` lọc đúng đơn. Form cũ chỉ báo thất bại sau phóng được thay bằng form dùng mã lý do mới trước/sau phóng, giữ nguyên trang sự cố rơi kiện. Nhãn mới có tiếng Việt/Anh.

Log nằm trong backend: `backend-test-admin-review-approved.log`, `backend-package-admin-review.log`; log mobile: `mobile-test-admin-review-approved.log`. Các log là đầu ra local, không đưa vào commit. Lượt test đầu trong sandbox bị lỗi đầu ra class và không truy cập được Docker; kết quả nghiệm thu chỉ dùng lượt build sạch có quyền truy cập Docker này.

## Quy tắc đã sửa trong đợt rà soát

- KTV có nhiệm vụ đang bay vẫn bận, gồm cả `DROP_REPORTED`: `backend/order-service/src/main/java/com/huynqb/laundrylocker/order/service/DronePickupService.java`.
- Tủ gửi phải có drone IDLE đang hoạt động, pin đã biết và trên ngưỡng trước bay, cùng ô DRONE trống và bãi đáp sẵn sàng: `DroneSourceLockerSelector.java`, `DroneSourceLockerSelectorTest.java`.
- Trước khi tự đóng đơn vì drone lỗi, job thử đổi sang drone rảnh cùng tủ, yêu cầu nạp/checklist lại và không đổi drone sau launch: `DroneDispatchSweeper.java`, `it/DroneDeliveryFailureFlowPostgresTest.java`.
- Đơn đang bay vẫn đánh dấu bị ảnh hưởng khi tủ/bãi đáp hoặc thời tiết chặn phục vụ; không tự đóng chuyến đang bay, cần đội bay xác nhận: `DroneDeliveryBlockService.java`.

## Giới hạn nghiệm thu nghiệp vụ

Test tích hợp dùng PostgreSQL thật nhưng mock các service ngoài order-service. Chưa nghiệm thu liên service, email SMTP thật hoặc drone vật lý.

Yêu cầu cân và niêm phong ngay tại nhà hiện chưa có field bắt buộc ở bước xác nhận lấy hàng (`DronePickupConfirmRequest` chỉ gồm mã lấy hàng, đối chiếu kiện, ghi chú). Cân/checklist/niêm phong vẫn lưu ở lúc nạp drone. Vì vậy chưa thể kết luận khớp 100% với bước 4 người dùng mô tả.
