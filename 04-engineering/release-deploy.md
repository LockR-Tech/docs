# Release & deploy production

## 1. Môi trường

| Thành phần | URL | Chạy trên | Nguồn deploy |
|---|---|---|---|
| API | `https://api.locker-drone.tech` | Azure VM `20.24.196.177` — `/opt/laundry-locker-microservices` | `LockR-Tech/backend` → `deploy-azure.yml` |
| Admin web | `https://admin.locker-drone.tech` | Cloudflare Worker `laundry-locker-frontend-1` | `LockR-Tech/frontend` → `deploy.yml` |
| Landing | `https://locker-drone.tech` | Cloudflare Worker `laundry-locker-landing` | `LockR-Tech/frontend` → `deploy.yml` |
| Mobile web | Worker `laundry-locker-mobile-web` | Cloudflare | `LockR-Tech/mobile` → `deploy-web.yml` |
| Trang chính sách | `https://lockr-tech.github.io/legal/privacy-policy.html` · `data-deletion.html` | GitHub Pages | `LockR-Tech/legal` (`main`, `/`) |
| App Android/iOS | Store (build tay) | — | `LockR-Tech/mobile` |
| Tủ vật lý | Raspberry Pi tại từng tủ | — | `LockR-Tech/iot` (cập nhật tay) |

**Chỉ có production. Không có staging.** Nguồn deploy duy nhất là org `LockR-Tech`; workflow deploy ở các repo cá nhân cũ đã bị tắt ([ADR-0003](../adr/0003-snapshot-sach-khi-chuyen-org.md)).

## 2. Cái gì deploy khi nào

| Merge vào `main` của | Điều kiện đường dẫn | Kết quả | Thời gian |
|---|---|---|---|
| backend | mọi file trừ `**.md`, `docs/**`, `.gitignore`, `LICENSE` | `mvn verify` → đóng gói → scp → **thay toàn bộ stack** trên VM → chờ health + 10 service đăng ký Eureka → smoke test | ~20 phút, có gián đoạn ngắn |
| frontend | `fe/**`, `landingPage/**`, `.github/workflows/deploy.yml` | build + `wrangler deploy` 2 Worker | ~2 phút, không gián đoạn |
| mobile | mọi file trừ `**.md`, `docs/**`, `DEPLOY-LOG.md` | `flutter test` (fail = không deploy) → build web → `wrangler deploy` | ~5 phút |
| iot, legal, docs | — | Không deploy tự động (legal: Pages tự build lại) | — |

Chạy tay: tab **Actions → chọn workflow → Run workflow** (`workflow_dispatch`).

## 3. Trước khi merge một thay đổi có deploy

