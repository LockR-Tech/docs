# Nối dây tủ `lockr-tu01` theo ảnh

| | |
|---|---|
| **Dùng khi** | Đang đứng trước khoang điện của tủ, cần biết dây nào bắt vào cọc nào |
| **Ảnh** | Ảnh gốc ở [`locker/`](../locker/) (toàn cảnh 2026-09-30, 12 ảnh chi tiết 2026-10-01). Ảnh có nhãn ở `img/tu01/`, sinh bằng `python scripts/annotate-tu01-photos.py` |
| **Bản đồ chân** | [cabinet-wiring-spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio) — file này chỉ thêm **vị trí thật trên tủ** |
| **Quy trình đầy đủ** | [controller-wiring-guide § 3–5](controller-wiring-guide.md#3-thứ-tự-nối-dây) |
| **Gap** | F2-G09 |

Quy ước: **ô N** dùng relay `IN(N)` và là ô số N của tủ `CAB-TU01` trên admin (`slot = N − 1` trong code). Số chân Pi là **số chân vật lý** trên header 40 chân.

## 0. An toàn

- Rút phích 220 V của nguồn tổ ong trước khi động vào dây. Chỉ cắm lại ở bước đo và bước thử.
- Tắt Pi trước khi cắm hoặc rút dây ở header: bấm nút nguồn trên Pi hai lần liền, đợi đèn chuyển đỏ, rồi rút USB-C.
- Chân GPIO chỉ chịu **3,3 V**. Trên domino 2, cọc `+12 V` nằm cách cọc tín hiệu hai cọc. Một dây 12 V chạm vào chân GPIO là hỏng Pi.

## 1. Toàn cảnh khoang điện

![Toàn cảnh khoang điện, đánh dấu A đến G](img/tu01/01-tong-quan.jpg)

| | Linh kiện | Việc phải làm |
|---|---|---|
| A | Cọc đầu vào của module relay (`DC+ DC− IN1…IN8`) | Nối 9 dây về Pi — § 3 |
| B | Hai cụm jumper vàng chọn mức kích | Đặt **H** — § 3 |
| C | **Domino 1** (TB-2512L, cạnh relay): 6 cặp dây tín hiệu khoá | Hàng phía relay còn trống, nối về Pi — § 4 |
| D | **Domino 2** (TB-2512L, cạnh driver): `+12 V`, `−V`, 4 dây tín hiệu driver, một cặp dây vàng | Nối 4 dây driver về Pi — § 5 |
| E | Driver TB6600 của nắp trượt | Không nối thẳng vào driver; đi qua domino 2 |
| F | Nguồn tổ ong 12 V | Kiểm công tắc 110/220 V — § 7 |
| G | Raspberry Pi 5, vệt xanh là header 40 chân | § 2 |

![Relay, domino 1, domino 2 và driver nhìn từ phía cửa khoang](img/tu01/08-hai-domino.jpg)

## 2. Pi: header 40 chân

![Header 40 chân của Pi 5 và header J14](img/tu01/02-pi-header.jpg)

- **Chân 1** ở đầu header **xa cổng USB**, hàng trong (phía quạt). **Chân 2** cùng vị trí, hàng ngoài (sát mép bo).
- Chân lẻ ở hàng trong, chân chẵn ở hàng ngoài. Chân *n* nằm ở cột thứ ⌈*n*/2⌉ tính từ đầu xa cổng USB.
- Header 2×2 **J14** cạnh cổng mạng là chân PoE. Không cắm dây điều khiển vào đó (đã cắm nhầm hai lần, sự cố 1 ở [hồ sơ Pi](pi-lockr-tu01.md#7-sự-cố-đã-gặp)).

## 3. Module relay — 9 dây

![Module relay: cọc đầu vào, jumper, thứ tự relay](img/tu01/03-relay.jpg)

Ảnh chụp từ phía domino nên thứ tự cọc đầu vào đọc từ trái sang là `IN8 … IN1, DC−, DC+`. Nhìn từ phía Pi thì ngược lại. **Luôn đối chiếu chữ in trên bo cạnh từng cọc.**

1. Chuyển jumper của kênh 1–7 sang **H**. Ở L, đầu vào chờ 5 V để nhả; GPIO của Pi chỉ đưa 3,3 V nên relay không nhả hẳn và khoá bị cấp điện liên tục.
2. Nối dây:

| Cọc relay | Chân Pi | Tín hiệu |
|---|---|---|
| `DC−` | 6 | GND |
| `DC+` | 2 | 5 V nuôi cuộn relay |
| `IN1` | 11 | GPIO17 · ô 1 |
| `IN2` | 13 | GPIO27 · ô 2 |
| `IN3` | 15 | GPIO22 · ô 3 |
| `IN4` | 16 | GPIO23 · ô 4 |
| `IN5` | 18 | GPIO24 · ô 5 |
| `IN6` | 22 | GPIO25 · ô 6 |
| `IN7` | 36 | GPIO16 · ô 7 |
| `IN8` | — | để trống |

3. Kiểm: chưa cắm 220 V, cắm USB-C cho Pi. Trong lúc Pi khởi động **không relay nào được kêu**. Relay nào kêu tách ngay là jumper kênh đó còn ở L.

Đầu ra relay (dây xanh mảnh) nhà cung cấp đã nối sẵn tới dây âm của khoá và `−V`. Không tháo.

## 4. Domino 1: dây tín hiệu khoá — 7 dây và 5 cầu nối

![Domino 1: hàng trống phía relay và 6 cặp dây tín hiệu](img/tu01/04-domino-1.jpg)

Hàng xa relay có 12 dây: nâu ở cọc chẵn, vàng ở cọc lẻ, mỗi cặp nâu + vàng là dây báo đóng/mở của một khoá. Hàng phía relay **trống**, dây về Pi bắt vào đó.

**Đo trước khi nối, bắt buộc:**

1. Cắm 220 V. Đồng hồ ở thang điện áp DC, que đen vào cọc 3 của domino 2 (`−V`). Chạm que đỏ lần lượt vào 12 cọc của domino 1: tất cả phải **0 V**.
2. Rút 220 V. Chuyển sang thang thông mạch, đặt hai que vào một cặp (cọc 1 và 2). Đóng rồi mở từng cửa: cửa nào làm đồng hồ đổi trạng thái thì cặp đó thuộc ô ấy. Ghi số ô lên băng dán.
3. Có điện áp ở bước 1 ⇒ **dừng**, không nối vào Pi.

Nối dây (thứ tự ô bên dưới là dự kiến; bước 2 cho thứ tự thật, lệch thì đổi `GPIO_DOOR_PINS` trong `.env`, không phải nối lại):

| Cọc domino 1 (hàng trống) | Nối tới | Tín hiệu |
|---|---|---|
| 2 | chân 25 của Pi | GND chung |
| 2 → 4 → 6 → 8 → 10 → 12 | 5 đoạn dây ngắn nối liền nhau | GND cho 6 cặp |
| 1 | chân 29 | GPIO5 · cửa ô 1 |
| 3 | chân 31 | GPIO6 · cửa ô 2 |
| 5 | chân 32 | GPIO12 · cửa ô 3 |
| 7 | chân 33 | GPIO13 · cửa ô 4 |
| 9 | chân 35 | GPIO19 · cửa ô 5 |
| 11 | chân 37 | GPIO26 · cửa ô 6 |

Không nối cọc GND chung này với `−V` của nguồn 12 V.

Cặp thứ bảy: xem cọc 11–12 của domino 2 ở § 5.

## 5. Domino 2 và driver TB6600 — 4 dây (và cặp dây vàng)

![Domino 2: cọc +12 V, −V, tín hiệu driver, cặp dây vàng](img/tu01/05-domino-2.jpg)

| Cọc domino 2 | Đang có | Việc phải làm |
|---|---|---|
| 1, 2 | Nhiều dây nâu: **+12 V** tới khoá và driver | Không chạm |
| 3 | Dây xanh: `−V` | Dùng làm điểm đo, không nối vào Pi |
| 4, 7 | Hai dây vàng sọc xanh từ driver: `PUL+` và `DIR−` | Đo thông mạch để biết cọc nào là cọc nào |
| 5 | Dây xanh từ driver: `PUL−` | Nối về Pi |
| 6 | Dây nâu từ driver: `DIR+` | Nối về Pi |
| 8, 9, 10 | Trống | — |
| 11, 12 | Một cặp dây vàng | Xác định: cửa ô 7 hay công tắc hành trình |

![Driver TB6600: 4 cọc tín hiệu đã nối sẵn về domino 2](img/tu01/06-tb6600.jpg)

Trên driver, `DIR−` và `PUL+` cùng dùng dây vàng sọc xanh nên ảnh không phân biệt được. Rút 220 V, đặt đồng hồ ở thang thông mạch: một que vào vít `PUL+` của driver, que kia lần lượt vào cọc 4 và cọc 7 của domino 2. Cọc nào kêu là `PUL+`, cọc còn lại là `DIR−`.

Nối dây vào **phía trống** của cọc 4–7:

| Tín hiệu driver | Cọc domino 2 | Chân Pi |
|---|---|---|
| `PUL+` | 4 hoặc 7 (theo kết quả đo) | 1 — **3,3 V**, không phải 5 V |
| `DIR+` | 6 | 17 — **3,3 V** |
| `PUL−` | 5 | 12 — GPIO18 |
| `DIR−` | 7 hoặc 4 | 40 — GPIO21 |

`ENA−`, `ENA+` trên driver để trống. Tài liệu nhà cung cấp bảo nối `PUL+`, `DIR+` vào 5 V; với Pi phải là 3,3 V ([spec § 6](cabinet-wiring-spec.md#6-bản-đồ-chân-gpio-của-pi-hardware_backendgpio)).

**Cặp dây vàng ở cọc 11–12.** Đo như § 4: 0 V so với `−V`, rồi thông mạch khi đóng mở cửa ô còn lại hoặc khi bấm tay công tắc hành trình của nắp.

- Là cặp tín hiệu của ô 7: cọc 11 → chân 38 (GPIO20), cọc 12 → chân 30 (GND).
- Là công tắc hành trình: nối theo § 6.

## 6. Công tắc hành trình của nắp trượt — 4 dây

Ảnh chưa cho thấy dây của hai công tắc hành trình. Tìm hai công tắc ở hai đầu ray nắp trượt và lần dây về khoang điện.

| Công tắc | Cọc `NO` → chân Pi | Cọc `COM` → chân Pi |
|---|---|---|
| Gốc (bị nhấn khi nắp **đóng** hết) | 7 — GPIO4 | 9 — GND |
| Cuối (bị nhấn khi nắp **mở** hết) | 19 — GPIO10 | 14 — GND |

Công tắc chỉ có cọc `NC`: vẫn nối được, đổi `LID_LIMIT_ACTIVE_LOW=false`.

## 7. Nguồn tổ ong

![Nguồn tổ ong: nhãn chọn 110/220 V và hàng cọc ra](img/tu01/07-nguon.jpg)

Công tắc chọn điện áp phải ở **220 V**. Không vặn biến trở `V ADJ`. Không có dây nào đi từ nguồn này vào Pi; Pi dùng nguồn USB-C 27 W riêng.

## 8. Điều ảnh chưa trả lời được

| # | Câu hỏi | Cách biết |
|---|---|---|
| 1 | Jumper đang ở H hay L | Đọc chữ in cạnh jumper; bước kiểm ở § 3 |
| 2 | Cặp nào trên domino 1 thuộc ô nào | Thông mạch khi đóng mở từng cửa (§ 4) |
| 3 | Dây tín hiệu khoá có phải tiếp điểm khô | Đo điện áp so với `−V` (§ 4) |
| 4 | Cọc 4 hay cọc 7 của domino 2 là `PUL+` | Thông mạch từ vít driver (§ 5) |
| 5 | Cặp dây vàng ở cọc 11–12 của domino 2 là gì | Thông mạch khi đóng mở cửa hoặc bấm công tắc (§ 5) |
| 6 | Dây hai công tắc hành trình về tới đâu | Lần dây từ ray nắp (§ 6) |

## 9. Sau khi nối

Bring-up theo [controller-wiring-guide § 5](controller-wiring-guide.md#5-kiểm-tra-từng-bước-bring-up): `debug_gpio.py pins`, `doors`, `open N`, `lid …`. Sai thứ tự ô, sai chiều nắp, relay kích ngược đều sửa bằng `.env`, không phải nối lại. Xong thì gán Pi vào tủ `CAB-TU01` trên admin (guide § 5.8) và chuyển tủ từ `MAINTENANCE` sang `ACTIVE`.
