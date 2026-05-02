# ============================================================
# BTC Sell Bot – Default Configuration
# ============================================================

# MT5 connection defaults
MT5_LOGIN = 0
MT5_PASSWORD = ""
MT5_SERVER = ""
MT5_PATH = ""  # path to terminal64.exe

# Symbol & timeframe
SYMBOL = "BTCUSD_m"
TIMEFRAME_MINUTES = 15  # M15

# Market identification
MARKET_THRESHOLD_PCT = 1.7  # percentage difference to trigger signal detection

# 6 fixed entries – each has: enabled, offset, volume, sl_offset, tp_offset
NUM_ENTRIES = 6
ENTRIES = [
    {"enabled": True,  "offset": 200,  "volume": 0.01, "sl": 1200, "tp": 500},
    {"enabled": True,  "offset": 350,  "volume": 0.01, "sl": 1200, "tp": 500},
    {"enabled": True,  "offset": 500,  "volume": 0.01, "sl": 1200, "tp": 500},
    {"enabled": True,  "offset": 650,  "volume": 0.01, "sl": 1200, "tp": 500},
    {"enabled": True,  "offset": 800,  "volume": 0.01, "sl": 1200, "tp": 500},
    {"enabled": True,  "offset": 950,  "volume": 0.01, "sl": 1200, "tp": 500},
]

# Telegram (chat_id auto-detected, lưu vào config file)
TELEGRAM_CHAT_ID = "-5257889262"

# Bot internals
MAGIC_NUMBER = 202604
DEVIATION = 50
CANDLE_POLL_SECONDS = 5  # how often to check for new candle
