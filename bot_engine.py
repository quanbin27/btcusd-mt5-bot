# ============================================================
# Bot Engine – Trading Logic (runs in QThread)
# ============================================================
from PyQt5.QtCore import QThread, pyqtSignal
import time
from datetime import datetime

import config
from mt5_handler import MT5Handler
from telegram_notifier import TelegramNotifier
from storage import load_config, save_config
from session_logger import SessionLogger


class BotEngine(QThread):
    """
    Main bot loop running on M15.

    Market Identification (chạy liên tục, kể cả trong lúc dò lệnh):
      1A. tracking_high – theo dõi đỉnh, chờ giảm 1.7%
      1B. tracking_low  – theo dõi đáy, chờ tăng 1.7%
      → Khi hoàn tất (1A→1B→bounce) → kích hoạt/reset dò lệnh

    Signal Detection (Phase 2):
      Cluster-based candle pattern → tìm điểm vào lệnh sell

    Monitoring (Phase 3):
      Theo dõi lệnh → TP hit → hủy pending → quay lại Phase 1
    """

    # Signals for UI updates
    log_signal = pyqtSignal(str)           # log messages
    status_signal = pyqtSignal(str)        # phase status
    market_signal = pyqtSignal(float, float, float)  # lowest, highest, current
    cluster_signal = pyqtSignal(float, float, bool)   # cluster_low, cluster_high, sell_ready
    prev_cluster_signal = pyqtSignal(float)  # prev_cluster_low (0 = không có)
    phase_signal = pyqtSignal(int)         # current phase number

    def __init__(self, mt5h: MT5Handler, params: dict, parent=None):
        super().__init__(parent)
        self.mt5h = mt5h
        self.params = params
        self._running = False

        # Params unpacking
        self.entries = params.get("entries", list(config.ENTRIES))
        self.threshold_pct = params.get("threshold_pct", config.MARKET_THRESHOLD_PCT)

        # Telegram – auto-detect chat_id
        self.tg = TelegramNotifier()
        self._init_telegram()

        # Market identification state
        self.market_state = "tracking_high"   # "tracking_high" or "tracking_low"
        self.highest = None
        self.lowest = None

        # Signal detection state
        self.signal_active = False
        self.cluster_high = None
        self.cluster_low = None
        self.sell_ready = False
        self.prev_cluster_low = None  # đáy cụm cũ đang chờ phá

        # Order monitoring state
        self.phase = 0   # 0=idle, 1=market_id, 2=signal_detect, 3=monitoring
        self.alert_only = False  # True = chỉ thông báo, không đặt lệnh
        self.orders_placed = False
        self.had_filled_positions = False
        self.last_candle_time = None

        # Health monitoring
        self._fail_count = 0
        self._last_heartbeat = 0

        # Session file logger
        self.slog = SessionLogger()

    # ── Telegram init ───────────────────────────────────────
    def _init_telegram(self):
        """Load or auto-detect Telegram chat_id."""
        saved = load_config()
        chat_id = saved.get("telegram_chat_id", "")
        if chat_id:
            self.tg.set_chat_id(chat_id)
            return
        # Auto-detect
        detected = self.tg.auto_detect_chat_id()
        if detected:
            self.tg.set_chat_id(detected)
            saved["telegram_chat_id"] = detected
            save_config(saved)

    # ── Public control ──────────────────────────────────────
    def stop(self):
        self._running = False

    def update_entries(self, entries: list, threshold_pct: float = None):
        """Cập nhật config realtime khi bot đang chạy."""
        self.entries = entries
        if threshold_pct is not None:
            self.threshold_pct = threshold_pct
        self.log("⚙️ Config đã cập nhật realtime!")
        self._send_config_to_telegram()

    def skip_market(self, high: float, low: float):
        """Bỏ qua xác định thị trường, nhảy thẳng tới dò tín hiệu."""
        # Chặn nếu đang Phase 3 (có lệnh pending)
        if self.phase == 3:
            self.log("⚠️ Không thể bỏ qua – đang theo dõi lệnh (Phase 3).")
            return

        # Nếu đã ở Phase 2 với cùng giá trị → bỏ qua
        if (self.phase == 2 and self.signal_active
                and self.highest == high and self.lowest == low):
            self.log("ℹ️ Đã ở GĐ 2 với cùng đỉnh/đáy. Không cần bỏ qua lại.")
            return

        self.highest = high
        self.lowest = low
        # Set tracking_high để market ID chỉ theo dõi đỉnh mới,
        # không tự trigger bounce → không reset cluster đang dò
        self.market_state = "tracking_high"
        self.signal_active = True
        self.cluster_high = None
        self.cluster_low = None
        self.sell_ready = False
        self.prev_cluster_low = None
        self.phase = 2
        self.phase_signal.emit(2)
        self.market_signal.emit(self.lowest, self.highest,
                                self.mt5h.get_current_price() or high)
        self.status_signal.emit("GĐ 2: Dò tín hiệu")
        self.log(f"⏭ Bỏ qua XĐTT – Đỉnh={high:.2f}  Đáy={low:.2f}")
        self.log("Chuyển sang GĐ 2: Dò tín hiệu ngay.")

    def _send_config_to_telegram(self):
        """Gửi bảng config hiện tại về Telegram."""
        lines = [f"⚙️ CẤU HÌNH (Ngưỡng: {self.threshold_pct}%)"]
        lines.append("─" * 36)
        for i, e in enumerate(self.entries):
            st = "✅" if e.get("enabled") else "❌"
            lines.append(
                f"{st} #{i+1}  Off={e['offset']}  "
                f"Vol={e['volume']}  SL={e['sl']}  TP={e['tp']}"
            )
        lines.append("─" * 36)
        self.tg.send_now("\n".join(lines))

    # ── Main loop ───────────────────────────────────────────
    def run(self):
        self._running = True
        self.slog.start_session()
        self.phase = 1
        self.phase_signal.emit(1)
        self.market_state = "tracking_high"
        self.signal_active = False
        self.log("🚀 Bot đã khởi động – GĐ 1A: Theo dõi đỉnh")
        self.status_signal.emit("GĐ 1A: Theo dõi đỉnh")

        # Initialize with current price
        price = self.mt5h.get_current_price()
        if price is None:
            self.log("❌ Không lấy được giá hiện tại. Dừng bot.")
            self.slog.end_session()
            return
        self.highest = price
        self.lowest = None
        self.log(f"Giá khởi tạo: {price:.2f}  |  highest={self.highest:.2f}")
        self.market_signal.emit(0, self.highest, price)

        # ── BỎ QUA NẾN CŨ – chỉ xử lý nến mới từ đây ──
        candles = self.mt5h.get_candles(count=10)
        if candles and len(candles) >= 2:
            self.last_candle_time = candles[-2]["time"]
            self.log(f"⏭ Bỏ qua nến cũ. Chờ nến mới sau {self.last_candle_time.strftime('%H:%M')}")

        # ── Gửi config + trạng thái Auto Trade về Telegram ──
        self._send_config_to_telegram()
        if self.alert_only:
            self.log("❌ Auto Trade: TẮT – chỉ thông báo, không đặt lệnh.")
        else:
            self.log("✅ Auto Trade: BẬT – bot sẽ đặt lệnh thật.")

        self._last_heartbeat = time.time()

        while self._running:
            try:
                self._tick()
            except Exception as e:
                self.log(f"❌ Error: {e}")
            time.sleep(config.CANDLE_POLL_SECONDS)

        self.log("🛑 Bot đã dừng.")
        self.status_signal.emit("Đã dừng")
        self.tg.flush_now()
        self.slog.end_session()

    def _tick(self):
        """Called every poll interval."""
        # ── Heartbeat mỗi 30 phút ──
        now_ts = time.time()
        if now_ts - self._last_heartbeat >= 1800:  # 30 min
            self._last_heartbeat = now_ts
            price = self.mt5h.get_current_price()
            if price:
                self.log_tech(f"💓 Heartbeat – giá hiện tại: {price:.2f}")
            else:
                self.log_tech("💓 Heartbeat – bot đang chạy (không lấy được giá)")

        candles = self.mt5h.get_candles(count=10)
        if not candles:
            self._fail_count += 1
            # Cảnh báo mỗi 5 phút (60 lần x 5s)
            if self._fail_count % 60 == 1:
                self.log_tech(f"⚠️ Không lấy được nến ({self._fail_count} lần). Kiểm tra kết nối MT5...")
            # Tự reconnect sau 2 phút mất kết nối (24 lần x 5s)
            if self._fail_count == 24:
                self.log_tech("🔄 Đang thử kết nối lại MT5...")
                self.mt5h.reconnect()
            return

        if self._fail_count > 0:
            self.log_tech(f"✅ Đã khôi phục kết nối sau {self._fail_count} lần thử.")
            self._fail_count = 0

        # The last completed candle is candles[-2], current forming is candles[-1]
        last_closed = candles[-2]

        # Check if new candle has formed
        candle_time = last_closed["time"]
        if candle_time == self.last_candle_time:
            # No new candle yet – but still monitor orders in phase 3
            if self.phase == 3:
                self._monitor_orders()
            # ── Real-time tick check: phá đáy → đánh luôn, không đợi nến đóng ──
            elif self.signal_active:
                self._tick_break_check(candles[-1])
            return

        self.last_candle_time = candle_time
        self.log(f"── Nến mới: {candle_time.strftime('%H:%M')} ──")

        # Phase 3: chỉ theo dõi lệnh, không xét thị trường
        if self.phase == 3:
            self._monitor_orders()
            return

        # ── Luôn chạy market identification ──
        market_triggered = self._market_identification(last_closed)

        if market_triggered:
            # Mô hình thị trường hoàn tất → kích hoạt/reset dò lệnh
            self._activate_signal_detection()

        # ── Nếu dò lệnh đang active, chạy signal detection ──
        if self.signal_active:
            self._signal_detect(last_closed)

    # ════════════════════════════════════════════════════════
    #  Market Identification (chạy liên tục)
    # ════════════════════════════════════════════════════════
    def _market_identification(self, candle: dict) -> bool:
        """
        Máy trạng thái 2 bước:
          tracking_high → giá giảm 1.7% → tracking_low → giá tăng 1.7% → triggered

        Returns True khi mô hình hoàn tất (bounce từ đáy detected).
        """
        h, l, c = candle["high"], candle["low"], candle["close"]

        if self.market_state == "tracking_high":
            # Cập nhật đỉnh nếu cao hơn
            if h > self.highest:
                self.highest = h
                self.log(f"  📈 Đỉnh cập nhật: {self.highest:.2f}")

            # Kiểm tra giá giảm >= threshold% từ đỉnh
            threshold_price = self.highest * (1 - self.threshold_pct / 100)
            if l < threshold_price:
                # Giảm đủ sâu → chuyển sang tracking_low
                self.market_state = "tracking_low"
                self.lowest = l
                self.log(f"  📉 Giảm {self.threshold_pct}%! Low {l:.2f} < ngưỡng {threshold_price:.2f}")
                self.log(f"  📉 Chuyển sang theo dõi đáy. Lowest = {self.lowest:.2f}")
                if not self.signal_active:
                    self.status_signal.emit("GĐ 1B: Theo dõi đáy")

            self.market_signal.emit(self.lowest or 0, self.highest, c)
            return False

        elif self.market_state == "tracking_low":
            # Cập nhật đáy nếu thấp hơn
            if l < self.lowest:
                self.lowest = l
                self.log(f"  📉 Đáy cập nhật: {self.lowest:.2f}")

            # Kiểm tra giá tăng >= threshold% từ đáy
            threshold_price = self.lowest * (1 + self.threshold_pct / 100)
            if h > threshold_price:
                # Tăng đủ mạnh → mô hình hoàn tất!
                self.log(f"  📈 Tăng {self.threshold_pct}%! High {h:.2f} > ngưỡng {threshold_price:.2f}")
                # Reset highest = high nến hiện tại, quay lại tracking_high
                self.highest = h
                self.market_state = "tracking_high"
                self.market_signal.emit(self.lowest, self.highest, c)
                return True  # → kích hoạt/reset dò lệnh

            self.market_signal.emit(self.lowest, self.highest, c)
            return False

        return False

    # ════════════════════════════════════════════════════════
    #  Activate / Reset Signal Detection
    # ════════════════════════════════════════════════════════
    def _activate_signal_detection(self):
        """Kích hoạt dò lệnh mới hoặc reset nếu đang dò."""
        if self.signal_active:
            self.log("🔄 Phát hiện thị trường mới! Reset dò lệnh.")
        else:
            self.log("✅ Mô hình thị trường hoàn tất!")

        self.signal_active = True
        self.cluster_high = None
        self.cluster_low = None
        self.sell_ready = False
        self.prev_cluster_low = None
        self.phase = 2
        self.phase_signal.emit(2)
        self.status_signal.emit("GĐ 2: Dò tín hiệu")
        self.log("🔍 Bắt đầu dò tín hiệu sell...")

    # ════════════════════════════════════════════════════════
    #  Real-time Break Check (mỗi 5s, không đợi nến đóng)
    # ════════════════════════════════════════════════════════
    def _tick_break_check(self, forming_candle: dict):
        """Check giá hiện tại (nến đang hình thành) phá đáy → đánh luôn."""
        price = float(forming_candle["close"])  # giá hiện tại

        # Check prev_cluster_low trước
        if self.prev_cluster_low is not None and price < self.prev_cluster_low:
            base = self.prev_cluster_low
            if self.sell_ready and self.cluster_low is not None and price < self.cluster_low:
                base = max(base, self.cluster_low)
            self.log(f"  ⚡ TICK BREAK! Giá {price:.2f} phá đáy {base:.2f}")
            self.cluster_low = base
            self._place_entries()
            self.prev_cluster_low = None
            self.prev_cluster_signal.emit(0)
            return

        # Check cluster_low (khi sell_ready)
        if self.sell_ready and self.cluster_low is not None and price < self.cluster_low:
            self.log(f"  ⚡ TICK BREAK! Giá {price:.2f} phá đáy cụm {self.cluster_low:.2f}")
            self.prev_cluster_low = None
            self.prev_cluster_signal.emit(0)
            self._place_entries()

    # ════════════════════════════════════════════════════════
    #  Signal Detection – Cluster Pattern (nến đã đóng)
    # ════════════════════════════════════════════════════════
    def _signal_detect(self, candle: dict):
        """Cluster-based candle pattern detection."""
        o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]
        is_green = c > o   # bullish
        is_red = c <= o     # bearish

        color = "🟢 Xanh" if is_green else "🔴 Đỏ"
        self.log(f"  {color}  O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f}")

        # ── Kiểm tra phá đáy cụm cũ (đang chờ) ──
        if self.prev_cluster_low is not None and c < self.prev_cluster_low:
            base = self.prev_cluster_low
            # Nếu cụm hiện tại (sell_ready) cũng bị phá → dùng đáy cao hơn
            if self.sell_ready and self.cluster_low is not None and c < self.cluster_low:
                base = max(base, self.cluster_low)
            self.log(f"  🔥 TÍN HIỆU! Close {c:.2f} phá đáy {base:.2f}")
            self.cluster_low = base
            self._place_entries()
            self.prev_cluster_low = None
            self.prev_cluster_signal.emit(0)
            return

        # ── Chưa có cụm ──
        if self.cluster_high is None:
            if is_red:
                self.cluster_high = h
                self.cluster_low = l
                self.sell_ready = False
                self.log(f"  📦 Cụm mới: đỉnh={h:.2f} đáy={l:.2f}")
                self.cluster_signal.emit(self.cluster_low, self.cluster_high, False)
            return

        # ── Đã có cụm ──
        # Chỉ cập nhật đáy khi chưa sell_ready (cluster đang hình thành)
        if l < self.cluster_low and not self.sell_ready:
            self.cluster_low = l
            self.log(f"  📦 Đáy cụm cập nhật: {self.cluster_low:.2f}")

        # Bật sell_ready khi High phá đỉnh cụm (bất kể xanh/đỏ)
        if not self.sell_ready and h > self.cluster_high:
            self.sell_ready = True
            self.log(f"  🟡 Sell Ready! High {h:.2f} > đỉnh cụm {self.cluster_high:.2f}")
            self.cluster_signal.emit(self.cluster_low, self.cluster_high, True)

        if is_green:
            self.cluster_signal.emit(self.cluster_low, self.cluster_high, self.sell_ready)

        elif is_red:
            if not self.sell_ready:
                self.log(f"  📦 Cụm cập nhật: đỉnh={self.cluster_high:.2f} đáy={self.cluster_low:.2f}")
                self.cluster_signal.emit(self.cluster_low, self.cluster_high, False)
            else:
                if c < self.cluster_low:
                    self.log(f"  🔥 TÍN HIỆU! Close {c:.2f} phá đáy cụm {self.cluster_low:.2f}")
                    self.prev_cluster_low = None
                    self.prev_cluster_signal.emit(0)
                    self._place_entries()
                else:
                    # Lưu đáy cụm cũ vào prev, tạo cụm mới
                    self.prev_cluster_low = self.cluster_low
                    self.prev_cluster_signal.emit(self.prev_cluster_low)
                    self.log(f"  📦 Lưu đáy cũ={self.prev_cluster_low:.2f} → Cụm mới: đỉnh={h:.2f} đáy={l:.2f}")
                    self.cluster_high = h
                    self.cluster_low = l
                    self.sell_ready = False
                    self.cluster_signal.emit(self.cluster_low, self.cluster_high, False)

    # ════════════════════════════════════════════════════════
    #  Place Entries & Order Monitoring
    # ════════════════════════════════════════════════════════
    def _place_entries(self):
        """Place sell limit orders for each enabled entry (or just alert)."""
        self.log("═" * 50)
        if self.alert_only:
            self.log("📢 TÍN HIỆU SELL (CHỈ THÔNG BÁO)")
        else:
            self.log("📥 ĐẶT LỆNH SELL LIMIT")
        self.log("═" * 50)

        base = self.cluster_low
        digits = self.mt5h.get_symbol_digits()
        placed_count = 0

        for i, entry in enumerate(self.entries):
            if not entry.get("enabled", True):
                self.log(f"  Entry #{i+1}: ⏭ Đã tắt, bỏ qua")
                continue

            offset = entry["offset"]
            volume = entry["volume"]
            sl_off = entry["sl"]
            tp_off = entry["tp"]

            entry_price = round(base + offset, digits)
            sl_price = round(base + sl_off, digits)
            tp_price = round(base - tp_off, digits)

            self.log(f"  Entry #{i+1}: price={entry_price:.2f}  Vol={volume}  SL={sl_price:.2f}  TP={tp_price:.2f}")

            if self.alert_only:
                placed_count += 1
                continue

            ok, msg = self.mt5h.place_sell_limit(
                volume=volume,
                price=entry_price,
                sl=sl_price,
                tp=tp_price,
            )
            self.log(f"    → {msg}")
            if ok:
                placed_count += 1

        if placed_count == 0:
            self.log("⚠️ Không có entry nào!")
            return

        if self.alert_only:
            self.log(f"📢 Đã thông báo {placed_count} entry. Tiếp tục dò lệnh...")
            # Reset cluster để tiếp tục dò lệnh mới
            self.cluster_high = None
            self.cluster_low = None
            self.sell_ready = False
            return

        self.orders_placed = True
        self.had_filled_positions = False
        self.signal_active = False
        self.phase = 3
        self.phase_signal.emit(3)
        self.status_signal.emit("GĐ 3: Theo dõi lệnh")
        self.log(f"📡 Đã đặt {placed_count} lệnh. Đang theo dõi...")

    def _monitor_orders(self):
        """Monitor filled positions. If TP hit → cancel remaining pending."""
        positions = self.mt5h.get_open_positions()
        pending = self.mt5h.get_pending_orders()

        if len(positions) > 0:
            self.had_filled_positions = True

        if self.had_filled_positions and len(positions) == 0:
            self.log("✅ TP HIT! Tất cả vị thế đã đóng. Đang hủy lệnh chờ...")
            messages = self.mt5h.cancel_all_pending()
            for m in messages:
                self.log(f"  {m}")
            self.log("🏁 Chu kỳ hoàn tất. Quay lại Giai đoạn 1.")
            self._reset_to_phase1()
            return


    # ════════════════════════════════════════════════════════
    #  Reset
    # ════════════════════════════════════════════════════════
    def _reset_to_phase1(self):
        """Reset toàn bộ state và quay về Phase 1A."""
        self.phase = 1
        self.phase_signal.emit(1)
        price = self.mt5h.get_current_price()
        if price:
            self.highest = price
        self.lowest = None
        self.market_state = "tracking_high"
        self.signal_active = False
        self.cluster_high = None
        self.cluster_low = None
        self.sell_ready = False
        self.prev_cluster_low = None
        self.orders_placed = False
        self.had_filled_positions = False
        self.last_candle_time = None
        self.status_signal.emit("GĐ 1A: Theo dõi đỉnh")
        self.log("🔄 Reset – GĐ 1A: Theo dõi đỉnh")

    # ── Helpers ─────────────────────────────────────────────
    def log(self, msg: str):
        """Log → UI + Telegram + File."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.log_signal.emit(full_msg)
        self.tg.send_log(full_msg)
        self.slog.write(full_msg)

    def log_tech(self, msg: str):
        """Log kỹ thuật → Telegram + File only (không hiện UI)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.tg.send_log(full_msg)
        self.slog.write(full_msg)
