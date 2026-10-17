# -*- coding: utf-8 -*-
"""K1 VMS — Dashboard page (Phase 13: useful side panel)"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QListWidget, QListWidgetItem, QWidget
)
from PySide6.QtCore import Qt
from ui import theme
from ui.pages import BasePage
from core.i18n import t


class StatCard(QFrame):
    def __init__(self, title, value="—", parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background: {theme.COLOR_BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.COLOR_BORDER};
            }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)
        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet(
            f"color: {theme.COLOR_TEXT_SECONDARY}; "
            f"font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        v.addWidget(t_lbl)
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"color: {theme.COLOR_TEXT_PRIMARY}; font-size: 22px; font-weight: 800;"
        )
        v.addWidget(self.value_lbl)

    def set_value(self, value, color=None):
        self.value_lbl.setText(value)
        self.value_lbl.setStyleSheet(
            f"color: {color or theme.COLOR_TEXT_PRIMARY}; "
            f"font-size: 22px; font-weight: 800;"
        )


class DashboardPage(BasePage):
    PAGE_KEY = "dashboard"
    PAGE_TITLE = "Dashboard"
    PANEL_TITLE = "Overview"

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(16)

        head = QLabel(t("dash.system_overview"))
        head.setStyleSheet(
            f"color: {theme.COLOR_TEXT_PRIMARY}; "
            f"font-size: 20px; font-weight: 700;"
        )
        v.addWidget(head)

        grid = QGridLayout(); grid.setSpacing(12)
        self.card_online = StatCard(t("dash.cameras_online"), "—")
        self.card_alarms = StatCard(t("dash.active_alarms"), "0")
        self.card_record = StatCard(t("dash.recording"), "—")
        self.card_ai = StatCard(t("dash.ai_engine"), t("header.ai_disabled"))
        grid.addWidget(self.card_online, 0, 0)
        grid.addWidget(self.card_alarms, 0, 1)
        grid.addWidget(self.card_record, 0, 2)
        grid.addWidget(self.card_ai, 0, 3)
        v.addLayout(grid)

        bottom = QHBoxLayout(); bottom.setSpacing(12)

        events_card = QFrame()
        events_card.setStyleSheet(f"""
            QFrame {{
                background: {theme.COLOR_BG_CARD};
                border-radius: 8px;
                border: 1px solid {theme.COLOR_BORDER};
            }}
        """)
        ev = QVBoxLayout(events_card)
        ev.setContentsMargins(16, 12, 16, 12)
        et = QLabel(t("dash.recent_events"))
        et.setStyleSheet(
            f"color: {theme.COLOR_TEXT_SECONDARY}; "
            f"font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        ev.addWidget(et)
        empty = QLabel(t("dash.no_events"))
        empty.setStyleSheet(
            f"color: {theme.COLOR_TEXT_MUTED}; font-size: 12px;")
        ev.addWidget(empty)
        ev.addStretch(1)
        bottom.addWidget(events_card, 1)

        health_card = QFrame()
        health_card.setStyleSheet(events_card.styleSheet())
        hv = QVBoxLayout(health_card)
        hv.setContentsMargins(16, 12, 16, 12)
        ht = QLabel(t("dash.system_health"))
        ht.setStyleSheet(et.styleSheet())
        hv.addWidget(ht)
        self.health_rows = {}
        for key in ["cpu", "ram", "storage", "network"]:
            row = QHBoxLayout()
            k = QLabel(t(f"dash.{key}"))
            k.setStyleSheet(
                f"color: {theme.COLOR_TEXT_SECONDARY}; font-size: 12px;")
            k.setFixedWidth(100)
            row.addWidget(k)
            vl = QLabel("—")
            vl.setStyleSheet(
                f"color: {theme.COLOR_TEXT_PRIMARY}; "
                f"font-size: 12px; font-weight: 600;"
            )
            row.addWidget(vl, 1)
            hv.addLayout(row)
            self.health_rows[key] = vl
        bottom.addWidget(health_card, 1)
        v.addLayout(bottom)
        v.addStretch(1)

        # پنل کناری
        self._pnl_online = None
        self._pnl_rec = None
        self._pnl_offline = None
        self._pnl_alarms = None
        self._pnl_events = None

    def update_stats(self, online, total, alarms, recording, ai_status):
        self.card_online.set_value(
            f"{online} / {total}",
            theme.COLOR_STATUS_ONLINE if online else theme.COLOR_STATUS_ERROR)
        self.card_alarms.set_value(
            str(alarms),
            theme.COLOR_STATUS_ERROR if alarms else theme.COLOR_TEXT_PRIMARY)
        self.card_record.set_value(
            str(recording),
            theme.COLOR_ACCENT if recording else theme.COLOR_TEXT_PRIMARY)
        ai_map = {
            "ready": t("header.ai_ready"),
            "disabled": t("header.ai_disabled"),
            "processing": t("header.ai_processing"),
            "error": t("header.ai_error"),
        }
        self.card_ai.set_value(
            ai_map.get(ai_status, ai_status.capitalize()),
            theme.COLOR_STATUS_ONLINE if ai_status == "ready"
            else theme.COLOR_TEXT_SECONDARY)

        # ★ آپدیت پنل کناری
        try:
            if self._pnl_online is not None:
                self._pnl_online._val_lbl.setText(f"{online} / {total}")
            if self._pnl_rec is not None:
                self._pnl_rec._val_lbl.setText(str(recording))
            if self._pnl_offline is not None:
                self._pnl_offline._val_lbl.setText(str(total - online))
            if self._pnl_alarms is not None:
                self._pnl_alarms._val_lbl.setText(str(alarms))
        except Exception:
            pass

    # ============================================================
    # Side panel helpers
    # ============================================================
    def _panel_stat(self, label, value, color):
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: {theme.COLOR_BG_CARD};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
            }}
        """)
        h = QHBoxLayout(box)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(6)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 10px; font-weight: 600; background: transparent;
        """)
        h.addWidget(lbl)
        h.addStretch(1)

        val = QLabel(value)
        val.setStyleSheet(f"""
            color: {color};
            font-size: 13px; font-weight: 700; background: transparent;
        """)
        h.addWidget(val)
        box._val_lbl = val
        return box

    def _nav_to(self, key):
        try:
            w = self.window()
            if hasattr(w, "_on_page_changed"):
                w._on_page_changed(key)
        except Exception as e:
            print(f"[dash] nav error: {e}")

    def build_panel_content(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(8)

        # وضعیت زنده
        t1 = QLabel("وضعیت زنده")
        t1.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
            padding-bottom: 2px;
        """)
        v.addWidget(t1)

        self._pnl_online = self._panel_stat(
            "آنلاین", "—", theme.COLOR_STATUS_ONLINE)
        v.addWidget(self._pnl_online)

        self._pnl_rec = self._panel_stat(
            "در حال ضبط", "—", theme.COLOR_ACCENT)
        v.addWidget(self._pnl_rec)

        self._pnl_offline = self._panel_stat(
            "آفلاین", "—", theme.COLOR_STATUS_ERROR)
        v.addWidget(self._pnl_offline)

        self._pnl_alarms = self._panel_stat(
            "هشدارها", "—", theme.COLOR_STATUS_WARNING)
        v.addWidget(self._pnl_alarms)

        # رویدادها
        t2 = QLabel("رویدادهای اخیر")
        t2.setStyleSheet(t1.styleSheet())
        v.addWidget(t2)

        self._pnl_events = QListWidget()
        self._pnl_events.setStyleSheet(f"""
            QListWidget {{
                background: {theme.COLOR_BG_DARK};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 5px;
                padding: 3px;
                font-size: 10px;
            }}
            QListWidget::item {{
                padding: 5px 6px; border-radius: 3px;
            }}
            QListWidget::item:hover {{
                background: {theme.COLOR_BG_HOVER};
            }}
        """)
        self._pnl_events.addItem("—  سیستم در حال اجراست")
        v.addWidget(self._pnl_events, 1)

        # دسترسی سریع
        t3 = QLabel("دسترسی سریع")
        t3.setStyleSheet(t1.styleSheet())
        v.addWidget(t3)

        for icon, label, key in [
            ("🎬", "پخش زنده", "live"),
            ("📹", "دوربین‌ها", "cameras"),
            ("🎞", "پخش مجدد", "playback"),
            ("⚙", "تنظیمات", "settings"),
        ]:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {theme.COLOR_BG_CARD};
                    color: {theme.COLOR_TEXT_PRIMARY};
                    border: 1px solid {theme.COLOR_BORDER};
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: 600;
                    text-align: right;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background: {theme.COLOR_BG_HOVER};
                    border-color: {theme.COLOR_ACCENT};
                }}
            """)
            btn.clicked.connect(lambda _=False, k=key: self._nav_to(k))
            v.addWidget(btn)

        return w