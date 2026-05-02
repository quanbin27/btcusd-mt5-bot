# ============================================================
# Session Logger – Ghi log mỗi session ra file trong /logs
# ============================================================
import os
import sys
from datetime import datetime


class SessionLogger:
    """Ghi toàn bộ log chi tiết ra file theo từng session."""

    def __init__(self):
        self._file = None
        self._path = None

    def start_session(self):
        """Tạo file log mới cho session hiện tại."""
        logs_dir = self._get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = os.path.join(logs_dir, f"session_{ts}.log")
        self._file = open(self._path, "w", encoding="utf-8")
        self._write(f"{'='*60}")
        self._write(f"Session bắt đầu: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        self._write(f"{'='*60}")

    def end_session(self):
        """Đóng file log khi session kết thúc."""
        if self._file:
            self._write(f"{'='*60}")
            self._write(f"Session kết thúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            self._write(f"{'='*60}")
            self._file.close()
            self._file = None

    def write(self, msg: str):
        """Ghi 1 dòng log (có timestamp)."""
        if self._file:
            self._write(msg)

    def _write(self, msg: str):
        try:
            self._file.write(msg + "\n")
            self._file.flush()
        except Exception:
            pass

    @staticmethod
    def _get_logs_dir() -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "logs")
