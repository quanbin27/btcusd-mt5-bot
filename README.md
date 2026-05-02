# BTC/USD MT5 Sell Bot

Bot tự động dò tín hiệu **Sell** cho cặp BTC/USD trên MetaTrader 5, sử dụng **Cluster Pattern** trên khung M15.

## Tổng quan

Bot hoạt động qua **3 giai đoạn tuần tự**:

```
GĐ 1: Xác định thị trường → GĐ 2: Dò tín hiệu Sell → GĐ 3: Theo dõi lệnh
         ↑                                                        │
         └────────────────── Reset ←──────────────────────────────┘
```

---

## Giai đoạn 1: Xác định thị trường (Market Identification)

Máy trạng thái 2 bước, chạy liên tục trên nến M15:

### 1A – Tracking High (theo dõi đỉnh)
- Khởi tạo: `highest = giá hiện tại`
- Mỗi nến: nếu `High > highest` → cập nhật `highest`
- **Trigger**: khi `Low < highest × (1 - ngưỡng%)` → giảm đủ sâu → chuyển 1B

### 1B – Tracking Low (theo dõi đáy)
- Khởi tạo: `lowest = Low của nến vừa trigger`
- Mỗi nến: nếu `Low < lowest` → cập nhật `lowest`
- **Trigger**: khi `High > lowest × (1 + ngưỡng%)` → bounce đủ mạnh → **Mô hình hoàn tất!**
- Sau trigger: `highest = High hiện tại`, quay lại tracking_high, kích hoạt GĐ 2

> **Ngưỡng mặc định: 1.7%** – có thể chỉnh trên UI.

### Bỏ qua XĐTT
User có thể nhập **đỉnh** và **đáy** thủ công rồi bấm **⏭ Bỏ qua XĐTT** để nhảy thẳng GĐ 2.

---

## Giai đoạn 2: Dò tín hiệu (Signal Detection – Cluster Pattern)

> **Market Identification vẫn chạy nền** trong GĐ 2. Nếu phát hiện cấu trúc thị trường mới → reset cluster.

### Cluster Pattern

**Mục tiêu**: Tìm cụm nến giảm, chờ giá phá ngược lên đỉnh cụm (xác nhận kháng cự), rồi phá xuống đáy cụm (tín hiệu sell).

#### Bước 1: Tạo cụm
- Chờ **nến ĐỎ** đầu tiên (Close ≤ Open)
- `cluster_high = High`, `cluster_low = Low`

#### Bước 2: Mở rộng cụm
- Nến ĐỎ tiếp theo: cập nhật `cluster_low` nếu Low thấp hơn
- **`cluster_high` KHÓA** từ nến đỏ đầu tiên (không cập nhật)

#### Bước 3: Bật cờ Sell Ready
- Nến **XANH** có `Close > cluster_high` → `sell_ready = True` 🟡
- Khi sell_ready bật: `cluster_low` cũng **KHÓA** (không cập nhật theo wick)

#### Bước 4: Chờ phá đáy

| Close nến đỏ | Hành động |
|---|---|
| `Close < cluster_low` | 🔥 **TÍN HIỆU SELL!** → đặt lệnh |
| `Close >= cluster_low` | Lưu `prev_cluster_low`, tạo cụm mới |

#### Bước 5: Đáy cũ chờ phá (prev_cluster_low)
- Khi sell_ready bật nhưng nến đỏ không phá đáy → đáy cụm cũ được **lưu lại**
- Bất kỳ nến nào (xanh hoặc đỏ) có `Close < prev_cluster_low` → 🔥 **TÍN HIỆU!**
- Chỉ giữ **1 đáy cũ** gần nhất (bị ghi đè nếu cụm mới cũng sell_ready rồi không phá)

### Ví dụ minh họa

```
Nến 1: ĐỎ  H=78353 L=78212 → 📦 Cụm: đỉnh=78353🔒 đáy=78212
Nến 2: ĐỎ  L=78129          → đáy cụm = 78129
Nến 3: ĐỎ  L=78027          → đáy cụm = 78027
Nến 4: XANH C=78364 > 78353  → 🟡 Sell Ready! Đáy KHÓA = 78027🔒
Nến 5: ĐỎ  C=78329 > 78027  → Không phá → Lưu prev=78027, cụm mới
Nến 6: XANH C=78366 > 78364  → 🟡 Sell Ready cụm mới!
Nến 7: ĐỎ  C=78207 < 78245  → 🔥 TÍN HIỆU! (phá đáy cũ hoặc mới)
```

---

## Đặt lệnh (Place Entries)

Khi có tín hiệu, **base = cluster_low** (hoặc prev_cluster_low nếu phá đáy cũ):

```
entry_price = base + offset
sl_price    = base + sl
tp_price    = base - tp
```

Hỗ trợ nhiều entry (tối đa 5), mỗi entry có:
- **Offset**: khoảng cách từ base đến giá vào
- **Volume**: khối lượng lệnh
- **SL**: khoảng cách Stop Loss
- **TP**: khoảng cách Take Profit

### 2 chế độ:
- **Auto Trade BẬT**: Đặt sell limit thật trên MT5 → chuyển GĐ 3
- **Auto Trade TẮT**: Chỉ log + gửi Telegram → reset cluster → tiếp tục dò

---

## Giai đoạn 3: Theo dõi lệnh (Order Monitoring)

- Kiểm tra mỗi 5 giây
- Phát hiện position filled → ghi nhận `had_filled_positions`
- Khi tất cả position đóng (TP hit) → hủy lệnh pending còn lại → reset về GĐ 1

---

## Tính năng phụ

### Hệ thống Log 3 kênh

| Kênh | Nội dung | Đích |
|---|---|---|
| **UI** | Tín hiệu, trạng thái, nến mới | Màn hình app |
| **Telegram** | Tất cả (UI + kỹ thuật) | Bot Telegram |
| **File** | Tất cả chi tiết | `logs/session_*.log` |

### Health Monitoring
- **Heartbeat**: Log giá mỗi 30 phút (Telegram + file)
- **Reconnect**: Mất nến 2 phút → tự reconnect MT5
- **Cảnh báo**: Mỗi 5 phút cảnh báo nếu không lấy được nến

---

## Cài đặt

### Yêu cầu
- Python 3.9+
- MetaTrader 5 (đã cài và đăng nhập)

### Cài đặt

```bash
pip install -r requirements.txt
```

### Cấu hình

1. Copy `.env.example` thành `.env`
2. Điền `TELEGRAM_BOT_TOKEN` vào `.env`

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Chạy

```bash
python main.py
```

### Build EXE

```bash
build_exe.bat
```

EXE output: `dist/BTC_Sell_Bot.exe`

---

## Cấu trúc file

```
btc_bot/
├── main.py                 # Entry point
├── ui_app.py               # Giao diện PyQt5
├── bot_engine.py           # Logic trading (QThread)
├── mt5_handler.py          # Kết nối MT5
├── telegram_notifier.py    # Gửi log Telegram (batched)
├── session_logger.py       # Ghi log file theo session
├── storage.py              # Lưu/load config JSON
├── config.py               # Hằng số cấu hình
├── app_icon.ico            # Icon ứng dụng
├── build_exe.bat           # Script build EXE
├── requirements.txt        # Dependencies
├── .env                    # Token (KHÔNG push git)
└── .env.example            # Template env
```