- [ ] CI xanh trên PR; đã chạy/test phần đổi ở local.
- [ ] Không có secret mới nằm trong code. Secret mới ⇒ đã thêm vào **GitHub secrets** hoặc **`.env` trên VM** _trước_ khi merge, và ghi **tên** vào [architecture § 7](../01-overview/architecture.md#7-cicd).
- [ ] Biến môi trường mới có giá trị mặc định an toàn; thiếu biến thì service fail rõ ràng, không chạy với giá trị dev.
- [ ] Migration DB tuân thủ § 4.
- [ ] Đổi hợp đồng API/MQTT dùng chung ⇒ client cũ (app đã phát hành, kiosk, Pi) vẫn chạy được, hoặc có kế hoạch cập nhật đồng thời.
- [ ] Người merge ở lại theo dõi tới khi workflow xanh và smoke test § 6 đạt.

## 4. Migration cơ sở dữ liệu

Flyway, **chỉ tiến, không lùi**. Rollback code **không** rollback schema ⇒ mọi migration phải để **bản code trước đó vẫn chạy được**.

1. **Không sửa** file migration đã merge. Sai ⇒ viết migration mới.
2. Đặt tên `V<n>__<mo_ta>.sql`, `n` tăng dần trong từng service.
3. Đổi schema phá vỡ ⇒ **expand → migrate → contract** qua ít nhất 2 lần deploy:
   - Deploy 1: thêm cột/bảng mới (nullable hoặc có default), code ghi cả cũ lẫn mới.
   - Deploy 2: backfill, code chỉ đọc cái mới.
   - Deploy 3: xoá cột/bảng cũ.
4. Không `DROP`/`RENAME` cột mà code đang chạy còn dùng.
5. Thêm `NOT NULL` ⇒ backfill trước trong migration riêng.
6. Index lớn trên bảng đông ⇒ `CREATE INDEX CONCURRENTLY` (migration riêng, không transaction).
7. Đổi image Postgres (ví dụ sang pgvector cho L4) ⇒ thử trên bản sao volume production trước, ghi ADR.

## 5. Rollback

**Nguyên tắc: khôi phục dịch vụ trước, tìm nguyên nhân sau.**

### Backend

| Tình huống | Cách làm |
|---|---|
| Deploy **thất bại** (health/Eureka không đạt trong 12 phút) | `deploy-from-artifact.sh` **tự rollback** về `/opt/laundry-locker-microservices.previous`. Kiểm tra log workflow. |
| Deploy **thành công nhưng lỗi nghiệp vụ** — cách chuẩn | `git revert <sha>` trên nhánh `hotfix/…` → PR → merge ⇒ pipeline deploy lại bản cũ (~20 phút). |
| Khẩn cấp, không chờ được pipeline | SSH vào VM: `cd /opt && sudo mv laundry-locker-microservices laundry-locker-microservices.bad && sudo mv laundry-locker-microservices.previous laundry-locker-microservices && cd laundry-locker-microservices && docker compose up -d --build --remove-orphans`. Sau đó **vẫn phải** revert trên `main`, nếu không lần merge sau sẽ deploy lại lỗi. |

⚠ `.previous` chỉ giữ **một** bản trước và bị ghi đè ở lần deploy kế. ⚠ Bản cũ phải tương thích schema hiện tại (§ 4) — nếu không Flyway sẽ từ chối khởi động.

### Cloudflare (admin web, landing, mobile web)

```bash
npx wrangler deployments list --name laundry-locker-frontend-1
npx wrangler rollback --name laundry-locker-frontend-1          # về bản ngay trước
```
Rồi `git revert` trên `main` như backend.

### App mobile đã phát hành

Không rollback được trên máy người dùng ⇒ tắt tính năng bằng feature flag / cấu hình từ server, phát hành bản vá, backend giữ tương thích với bản app cũ.

## 6. Kiểm tra sau deploy

Workflow backend tự chạy các kiểm tra này; khi deploy/rollback tay thì chạy lại:

```bash
curl -fsS https://api.locker-drone.tech/actuator/health           # 200
curl -fsS -o /dev/null -w '%{http_code}\n' https://api.locker-drone.tech/api/lockers        # 200
curl -s  -o /dev/null -w '%{http_code}\n' https://api.locker-drone.tech/api/admin/users     # 401
curl -fsS -o /dev/null -w '%{http_code}\n' https://admin.locker-drone.tech                  # 200
curl -fsS -o /dev/null -w '%{http_code}\n' https://locker-drone.tech                        # 200
```

Sau đó thử tay luồng bị ảnh hưởng (đăng nhập, tạo đơn, mở tủ bằng giả lập).

## 7. Secret

| Nơi lưu | Secret (chỉ ghi tên) |
|---|---|
| GitHub `backend` | `AZURE_VM_HOST`, `AZURE_VM_USER`, `AZURE_VM_PORT`, `AZURE_VM_SSH_KEY` |
| GitHub `frontend`, `mobile` | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| VM `/opt/laundry-locker-microservices/.env` | Cấu hình runtime backend: SMTP, VNPay, MoMo, bootstrap admin, Firebase, `CLOUDINARY_URL`… (được giữ lại qua mỗi lần deploy) |

Luật: secret không bao giờ nằm trong repo, issue, PR, chat hay tài liệu. Lộ ⇒ **xoay ngay**, ghi vào STATUS § 2. Giá trị secret GitHub không đọc lại được — nhập mới thì lấy từ nguồn gốc (Cloudflare dashboard, `~/.ssh`, nhà cung cấp).

## 8. Phát hành có phiên bản

- **Backend**: tag `vX.Y.Z` trên `main` ⇒ `backend-release.yml` tạo GitHub Release kèm artifact, SBOM, attestation. Tag không tự deploy.
- **Mobile**: tăng `version: X.Y.Z+build` trong `pubspec.yaml` trước khi build lên store.
- Semver: `MAJOR` phá vỡ API/hợp đồng · `MINOR` tính năng · `PATCH` sửa lỗi.
