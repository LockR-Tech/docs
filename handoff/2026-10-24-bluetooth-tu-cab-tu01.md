# Bàn giao — Bluetooth (BLE beacon) của tủ CAB-TU01 (2026-10-24)

> Dành cho người hoặc AI agent sửa tiếp phần Bluetooth. Việc này **để sửa sau**: các thay đổi code dưới đây mới nằm trong working tree trên máy dev, **chưa commit, chưa lên Pi**.
> Quy trình chung vẫn theo [AGENTS.md](../AGENTS.md) và [STATUS.md](../STATUS.md). File này không chứa secret.

## 1. Bluetooth trong hệ thống làm gì

| Thành phần | Vai trò | Code |
|---|---|---|
| Pi của tủ | **Chỉ phát quảng bá BLE** tên `LOCKR_<mã tủ>` (vd. `LOCKR_CAB-TU01`). Không có GATT service, **không nhận lệnh mở qua Bluetooth** | `iot/services/ble_service.py`, khởi động trong `iot/main.py` (`BLE_ENABLED`, `BLE_DEVICE_NAME` trong `.env`) |
| App mobile | Tab "Bluetooth" trong hộp mở tủ: quét beacon, khớp tên với mã tủ, RSSI ≥ -78 dBm (≈ < 2 m) ⇒ hiện nút mở 1 chạm. **Lệnh mở vẫn đi qua server** (`_doPhysicalUnlock` → API → MQTT → Pi) và **cần có đơn** | `mobile/lib/core/services/locker_ble_service.dart`, `mobile/lib/features/locker_ops/presentation/widgets/locker_unlock_modal.dart` |

Bluetooth chỉ là **cổng xác nhận đang đứng gần tủ**, không phải kênh điều khiển.

## 2. Hiện trạng đo được ngày 2026-10-24

- Pi `lockr-tu01` online: `GET http://lockr-tu01.local:8000/health` → `ok`; `/system/info` → MAC Wi-Fi `2C:CF:67:DB:C5:C3`, IP `10.3.82.140`, 1 tủ.
- Quét BLE chủ động 20 giây từ laptop (Windows, chương trình ở mục 6) thấy Pi ở **`2C:CF:67:DB:C5:C4`** (MAC Wi-Fi + 1), **-72 dBm, connectable, nhưng KHÔNG có tên** trong gói quảng bá/scan response.
- Hệ quả: app mobile (và web) lọc theo tên `LOCKR_*` nên **không nhận ra tủ** ⇒ tab Bluetooth luôn báo "Không tìm thấy sóng Bluetooth của tủ".
- Không SSH được vào Pi từ laptop dev hiện tại (khoá `id_ed25519` của laptop này bị từ chối; khoá đúng nằm trên laptop cũ — xem hồ sơ Pi riêng), nên **chưa đọc được log BLE trên Pi**.

## 3. Nguyên nhân (suy ra từ code — cần xác nhận bằng log trên Pi)

`BleAdvertiserService._start_linux_advertising` thử 2 cách:

1. `sudo btmgmt … name <tên> … advertising on` — cách này có đưa tên vào scan response. Nhưng Raspberry Pi OS thường **không cài `btmgmt`** ⇒ `FileNotFoundError` ⇒ rơi xuống cách 2.
2. Mở `bluetoothctl` và gửi `power on` · `system-alias <tên>` · `advertise on`. `system-alias` chỉ đổi tên **adapter**; quảng bá đăng ký bằng `advertise on` mặc định **không mang tên** ⇒ đúng hiện tượng ở mục 2.

Xác nhận trên Pi: `journalctl -u lockr-controller | grep -i BLE` — thấy `broadcasting via persistent bluetoothctl` là đúng nhánh 2.

## 4. Thay đổi đã làm (working tree, chưa commit)

