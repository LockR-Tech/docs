# Sơ đồ

Mỗi sơ đồ là **đúng một trang A4**, in được. Nguồn Mermaid trong `src/`, PDF trong `pdf/`. Luật vẽ và metadata: [documentation-rules § 4](../04-engineering/documentation-rules.md#4-sơ-đồ).

| Sơ đồ | PDF | Nguồn | Khổ | Dùng cho |
|---|---|---|---|---|
| Kiến trúc hệ thống | [architecture.pdf](pdf/architecture.pdf) | [architecture.mmd](src/architecture.mmd) | A4 ngang | Tổng quan, rủi ro bảo mật |
| Trạng thái đơn hàng (`orders.status`) | [order-status.pdf](pdf/order-status.pdf) | [order-status.mmd](src/order-status.mmd) | A4 dọc | L1, L2 |
| Vòng đời giao hàng drone (`deliveryStage`, mission) | [drone-mission.pdf](pdf/drone-mission.pdf) | [drone-mission.mmd](src/drone-mission.mmd) | A4 dọc | L1 |
| Trạng thái drone (`DroneUnit.status`) | [drone-status.pdf](pdf/drone-status.pdf) | [drone-status.mmd](src/drone-status.mmd) | A4 dọc | L1, L3 |
| Trạng thái ô tủ (`locker_boxes.status`) | [locker-cell-status.pdf](pdf/locker-cell-status.pdf) | [locker-cell-status.mmd](src/locker-cell-status.mmd) | A4 dọc | L2, L3 |

Các sơ đồ trạng thái vẽ **hiện trạng code** và đánh dấu luôn phần **cần có để đạt 100 %** (nét đứt xám), phần **chỉ chạy ở DEMO** (vàng) và **lỗ hổng** (đỏ) — nên chúng vừa là tài liệu vừa là bản đồ việc cần làm. Khi code thay đổi, sửa `.mmd` rồi render lại.

## Render

Cần Node ≥ 20 và Chrome hoặc Edge (hoặc đặt `CHROME_PATH`).

```bash
npm ci
npm run diagrams                  # render tất cả vào pdf/
npm run diagrams -- order-status  # chỉ một sơ đồ
npm run diagrams:check            # chỉ kiểm tra, không ghi pdf/ (CI dùng lệnh này)
```

Kết quả mỗi dòng: `✓ order-status.pdf  pages=1  scale=0.872`. `pages` phải bằng 1; `scale` dưới 0,40 bị coi là lỗi vì chữ in ra quá nhỏ — hãy tách sơ đồ hoặc đổi `@orientation`.
