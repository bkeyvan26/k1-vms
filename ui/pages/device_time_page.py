# -*- coding: utf-8 -*-
"""K1 VMS — Device Time Management (Phase 17.0 — کامل)

★ تغییرات Phase 17.0:
  - LocalLoadingOverlay داخل صفحه (نه ActivityBus سراسری)
  - Reference NTP server برای drift
  - Cancel واقعی برای لغو عملیات
  - _SimpleUserDlg با رمز فعلی + تکرار رمز + تأیید
  - منع NVR + دوربین با هم
  - دکمه «اعمال روی انتخاب‌شده‌ها»
"""
import datetime
import webbrowser
import socket
import struct
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QDateTimeEdit,
    QProgressBar, QAbstractItemView, QDialog, QFormLayout,
    QSpinBox, QMessageBox, QMenu, QComboBox, QWidget, QTextEdit,
    QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime
from PySide6.QtGui import QColor, QAction, QBrush

from ui import theme
from ui.pages import BasePage
from ui.dialogs import (
    info as dlg_info, warning as dlg_warning,
)
from core.camera_manager import CameraManager
from core.nvr_manager import NVRManager
from core.device_time_manager import (
    DeviceTimeManager, DeviceTimeInfo,
)
from core import settings_manager
from core.i18n import t


# ============================================================
# Constants
# ============================================================
C_SYNCED   = "#3fb950"
C_MINOR    = "#d29922"
C_MODERATE = "#e07b1f"
C_MAJOR    = "#f85149"
C_OFFLINE  = "#4a5361"
C_MUTED    = "#7f8c8d"
C_ACCENT   = "#16a085"
C_WEB      = "#58a6ff"

BG_ROW = "#0f1216"
BG_HDR = "#0c0f13"

D_SYNCED, D_MINOR, D_MODERATE = 2, 30, 300

PROTO_COLORS = {
    "onvif": "#58a6ff", "http_dahua": "#3fb950",
    "http_hikvision": "#f85149", "http_uniview": "#a371f7",
    "http_mna": "#2dd4bf", "http_kdt": "#2dd4bf",
    "http_axis": "#f39c12",
}

TIMEZONES = [
    ("UTC-12:00", -12.0), ("UTC-11:00", -11.0), ("UTC-10:00", -10.0),
    ("UTC-09:00", -9.0), ("UTC-08:00", -8.0), ("UTC-07:00", -7.0),
    ("UTC-06:00", -6.0), ("UTC-05:00", -5.0), ("UTC-04:00", -4.0),
    ("UTC-03:30", -3.5), ("UTC-03:00", -3.0), ("UTC-02:00", -2.0),
    ("UTC-01:00", -1.0), ("UTC+00:00", 0.0), ("UTC+01:00", 1.0),
    ("UTC+02:00", 2.0), ("UTC+03:00", 3.0), ("UTC+03:30", 3.5),
    ("UTC+04:00", 4.0), ("UTC+04:30", 4.5), ("UTC+05:00", 5.0),
    ("UTC+05:30", 5.5), ("UTC+06:00", 6.0), ("UTC+07:00", 7.0),
    ("UTC+08:00", 8.0), ("UTC+09:00", 9.0), ("UTC+10:00", 10.0),
    ("UTC+11:00", 11.0), ("UTC+12:00", 12.0),
]

DEFAULT_TZ = 3.5
SETTINGS_NTP_LAST = "device_time_last_ntp"
SETTINGS_NTP_HISTORY = "device_time_ntp_history"
SETTINGS_REF_SERVER = "device_time_reference_server"

NTP_DEFAULTS = [
    "pool.ntp.org", "ir.pool.ntp.org", "time.google.com",
    "time.windows.com", "time.cloudflare.com", "ntp.aliyun.com",
    "asia.pool.ntp.org", "europe.pool.ntp.org",
]


def _proto_badge(p):
    if not p: return "—"
    if p == "onvif": return "ONVIF"
    if p.startswith("http_"): return p[5:].capitalize()
    return p.upper()


def _proto_color(p):
    return PROTO_COLORS.get(p or "", C_MUTED)


def _drift_calc(dev_dt, ref_dt):
    if dev_dt is None or ref_dt is None:
        return "—", C_OFFLINE
    drift = (dev_dt - ref_dt).total_seconds()
    a = abs(drift)
    sign = "+" if drift >= 0 else "−"
    if a <= D_SYNCED: return "✓ همگام", C_SYNCED
    if a <= D_MINOR: return f"{sign}{a:.0f}s", C_MINOR
    if a <= D_MODERATE: return f"{sign}{a/60:.1f}m", C_MODERATE
    return f"{sign}{a/3600:.1f}h", C_MAJOR


def _is_auth_error(err):
    if not err: return False
    e = err.lower()
    return any(x in e for x in
                ("401", "403", "unauthorized", "forbidden",
                 "auth", "permission", "credential"))


# ============================================================
# Local Loading Overlay
# ============================================================
class LocalLoadingOverlay(QFrame):
    _FRAMES = ("◐", "◓", "◑", "◒")

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet(
            "QFrame { background: rgba(5,8,12,210); border: none; "
            "border-radius: 8px; }")
        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(8)

        self.icon = QLabel(self._FRAMES[0])
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet(
            f"color:{C_ACCENT};font-size:36px;font-weight:700;"
            f"background:transparent;")
        v.addWidget(self.icon)

        self.text = QLabel("در حال بارگذاری...")
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet(
            f"color:{theme.COLOR_TEXT_PRIMARY};font-size:12px;"
            f"font-weight:700;background:transparent;")
        v.addWidget(self.text)

        self.progress = QProgressBar()
        self.progress.setFixedWidth(280)
        self.progress.setStyleSheet(f"""QProgressBar {{
            background:{BG_HDR};color:white;
            border:1px solid {theme.COLOR_BORDER};border-radius:5px;
            height:20px;text-align:center;font-size:10px;font-weight:700; }}
            QProgressBar::chunk {{ background:{C_ACCENT};border-radius:4px; }}""")
        v.addWidget(self.progress, 0, Qt.AlignCenter)

        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._spin)
        self.hide()

    def _spin(self):
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self.icon.setText(self._FRAMES[self._frame])

    def show_loading(self, text="در حال بارگذاری..."):
        self.text.setText(text)
        self.progress.setValue(0)
        self.progress.setFormat("0%")
        self._frame = 0
        self.icon.setText(self._FRAMES[0])
        self.raise_()
        self.show()
        self._timer.start(100)

    def update_progress(self, done, total, name=""):
        pct = int(done * 100 / max(1, total))
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self.progress.setFormat(f"{done}/{total}  ({pct}%)")
        if name:
            self.text.setText(f"در حال پردازش: {name[:35]}")

    def hide_loading(self):
        self._timer.stop()
        self.hide()


# ============================================================
# Worker
# ============================================================
class TimeWorker(QThread):
    progress = Signal(int, int, str)
    finished_all = Signal(list, str)
    error = Signal(str)

    def __init__(self, devices, mode, params, parent=None):
        super().__init__(parent)
        self.devices = devices
        self.mode = mode
        self.params = params or {}
        self.mgr = DeviceTimeManager()

    def cancel(self):
        try:
            self.mgr.cancel()
        except Exception:
            pass

    def run(self):
        try:
            self.mgr.set_devices(self.devices)

            def on_prog(d, t, dev):
                self.progress.emit(d, t, dev.name or dev.ip)

            if self.mode == "read":
                r = self.mgr.read_all_times(on_progress=on_prog)
            elif self.mode == "sync_pc":
                r = self.mgr.sync_all_to_pc(on_progress=on_prog)
            elif self.mode == "manual":
                dt = self.params.get("dt") or datetime.datetime.now()
                r = self.mgr.set_time_batch(self.devices, dt, on_progress=on_prog)
            elif self.mode == "ntp":
                srv = self.params.get("ntp_server", "pool.ntp.org")
                r = self.mgr.enable_ntp_all(srv, on_progress=on_prog)
            elif self.mode == "timezone":
                r = self.mgr.set_timezone_batch(
                    self.devices, self.params.get("tz_value", DEFAULT_TZ),
                    on_progress=on_prog)
            else:
                r = []
            self.finished_all.emit(r, self.mode)
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
# Set Time Method Dialog
# ============================================================
class SetTimeMethodDialog(QDialog):
    MODE_PC = "pc"
    MODE_MANUAL = "manual"
    MODE_NTP = "ntp"

    def __init__(self, device_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیم زمان و تاریخ")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.chosen = None
        self._options = {}

        v = QVBoxLayout(self)
        v.setContentsMargins(22, 18, 22, 16); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(10)
        ic = QLabel("🕒")
        ic.setStyleSheet("font-size:20px;background:transparent;")
        h.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(0)
        t1 = QLabel("تنظیم زمان و تاریخ دستگاه‌ها")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel(f"روی {device_count} دستگاه اعمال می‌شود")
        t2.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:10px;background:transparent;")
        tv.addWidget(t2)
        h.addLayout(tv, 1)
        v.addLayout(h)

        options = [
            (self.MODE_PC, "🖥", "هماهنگ‌سازی با رایانه شما",
             "ساعت همه با ساعت این کامپیوتر برابر می‌شود."),
            (self.MODE_MANUAL, "✏", "زمان دستی",
             "ساعت دقیق دلخواه را وارد کنید."),
            (self.MODE_NTP, "🌐", "سرور NTP",
             "از یک سرور NTP برای همگام‌سازی دائمی."),
        ]
        for i, (key, icon, title, desc) in enumerate(options):
            w = self._make_option(key, icon, title, desc)
            v.addWidget(w)
            if i == 0: self._select(key)

        v.addSpacing(4)
        br = QHBoxLayout(); br.setSpacing(8); br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(self._btn_sec())
        bc.clicked.connect(self.reject); br.addWidget(bc)
        bo = QPushButton("ادامه  ▶"); bo.setFixedHeight(32)
        bo.setCursor(Qt.PointingHandCursor)
        bo.setStyleSheet(self._btn_pri())
        bo.clicked.connect(self._on_next); br.addWidget(bo)
        v.addLayout(br)

    def _make_option(self, key, icon, title, desc):
        w = QFrame()
        w.setCursor(Qt.PointingHandCursor)
        w.setFixedHeight(58)
        w.setStyleSheet(self._wrap_qss(False))
        wl = QHBoxLayout(w)
        wl.setContentsMargins(12, 8, 12, 8); wl.setSpacing(10)
        ic = QLabel(icon)
        ic.setFixedSize(32, 32); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"color:{C_ACCENT};background:{C_ACCENT}22;"
                          f"border-radius:16px;font-size:14px;")
        wl.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(1)
        t1 = QLabel(title)
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:12px;font-weight:700;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel(desc); t2.setWordWrap(True)
        t2.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:10px;background:transparent;")
        tv.addWidget(t2)
        wl.addLayout(tv, 1)
        w.mousePressEvent = lambda e, k=key: self._select(k)
        self._options[key] = w
        return w

    def _wrap_qss(self, active):
        b = f"2px solid {C_ACCENT}" if active else f"1px solid {theme.COLOR_BORDER}"
        return f"QFrame {{ background:{BG_ROW};border:{b};border-radius:8px; }}"

    def _select(self, key):
        self.chosen = key
        for k, w in self._options.items():
            w.setStyleSheet(self._wrap_qss(k == key))

    def _btn_pri(self):
        return f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 20px;
            font-size:12px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}"""

    def _btn_sec(self):
        return f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 16px;font-size:12px; }}
            QPushButton:hover {{ background:{theme.COLOR_BG_HOVER}; }}"""

    def _on_next(self):
        if self.chosen is None:
            QMessageBox.warning(self, "خطا", "یک روش انتخاب کنید.")
            return
        self.accept()


