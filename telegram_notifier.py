# ============================================================
# Telegram Notifier – Send ALL logs to Telegram (batched)
# ============================================================
import os
import sys
import requests
import threading
import time

from dotenv import load_dotenv

# Load .env từ thư mục exe (PyInstaller) hoặc thư mục dev
_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_base, '.env'))


class TelegramNotifier:
    """Gửi tất cả log về Telegram, gom tin nhắn trong 2 giây."""

    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
    BATCH_INTERVAL = 2  # seconds – gom tin nhắn trước khi gửi

    def __init__(self, chat_id: str = ""):
        self.chat_id = chat_id
        self.enabled = bool(chat_id)
        self._buffer = []
        self._lock = threading.Lock()
        self._timer = None

    def set_chat_id(self, chat_id: str):
        self.chat_id = chat_id.strip()
        self.enabled = bool(self.chat_id)

    # ── Auto-detect chat_id ─────────────────────────────────
    def auto_detect_chat_id(self) -> str | None:
        """Lấy chat_id từ tin nhắn gần nhất gửi tới bot."""
        try:
            r = requests.get(f"{self.API_URL}/getUpdates", timeout=5)
            data = r.json()
            if data.get("ok") and data.get("result"):
                last = data["result"][-1]
                chat = last.get("message", {}).get("chat", {})
                return str(chat.get("id", ""))
        except Exception:
            pass
        return None

    # ── Send log (batched) ──────────────────────────────────
    def send_log(self, msg: str):
        """Thêm log vào buffer, gửi sau BATCH_INTERVAL giây."""
        if not self.enabled or not self.chat_id:
            return
        with self._lock:
            self._buffer.append(msg)
            if self._timer is None:
                self._timer = threading.Timer(
                    self.BATCH_INTERVAL, self._flush)
                self._timer.daemon = True
                self._timer.start()

    def flush_now(self):
        """Gửi ngay lập tức (dùng khi bot dừng)."""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._flush()

    def _flush(self):
        with self._lock:
            if not self._buffer:
                self._timer = None
                return
            text = "\n".join(self._buffer)
            self._buffer.clear()
            self._timer = None

        # Telegram giới hạn 4096 ký tự
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            self._send_sync(f"<pre>{chunk}</pre>")

    def _send_sync(self, text: str):
        try:
            requests.post(
                f"{self.API_URL}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
        except Exception:
            pass

    # ── Send immediate (cho config, start/stop) ─────────────
    def send_now(self, text: str):
        """Gửi ngay, không buffer."""
        if not self.enabled or not self.chat_id:
            return
        t = threading.Thread(
            target=self._send_sync, args=(text,), daemon=True)
        t.start()