| Repo | File | Nội dung | Kiểm thử |
|---|---|---|---|
| iot | `services/ble_service.py` | Nhánh `bluetoothctl` đặt tên trong menu advertise trước khi bật: `menu advertise` → `name <tên>` → `back` → `advertise on` | `tests/test_ble_service.py` thêm `test_bluetoothctl_fallback_puts_the_locker_name_in_the_advertisement`; 6/6 test BLE xanh (`python -m unittest tests.test_ble_service`) |
| frontend | `fe/src/pages/Admin/lockers/components/LockerBluetoothPanel.tsx` (mới), gắn vào `layout-view.tsx` trên "Nhật ký vận hành & IoT" | Khung "Kiểm tra Bluetooth & mở thử ô" ở `/admin/lockers/:id`: Web Bluetooth (Chrome/Edge) `requestDevice({ namePrefix: "LOCKR" })`, khớp tên theo cùng quy tắc với app, đo RSSI bằng `watchAdvertisements` nếu bật `chrome://flags/#enable-experimental-web-platform-features`; thấy đúng tủ (và đủ gần nếu đo được) thì bật nút "Mở ô N" — gọi `POST /api/locker-technician/cabinet/{lockerId}/boxes/{boxId}/open` (ADMIN/KTV) | `tsc` + `eslint` sạch (chưa chạy thử với tủ vì Pi chưa phát tên) |

Lệnh `name` trong menu advertise cần BlueZ đủ mới; Raspberry Pi OS Bookworm (BlueZ 5.66) có.

## 5. Việc còn lại

1. **Quyết giữ hay bỏ** hai thay đổi ở mục 4 (người dùng muốn sửa Bluetooth sau). Giữ thì commit theo nhánh + PR; bỏ thì `git checkout -- <file>` và xoá file mới.
2. **Cập nhật Pi** (cần laptop có khoá SSH): đưa `ble_service.py` mới lên `~/iot`, `sudo systemctl restart lockr-controller`, đọc `journalctl -u lockr-controller | grep -i BLE`.
3. **Xác nhận bằng quét lại** (mục 6): phải thấy `2C:CF:67:DB:C5:C4 … LOCKR_CAB-TU01`. Vẫn không có tên ⇒ thử cài `bluez` đầy đủ có `btmgmt`, hoặc chuyển sang đăng ký quảng bá qua D-Bus (`org.bluez.LEAdvertisingManager1`) với `LocalName`.
4. **Thử đầu-cuối**: app mobile (tab Bluetooth của một đơn ở tủ CAB-TU01) và khung Bluetooth trên admin web.
5. Cân nhắc: `resolve_device_name` lấy `code` từ cabinet state; nếu lệnh setup từ backend không gửi `code` thì tên có thể thành `LOCKR_<tên tủ>` — app vẫn khớp nhờ hậu tố 4 ký tự (`TU01`) nhưng nên kiểm.
6. Ghi lại vào [pi-lockr-tu01.md](../03-hardware/pi-lockr-tu01.md) khi đã sửa xong trên Pi.

## 6. Công cụ quét BLE trên Windows (đã dùng ở mục 2)

PowerShell 5.1 không đăng ký được sự kiện WinRT, nên dùng một chương trình .NET nhỏ (`dotnet run -c Release -- 20`):

`blescan.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0-windows10.0.19041.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
```

`Program.cs`

```csharp
// Quét quảng bá BLE quanh máy trong N giây; đánh dấu beacon tủ LOCKR_* và Pi (MAC 2C:CF:67…).
using System.Collections.Concurrent;
using Windows.Devices.Bluetooth.Advertisement;

int seconds = args.Length > 0 ? int.Parse(args[0]) : 15;
var seen = new ConcurrentDictionary<ulong, (string Name, short Rssi, bool Connectable)>();
var watcher = new BluetoothLEAdvertisementWatcher { ScanningMode = BluetoothLEScanningMode.Active };
watcher.Received += (_, e) =>
{
    var name = e.Advertisement.LocalName ?? "";
    seen.AddOrUpdate(e.BluetoothAddress,
        (name, e.RawSignalStrengthInDBm, e.IsConnectable),
        (_, old) => (string.IsNullOrEmpty(name) ? old.Name : name, Math.Max(old.Rssi, e.RawSignalStrengthInDBm), old.Connectable || e.IsConnectable));
};
watcher.Start();
await Task.Delay(TimeSpan.FromSeconds(seconds));
watcher.Stop();
Console.WriteLine($"Tổng thiết bị: {seen.Count}");
foreach (var (addr, v) in seen.OrderByDescending(kv => kv.Value.Rssi))
{
    var mac = string.Join(":", BitConverter.GetBytes(addr).Take(6).Reverse().Select(b => b.ToString("X2")));
    var mark = v.Name.StartsWith("LOCKR", StringComparison.OrdinalIgnoreCase) || mac.StartsWith("2C:CF:67") ? ">>" : "  ";
    Console.WriteLine($"{mark} {mac}  {v.Rssi,4} dBm  {(v.Connectable ? "conn" : "    ")}  {v.Name}");
}
```