# ============================================================
# NTP Dialog
# ============================================================
class NTPDialog(QDialog):
    def __init__(self, device_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیم NTP")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.result_server = None
        self.result_tz = None

        v = QVBoxLayout(self)
        v.setContentsMargins(22, 18, 22, 16); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(10)
        ic = QLabel("🌐")
        ic.setStyleSheet("font-size:20px;background:transparent;")
        h.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(0)
        t1 = QLabel("تنظیم سرور NTP")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel(f"برای {device_count} دستگاه اعمال می‌شود")
        t2.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:10px;background:transparent;")
        tv.addWidget(t2)
        h.addLayout(tv, 1)
        v.addLayout(h)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.combo = QComboBox()
        self.combo.setEditable(True)
        try:
            self.combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        self.combo.setMinimumWidth(320)
        self.combo.setMinimumHeight(32)

        last = ""
        history = []
        try:
            s = settings_manager.load_settings()
            last = getattr(s, SETTINGS_NTP_LAST, "") or ""
            history = getattr(s, SETTINGS_NTP_HISTORY, []) or []
        except Exception:
            pass

        items = []
        if last: items.append(last)
        for x in history:
            if x not in items: items.append(x)
        for x in NTP_DEFAULTS:
            if x not in items: items.append(x)
        for x in items:
            self.combo.addItem(x)
        self.combo.setCurrentText(last or "pool.ntp.org")
        self.combo.setStyleSheet(self._input_qss())

        form.addRow(self._lbl("سرور NTP:"), self.combo)
        v.addLayout(form)

        info = QLabel(
            "💡 می‌توانید سرور دلخواه تایپ کنید، "
            "یا با کلیک روی ▼ از لیست پیشنهادی انتخاب کنید.")
        info.setWordWrap(True)
        info.setStyleSheet(f"""color:{C_MUTED};font-size:10px;
            background:{BG_ROW};padding:6px 10px;border-radius:5px;
            border-left:3px solid {C_ACCENT};""")
        v.addWidget(info)

        tz_row = QHBoxLayout(); tz_row.setSpacing(8)
        self.tz_check = QCheckBox("اعمال TimeZone")
        self.tz_check.setCursor(Qt.PointingHandCursor)
        self.tz_check.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.COLOR_TEXT_PRIMARY};
                font-size: 11px; font-weight: 600;
                spacing: 6px; background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 3px; background: {BG_ROW};
            }}
            QCheckBox::indicator:checked {{
                background: {C_ACCENT}; border-color: {C_ACCENT};
            }}
        """)
        tz_row.addWidget(self.tz_check)

        self.tz_combo = QComboBox()
        for label, val in TIMEZONES:
            self.tz_combo.addItem(label, val)
        idx = self.tz_combo.findData(DEFAULT_TZ)
        if idx >= 0: self.tz_combo.setCurrentIndex(idx)
        self.tz_combo.setEnabled(False)
        self.tz_combo.setStyleSheet(self._input_qss(disabled=True))
        self.tz_check.toggled.connect(self._on_tz_toggle)
        tz_row.addWidget(self.tz_combo, 1)
        v.addLayout(tz_row)

        br = QHBoxLayout(); br.setSpacing(6); br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(self._btn_sec())
        bc.clicked.connect(self.reject); br.addWidget(bc)
        bo = QPushButton("اعمال  ✓"); bo.setFixedHeight(32)
        bo.setCursor(Qt.PointingHandCursor)
        bo.setStyleSheet(self._btn_pri())
        bo.clicked.connect(self._on_apply); br.addWidget(bo)
        v.addLayout(br)

    def _on_tz_toggle(self, checked):
        self.tz_combo.setEnabled(checked)
        self.tz_combo.setStyleSheet(self._input_qss(disabled=not checked))

    def _lbl(self, txt):
        l = QLabel(txt)
        l.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:12px;font-weight:600;background:transparent;")
        return l

    def _input_qss(self, disabled=False):
        if disabled:
            return f"""
                QComboBox {{
                    background: #0a0d10; color: #4a5361;
                    border: 1px solid #1a1e24; border-radius: 5px;
                    padding: 5px 8px; font-size: 12px; min-height: 22px;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: center right;
                    width: 24px; border: none; background: transparent;
                }}
                QComboBox::down-arrow {{
                    image: none; width: 0; height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 5px solid #2a3038; margin-right: 6px;
                }}
            """
        return f"""
            QComboBox {{
                background: {BG_ROW}; color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 5px; padding: 5px 8px;
                font-size: 12px; min-height: 22px;
            }}
            QComboBox:focus {{ border: 1px solid {C_ACCENT}; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px; border: none; background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none; width: 0; height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {theme.COLOR_TEXT_SECONDARY};
                margin-right: 6px;
            }}
            QComboBox::down-arrow:on {{
                border-top: 6px solid {C_ACCENT};
            }}
            QComboBox QAbstractItemView {{
                background: {BG_ROW}; color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                selection-background-color: {C_ACCENT};
                padding: 4px; outline: none;
            }}
        """

    def _btn_pri(self):
        return f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 20px;
            font-size:12px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}"""

    def _btn_sec(self):
        return f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 16px;font-size:12px; }}
            QPushButton:hover {{ background:{theme.COLOR_BG_HOVER}; }}"""

    def _on_apply(self):
        srv = (self.combo.currentText() or "").strip()
        if not srv:
            QMessageBox.warning(self, "خطا", "سرور NTP خالی است.")
            return
        self.result_server = srv
        if self.tz_check.isChecked():
            self.result_tz = self.tz_combo.currentData()
        try:
            s = settings_manager.load_settings()
            setattr(s, SETTINGS_NTP_LAST, srv)
            hist = getattr(s, SETTINGS_NTP_HISTORY, []) or []
            if srv not in hist:
                hist.insert(0, srv); hist = hist[:10]
            setattr(s, SETTINGS_NTP_HISTORY, hist)
            settings_manager.save_settings(s)
        except Exception:
            pass
        self.accept()


# ============================================================
# Manual Time Dialog
# ============================================================
class ManualTimeDialog(QDialog):
    def __init__(self, count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("زمان دستی")
        self.setModal(True); self.setMinimumWidth(440)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.result_dt = None
        self.result_tz = None

        v = QVBoxLayout(self)
        v.setContentsMargins(22, 18, 22, 16); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(10)
        ic = QLabel("✏")
        ic.setStyleSheet("font-size:20px;background:transparent;")
        h.addWidget(ic)
        t1 = QLabel(f"زمان دستی — {count} دستگاه")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        h.addWidget(t1, 1)
        v.addLayout(h)

        dt_row = QHBoxLayout(); dt_row.setSpacing(6)
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setDateTime(QDateTime.currentDateTime())
        self.dt_edit.setDisplayFormat("yyyy-MM-dd  HH:mm:ss")
        self.dt_edit.setStyleSheet(f"""
            QDateTimeEdit {{ background:{BG_ROW};color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};border-radius:5px;
                padding:6px 10px;font-size:13px;font-weight:600;min-height:22px; }}
            QDateTimeEdit:focus {{ border:1px solid {C_ACCENT}; }}
        """)
        dt_row.addWidget(self.dt_edit, 1)
        bnow = QPushButton("حالا")
        bnow.setFixedHeight(32); bnow.setCursor(Qt.PointingHandCursor)
        bnow.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{C_ACCENT};border:1px solid {C_ACCENT};
            border-radius:5px;padding:0 12px;font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:{C_ACCENT};color:white; }}""")
        bnow.clicked.connect(
            lambda: self.dt_edit.setDateTime(QDateTime.currentDateTime()))
        dt_row.addWidget(bnow)
        v.addLayout(dt_row)

        tz_row = QHBoxLayout(); tz_row.setSpacing(8)
        self.tz_check = QCheckBox("اعمال TimeZone")
        self.tz_check.setCursor(Qt.PointingHandCursor)
        self.tz_check.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.COLOR_TEXT_PRIMARY};
                font-size: 11px; font-weight: 600;
                spacing: 6px; background: transparent;
            }}
            QCheckBox::indicator {{
                width: 14px; height: 14px;
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 3px; background: {BG_ROW};
            }}
            QCheckBox::indicator:checked {{
                background: {C_ACCENT}; border-color: {C_ACCENT};
            }}
        """)
        tz_row.addWidget(self.tz_check)

        self.tz_combo = QComboBox()
        for l, val in TIMEZONES:
            self.tz_combo.addItem(l, val)
        idx = self.tz_combo.findData(DEFAULT_TZ)
        if idx >= 0: self.tz_combo.setCurrentIndex(idx)
        self.tz_combo.setEnabled(False)
        self.tz_combo.setStyleSheet(self._tz_disabled_qss())
        self.tz_check.toggled.connect(self._on_tz_toggle)
        tz_row.addWidget(self.tz_combo, 1)
        v.addLayout(tz_row)

        br = QHBoxLayout(); br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 16px;font-size:12px; }}""")
        bc.clicked.connect(self.reject); br.addWidget(bc)
        bo = QPushButton("اعمال  ✓"); bo.setFixedHeight(32)
        bo.setCursor(Qt.PointingHandCursor)
        bo.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 20px;
            font-size:12px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        bo.clicked.connect(self._apply); br.addWidget(bo)
        v.addLayout(br)

    def _tz_disabled_qss(self):
        return f"""QComboBox {{ background:#0a0d10;color:#4a5361;
            border:1px solid #1a1e24;border-radius:5px;
            padding:5px 8px;font-size:12px;min-height:20px; }}
            QComboBox QAbstractItemView {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            selection-background-color:{C_ACCENT}; }}"""

    def _tz_enabled_qss(self):
        return f"""QComboBox {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};border-radius:5px;
            padding:5px 8px;font-size:12px;min-height:20px; }}
            QComboBox QAbstractItemView {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            selection-background-color:{C_ACCENT}; }}"""

    def _on_tz_toggle(self, checked):
        self.tz_combo.setEnabled(checked)
        if checked:
            self.tz_combo.setStyleSheet(self._tz_enabled_qss())
        else:
            self.tz_combo.setStyleSheet(self._tz_disabled_qss())

    def _apply(self):
        q = self.dt_edit.dateTime()
        self.result_dt = datetime.datetime(
            q.date().year(), q.date().month(), q.date().day(),
            q.time().hour(), q.time().minute(), q.time().second())
        if self.tz_check.isChecked():
            self.result_tz = self.tz_combo.currentData()
        self.accept()


