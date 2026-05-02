# ============================================================
# UI Application – PyQt5 Light-Themed Trading Bot Interface
# ============================================================
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget,
    QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox,
    QFileDialog, QFrame, QGridLayout, QMessageBox, QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QTextCursor

import config
from mt5_handler import MT5Handler
from bot_engine import BotEngine
from storage import load_config, save_config


# ════════════════════════════════════════════════════════════
#  Stylesheet – Clean Light Theme
# ════════════════════════════════════════════════════════════
LIGHT_STYLESHEET = """
/* ── Global ─────────────────────────────────────────────── */
QWidget {
    background-color: #f5f6fa;
    color: #2d3436;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 20px;
}
QMainWindow {
    background-color: #f5f6fa;
}

/* ── Tab Widget ─────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #dfe6e9;
    border-radius: 10px;
    background: #ffffff;
    margin-top: -1px;
}
QTabBar::tab {
    background: #f0f0f5;
    color: #636e72;
    padding: 10px 28px;
    margin-right: 2px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 600;
    border: 1px solid #dfe6e9;
    border-bottom: none;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #6c5ce7;
    border-bottom: 2px solid #6c5ce7;
}
QTabBar::tab:hover:!selected {
    background: #e8e8f0;
    color: #2d3436;
}

/* ── Group Box ──────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #dfe6e9;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 30px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 14px;
    color: #6c5ce7;
    font-weight: 700;
    font-size: 13px;
}

/* ── Input Fields ───────────────────────────────────────── */
QLineEdit, QDoubleSpinBox, QSpinBox {
    background: #f8f9fb;
    border: 1px solid #dfe6e9;
    border-radius: 7px;
    padding: 8px 12px;
    color: #2d3436;
    selection-background-color: #a29bfe;
}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1.5px solid #6c5ce7;
    background: #ffffff;
}
QLineEdit:disabled, QDoubleSpinBox:disabled, QSpinBox:disabled {
    background: #f0f0f5;
    color: #b2bec3;
}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {
    width: 20px;
    border: none;
    background: #e8e8f0;
    border-radius: 3px;
}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #d5d5e0;
}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6c5ce7, stop:1 #a29bfe);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #7c6ff7, stop:1 #b3acfe);
}
QPushButton:pressed {
    background: #5a4dd4;
}
QPushButton:disabled {
    background: #dfe6e9;
    color: #b2bec3;
}
QPushButton#btnStop {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e74c3c, stop:1 #fd7272);
}
QPushButton#btnStop:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #fd7272, stop:1 #ff9090);
}
QPushButton#btnConnect {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00b894, stop:1 #55efc4);
}
QPushButton#btnConnect:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #55efc4, stop:1 #7fffd4);
}
QPushButton#btnBrowse {
    padding: 8px 16px;
    font-size: 12px;
}

/* ── Log Area ───────────────────────────────────────────── */
QTextEdit#logArea {
    background: #fafbfd;
    border: 1px solid #dfe6e9;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 16px;
    color: #2d3436;
}

/* ── Labels ─────────────────────────────────────────────── */
QLabel {
    color: #636e72;
    font-size: 16px;
    background: transparent;
}
QLabel#titleLabel {
    color: #6c5ce7;
    font-weight: 800;
    font-size: 22px;
}
QLabel#statusLabel {
    color: #6c5ce7;
    font-weight: 700;
    font-size: 20px;
}
QLabel#valueLabel {
    color: #2d3436;
    font-size: 20px;
    font-weight: 600;
}

/* ── Indicator cards ────────────────────────────────────── */
QFrame#card {
    background: #ffffff;
    border: 1px solid #dfe6e9;
    border-radius: 10px;
    padding: 10px;
}

/* ── Entry row cards ────────────────────────────────────── */
QFrame#entryRow {
    background: #f8f9fb;
    border: 1px solid #eef0f5;
    border-radius: 8px;
    padding: 6px 10px;
}
QFrame#entryRowAlt {
    background: #ffffff;
    border: 1px solid #eef0f5;
    border-radius: 8px;
    padding: 6px 10px;
}

/* ── Scrollbar ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: #f5f6fa;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #d5d5e0;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #b5b5c5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ BTC Sell Bot – MT5")
        self.setMinimumSize(920, 720)

        # Set app icon
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base, "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.mt5h = MT5Handler()
        self.engine = None
        self.saved_cfg = load_config()

        self._build_ui()
        self._load_saved_config()
        self.setStyleSheet(LIGHT_STYLESHEET)
        self.showMaximized()  # mở fullscreen

    # ════════════════════════════════════════════════════════
    #  Build UI
    # ════════════════════════════════════════════════════════
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ── Title ───────────────────────────────────────────
        title = QLabel("⚡  BTC SELL BOT")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ── Tabs ────────────────────────────────────────────
        tabs = QTabWidget()
        main_layout.addWidget(tabs, stretch=1)

        tabs.addTab(self._build_account_tab(), "🔗  Tài khoản")
        tabs.addTab(self._build_config_tab(), "⚙️  Cấu hình")
        tabs.addTab(self._build_monitor_tab(), "📡  Theo dõi")

    # ── Tab 1: Account ──────────────────────────────────────
    def _build_account_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        grp = QGroupBox("Kết nối MT5")
        form = QFormLayout(grp)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_login = QLineEdit()
        self.inp_login.setPlaceholderText("Số tài khoản")
        form.addRow("Tài khoản:", self.inp_login)

        self.inp_password = QLineEdit()
        self.inp_password.setPlaceholderText("Mật khẩu")
        self.inp_password.setEchoMode(QLineEdit.Password)
        form.addRow("Mật khẩu:", self.inp_password)

        self.inp_server = QLineEdit()
        self.inp_server.setPlaceholderText("VD: Exness-MT5Real15")
        form.addRow("Máy chủ:", self.inp_server)

        path_row = QHBoxLayout()
        self.inp_path = QLineEdit()
        self.inp_path.setPlaceholderText("Đường dẫn terminal64.exe (không bắt buộc)")
        path_row.addWidget(self.inp_path)
        btn_browse = QPushButton("Chọn")
        btn_browse.setObjectName("btnBrowse")
        btn_browse.clicked.connect(self._browse_path)
        path_row.addWidget(btn_browse)
        form.addRow("Đường dẫn MT5:", path_row)

        self.inp_symbol = QLineEdit(config.SYMBOL)
        form.addRow("Symbol:", self.inp_symbol)

        layout.addWidget(grp)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.btn_connect = QPushButton("Kết nối")
        self.btn_connect.setObjectName("btnConnect")
        self.btn_connect.clicked.connect(self._connect_mt5)
        btn_row.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Ngắt kết nối")
        self.btn_disconnect.setObjectName("btnStop")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self._disconnect_mt5)
        btn_row.addWidget(self.btn_disconnect)
        layout.addLayout(btn_row)

        self.lbl_conn_status = QLabel("Chưa kết nối")
        self.lbl_conn_status.setObjectName("statusLabel")
        self.lbl_conn_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_conn_status)

        layout.addStretch()
        return page

    # ── Tab 2: Config ───────────────────────────────────────
    def _build_config_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        # Market threshold
        grp_market = QGroupBox("Thông số thị trường")
        form_market = QFormLayout(grp_market)
        form_market.setSpacing(10)
        form_market.setLabelAlignment(Qt.AlignRight)

        self.spn_threshold = QDoubleSpinBox()
        self.spn_threshold.setRange(0.1, 20.0)
        self.spn_threshold.setDecimals(1)
        self.spn_threshold.setSingleStep(0.1)
        self.spn_threshold.setValue(config.MARKET_THRESHOLD_PCT)
        self.spn_threshold.setSuffix(" %")
        form_market.addRow("Ngưỡng thị trường:", self.spn_threshold)

        layout.addWidget(grp_market)

        # ── 6 Entries ───────────────────────────────────────
        grp_entries = QGroupBox("Cấu hình 6 Entry  (offset tính từ đáy cụm)")
        entries_vlayout = QVBoxLayout(grp_entries)
        entries_vlayout.setSpacing(0)
        entries_vlayout.setContentsMargins(12, 24, 12, 12)

        # Header
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(
            "background: #6c5ce7; border-radius: 8px 8px 0 0; padding: 0;")
        hdr_grid = QGridLayout(hdr_frame)
        hdr_grid.setContentsMargins(10, 8, 10, 8)
        hdr_grid.setSpacing(4)

        hdr_texts = ["", "#", "Offset", "Volume", "SL", "TP"]
        hdr_widths = [75, 30, 1, 1, 1, 1]
        hdr_stretches = [0, 0, 1, 1, 1, 1]
        for col, (txt, w, s) in enumerate(zip(hdr_texts, hdr_widths, hdr_stretches)):
            lbl = QLabel(txt)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "color: #ffffff; font-weight: 700; font-size: 13px; background: transparent;")
            if w > 1:
                lbl.setFixedWidth(w)
            hdr_grid.addWidget(lbl, 0, col)
            hdr_grid.setColumnStretch(col, s)

        entries_vlayout.addWidget(hdr_frame)

        # Entry rows
        self.entry_rows = []
        for i in range(6):
            row_data = self._create_entry_row(i)
            entries_vlayout.addWidget(row_data["frame"])
            self.entry_rows.append(row_data)

        layout.addWidget(grp_entries)

        # Apply button
        self.btn_apply = QPushButton("✔  Áp dụng thay đổi")
        self.btn_apply.setFixedHeight(40)
        self.btn_apply.clicked.connect(self._apply_config)
        layout.addWidget(self.btn_apply)

        layout.addStretch()
        return page

    def _create_entry_row(self, index: int) -> dict:
        """Create one entry row as a styled QFrame card."""
        cfg = config.ENTRIES[index] if index < len(config.ENTRIES) else config.ENTRIES[-1]

        frame = QFrame()
        frame.setObjectName("entryRow" if index % 2 == 0 else "entryRowAlt")

        grid = QGridLayout(frame)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setSpacing(8)

        # Col 0: Toggle button
        btn = QPushButton("● BẬT" if cfg["enabled"] else "○ TẮT")
        btn.setFixedSize(75, 34)
        btn.setCheckable(True)
        btn.setChecked(cfg["enabled"])
        btn.setStyleSheet(self._toggle_style(cfg["enabled"]))
        btn.clicked.connect(lambda checked, b=btn: self._on_toggle_entry(b, checked))
        grid.addWidget(btn, 0, 0)

        # Col 1: Label
        lbl = QLabel(f"#{index + 1}")
        lbl.setFixedWidth(30)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-weight: 700; font-size: 15px; color: #6c5ce7;")
        grid.addWidget(lbl, 0, 1)

        # Col 2: Offset
        spn_offset = QDoubleSpinBox()
        spn_offset.setRange(0, 50000)
        spn_offset.setDecimals(0)
        spn_offset.setSingleStep(50)
        spn_offset.setValue(cfg["offset"])
        spn_offset.setSuffix(" USD")
        grid.addWidget(spn_offset, 0, 2)

        # Col 3: Volume
        spn_vol = QDoubleSpinBox()
        spn_vol.setRange(0.01, 100.0)
        spn_vol.setDecimals(2)
        spn_vol.setSingleStep(0.01)
        spn_vol.setValue(cfg["volume"])
        spn_vol.setSuffix(" lot")
        grid.addWidget(spn_vol, 0, 3)

        # Col 4: SL
        spn_sl = QDoubleSpinBox()
        spn_sl.setRange(0, 50000)
        spn_sl.setDecimals(0)
        spn_sl.setSingleStep(50)
        spn_sl.setValue(cfg["sl"])
        spn_sl.setSuffix(" USD")
        grid.addWidget(spn_sl, 0, 4)

        # Col 5: TP
        spn_tp = QDoubleSpinBox()
        spn_tp.setRange(0, 50000)
        spn_tp.setDecimals(0)
        spn_tp.setSingleStep(50)
        spn_tp.setValue(cfg["tp"])
        spn_tp.setSuffix(" USD")
        grid.addWidget(spn_tp, 0, 5)

        # Column stretches (match header)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)
        grid.setColumnStretch(5, 1)

        return {
            "frame": frame,
            "btn_toggle": btn,
            "spn_offset": spn_offset,
            "spn_vol": spn_vol,
            "spn_sl": spn_sl,
            "spn_tp": spn_tp,
        }

    def _toggle_style(self, enabled: bool) -> str:
        if enabled:
            return (
                "QPushButton { background: #00b894; color: white; border: none; "
                "border-radius: 8px; font-weight: 800; font-size: 13px; "
                "padding: 4px 8px; }"
                "QPushButton:hover { background: #00cca3; }"
            )
        else:
            return (
                "QPushButton { background: #e74c3c; color: white; border: none; "
                "border-radius: 8px; font-weight: 800; font-size: 13px; "
                "padding: 4px 8px; }"
                "QPushButton:hover { background: #ff6b6b; }"
            )

    def _on_toggle_entry(self, btn: QPushButton, checked: bool):
        btn.setText("● BẬT" if checked else "○ TẮT")
        btn.setStyleSheet(self._toggle_style(checked))

    def _alert_btn_style(self, active: bool) -> str:
        if active:
            return (
                "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #e17055, stop:1 #fdcb6e); color: white; border: none; "
                "border-radius: 8px; font-weight: 700; font-size: 15px; "
                "padding: 10px 28px; }"
                "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #fdcb6e, stop:1 #ffeaa7); }"
            )
        else:
            return (
                "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #636e72, stop:1 #b2bec3); color: white; border: none; "
                "border-radius: 8px; font-weight: 700; font-size: 15px; "
                "padding: 10px 28px; }"
                "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #b2bec3, stop:1 #dfe6e9); }"
            )

    def _toggle_alert_mode(self, checked: bool):
        """Live toggle auto trade – cập nhật bot đang chạy ngay."""
        self.btn_alert.setStyleSheet(self._alert_btn_style(checked))
        if checked:
            self.btn_alert.setText("✅  Auto Trade: BẬT")
            msg = "✅ Auto Trade BẬT – bot sẽ đặt lệnh thật."
        else:
            self.btn_alert.setText("❌  Auto Trade: TẮT")
            msg = "❌ Auto Trade TẮT – bot chỉ thông báo."

        # Live update vào bot đang chạy + gửi log qua cả UI và Telegram
        if self.engine and self.engine.isRunning():
            self.engine.alert_only = not checked
            self.engine.log(msg)  # → gửi UI + Telegram
        else:
            self._on_log(f"[UI] {msg}")

    def _apply_config(self):
        """Áp dụng config vào bot đang chạy (realtime) + lưu + gửi Telegram."""
        entries = []
        for row in self.entry_rows:
            entries.append({
                "enabled": row["btn_toggle"].isChecked(),
                "offset": row["spn_offset"].value(),
                "volume": row["spn_vol"].value(),
                "sl": row["spn_sl"].value(),
                "tp": row["spn_tp"].value(),
            })

        threshold = self.spn_threshold.value()

        # Cập nhật vào bot đang chạy
        if self.engine and self.engine.isRunning():
            self.engine.update_entries(entries, threshold)
            self._on_log("[UI] ✔ Config đã cập nhật vào bot đang chạy.")
        else:
            self._on_log("[UI] ✔ Config đã lưu (bot chưa chạy).")

        # Lưu config
        self._save_all_config()

    # ── Tab 3: Monitor ──────────────────────────────────────
    def _build_monitor_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        # Status cards
        cards_grid = QGridLayout()
        cards_grid.setSpacing(10)

        self.card_phase = self._make_card("GIAI ĐOẠN", "Chờ")
        cards_grid.addWidget(self.card_phase["frame"], 0, 0)

        self.card_lowest = self._make_card("GIÁ THẤP NHẤT", "–")
        cards_grid.addWidget(self.card_lowest["frame"], 0, 1)

        self.card_highest = self._make_card("GIÁ CAO NHẤT", "–")
        cards_grid.addWidget(self.card_highest["frame"], 0, 2)

        self.card_current = self._make_card("GIÁ HIỆN TẠI", "–")
        cards_grid.addWidget(self.card_current["frame"], 0, 3)

        self.card_clow = self._make_card("ĐÁY CỤM", "–")
        cards_grid.addWidget(self.card_clow["frame"], 1, 0)

        self.card_chigh = self._make_card("ĐỈNH CỤM", "–")
        cards_grid.addWidget(self.card_chigh["frame"], 1, 1)

        self.card_sell_ready = self._make_card("SELL READY", "Chưa")
        cards_grid.addWidget(self.card_sell_ready["frame"], 1, 2)

        self.card_prev_cluster = self._make_card("ĐÁY CŨ CHỜ PHÁ", "–")
        cards_grid.addWidget(self.card_prev_cluster["frame"], 2, 0)

        self.card_orders = self._make_card("TRẠNG THÁI", "Chờ")
        cards_grid.addWidget(self.card_orders["frame"], 2, 1)

        layout.addLayout(cards_grid)

        # Control buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_start = QPushButton("▶  Chạy Bot")
        self.btn_start.clicked.connect(self._start_bot)
        btn_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("■  Dừng Bot")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_bot)
        btn_row.addWidget(self.btn_stop)

        self.btn_cancel = QPushButton("🗑  Hủy tất cả lệnh")
        self.btn_cancel.clicked.connect(self._cancel_orders)
        btn_row.addWidget(self.btn_cancel)

        self.btn_alert = QPushButton("❌  Auto Trade: TẮT")
        self.btn_alert.setCheckable(True)
        self.btn_alert.setChecked(False)
        self.btn_alert.setStyleSheet(self._alert_btn_style(False))
        self.btn_alert.clicked.connect(self._toggle_alert_mode)
        btn_row.addWidget(self.btn_alert)

        layout.addLayout(btn_row)

        # ── Skip market identification row ──
        skip_row = QHBoxLayout()
        skip_row.setSpacing(10)

        lbl_peak = QLabel("Đỉnh:")
        lbl_peak.setStyleSheet("font-weight:700; background:transparent;")
        skip_row.addWidget(lbl_peak)

        self.spn_manual_high = QDoubleSpinBox()
        self.spn_manual_high.setRange(0, 999999)
        self.spn_manual_high.setDecimals(2)
        self.spn_manual_high.setSingleStep(100)
        self.spn_manual_high.setValue(0)
        self.spn_manual_high.setSuffix(" USD")
        skip_row.addWidget(self.spn_manual_high)

        lbl_bottom = QLabel("Đáy:")
        lbl_bottom.setStyleSheet("font-weight:700; background:transparent;")
        skip_row.addWidget(lbl_bottom)

        self.spn_manual_low = QDoubleSpinBox()
        self.spn_manual_low.setRange(0, 999999)
        self.spn_manual_low.setDecimals(2)
        self.spn_manual_low.setSingleStep(100)
        self.spn_manual_low.setValue(0)
        self.spn_manual_low.setSuffix(" USD")
        skip_row.addWidget(self.spn_manual_low)

        self.btn_skip_market = QPushButton("⏭  Bỏ qua XĐTT")
        self.btn_skip_market.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #0984e3, stop:1 #74b9ff); color: white; border: none; "
            "border-radius: 8px; font-weight: 700; padding: 10px 20px; }"
            "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #74b9ff, stop:1 #a8d8ff); }")
        self.btn_skip_market.clicked.connect(self._skip_market_id)
        skip_row.addWidget(self.btn_skip_market)

        layout.addLayout(skip_row)

        # Log
        self.log_area = QTextEdit()
        self.log_area.setObjectName("logArea")
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area, stretch=1)

        return page

    def _make_card(self, label_text: str, value_text: str) -> dict:
        frame = QFrame()
        frame.setObjectName("card")
        v = QVBoxLayout(frame)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "color: #b2bec3; font-size: 14px; font-weight: 700; "
            "letter-spacing: 1px; background: transparent;")
        lbl.setAlignment(Qt.AlignCenter)

        val = QLabel(value_text)
        val.setObjectName("valueLabel")
        val.setAlignment(Qt.AlignCenter)

        v.addWidget(lbl)
        v.addWidget(val)
        return {"frame": frame, "label": lbl, "value": val}

    # ════════════════════════════════════════════════════════
    #  Actions
    # ════════════════════════════════════════════════════════
    def _browse_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn MT5 Terminal", "", "Executable (*.exe)")
        if path:
            self.inp_path.setText(path)

    def _connect_mt5(self):
        login_text = self.inp_login.text().strip()
        if not login_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số tài khoản.")
            return
        try:
            login = int(login_text)
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Tài khoản phải là số.")
            return

        password = self.inp_password.text()
        server = self.inp_server.text().strip()
        path = self.inp_path.text().strip()
        symbol = self.inp_symbol.text().strip()

        ok, msg = self.mt5h.connect(login, password, server, path, symbol)
        if ok:
            self.lbl_conn_status.setText("✅ " + msg)
            self.lbl_conn_status.setStyleSheet(
                "color: #00b894; font-weight: 700; font-size: 15px;")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self._set_inputs_enabled(False)
            # Lưu thông tin tài khoản
            self._save_all_config()
        else:
            self.lbl_conn_status.setText("❌ " + msg)
            self.lbl_conn_status.setStyleSheet(
                "color: #e74c3c; font-weight: 700; font-size: 15px;")

    def _disconnect_mt5(self):
        if self.engine and self.engine.isRunning():
            self._stop_bot()
        self.mt5h.disconnect()
        self.lbl_conn_status.setText("Đã ngắt kết nối")
        self.lbl_conn_status.setStyleSheet(
            "color: #636e72; font-weight: 700; font-size: 15px;")
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self._set_inputs_enabled(True)

    def _set_inputs_enabled(self, enabled: bool):
        self.inp_login.setEnabled(enabled)
        self.inp_password.setEnabled(enabled)
        self.inp_server.setEnabled(enabled)
        self.inp_path.setEnabled(enabled)
        self.inp_symbol.setEnabled(enabled)

    def _start_bot(self):
        if not self.mt5h.connected:
            QMessageBox.warning(self, "Lỗi", "Vui lòng kết nối MT5 trước.")
            return

        entries = []
        for row in self.entry_rows:
            entries.append({
                "enabled": row["btn_toggle"].isChecked(),
                "offset": row["spn_offset"].value(),
                "volume": row["spn_vol"].value(),
                "sl": row["spn_sl"].value(),
                "tp": row["spn_tp"].value(),
            })

        params = {
            "entries": entries,
            "threshold_pct": self.spn_threshold.value(),
        }

        # Lưu config mỗi lần chạy bot
        self._save_all_config()

        self.engine = BotEngine(self.mt5h, params)
        self.engine.alert_only = not self.btn_alert.isChecked()
        self.engine.log_signal.connect(self._on_log)
        self.engine.status_signal.connect(self._on_status)
        self.engine.market_signal.connect(self._on_market_update)
        self.engine.cluster_signal.connect(self._on_cluster_update)
        self.engine.prev_cluster_signal.connect(self._on_prev_cluster_update)
        self.engine.phase_signal.connect(self._on_phase_update)
        self.engine.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _stop_bot(self):
        if self.engine:
            self.engine.stop()
            self.engine.wait(5000)
            self.engine = None
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _cancel_orders(self):
        if not self.mt5h.connected:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối MT5.")
            return
        messages = self.mt5h.cancel_all_pending()
        for m in messages:
            if self.engine and self.engine.isRunning():
                self.engine.log(f"🗑 {m}")
            else:
                self._on_log(f"🗑 {m}")
        if not messages:
            msg = "Không có lệnh chờ nào để hủy."
            if self.engine and self.engine.isRunning():
                self.engine.log(msg)
            else:
                self._on_log(msg)

    def _skip_market_id(self):
        """Bỏ qua xác định thị trường, nhảy thẳng dò tín hiệu."""
        if not self.engine or not self.engine.isRunning():
            QMessageBox.warning(self, "Lỗi", "Bot chưa chạy.")
            return

        high = self.spn_manual_high.value()
        low = self.spn_manual_low.value()

        if high <= 0 or low <= 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập giá đỉnh và đáy > 0.")
            return
        if low >= high:
            QMessageBox.warning(self, "Lỗi", "Giá đáy phải nhỏ hơn giá đỉnh.")
            return

        self.engine.skip_market(high, low)

    # ════════════════════════════════════════════════════════
    #  Signal Handlers (from BotEngine)
    # ════════════════════════════════════════════════════════
    def _on_log(self, msg: str):
        self.log_area.append(msg)
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_area.setTextCursor(cursor)

    def _on_status(self, status: str):
        self.card_orders["value"].setText(status)

    def _on_market_update(self, lowest: float, highest: float, current: float):
        self.card_lowest["value"].setText(f"{lowest:.2f}" if lowest else "–")
        self.card_highest["value"].setText(f"{highest:.2f}")
        self.card_current["value"].setText(f"{current:.2f}")

    def _on_cluster_update(self, clow: float, chigh: float, sell_ready: bool):
        self.card_clow["value"].setText(f"{clow:.2f}")
        self.card_chigh["value"].setText(f"{chigh:.2f}")
        ready_text = "CÓ ✅" if sell_ready else "Chưa"
        ready_color = "#00b894" if sell_ready else "#e74c3c"
        self.card_sell_ready["value"].setText(ready_text)
        self.card_sell_ready["value"].setStyleSheet(
            f"color: {ready_color}; font-size: 20px; font-weight: 600;")

    def _on_prev_cluster_update(self, prev_low: float):
        if prev_low > 0:
            self.card_prev_cluster["value"].setText(f"{prev_low:.2f}")
            self.card_prev_cluster["value"].setStyleSheet(
                "color: #e17055; font-size: 20px; font-weight: 600;")
        else:
            self.card_prev_cluster["value"].setText("–")
            self.card_prev_cluster["value"].setStyleSheet(
                "color: #2d3436; font-size: 20px; font-weight: 600;")

    def _on_phase_update(self, phase: int):
        phase_names = {
            0: "Chờ",
            1: "GĐ 1: Xác định TT",
            2: "GĐ 2: Dò tín hiệu",
            3: "GĐ 3: Theo dõi lệnh",
        }
        phase_colors = {
            0: "#b2bec3",
            1: "#fdcb6e",
            2: "#6c5ce7",
            3: "#00b894",
        }
        self.card_phase["value"].setText(phase_names.get(phase, "?"))
        self.card_phase["value"].setStyleSheet(
            f"color: {phase_colors.get(phase, '#2d3436')}; "
            f"font-size: 14px; font-weight: 600;")

    # ════════════════════════════════════════════════════════
    #  Config Persistence
    # ════════════════════════════════════════════════════════
    def _load_saved_config(self):
        """Load saved config into UI fields."""
        c = self.saved_cfg
        if not c:
            return

        # Account tab
        if c.get("login"):
            self.inp_login.setText(str(c["login"]))
        if c.get("password"):
            self.inp_password.setText(c["password"])
        if c.get("server"):
            self.inp_server.setText(c["server"])
        if c.get("path"):
            self.inp_path.setText(c["path"])
        if c.get("symbol"):
            self.inp_symbol.setText(c["symbol"])

        # Config tab
        if "threshold_pct" in c:
            self.spn_threshold.setValue(c["threshold_pct"])

        # Entry rows
        saved_entries = c.get("entries", [])
        for i, row in enumerate(self.entry_rows):
            if i < len(saved_entries):
                e = saved_entries[i]
                row["btn_toggle"].setChecked(e.get("enabled", True))
                row["btn_toggle"].setText(
                    "● BẬT" if e.get("enabled", True) else "○ TẮT")
                row["btn_toggle"].setStyleSheet(
                    self._toggle_style(e.get("enabled", True)))
                row["spn_offset"].setValue(e.get("offset", 200))
                row["spn_vol"].setValue(e.get("volume", 0.01))
                row["spn_sl"].setValue(e.get("sl", 1200))
                row["spn_tp"].setValue(e.get("tp", 500))

    def _save_all_config(self):
        """Save all UI fields to config file."""
        entries = []
        for row in self.entry_rows:
            entries.append({
                "enabled": row["btn_toggle"].isChecked(),
                "offset": row["spn_offset"].value(),
                "volume": row["spn_vol"].value(),
                "sl": row["spn_sl"].value(),
                "tp": row["spn_tp"].value(),
            })

        data = {
            "login": self.inp_login.text().strip(),
            "password": self.inp_password.text(),
            "server": self.inp_server.text().strip(),
            "path": self.inp_path.text().strip(),
            "symbol": self.inp_symbol.text().strip(),
            "threshold_pct": self.spn_threshold.value(),
            "entries": entries,
        }

        # Giữ lại telegram_chat_id nếu đã có
        old = load_config()
        if old.get("telegram_chat_id"):
            data["telegram_chat_id"] = old["telegram_chat_id"]

        save_config(data)

    # ════════════════════════════════════════════════════════
    #  Cleanup
    # ════════════════════════════════════════════════════════
    def closeEvent(self, event):
        self._save_all_config()
        if self.engine and self.engine.isRunning():
            self.engine.stop()
            self.engine.wait(3000)
        self.mt5h.disconnect()
        event.accept()