# ============================================================
# Timezone Dialog
# ============================================================
class TimezoneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیم TimeZone")
        self.setModal(True); self.setMinimumWidth(380)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.result_tz = None

        v = QVBoxLayout(self)
        v.setContentsMargins(22, 18, 22, 16); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(10)
        ic = QLabel("🌍")
        ic.setStyleSheet("font-size:20px;background:transparent;")
        h.addWidget(ic)
        t1 = QLabel("منطقه زمانی")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        h.addWidget(t1, 1)
        v.addLayout(h)

        self.combo = QComboBox()
        for l, val in TIMEZONES:
            self.combo.addItem(l, val)
        idx = self.combo.findData(DEFAULT_TZ)
        if idx >= 0: self.combo.setCurrentIndex(idx)
        self.combo.setStyleSheet(f"""QComboBox {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};border-radius:6px;
            padding:8px 10px;font-size:13px;min-height:22px; }}
            QComboBox QAbstractItemView {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            selection-background-color:{C_ACCENT}; }}""")
        v.addWidget(self.combo)

        br = QHBoxLayout(); br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(30)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 14px;font-size:12px; }}""")
        bc.clicked.connect(self.reject); br.addWidget(bc)
        bo = QPushButton("اعمال"); bo.setFixedHeight(30)
        bo.setCursor(Qt.PointingHandCursor)
        bo.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 18px;
            font-size:12px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        bo.clicked.connect(self._ok); br.addWidget(bo)
        v.addLayout(br)

    def _ok(self):
        self.result_tz = self.combo.currentData()
        self.accept()


# ============================================================
# Credentials Dialog
# ============================================================
class CredentialsDialog(QDialog):
    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.setWindowTitle("اطلاعات ورود دستگاه")
        self.setModal(True); self.setMinimumWidth(440)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 14); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(8)
        ic = QLabel("🔑")
        ic.setStyleSheet("font-size:18px;background:transparent;")
        h.addWidget(ic)
        t1 = QLabel("اطلاعات ورود اتصال")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        h.addWidget(t1); h.addStretch(1)
        v.addLayout(h)

        ip_lbl = QLabel(f"  {device.name or device.ip}   ({device.ip})")
        ip_lbl.setStyleSheet(f"color:{C_ACCENT};font-family:Consolas;"
                              f"font-size:11px;background:{BG_ROW};"
                              f"padding:6px 10px;border-radius:5px;")
        v.addWidget(ip_lbl)

        form = QFormLayout(); form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row = QHBoxLayout(); row.setSpacing(4)
        self.user_edit = QLineEdit(device.user or "admin")
        self.user_edit.setStyleSheet(self._qss())
        row.addWidget(self.user_edit, 1)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(int(device.port or 80))
        self.port_spin.setFixedWidth(70)
        self.port_spin.setStyleSheet(f"""QSpinBox {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:5px;padding:5px 6px;
            font-size:11px;min-height:18px; }}""")
        row.addWidget(self.port_spin)
        rw = QWidget(); rw.setLayout(row)
        form.addRow(self._lbl("کاربر / پورت"), rw)

        pr = QHBoxLayout(); pr.setSpacing(4)
        self.pass_edit = QLineEdit(device.password or "")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setStyleSheet(self._qss())
        pr.addWidget(self.pass_edit, 1)
        self.show_btn = QPushButton("👁")
        self.show_btn.setCheckable(True)
        self.show_btn.setFixedSize(28, 28)
        self.show_btn.setCursor(Qt.PointingHandCursor)
        self.show_btn.setStyleSheet(f"""QPushButton {{ background:{BG_ROW};
            color:{C_MUTED};border:1px solid {theme.COLOR_BORDER};
            border-radius:5px; }}
            QPushButton:checked {{ background:{C_ACCENT};color:white; }}""")
        self.show_btn.toggled.connect(
            lambda c: self.pass_edit.setEchoMode(
                QLineEdit.Normal if c else QLineEdit.Password))
        pr.addWidget(self.show_btn)
        pw = QWidget(); pw.setLayout(pr)
        form.addRow(self._lbl("رمز عبور"), pw)
        v.addLayout(form)

        self.test_lbl = QLabel("")
        self.test_lbl.setWordWrap(True)
        self.test_lbl.setVisible(False)
        v.addWidget(self.test_lbl)

        v.addStretch(1)

        br = QHBoxLayout(); br.setSpacing(6)
        bt = QPushButton("🧪 تست اتصال")
        bt.setFixedHeight(32); bt.setCursor(Qt.PointingHandCursor)
        bt.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{C_ACCENT};border:1px solid {C_ACCENT};
            border-radius:6px;padding:0 12px;
            font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:{C_ACCENT};color:white; }}""")
        bt.clicked.connect(self._test); br.addWidget(bt)

        saved = DeviceTimeManager.load_credentials()
        if device.ip in saved:
            bd = QPushButton("🗑"); bd.setFixedSize(32, 32)
            bd.setCursor(Qt.PointingHandCursor)
            bd.setStyleSheet(f"""QPushButton {{ background:transparent;
                color:{C_MAJOR};border:1px solid {C_MAJOR};
                border-radius:6px;font-size:12px; }}
                QPushButton:hover {{ background:{C_MAJOR};color:white; }}""")
            bd.clicked.connect(self._delete); br.addWidget(bd)

        br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 14px;font-size:11px; }}""")
        bc.clicked.connect(self.reject); br.addWidget(bc)

        bs = QPushButton("💾 ذخیره"); bs.setFixedHeight(32)
        bs.setCursor(Qt.PointingHandCursor)
        bs.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 16px;
            font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        bs.clicked.connect(self._save); br.addWidget(bs)
        v.addLayout(br)

    def _lbl(self, txt):
        l = QLabel(txt)
        l.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:11px;font-weight:600;background:transparent;")
        return l

    def _qss(self):
        return f"""QLineEdit {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:5px;padding:5px 8px;
            font-size:11px;min-height:18px; }}
            QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}"""

    def _test(self):
        self.test_lbl.setVisible(True)
        self.test_lbl.setText("⏳ در حال تست...")
        self.test_lbl.setStyleSheet(
            f"color:{C_MUTED};font-size:10px;background:transparent;")
        try:
            td = DeviceTimeInfo(
                uid=self.device.uid, name=self.device.name,
                ip=self.device.ip, port=int(self.port_spin.value()),
                user=self.user_edit.text().strip(),
                password=self.pass_edit.text())
            mgr = DeviceTimeManager(); mgr.set_devices([td])
            results = mgr.read_all_times()
            r = results[0] if results else None
            if r and r.reachable and not r.error:
                dt_str = (r.current_dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                           if r.current_dt else "—")
                self.test_lbl.setText(
                    f"✅ {_proto_badge(r.protocol)}  •  {r.brand}  •  {dt_str}")
                self.test_lbl.setStyleSheet(
                    f"color:{C_SYNCED};font-size:10px;background:transparent;")
            else:
                self.test_lbl.setText(f"❌ {(r.error if r else '—') or '—'}")
                self.test_lbl.setStyleSheet(
                    f"color:{C_MAJOR};font-size:10px;background:transparent;")
        except Exception as e:
            self.test_lbl.setText(f"❌ {str(e)[:200]}")

    def _save(self):
        u = self.user_edit.text().strip()
        if not u:
            QMessageBox.warning(self, "خطا", "نام کاربری خالی است.")
            return
        if not DeviceTimeManager.update_credentials(
                self.device.ip, u, self.pass_edit.text(),
                int(self.port_spin.value())):
            QMessageBox.warning(self, "خطا", "ذخیره ناموفق.")
            return
        self.accept()

    def _delete(self):
        if QMessageBox.question(self, "حذف", "اطلاعات حذف شود؟",
                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        DeviceTimeManager.remove_credentials(self.device.ip)
        self.accept()


# ============================================================
# Simple User Dialog (با رمز فعلی و تکرار)
# ============================================================
class _SimpleUserDlg(QDialog):
    def __init__(self, parent=None, title="کاربر", need_level=False,
                  username="", ask_old=False, old_pass=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True); self.setMinimumWidth(380)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.username = username
        self.password = ""
        self.old_password = old_pass
        self.level = "User"

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 16); v.setSpacing(12)

        t = QLabel(title)
        t.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                         f"font-size:13px;font-weight:800;background:transparent;")
        v.addWidget(t)

        form = QFormLayout(); form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.user_edit = QLineEdit(username)
        if username:
            self.user_edit.setReadOnly(True)
        self.user_edit.setStyleSheet(self._qss())
        form.addRow(self._l("نام کاربری:"), self.user_edit)

        # رمز فعلی (فقط هنگام تغییر)
        self.old_pass_edit = None
        if ask_old:
            self.old_pass_edit = QLineEdit()
            self.old_pass_edit.setEchoMode(QLineEdit.Password)
            self.old_pass_edit.setText(old_pass or "")
            self.old_pass_edit.setStyleSheet(self._qss())
            form.addRow(self._l("رمز فعلی:"), self.old_pass_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setStyleSheet(self._qss())
        form.addRow(self._l("رمز جدید:"), self.pass_edit)

        self.pass2_edit = QLineEdit()
        self.pass2_edit.setEchoMode(QLineEdit.Password)
        self.pass2_edit.setStyleSheet(self._qss())
        form.addRow(self._l("تکرار رمز جدید:"), self.pass2_edit)

        self.level_combo = None
        if need_level:
            self.level_combo = QComboBox()
            for lv in ["Administrator", "Operator", "User"]:
                self.level_combo.addItem(lv, lv)
            self.level_combo.setStyleSheet(f"""QComboBox {{ background:{BG_ROW};
                color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};
                border-radius:5px;padding:5px 8px;
                font-size:11px;min-height:22px; }}
                QComboBox QAbstractItemView {{ background:{BG_ROW};
                color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};
                selection-background-color:{C_ACCENT}; }}""")
            form.addRow(self._l("سطح:"), self.level_combo)

        v.addLayout(form)

        warn = QLabel("⚠ رمز باید حداقل ۴ کاراکتر باشد. "
                       "پس از تغییر، حتماً یادداشت کنید.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"""color:{C_MINOR};font-size:10px;
            background:#241c0a;padding:6px 10px;border-radius:5px;
            border-left:3px solid {C_MINOR};""")
        v.addWidget(warn)

        br = QHBoxLayout(); br.addStretch(1)
        bc = QPushButton("انصراف"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 16px;font-size:11px; }}""")
        bc.clicked.connect(self.reject); br.addWidget(bc)
        bo = QPushButton("تأیید"); bo.setFixedHeight(32)
        bo.setCursor(Qt.PointingHandCursor)
        bo.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 18px;
            font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        bo.clicked.connect(self._ok); br.addWidget(bo)
        v.addLayout(br)

    def _qss(self):
        return f"""QLineEdit {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:5px;padding:5px 8px;
            font-size:11px;min-height:20px; }}
            QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}"""

    def _l(self, txt):
        l = QLabel(txt)
        l.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                         f"font-size:11px;font-weight:600;background:transparent;")
        return l

    def _ok(self):
        self.username = self.user_edit.text().strip()
        p1 = self.pass_edit.text()
        p2 = self.pass2_edit.text()

        if not self.username:
            QMessageBox.warning(self, "خطا", "نام کاربری خالی است.")
            return

        if p1 != p2:
            QMessageBox.warning(self, "خطا",
                "رمز جدید و تکرار آن مطابقت ندارند.")
            return

        if len(p1) < 4:
            QMessageBox.warning(self, "خطا",
                "رمز باید حداقل ۴ کاراکتر باشد.")
            return

        # رمز فعلی اجباری اگر ask_old
        if self.old_pass_edit is not None:
            if not self.old_pass_edit.text():
                QMessageBox.warning(self, "خطا",
                    "لطفاً رمز فعلی کاربر را وارد کنید.")
                return

        # تأیید نهایی
        if QMessageBox.question(self, "تأیید",
            f"آیا از تغییر رمز کاربر «{self.username}» مطمئن هستید؟",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        self.password = p1
        if self.level_combo:
            self.level = self.level_combo.currentData()
        self.accept()


# ============================================================
# User Management Dialog
# ============================================================
class UserManagementDialog(QDialog):
    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.devices = devices if isinstance(devices, list) else [devices]
        self.current_dev = self.devices[0]
        self.setWindowTitle("مدیریت کاربران دستگاه")
        self.setModal(True)
        self.setMinimumSize(640, 560)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 16); v.setSpacing(12)

        h = QHBoxLayout(); h.setSpacing(10)
        ic = QLabel("👥")
        ic.setStyleSheet("font-size:20px;background:transparent;")
        h.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(0)
        t1 = QLabel("مدیریت کاربران ONVIF")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel(f"{len(self.devices)} دستگاه در لیست")
        t2.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:10px;background:transparent;")
        tv.addWidget(t2)
        h.addLayout(tv, 1)
        v.addLayout(h)

        if len(self.devices) > 1:
            dev_row = QHBoxLayout(); dev_row.setSpacing(6)
            dl = QLabel("دستگاه:")
            dl.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                              f"font-size:11px;font-weight:600;background:transparent;")
            dev_row.addWidget(dl)
            self.dev_combo = QComboBox()
            for d in self.devices:
                self.dev_combo.addItem(f"{d.name or d.ip}   ({d.ip})", d.uid)
            self.dev_combo.currentIndexChanged.connect(self._on_dev_changed)
            self.dev_combo.setStyleSheet(f"""QComboBox {{ background:{BG_ROW};
                color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};
                border-radius:5px;padding:4px 8px;font-size:11px;
                min-height:22px; }}
                QComboBox QAbstractItemView {{ background:{BG_ROW};
                color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};
                selection-background-color:{C_ACCENT}; }}""")
            dev_row.addWidget(self.dev_combo, 1)
            v.addLayout(dev_row)
        else:
            self.dev_combo = None

        list_wrap = QFrame()
        list_wrap.setStyleSheet(f"QFrame {{ background:{BG_ROW};"
                                 f"border:1px solid {theme.COLOR_BORDER};"
                                 f"border-radius:6px; }}")
        lw = QVBoxLayout(list_wrap)
        lw.setContentsMargins(1, 1, 1, 1); lw.setSpacing(0)

        self.user_list = QTreeWidget()
        self.user_list.setColumnCount(3)
        self.user_list.setHeaderLabels(["نام کاربری", "سطح دسترسی", "راهنما"])
        hdr = self.user_list.headerItem()
        for i in range(3):
            hdr.setTextAlignment(i, Qt.AlignRight | Qt.AlignVCenter)
        self.user_list.setColumnWidth(0, 200)
        self.user_list.setColumnWidth(1, 150)
        self.user_list.setRootIsDecorated(False)
        self.user_list.setUniformRowHeights(True)
        self.user_list.setStyleSheet(f"""
            QTreeWidget {{ background:{BG_ROW};
                color:{theme.COLOR_TEXT_PRIMARY};border:none;
                font-size:11px;outline:none; }}
            QTreeWidget::item {{ padding:5px 4px;
                border-bottom:1px solid #1a1e24;min-height:24px; }}
            QTreeWidget::item:selected {{ background:{C_ACCENT};color:white; }}
            QHeaderView::section {{ background:{BG_HDR};
                color:{theme.COLOR_TEXT_SECONDARY};border:none;
                border-bottom:1px solid {theme.COLOR_BORDER};
                padding:6px 4px;font-size:10px;font-weight:700; }}
        """)
        self.user_list.itemDoubleClicked.connect(self._on_user_dbl)
        lw.addWidget(self.user_list)
        v.addWidget(list_wrap, 1)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                                       f"font-size:10px;background:transparent;")
        v.addWidget(self.status_lbl)

        btn_row = QHBoxLayout(); btn_row.setSpacing(6)
        btn_row.addWidget(self._tool_btn("🔄", "بازخوانی", self._load_users))
        btn_row.addWidget(self._tool_btn("➕", "کاربر جدید", self._add_user))
        btn_row.addWidget(self._tool_btn("🔑", "تغییر رمز", self._change_pwd,
                                           primary=True))
        btn_row.addWidget(self._tool_btn("🗑", "حذف کاربر", self._delete_user,
                                           danger=True))
        btn_row.addStretch(1)
        bc = QPushButton("بستن"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;padding:0 16px;font-size:11px; }}
            QPushButton:hover {{ background:{theme.COLOR_BG_HOVER}; }}""")
        bc.clicked.connect(self.accept)
        btn_row.addWidget(bc)
        v.addLayout(btn_row)

        if len(self.devices) > 1:
            bulk = QFrame()
            bulk.setStyleSheet(f"QFrame {{ background:{BG_HDR};"
                               f"border:1px solid {theme.COLOR_BORDER};"
                               f"border-radius:6px; }}")
            bw = QHBoxLayout(bulk)
            bw.setContentsMargins(10, 8, 10, 8); bw.setSpacing(8)

            bl = QLabel("🔐 تغییر رمز گروهی:")
            bl.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                              f"font-size:11px;font-weight:700;background:transparent;")
            bw.addWidget(bl)

            self.bulk_user = QLineEdit()
            self.bulk_user.setPlaceholderText("کاربر")
            self.bulk_user.setStyleSheet(self._qss())
            self.bulk_user.setFixedWidth(120)
            bw.addWidget(self.bulk_user)

            self.bulk_pass = QLineEdit()
            self.bulk_pass.setPlaceholderText("رمز جدید")
            self.bulk_pass.setEchoMode(QLineEdit.Password)
            self.bulk_pass.setStyleSheet(self._qss())
            self.bulk_pass.setFixedWidth(160)
            bw.addWidget(self.bulk_pass)

            # ★ «اعمال روی انتخاب‌شده‌ها»
            b_bulk = QPushButton("اعمال روی انتخاب‌شده‌ها")
            b_bulk.setFixedHeight(28); b_bulk.setCursor(Qt.PointingHandCursor)
            b_bulk.setStyleSheet(f"""QPushButton {{ background:{C_MODERATE};
                color:white;border:none;border-radius:5px;padding:0 14px;
                font-size:11px;font-weight:700; }}
                QPushButton:hover {{ background:#d68910; }}""")
            b_bulk.clicked.connect(self._bulk_change_pwd)
            bw.addWidget(b_bulk)
            bw.addStretch(1)
            v.addWidget(bulk)

        QTimer.singleShot(100, self._load_users)

    def _qss(self):
        return f"""QLineEdit {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:5px;padding:4px 8px;
            font-size:11px;min-height:18px; }}
            QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}"""

    def _tool_btn(self, icon, label, cb, primary=False, danger=False):
        b = QPushButton(f"  {icon}  {label}")
        b.setFixedHeight(30); b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(cb)
        if danger:
            b.setStyleSheet(f"""QPushButton {{ background:transparent;
                color:{C_MAJOR};border:1px solid {C_MAJOR};
                border-radius:5px;padding:0 10px;
                font-size:10px;font-weight:700; }}
                QPushButton:hover {{ background:{C_MAJOR};color:white; }}""")
        elif primary:
            b.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};
                color:white;border:none;border-radius:5px;padding:0 12px;
                font-size:10px;font-weight:700; }}
                QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        else:
            b.setStyleSheet(f"""QPushButton {{ background:{BG_HDR};
                color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};
                border-radius:5px;padding:0 10px;font-size:10px; }}
                QPushButton:hover {{ background:{theme.COLOR_BG_HOVER};
                border-color:{C_ACCENT}; }}""")
        return b

    def _on_dev_changed(self, idx):
        uid = self.dev_combo.itemData(idx)
        for d in self.devices:
            if d.uid == uid:
                self.current_dev = d
                break
        self._load_users()

    def _load_users(self):
        self.user_list.clear()
        self.status_lbl.setText("⏳ خواندن کاربران…")
        try:
            mgr = DeviceTimeManager()
            ok, users, err = mgr.get_users(self.current_dev)
            if not ok:
                self.status_lbl.setText(f"❌ {err[:120]}")
                return
            for u in users:
                it = QTreeWidgetItem(self.user_list)
                it.setText(0, u.get("username", ""))
                it.setText(1, u.get("level", ""))
                it.setText(2, "دابل‌کلیک = تغییر رمز")
                it.setForeground(2, QBrush(QColor(C_MUTED)))
                it.setData(0, Qt.UserRole, u.get("username", ""))
            self.status_lbl.setText(f"✅ {len(users)} کاربر")
        except Exception as e:
            self.status_lbl.setText(f"❌ {str(e)[:120]}")

    def _selected_user(self):
        it = self.user_list.currentItem()
        if it is None:
            return None
        return it.data(0, Qt.UserRole)

    def _add_user(self):
        dlg = _SimpleUserDlg(self, title="افزودن کاربر جدید", need_level=True)
        if dlg.exec() != QDialog.Accepted:
            return
        mgr = DeviceTimeManager()
        ok, err = mgr.add_user(self.current_dev, dlg.username,
                                dlg.password, dlg.level)
        if ok:
            self.status_lbl.setText(f"✅ کاربر {dlg.username} اضافه شد")
            self._load_users()
        else:
            QMessageBox.warning(self, "خطا", err)

    def _change_pwd(self):
        u = self._selected_user()
        if not u:
            QMessageBox.warning(self, "خطا", "کاربری انتخاب نشده.")
            return
        dlg = _SimpleUserDlg(self, title=f"تغییر رمز کاربر «{u}»",
                              need_level=False, username=u,
                              ask_old=True,
                              old_pass=self.current_dev.password or "")
        if dlg.exec() != QDialog.Accepted:
            return
        mgr = DeviceTimeManager()
        ok, err = mgr.set_user(self.current_dev, u, dlg.password)
        if ok:
            self.status_lbl.setText(f"✅ رمز {u} تغییر کرد")
            self._load_users()
        else:
            QMessageBox.warning(self, "خطا", err)

    def _delete_user(self):
        u = self._selected_user()
        if not u:
            QMessageBox.warning(self, "خطا", "کاربری انتخاب نشده.")
            return
        if QMessageBox.question(self, "حذف",
            f"کاربر «{u}» حذف شود؟",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        mgr = DeviceTimeManager()
        ok, err = mgr.delete_user(self.current_dev, u)
        if ok:
            self.status_lbl.setText(f"✅ {u} حذف شد")
            self._load_users()
        else:
            QMessageBox.warning(self, "خطا", err)

    def _on_user_dbl(self, item, col):
        self._change_pwd()

    def _bulk_change_pwd(self):
        u = self.bulk_user.text().strip()
        p = self.bulk_pass.text()
        if not u or not p:
            QMessageBox.warning(self, "خطا", "کاربر و رمز را وارد کنید.")
            return
        n = len(self.devices)
        ips = ", ".join(d.ip for d in self.devices[:5])
        if n > 5:
            ips += f" و {n-5} دستگاه دیگر"
        if QMessageBox.question(self, "تأیید تغییر رمز گروهی",
            f"رمز کاربر «{u}» روی {n} دستگاه زیر تغییر کند؟\n\n{ips}",
            QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        mgr = DeviceTimeManager()
        ok_list, fail_list = [], []
        for dev in self.devices:
            ok, err = mgr.set_user(dev, u, p)
            if ok:
                ok_list.append(dev.ip)
                if u == (dev.user or "admin"):
                    DeviceTimeManager.update_credentials(dev.ip, u, p, dev.port)
            else:
                fail_list.append((dev.ip, err[:80]))

        msg = f"✅ {len(ok_list)} موفق از {n}"
        if fail_list:
            msg += f"\n\n❌ {len(fail_list)} ناموفق:"
            for ip, e in fail_list[:8]:
                msg += f"\n  {ip}: {e}"
        QMessageBox.information(self, "نتیجه", msg)
        self._load_users()


# ============================================================
# Result Dialog
# ============================================================
class ResultDialog(QDialog):
    def __init__(self, results, title="نتیجه", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setMinimumHeight(380)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")
        self.retry_devices = []

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 14); v.setSpacing(10)
        ok_list = [r for r in results if r.reachable and not r.error]
        fail_list = [r for r in results if r.error or not r.reachable]

        h = QHBoxLayout(); h.setSpacing(8)
        ic = QLabel("✅" if not fail_list else "⚠")
        ic.setStyleSheet("font-size:22px;background:transparent;")
        h.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(0)
        t1 = QLabel(title)
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:14px;font-weight:800;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel(f"✅ {len(ok_list)} موفق  •  ❌ {len(fail_list)} ناموفق")
        t2.setStyleSheet(f"color:{C_SYNCED if not fail_list else C_MODERATE};"
                          f"font-size:10px;background:transparent;font-weight:600;")
        tv.addWidget(t2)
        h.addLayout(tv, 1)
        v.addLayout(h)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet(f"""QTextEdit {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:6px;font-family:Consolas;
            font-size:11px;padding:8px; }}""")

        lines = []
        if ok_list:
            lines.append("━━━ ✅ موفق ━━━")
            for r in ok_list:
                lines.append(f"  ✓ {r.name or r.ip}   [{_proto_badge(r.protocol)}]")
            lines.append("")
        if fail_list:
            lines.append("━━━ ❌ ناموفق ━━━")
            for r in fail_list:
                err = (r.error or "unreachable")[:100]
                auth = " 🔑" if _is_auth_error(r.error or "") else ""
                lines.append(f"  ✗ {r.name or r.ip}{auth}")
                lines.append(f"      → {err}")
                self.retry_devices.append(r)
        self.text.setText("\n".join(lines))
        v.addWidget(self.text, 1)

        br = QHBoxLayout(); br.setSpacing(6)
        if fail_list:
            bret = QPushButton("🔄 تلاش دوباره")
            bret.setFixedHeight(32); bret.setCursor(Qt.PointingHandCursor)
            bret.setStyleSheet(f"""QPushButton {{ background:{C_MODERATE};
                color:white;border:none;border-radius:6px;padding:0 14px;
                font-size:11px;font-weight:700; }}
                QPushButton:hover {{ background:#d68910; }}""")
            bret.clicked.connect(lambda: self.done(2))
            br.addWidget(bret)
            auth_fails = [r for r in fail_list if _is_auth_error(r.error or "")]
            if auth_fails:
                bfix = QPushButton("🔑 اصلاح اطلاعات")
                bfix.setFixedHeight(32); bfix.setCursor(Qt.PointingHandCursor)
                bfix.setStyleSheet(f"""QPushButton {{ background:transparent;
                    color:{C_ACCENT};border:1px solid {C_ACCENT};
                    border-radius:6px;padding:0 14px;
                    font-size:11px;font-weight:700; }}
                    QPushButton:hover {{ background:{C_ACCENT};color:white; }}""")
                bfix.clicked.connect(lambda: self._fix(auth_fails))
                br.addWidget(bfix)
        br.addStretch(1)
        bc = QPushButton("بستن"); bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};color:white;
            border:none;border-radius:6px;padding:0 20px;
            font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
        bc.clicked.connect(self.accept); br.addWidget(bc)
        v.addLayout(br)

    def _fix(self, devices):
        for d in devices:
            CredentialsDialog(d, self).exec()
        self.done(3)


# ============================================================
# Main Page
# ============================================================
class DeviceTimePage(BasePage):
    PAGE_KEY = "device_time"
    PAGE_TITLE = "همگام‌سازی ساعت"
    PANEL_TITLE = "کنترل ساعت"
    HAS_PANEL = False

    def __init__(self, nvr_engine=None, parent=None):
        super().__init__(parent)
        self.cam_manager = CameraManager()
        self.nvr_manager = NVRManager.instance()
        self._worker = None
        self.devices = []
        self._dev_by_uid = {}
        self._items = {}
        self._groups = {}
        self._only_drift = False
        self._only_drift2 = False
        self._checked = set()
        self._progress_dlg = None
        self._progress_bar = None
        self._progress_status = None
        self._ref_dt = None
        self._ref_server = "time.windows.com"
        try:
            s = settings_manager.load_settings()
            rs = getattr(s, SETTINGS_REF_SERVER, "") or ""
            if rs:
                self._ref_server = rs
        except Exception:
            pass

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10); v.setSpacing(8)

        v.addWidget(self._build_header())
        v.addWidget(self._build_toolbar())
        v.addWidget(self._build_filter())
        v.addWidget(self._build_tree_wrap(), 1)

        self._loading = LocalLoadingOverlay(self)

        QTimer.singleShot(150, self._reload)
        QTimer.singleShot(100, self._position_loading)

    def _position_loading(self):
        try:
            self._loading.setGeometry(self.rect())
        except Exception:
            pass

    def resizeEvent(self, e):
        super().resizeEvent(e)
        try:
            self._loading.setGeometry(self.rect())
        except Exception:
            pass

    def _build_header(self):
        bar = QFrame()
        bar.setFixedHeight(58)
        bar.setStyleSheet(f"QFrame {{ background:{BG_ROW};"
                           f"border:1px solid {theme.COLOR_BORDER};"
                           f"border-radius:8px; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 6, 14, 6); h.setSpacing(12)
        ic = QLabel("🕒")
        ic.setStyleSheet("font-size:18px;background:transparent;")
        h.addWidget(ic)
        tv = QVBoxLayout(); tv.setSpacing(0)
        t1 = QLabel("همگام‌سازی ساعت دستگاه‌ها")
        t1.setStyleSheet(f"color:{theme.COLOR_TEXT_PRIMARY};"
                          f"font-size:13px;font-weight:800;background:transparent;")
        tv.addWidget(t1)
        t2 = QLabel("مدیریت ساعت، منطقه زمانی و کاربران روی دوربین‌ها و NVRها")
        t2.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:9px;background:transparent;")
        tv.addWidget(t2)
        h.addLayout(tv); h.addSpacing(16)

        self.chip_total = self._chip("کل", "0", "#58a6ff")
        self.chip_sync  = self._chip("همگام", "0", C_SYNCED)
        self.chip_drift = self._chip("اختلاف", "0", C_MODERATE)
        self.chip_off   = self._chip("آفلاین", "0", C_OFFLINE)
        for c in (self.chip_total, self.chip_sync,
                   self.chip_drift, self.chip_off):
            h.addWidget(c)
        h.addStretch(1)
        return bar

    def _chip(self, label, value, color):
        f = QFrame()
        f.setStyleSheet(f"QFrame {{ background:{BG_HDR};border-radius:6px; }}")
        f.setFixedHeight(40)
        h = QHBoxLayout(f)
        h.setContentsMargins(8, 4, 8, 4); h.setSpacing(6)
        v = QVBoxLayout(); v.setSpacing(0)
        tl = QLabel(label)
        tl.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:8px;font-weight:700;background:transparent;")
        v.addWidget(tl)
        vl = QLabel(value)
        vl.setStyleSheet(f"color:{color};font-size:14px;font-weight:800;"
                          f"background:transparent;")
        v.addWidget(vl)
        h.addLayout(v)
        f._value = vl
        return f

    def _build_toolbar(self):
        bar = QFrame()
        bar.setFixedHeight(38)
        bar.setStyleSheet(f"QFrame {{ background:{BG_ROW};"
                           f"border:1px solid {theme.COLOR_BORDER};"
                           f"border-radius:8px; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 4, 8, 4); h.setSpacing(6)

        def _btn(icon, label, cb, primary=False):
            b = QPushButton(f"  {icon}  {label}")
            b.setFixedHeight(28); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(cb)
            if primary:
                b.setStyleSheet(f"""QPushButton {{ background:{C_ACCENT};
                    color:white;border:none;border-radius:5px;padding:0 12px;
                    font-size:10px;font-weight:700; }}
                    QPushButton:hover {{ background:{theme.COLOR_ACCENT_HOVER}; }}""")
            else:
                b.setStyleSheet(f"""QPushButton {{ background:{BG_HDR};
                    color:{theme.COLOR_TEXT_PRIMARY};
                    border:1px solid {theme.COLOR_BORDER};
                    border-radius:5px;padding:0 10px;
                    font-size:10px;font-weight:600; }}
                    QPushButton:hover {{ background:{theme.COLOR_BG_HOVER};
                    border-color:{C_ACCENT}; }}""")
            return b

        h.addWidget(_btn("🔄", "خواندن همه", self._read_all, primary=True))
        h.addWidget(_btn("🕒", "تنظیم زمان…", self._open_set_time))
        h.addWidget(_btn("👥", "مدیریت کاربران…", self._open_user_mgmt))
        h.addSpacing(8)
        h.addWidget(_btn("☑", "انتخاب همه", self._select_all))
        h.addWidget(_btn("☐", "لغو انتخاب", self._clear_sel))
        h.addStretch(1)
        self.count_lbl = QLabel("انتخاب: 0")
        self.count_lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                                       f"font-size:10px;background:transparent;")
        h.addWidget(self.count_lbl)
        return bar

    def _build_filter(self):
        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"QFrame {{ background:{BG_ROW};"
                           f"border:1px solid {theme.COLOR_BORDER};"
                           f"border-radius:8px; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 3, 8, 3); h.setSpacing(6)

        si = QLabel("🔍")
        si.setStyleSheet(f"color:{theme.COLOR_TEXT_SECONDARY};"
                          f"font-size:11px;background:transparent;")
        h.addWidget(si)

        self.search = QLineEdit()
        self.search.setPlaceholderText("جستجو…")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(200)
        self.search.setStyleSheet(f"""QLineEdit {{ background:{BG_HDR};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};border-radius:5px;
            padding:2px 8px;font-size:10px;min-height:18px; }}
            QLineEdit:focus {{ border:1px solid {C_ACCENT}; }}""")
        self.search.textChanged.connect(self._apply_filter)
        h.addWidget(self.search)

        self.filter = QComboBox()
        for lbl, key in [("همه", "all"), ("همگام", "synced"),
                          ("اختلاف", "drifted"), ("آفلاین", "offline"),
                          ("دارای Credentials", "cred")]:
            self.filter.addItem(lbl, key)
        self.filter.setFixedWidth(130)
        self.filter.setStyleSheet(f"""QComboBox {{ background:{BG_HDR};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};border-radius:5px;
            padding:2px 8px;font-size:10px;min-height:18px; }}
            QComboBox QAbstractItemView {{ background:{BG_ROW};
            color:{theme.COLOR_TEXT_PRIMARY};
            border:1px solid {theme.COLOR_BORDER};
            selection-background-color:{C_ACCENT}; }}""")
        self.filter.currentIndexChanged.connect(self._apply_filter)
        h.addWidget(self.filter)

        self.btn_drift2 = QPushButton("⏱ اختلاف > ۲ دقیقه")
        self.btn_drift2.setCheckable(True)
        self.btn_drift2.setCursor(Qt.PointingHandCursor)
        self.btn_drift2.setFixedHeight(24)
        self.btn_drift2.setStyleSheet(f"""QPushButton {{ background:transparent;
            color:{theme.COLOR_TEXT_SECONDARY};
            border:1px solid {theme.COLOR_BORDER};
            border-radius:5px;padding:0 10px;
            font-size:9px;font-weight:700; }}
            QPushButton:hover {{ border-color:{C_MAJOR};color:{C_MAJOR}; }}
            QPushButton:checked {{ background:{C_MAJOR}22;
            color:{C_MAJOR};border-color:{C_MAJOR}; }}""")
        self.btn_drift2.toggled.connect(self._on_drift2_toggle)
        h.addWidget(self.btn_drift2)

        h.addStretch(1)
        return bar

    def _build_tree_wrap(self):
        wrap = QFrame()
        wrap.setStyleSheet(f"QFrame {{ background:{BG_ROW};"
                            f"border:1px solid {theme.COLOR_BORDER};"
                            f"border-radius:8px; }}")
        w = QVBoxLayout(wrap)
        w.setContentsMargins(1, 1, 1, 1); w.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(8)
        self.tree.setHeaderLabels([
            "", "نام دستگاه", "آدرس IP", "پروتکل",
            "اختلاف", "زمان", "🌐 وب", "وضعیت"
        ])
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setRootIsDecorated(False)
        self.tree.setAnimated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setIndentation(0)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._ctx_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._dbl_click)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemSelectionChanged.connect(self._update_count)

        hdr = self.tree.headerItem()
        for i in range(8):
            hdr.setTextAlignment(i, Qt.AlignRight | Qt.AlignVCenter)

        self.tree.header().setStretchLastSection(True)
        self.tree.setColumnWidth(0, 26)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 115)
        self.tree.setColumnWidth(3, 75)
        self.tree.setColumnWidth(4, 75)
        self.tree.setColumnWidth(5, 80)
        self.tree.setColumnWidth(6, 55)

        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {BG_ROW}; color: {theme.COLOR_TEXT_PRIMARY};
                border: none; font-size: 10px; outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 2px;
                border-bottom: 1px solid #1a1e24;
                min-height: 22px;
            }}
            QTreeWidget::item:selected {{
                background: {C_ACCENT}; color: white;
            }}
            QTreeWidget::item:hover {{ background: #161b22; }}
            QHeaderView {{ background: {BG_HDR}; }}
            QHeaderView::section {{
                background: {BG_HDR};
                color: {theme.COLOR_TEXT_SECONDARY};
                border: none;
                border-bottom: 1px solid {theme.COLOR_BORDER};
                padding: 6px 4px; font-size: 9px; font-weight: 700;
            }}
            QHeaderView::section:hover {{
                background: #141a21; color: {C_ACCENT};
            }}
        """)
        w.addWidget(self.tree)
        return wrap

    # ============================================================
    def _reload(self):
        try:
            cams = self.cam_manager.all()
            self.devices = DeviceTimeManager.build_device_list_from_cameras(
                cams, apply_saved_credentials=True)
        except Exception as e:
            print(f"[device_time] reload: {e}")
            self.devices = []
        self._dev_by_uid = {d.uid: d for d in self.devices}
        self._rebuild_tree()
        self._update_stats()
        QTimer.singleShot(300, self._auto_read)

    def _auto_read(self):
        if not self.devices:
            return
        # ★ overlay محلی (نه ActivityBus سراسری)
        self._loading.show_loading("در حال بردن وضعیت دستگاه‌ها...")
        QTimer.singleShot(100, lambda: self._run(
            self.devices, "read", quiet=True, show_progress=False))

    def _rebuild_tree(self):
        saved_expanded = set()
        for key, top in self._groups.items():
            if top.isExpanded():
                saved_expanded.add(key)

        self.tree.setUpdatesEnabled(False)
        self.tree.blockSignals(True)
        self.tree.clear()
        self._items.clear(); self._groups.clear()

        try:
            nvr_by_uid = {n.uid: n for n in self.nvr_manager.all()}
        except Exception:
            nvr_by_uid = {}

        saved_creds = DeviceTimeManager.load_credentials()
        cams = self.cam_manager.all()
        cam_by_uid = {c.uid: c for c in cams}

        nvr_map = {}; standalone = []
        for dev in self.devices:
            cam = cam_by_uid.get(dev.uid)
            if cam and cam.nvr_uid and cam.nvr_uid in nvr_by_uid:
                nvr_map.setdefault(cam.nvr_uid, []).append(dev)
            else:
                standalone.append(dev)

        for nvr_uid, devs in nvr_map.items():
            nvr = nvr_by_uid[nvr_uid]
            self._add_group(f"nvr:{nvr_uid}",
                             f"📹  {nvr.name}   ({len(devs)})",
                             "#c39bd3", devs, saved_creds, saved_expanded)
        if standalone:
            self._add_group("standalone",
                             f"📷  دوربین‌های مستقل   ({len(standalone)})",
                             "#85c1e9", standalone, saved_creds, saved_expanded)

        for uid, item in self._items.items():
            item.setCheckState(0, Qt.Checked if uid in self._checked
                                else Qt.Unchecked)

        self.tree.blockSignals(False)
        self.tree.setUpdatesEnabled(True)
        self._apply_filter()
        self._update_count()

    def _add_group(self, key, title, color, devs, saved_creds, saved_expanded):
        grp = QTreeWidgetItem(self.tree)
        grp.setText(0, "")
        grp.setText(1, title)
        for i in range(2, 8):
            grp.setText(i, "")
        f = grp.font(1); f.setBold(True); f.setPointSize(9)
        grp.setFont(1, f)
        grp.setForeground(1, QBrush(QColor(color)))
        grp.setFlags(grp.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
        grp.setCheckState(0, Qt.Unchecked)
        grp.setData(0, Qt.UserRole, None)
        grp.setData(0, Qt.UserRole + 1, key)
        self._groups[key] = grp

        for dev in devs:
            it = self._make_item(dev, grp, saved_creds)
            self._items[dev.uid] = it

        grp.setExpanded(key in saved_expanded or not saved_expanded)

    def _make_item(self, dev, parent, saved_creds):
        it = QTreeWidgetItem(parent)
        it.setText(0, "")
        it.setText(1, dev.name or dev.ip)
        it.setText(2, dev.ip or "—")
        it.setText(3, "—")
        it.setText(4, "—")
        it.setText(5, "—")
        it.setText(6, "🌐")
        it.setForeground(6, QBrush(QColor(C_WEB)))
        it.setTextAlignment(6, Qt.AlignCenter)
        it.setToolTip(6, f"باز کردن http://{dev.ip}")

        has_cred = dev.ip in saved_creds
        if has_cred:
            it.setText(7, "⏳ خواندن…")
            it.setForeground(7, QBrush(QColor(C_MUTED)))
        else:
            it.setText(7, "⚠ بدون Credentials")
            it.setForeground(7, QBrush(QColor(C_MODERATE)))

        it.setData(0, Qt.UserRole, dev.uid)
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
        it.setCheckState(0, Qt.Unchecked)
        return it

    def _on_item_clicked(self, item, col):
        if col != 6:
            return
        uid = item.data(0, Qt.UserRole)
        if not uid:
            return
        dev = self._dev_by_uid.get(uid)
        if dev and dev.ip:
            try:
                webbrowser.open(f"http://{dev.ip}")
            except Exception as e:
                print(f"[web] {e}")

    def _on_drift_toggle(self, on):
        self._only_drift = on
        self._apply_filter()

    def _on_drift2_toggle(self, on):
        self._only_drift2 = on
        self._apply_filter()

    def _apply_filter(self):
        text = (self.search.text() or "").strip().lower()
        mode = self.filter.currentData() or "all"
        saved = DeviceTimeManager.load_credentials()

        for key, top in self._groups.items():
            any_visible = False
            for i in range(top.childCount()):
                child = top.child(i)
                uid = child.data(0, Qt.UserRole)
                dev = self._dev_by_uid.get(uid)
                if dev is None:
                    child.setHidden(True); continue

                ms = True
                if text:
                    ms = (text in (dev.name or "").lower()
                           or text in (dev.ip or "").lower())

                mm = True
                if mode == "cred":
                    mm = dev.ip in saved
                elif mode == "offline":
                    mm = not dev.reachable
                elif mode == "synced":
                    mm = dev.reachable and self._is_synced(dev)
                elif mode == "drifted":
                    mm = dev.reachable and not self._is_synced(dev)
                if self._only_drift:
                    mm = mm and dev.reachable and not self._is_synced(dev)

                if self._only_drift2:
                    if not (dev.reachable and dev.current_dt and self._ref_dt):
                        mm = False
                    else:
                        drift = abs((dev.current_dt - self._ref_dt).total_seconds())
                        if drift < 120:
                            mm = False

                visible = ms and mm
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            top.setHidden(not any_visible)

    def _is_synced(self, dev):
        if not dev.current_dt: return False
        ref = self._ref_dt or datetime.datetime.now(datetime.timezone.utc)
        return abs((dev.current_dt - ref).total_seconds()) <= D_SYNCED

    def _on_item_changed(self, item, col):
        if col == 0:
            uid = item.data(0, Qt.UserRole)
            if uid:
                if item.checkState(0) == Qt.Checked:
                    self._checked.add(uid)
                else:
                    self._checked.discard(uid)
            self._update_count()

    def _update_count(self):
        n = len(self._selected())
        self.count_lbl.setText(f"انتخاب: {n}")

    def _selected(self):
        uids = set(self._checked)
        for it in self.tree.selectedItems():
            u = it.data(0, Qt.UserRole)
            if u:
                uids.add(u)
        return [self._dev_by_uid[uid]
                for uid in uids if uid in self._dev_by_uid]

    def _fetch_reference_time(self):
        """خواندن زمان از سرور NTP مرجع."""
        try:
            buf = b'\x1b' + 47 * b'\0'
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2.0)
            s.sendto(buf, (self._ref_server, 123))
            data, _ = s.recvfrom(1024)
            s.close()
            if data:
                unpacked = struct.unpack('!12I', data)
                ntp_time = unpacked[10] - 2208988800
                return datetime.datetime.fromtimestamp(
                    ntp_time, tz=datetime.timezone.utc)
        except Exception as e:
            print(f"[NTP-ref] {self._ref_server}: {e}")
        return datetime.datetime.now(datetime.timezone.utc)

    def _ctx_menu(self, pos):
        it = self.tree.itemAt(pos)
        if it is not None:
            uid = it.data(0, Qt.UserRole)
            if uid and not it.isSelected():
                self.tree.clearSelection()
                it.setSelected(True)

        dev = None
        if it is not None:
            uid = it.data(0, Qt.UserRole)
            if uid:
                dev = self._dev_by_uid.get(uid)

        targets = self._selected()
        if dev is not None and dev.uid not in [d.uid for d in targets]:
            targets = [dev]

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{BG_ROW};color:{theme.COLOR_TEXT_PRIMARY};
                border:1px solid {theme.COLOR_BORDER};padding:4px;
                border-radius:6px; }}
            QMenu::item {{ padding:7px 22px;border-radius:4px;font-size:11px; }}
            QMenu::item:selected {{ background:{C_ACCENT};color:white; }}
            QMenu::separator {{ height:1px;background:{theme.COLOR_BORDER};
                margin:4px 8px; }}
        """)

        if not targets:
            a = QAction("🔄  خواندن همه زمان‌ها", self)
            a.triggered.connect(self._read_all); menu.addAction(a)
            a = QAction("☑  انتخاب همه", self)
            a.triggered.connect(self._select_all); menu.addAction(a)
            a = QAction("☐  لغو انتخاب", self)
            a.triggered.connect(self._clear_sel); menu.addAction(a)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return

        n = len(targets)
        hdr = QAction(f"📌  {n} دستگاه انتخاب‌شده", self)
        hdr.setEnabled(False); menu.addAction(hdr)
        menu.addSeparator()

        m_time = menu.addMenu("⏰  تنظیم زمان و تاریخ")
        m_time.setStyleSheet(menu.styleSheet())
        a = QAction("🖥  هماهنگ‌سازی با رایانه شما", self)
        a.triggered.connect(lambda: self._run(targets, "sync_pc"))
        m_time.addAction(a)
        a = QAction("✏  زمان دستی…", self)
        a.triggered.connect(lambda: self._run_manual(targets))
        m_time.addAction(a)
        a = QAction("🌐  سرور NTP…", self)
        a.triggered.connect(lambda: self._run_ntp(targets))
        m_time.addAction(a)
        a = QAction("🌍  تنظیم TimeZone…", self)
        a.triggered.connect(lambda: self._run_timezone(targets))
        m_time.addAction(a)

        m_user = menu.addMenu("👥  مدیریت کاربران")
        m_user.setStyleSheet(menu.styleSheet())
        a = QAction("🆕  افزودن / تغییر / حذف کاربر…", self)
        a.triggered.connect(lambda: self._open_user_mgmt_for(targets))
        m_user.addAction(a)
        if dev is not None:
            a = QAction("🔑  ویرایش Credentials اتصال…", self)
            a.triggered.connect(lambda: self._edit_creds(dev))
            m_user.addAction(a)
            a = QAction("🧪  تست اتصال", self)
            a.triggered.connect(
                lambda: self._run([dev], "read", quiet=True))
            m_user.addAction(a)

        menu.addSeparator()
        a = QAction("🔄  خواندن زمان", self)
        a.triggered.connect(lambda: self._run(targets, "read"))
        menu.addAction(a)
        if dev is not None and dev.ip:
            a = QAction("🌐  باز کردن وب‌پنل", self)
            a.triggered.connect(lambda: self._open_web(dev.ip))
            menu.addAction(a)
        a = QAction("📋  کپی IP" + ("ها" if n > 1 else ""), self)
        a.triggered.connect(lambda: self._copy_ips(targets))
        menu.addAction(a)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _open_web(self, ip):
        try:
            webbrowser.open(f"http://{ip}")
        except Exception as e:
            print(f"[web] {e}")

    def _copy_ips(self, devices):
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(
                "\n".join(d.ip for d in devices if d.ip))
        except Exception:
            pass

    def _dbl_click(self, it, col):
        uid = it.data(0, Qt.UserRole)
        if not uid:
            return
        dev = self._dev_by_uid.get(uid)
        if dev:
            self._open_set_time()

    def _open_set_time(self):
        d = self._selected()
        if not d:
            dlg_info(self, "دستگاهی انتخاب نشده.", "زمان")
            return
        dlg = SetTimeMethodDialog(len(d), self)
        if dlg.exec() != QDialog.Accepted:
            return
        m = dlg.chosen
        if m == SetTimeMethodDialog.MODE_PC:
            self._run(d, "sync_pc")
        elif m == SetTimeMethodDialog.MODE_MANUAL:
            self._run_manual(d)
        elif m == SetTimeMethodDialog.MODE_NTP:
            self._run_ntp(d)

    def _open_user_mgmt(self):
        d = self._selected()
        if not d:
            dlg_info(self,
                      "ابتدا حداقل یک دستگاه انتخاب کنید.",
                      "مدیریت کاربران")
            return
        self._open_user_mgmt_for(d)

    def _open_user_mgmt_for(self, devices):
        if not devices:
            return
        has_nvr = False
        has_cam = False
        for d in devices:
            is_nvr = False
            try:
                for n in self.nvr_manager.all():
                    if n.uid == d.uid:
                        is_nvr = True
                        break
            except Exception:
                pass

            cam = self.cam_manager.get(d.uid)
            if is_nvr:
                has_nvr = True
            elif cam is not None and getattr(cam, "nvr_uid", ""):
                has_cam = True
            elif cam is not None:
                name = (getattr(cam, "name", "") or "").lower()
                if any(k in name for k in ("nvr", "خدمات شهر", "khadamat")):
                    has_nvr = True
                else:
                    has_cam = True

        if has_nvr and has_cam:
            dlg_info(self,
                      "امکان ویرایش گروهی دستگاه ضبط و دوربین با هم وجود ندارد.\n\n"
                      "لطفاً فقط یکی از این دو مورد را انتخاب کنید:\n"
                      "• دستگاه‌های ضبط (NVR)\n"
                      "• دوربین‌ها",
                      "خطا")
            return

        dlg = UserManagementDialog(devices, self)
        dlg.exec()

    def _run_manual(self, targets):
        dlg = ManualTimeDialog(len(targets), self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._run(targets, "manual", {"dt": dlg.result_dt})
        if dlg.result_tz is not None:
            QTimer.singleShot(600, lambda: self._run(
                targets, "timezone", {"tz_value": dlg.result_tz},
                quiet=True, show_progress=False))

    def _run_ntp(self, targets):
        dlg = NTPDialog(len(targets), self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._run(targets, "ntp", {"ntp_server": dlg.result_server})
        if dlg.result_tz is not None:
            QTimer.singleShot(600, lambda: self._run(
                targets, "timezone", {"tz_value": dlg.result_tz},
                quiet=True, show_progress=False))

    def _run_timezone(self, targets):
        dlg = TimezoneDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        self._run(targets, "timezone", {"tz_value": dlg.result_tz})

    def _read_all(self):
        if not self.devices:
            dlg_info(self, "دستگاهی برای خواندن وجود ندارد.", "خواندن زمان")
            return
        self._run(self.devices, "read", quiet=True, show_progress=True)

    def _select_all(self):
        self.tree.blockSignals(True)
        self._checked = set(self._items.keys())
        for it in self._items.values():
            it.setCheckState(0, Qt.Checked)
        self.tree.blockSignals(False)
        self._update_count()

    def _clear_sel(self):
        self.tree.blockSignals(True)
        self._checked.clear()
        for it in self._items.values():
            it.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)
        self._update_count()

    def _edit_creds(self, dev):
        if CredentialsDialog(dev, self).exec() == QDialog.Accepted:
            self._reload()

    # ============================================================
    # Worker runner
    # ============================================================
    def _run(self, devices, mode, params=None, quiet=False,
             show_progress=None):
        if not devices:
            return
        if self._worker and self._worker.isRunning():
            if not quiet:
                dlg_info(self, "عملیات در جریان است.", "صبر")
            return

        if show_progress is None:
            show_progress = not (mode == "read" and quiet)

        mode_titles = {
            "read": "در حال خواندن زمان",
            "sync_pc": "در حال هماهنگ‌سازی با رایانه",
            "manual": "در حال تنظیم زمان دستی",
            "ntp": "در حال تنظیم NTP",
            "timezone": "در حال تنظیم TimeZone",
        }
        title = mode_titles.get(mode, "در حال اعمال")

        # ★ overlay محلی
        if quiet:
            self._loading.show_loading(f"{title}...")
        else:
            self._show_progress_dialog(len(devices), title)

        self._worker = TimeWorker(devices, mode, params or {}, self)
        self._worker.finished_all.connect(
            lambda r, m: self._on_done(r, m, quiet))

        def _on_err(e):
            self._close_progress_dialog()
            self._loading.hide_loading()
            if not quiet:
                dlg_warning(self, f"خطا: {e}", "خطا")
        self._worker.error.connect(_on_err)

        self._worker.progress.connect(self._on_progress_combined)
        self._worker.start()

    def _show_progress_dialog(self, total, mode_title="در حال اعمال"):
        if self._progress_dlg is not None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(mode_title)
        dlg.setModal(False)
        dlg.setMinimumWidth(440)
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(f"QDialog {{ background:{theme.COLOR_BG_PANEL}; }}")

        v = QVBoxLayout(dlg)
        v.setContentsMargins(20, 16, 20, 14); v.setSpacing(10)

        title_lbl = QLabel(f"{mode_title}…")
        title_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_PRIMARY};font-size:12px;"
            f"font-weight:700;background:transparent;")
        v.addWidget(title_lbl)

        pb = QProgressBar()
        pb.setRange(0, total); pb.setValue(0)
        pb.setFormat(f"0 / {total}  (0%)")
        pb.setStyleSheet(f"""QProgressBar {{ background:{BG_HDR};color:white;
            border:1px solid {theme.COLOR_BORDER};border-radius:5px;
            height:24px;text-align:center;font-size:11px;font-weight:700; }}
            QProgressBar::chunk {{ background:{C_ACCENT};border-radius:4px; }}""")
        v.addWidget(pb)

        self._progress_status = QLabel("در حال شروع…")
        self._progress_status.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SECONDARY};font-size:10px;"
            f"background:transparent;")
        self._progress_status.setWordWrap(True)
        v.addWidget(self._progress_status)

        br = QHBoxLayout()
        br.addStretch(1)
        bc = QPushButton("لغو عملیات")
        bc.setFixedHeight(32)
        bc.setCursor(Qt.PointingHandCursor)
        bc.setStyleSheet(f"""
            QPushButton {{ background:{C_MAJOR};color:white;
                border:none;border-radius:5px;padding:0 18px;
                font-size:11px;font-weight:700; }}
            QPushButton:hover {{ background:#c0392b; }}
        """)
        bc.clicked.connect(self._cancel_operation)
        br.addWidget(bc)
        v.addLayout(br)

        self._progress_dlg = dlg
        self._progress_bar = pb
        dlg.show()

    def _cancel_operation(self):
        try:
            if self._worker and self._worker.isRunning():
                self._worker.cancel()
                dlg_info(self, "درخواست لغو ارسال شد. دستگاه‌های در حال پردازش "
                                "ادامه می‌یابند، بقیه لغو می‌شوند.", "لغو")
            else:
                dlg_info(self, "عملیاتی در جریان نیست.", "لغو")
        except Exception as e:
            print(f"[cancel] {e}")
        self._close_progress_dialog()
        self._loading.hide_loading()

    def _close_progress_dialog(self):
        try:
            dlg = self._progress_dlg
            if dlg is not None:
                dlg.blockSignals(True)
                dlg.accept()
                dlg.deleteLater()
        except Exception:
            pass
        finally:
            self._progress_dlg = None
            self._progress_bar = None
            self._progress_status = None

    def _on_progress_combined(self, done, total, name):
        try:
            self._loading.update_progress(done, total, name)
        except Exception:
            pass
        if self._progress_bar is not None:
            try:
                pct = int(done * 100 / max(1, total))
                self._progress_bar.setValue(done)
                self._progress_bar.setFormat(f"{done}/{total}  ({pct}%)")
                if self._progress_status is not None:
                    self._progress_status.setText(
                        f"در حال پردازش: {name}   ({done} از {total})")
            except Exception:
                pass

    def _on_done(self, results, mode, quiet):
        self._loading.hide_loading()
        self._close_progress_dialog()

        # ★ مرجع زمان
        self._ref_dt = self._fetch_reference_time()

        for r in results:
            ex = self._dev_by_uid.get(r.uid)
            if ex:
                ex.current_dt = r.current_dt
                ex.reachable = r.reachable
                ex.error = r.error
                ex.brand = r.brand
                ex.protocol = r.protocol
                ex.read_at = getattr(r, "read_at", None)

            item = self._items.get(r.uid)
            if item is None:
                continue

            item.setText(3, _proto_badge(r.protocol))
            item.setForeground(3, QBrush(QColor(_proto_color(r.protocol))))
            f = item.font(3); f.setBold(True); item.setFont(3, f)

            if r.current_dt and not r.error and self._ref_dt:
                txt, col = _drift_calc(r.current_dt, self._ref_dt)
                item.setText(4, txt)
                item.setForeground(4, QBrush(QColor(col)))
                f = item.font(4); f.setBold(True); item.setFont(4, f)
            else:
                item.setText(4, "—")

            if r.current_dt:
                item.setText(5, r.current_dt.astimezone().strftime("%H:%M:%S"))
            else:
                item.setText(5, "—")

            if r.error:
                item.setText(7, f"❌ {r.error[:35]}")
                item.setForeground(7, QBrush(QColor(C_MAJOR)))
                item.setToolTip(7, r.error)
            elif r.reachable:
                item.setText(7, "✅ آنلاین")
                item.setForeground(7, QBrush(QColor(C_SYNCED)))
                item.setToolTip(7, "")

        self._update_stats()

        if quiet or mode == "read":
            return

        title_map = {
            "sync_pc": "نتیجه هماهنگ‌سازی",
            "manual": "نتیجه زمان دستی",
            "ntp": "نتیجه NTP",
            "timezone": "نتیجه TimeZone",
        }
        dlg = ResultDialog(results, title_map.get(mode, "نتیجه"), self)
        res = dlg.exec()
        if res == 2:
            self._run(dlg.retry_devices, mode, {}, quiet=False)
        elif res == 3:
            self._reload()

    def _update_stats(self):
        synced = drifted = offline = 0
        ref = self._ref_dt or datetime.datetime.now(datetime.timezone.utc)
        for d in self.devices:
            if not d.reachable or d.current_dt is None:
                offline += 1
            else:
                drift = abs((d.current_dt - ref).total_seconds())
                if drift <= D_SYNCED:
                    synced += 1
                else:
                    drifted += 1
        self.chip_total._value.setText(str(len(self.devices)))
        self.chip_sync._value.setText(str(synced))
        self.chip_drift._value.setText(str(drifted))
        self.chip_off._value.setText(str(offline))

    def on_show(self):
        self._reload()

    def on_hide(self):
        pass