# -*- coding: utf-8 -*-
"""K1 VMS — Settings page (Phase 14: 12 tabs + Advanced)

تغییرات Phase 14:
  - تب «تنظیمات تخصصی» اضافه شد (AdvancedSettingsTab)
  - ذخیره‌سازی خودکار مقادیر تخصصی در _on_save
  - کلید میانبر برای تب تخصصی
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSpinBox,
    QDoubleSpinBox, QCheckBox, QComboBox, QFormLayout, QProgressBar,
    QMessageBox, QListWidget, QListWidgetItem, QStackedWidget, QWidget,
    QGridLayout, QScrollArea, QSlider, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ui import theme
from ui.pages import BasePage
from ui.pages.settings_advanced_tab import AdvancedSettingsTab
from core.i18n import t, get_language
from core.storage_manager import StorageManager
from core import settings_manager
import config


# ============================================================
# QSS helpers
# ============================================================
def _spin_qss():
    return f"""
        QSpinBox, QDoubleSpinBox {{
            background: #0d1014;
            color: #ecf0f1;
            border: 1px solid #2c333c;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
            font-weight: 700;
            min-height: 22px;
            min-width: 120px;
            selection-background-color: {theme.COLOR_ACCENT};
            selection-color: white;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {theme.COLOR_ACCENT};
            background: #1a1f26;
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            background: #2c333c;
            width: 20px;
            border: none;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {theme.COLOR_ACCENT};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid #ecf0f1;
            width: 0; height: 0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #ecf0f1;
            width: 0; height: 0;
        }}
    """


def _checkbox_qss():
    return f"""
        QCheckBox {{
            color: {theme.COLOR_TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 600;
            spacing: 10px;
            padding: 4px;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 20px; height: 20px;
            border: 2px solid #6b7280;
            border-radius: 5px;
            background: #0d1014;
        }}
        QCheckBox::indicator:hover {{
            border-color: {theme.COLOR_ACCENT};
        }}
        QCheckBox::indicator:checked {{
            background: {theme.COLOR_ACCENT};
            border-color: {theme.COLOR_ACCENT};
        }}
    """


def _combo_qss():
    return f"""
        QComboBox {{
            background: #0d1014;
            color: #ecf0f1;
            border: 1px solid #2c333c;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
            font-weight: 600;
            min-height: 22px;
            min-width: 120px;
        }}
        QComboBox:focus {{
            border: 1px solid {theme.COLOR_ACCENT};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background: {theme.COLOR_BG_CARD};
            color: {theme.COLOR_TEXT_PRIMARY};
            border: 1px solid #2c333c;
            selection-background-color: {theme.COLOR_ACCENT};
            outline: none;
            padding: 4px;
        }}
    """


def _line_qss():
    return f"""
        QLineEdit {{
            background: #0d1014;
            color: #ecf0f1;
            border: 1px solid #2c333c;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            min-height: 20px;
        }}
        QLineEdit:focus {{
            border: 1px solid {theme.COLOR_ACCENT};
        }}
    """


def _label_qss(primary=True, size=12):
    color = (theme.COLOR_TEXT_PRIMARY if primary
             else theme.COLOR_TEXT_SECONDARY)
    weight = "600" if primary else "500"
    return (f"color: {color}; font-size: {size}px; "
            f"font-weight: {weight}; background: transparent;")


def _slider_qss():
    return f"""
        QSlider::groove:horizontal {{
            height: 6px; background: #2c333c; border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: {theme.COLOR_ACCENT}; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: white; width: 14px; height: 14px;
            margin: -5px 0; border-radius: 7px;
        }}
    """


# ============================================================
# Reusable widgets
# ============================================================
class SettingsCard(QFrame):
    def __init__(self, title="", subtitle="", icon="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            SettingsCard {{
                background: {theme.COLOR_BG_CARD};
                border: 1px solid #2c333c;
                border-radius: 10px;
            }}
        """)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 16, 20, 18)
        self._lay.setSpacing(10)

        if title:
            head = QHBoxLayout()
            head.setSpacing(8)
            if icon:
                ic = QLabel(icon)
                ic.setStyleSheet("font-size: 16px; background: transparent;")
                head.addWidget(ic)
            tlbl = QLabel(title)
            tlbl.setStyleSheet(f"""
                color: {theme.COLOR_TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 700;
                background: transparent;
            """)
            head.addWidget(tlbl)
            head.addStretch(1)
            self._lay.addLayout(head)
            if subtitle:
                slbl = QLabel(subtitle)
                slbl.setWordWrap(True)
                slbl.setStyleSheet(f"""
                    color: {theme.COLOR_TEXT_SECONDARY};
                    font-size: 11px;
                    background: transparent;
                """)
                self._lay.addWidget(slbl)

    def body(self):
        return self._lay


class ScrollPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: transparent;
                width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #3a4550; min-height: 30px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a5560;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
        """)

        inner = QWidget()
        self.content_layout = QVBoxLayout(inner)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(16)

        scroll.setWidget(inner)
        outer.addWidget(scroll)


# ============================================================
# Settings Page
# ============================================================
class SettingsPage(BasePage):
    PAGE_KEY = "settings"
    PAGE_TITLE = "Settings"
    PANEL_TITLE = "تنظیمات"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sm = StorageManager.instance()
        self._loading = False

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_stats)

        self._build()
        self._load_all()

        QTimer.singleShot(200, self._refresh_stats)
        self._refresh_timer.start(10000)

    # ============================================================
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = self._make_sidebar()
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {theme.COLOR_BG_APP};")

        self.stack.addWidget(self._page_recording())
        self.stack.addWidget(self._page_storage())
        self.stack.addWidget(self._page_folders())
        self.stack.addWidget(self._page_live())
        self.stack.addWidget(self._page_appearance())
        self.stack.addWidget(self._page_startup())
        self.stack.addWidget(self._page_alarms())
        self.stack.addWidget(self._page_notify())
        self.stack.addWidget(self._page_security())
        self.stack.addWidget(self._page_ai())

        # ★ Phase 14 — تب تخصصی
        self.advanced_tab = AdvancedSettingsTab()
        self.stack.addWidget(self.advanced_tab)

        self.stack.addWidget(self._page_about())

        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    # ============================================================
    def _make_header(self):
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {theme.COLOR_BG_HEADER};
                border-bottom: 1px solid {theme.COLOR_BORDER};
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 8, 20, 8)
        h.setSpacing(10)

        icon = QLabel("⚙")
        icon.setStyleSheet("font-size: 22px; background: transparent;")
        h.addWidget(icon)

        title = QLabel(t("set.title"))
        title.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 800;
            background: transparent;
        """)
        h.addWidget(title)
        h.addStretch(1)

        self.save_btn = QPushButton("💾  " + t("common.save"))
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(34)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {theme.COLOR_ACCENT_HOVER};
            }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        h.addWidget(self.save_btn)

        self.reload_btn = QPushButton("🔄  " + t("common.refresh"))
        self.reload_btn.setCursor(Qt.PointingHandCursor)
        self.reload_btn.setFixedHeight(34)
        self.reload_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme.COLOR_BG_HOVER};
            }}
        """)
        self.reload_btn.clicked.connect(self._load_all)
        h.addWidget(self.reload_btn)

        return bar

    # ============================================================
    def _make_sidebar(self):
        side = QListWidget()
        side.setFixedWidth(220)
        side.setStyleSheet(f"""
            QListWidget {{
                background: {theme.COLOR_BG_PANEL};
                border: none;
                border-right: 1px solid #2c333c;
                padding: 12px 10px;
                outline: none;
            }}
            QListWidget::item {{
                color: {theme.COLOR_TEXT_SECONDARY};
                padding: 10px 16px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 2px;
            }}
            QListWidget::item:hover {{
                background: #232932;
                color: {theme.COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background: {theme.COLOR_ACCENT};
                color: white;
            }}
        """)

        items = [
            ("🎬", t("set.tab.recording")),
            ("💾", t("set.tab.storage")),
            ("📁", t("set.tab.folders")),
            ("📺", t("set.tab.live")),
            ("🎨", t("set.tab.appearance")),
            ("🚀", t("set.tab.startup")),
            ("🔔", t("set.tab.alarms")),
            ("📢", t("set.tab.notify")),
            ("🔒", t("set.tab.security")),
            ("🤖", t("set.ai.title")),
            ("⚡", t("set.tab.advanced")),   # ★ Phase 14
            ("ℹ",  t("set.tab.about")),
        ]
        for icon, label in items:
            side.addItem(QListWidgetItem(f"  {icon}   {label}"))
        return side

    # ============================================================
    # Helpers
    # ============================================================
    def _lbl(self, text, primary=True, size=13):
        l = QLabel(text)
        l.setStyleSheet(_label_qss(primary, size))
        return l

    def _hint(self, text):
        l = QLabel(text)
        l.setWordWrap(True)
        l.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 11px;
            background: {theme.COLOR_BG_DARK};
            padding: 10px 12px;
            border-radius: 6px;
            border-left: 3px solid {theme.COLOR_ACCENT};
        """)
        return l

    def _stat_box(self, label):
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: {theme.COLOR_BG_DARK};
                border: 1px solid #232932;
                border-radius: 8px;
            }}
        """)
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 10px; font-weight: 600; background: transparent;
        """)
        v.addWidget(lbl)
        val = QLabel("—")
        val.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_PRIMARY};
            font-size: 14px; font-weight: 700; background: transparent;
        """)
        v.addWidget(val)
        box._value = val
        return box

    def _form(self):
        f = QFormLayout()
        f.setSpacing(12)
        f.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        f.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        return f

    # ============================================================
    # Page 1: Recording
    # ============================================================
    def _page_recording(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.record.title"), t("set.record.hint"), "🎬")
        b = c1.body()

        self.rec_enabled_chk = QCheckBox(t("set.record.enabled"))
        self.rec_enabled_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.rec_enabled_chk)

        form = self._form()
        self.rec_segment_spin = QSpinBox()
        self.rec_segment_spin.setRange(1, 30)
        self.rec_segment_spin.setValue(5)
        self.rec_segment_spin.setSuffix("  دقیقه")
        self.rec_segment_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.record.segment")), self.rec_segment_spin)

        self.rec_format_combo = QComboBox()
        self.rec_format_combo.addItem("MPEG-TS  (.ts)", ".ts")
        self.rec_format_combo.addItem("MP4  (.mp4)", ".mp4")
        self.rec_format_combo.setStyleSheet(_combo_qss())
        form.addRow(self._lbl(t("set.record.format")), self.rec_format_combo)
        b.addLayout(form)
        b.addWidget(self._hint(t("set.record.segment_hint")))
        lay.addWidget(c1)

        # Motion
        c2 = SettingsCard(t("set.record.motion_title"),
                          t("set.record.motion_hint"), "⚠")
        b2 = c2.body()

        self.motion_enabled_chk = QCheckBox(t("set.record.motion_enabled"))
        self.motion_enabled_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.motion_enabled_chk)

        self.motion_after_chk = QCheckBox(t("set.record.motion_after"))
        self.motion_after_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.motion_after_chk)

        form2 = self._form()
        self.pre_buffer_spin = QSpinBox()
        self.pre_buffer_spin.setRange(0, 60)
        self.pre_buffer_spin.setValue(5)
        self.pre_buffer_spin.setSuffix("  ثانیه")
        self.pre_buffer_spin.setStyleSheet(_spin_qss())
        form2.addRow(self._lbl(t("set.record.pre_buffer")), self.pre_buffer_spin)

        self.post_buffer_spin = QSpinBox()
        self.post_buffer_spin.setRange(0, 60)
        self.post_buffer_spin.setValue(5)
        self.post_buffer_spin.setSuffix("  ثانیه")
        self.post_buffer_spin.setStyleSheet(_spin_qss())
        form2.addRow(self._lbl(t("set.record.post_buffer")), self.post_buffer_spin)

        self.sensitivity_spin = QSpinBox()
        self.sensitivity_spin.setRange(1, 400)
        self.sensitivity_spin.setValue(100)
        self.sensitivity_spin.setStyleSheet(_spin_qss())
        form2.addRow(self._lbl(t("set.record.sensitivity")), self.sensitivity_spin)

        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(20, 200000)
        self.min_area_spin.setValue(400)
        self.min_area_spin.setStyleSheet(_spin_qss())
        form2.addRow(self._lbl(t("set.record.min_area")), self.min_area_spin)
        b2.addLayout(form2)
        lay.addWidget(c2)

        # Health
        c3 = SettingsCard(t("set.record.health_title"),
                          t("set.record.health_hint"), "🩺")
        b3 = c3.body()

        self.corrupted_chk = QCheckBox(t("set.record.corrupted_cleanup"))
        self.corrupted_chk.setStyleSheet(_checkbox_qss())
        b3.addWidget(self.corrupted_chk)

        form3 = self._form()
        self.disk_policy_combo = QComboBox()
        self.disk_policy_combo.addItem(t("set.record.disk_policy.delete"),
                                       "delete_oldest")
        self.disk_policy_combo.addItem(t("set.record.disk_policy.stop"),
                                       "stop")
        self.disk_policy_combo.addItem(t("set.record.disk_policy.rotate"),
                                       "rotate")
        self.disk_policy_combo.setStyleSheet(_combo_qss())
        form3.addRow(self._lbl(t("set.record.disk_policy")),
                     self.disk_policy_combo)
        b3.addLayout(form3)
        lay.addWidget(c3)

        lay.addStretch(1)
        return page

    # ============================================================
    # Page 2: Storage
    # ============================================================
    def _page_storage(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.storage.title"), t("set.storage.hint"), "💾")
        b = c1.body()

        self.disk_bar = QProgressBar()
        self.disk_bar.setRange(0, 100)
        self.disk_bar.setValue(0)
        self.disk_bar.setTextVisible(True)
        self.disk_bar.setFixedHeight(28)
        b.addWidget(self.disk_bar)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.stat_disk_used = self._stat_box(t("set.storage.disk_used"))
        self.stat_record_size = self._stat_box(t("set.storage.rec_size"))
        self.stat_file_count = self._stat_box(t("set.storage.file_count"))
        self.stat_oldest = self._stat_box(t("set.storage.oldest"))
        self.stat_newest = self._stat_box(t("set.storage.newest"))
        grid.addWidget(self.stat_disk_used, 0, 0)
        grid.addWidget(self.stat_record_size, 0, 1)
        grid.addWidget(self.stat_file_count, 0, 2)
        grid.addWidget(self.stat_oldest, 1, 0)
        grid.addWidget(self.stat_newest, 1, 1)
        b.addLayout(grid)
        lay.addWidget(c1)

        # Policy
        c2 = SettingsCard(t("set.storage.policy_title"),
                          t("set.storage.policy_hint"), "🕐")
        b2 = c2.body()

        self.auto_cleanup_chk = QCheckBox(t("set.storage.auto_cleanup"))
        self.auto_cleanup_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.auto_cleanup_chk)

        form = self._form()

        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 3650)
        self.retention_spin.setValue(7)
        self.retention_spin.setStyleSheet(_spin_qss())
        w = QWidget()
        wl = QHBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(6)
        wl.addWidget(self.retention_spin)
        wl.addWidget(self._lbl(t("set.storage.days"), False, 12))
        wl.addStretch(1)
        form.addRow(self._lbl(t("set.storage.keep_days")), w)

        self.quota_percent_spin = QSpinBox()
        self.quota_percent_spin.setRange(0, 100)
        self.quota_percent_spin.setValue(0)
        self.quota_percent_spin.setSuffix("  %")
        self.quota_percent_spin.setStyleSheet(_spin_qss())
        w2 = QWidget()
        wl2 = QHBoxLayout(w2); wl2.setContentsMargins(0,0,0,0); wl2.setSpacing(6)
        wl2.addWidget(self.quota_percent_spin)
        wl2.addWidget(self._lbl(t("set.storage.of_disk"), False, 12))
        wl2.addStretch(1)
        form.addRow(self._lbl(t("set.storage.max_percent")), w2)

        self.quota_gb_spin = QDoubleSpinBox()
        self.quota_gb_spin.setRange(0, 1000000)
        self.quota_gb_spin.setValue(0)
        self.quota_gb_spin.setDecimals(1)
        self.quota_gb_spin.setSingleStep(50)
        self.quota_gb_spin.setSuffix("  GB")
        self.quota_gb_spin.setSpecialValueText(t("set.storage.unlimited"))
        self.quota_gb_spin.setStyleSheet(_spin_qss())
        w3 = QWidget()
        wl3 = QHBoxLayout(w3); wl3.setContentsMargins(0,0,0,0); wl3.setSpacing(6)
        wl3.addWidget(self.quota_gb_spin)
        wl3.addWidget(self._lbl(t("set.storage.gb_or_unlimited"), False, 11))
        wl3.addStretch(1)
        form.addRow(self._lbl(t("set.storage.max_gb")), w3)

        self.cleanup_interval_spin = QSpinBox()
        self.cleanup_interval_spin.setRange(1, 168)
        self.cleanup_interval_spin.setValue(6)
        self.cleanup_interval_spin.setStyleSheet(_spin_qss())
        w4 = QWidget()
        wl4 = QHBoxLayout(w4); wl4.setContentsMargins(0,0,0,0); wl4.setSpacing(6)
        wl4.addWidget(self.cleanup_interval_spin)
        wl4.addWidget(self._lbl(t("set.storage.hours"), False, 12))
        wl4.addStretch(1)
        form.addRow(self._lbl(t("set.storage.cleanup_interval")), w4)

        self.cleanup_hour_spin = QSpinBox()
        self.cleanup_hour_spin.setRange(0, 23)
        self.cleanup_hour_spin.setValue(3)
        self.cleanup_hour_spin.setSuffix(":00")
        self.cleanup_hour_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.storage.cleanup_hour")),
                    self.cleanup_hour_spin)

        self.snapshot_ret_spin = QSpinBox()
        self.snapshot_ret_spin.setRange(1, 3650)
        self.snapshot_ret_spin.setValue(30)
        self.snapshot_ret_spin.setStyleSheet(_spin_qss())
        w5 = QWidget()
        wl5 = QHBoxLayout(w5); wl5.setContentsMargins(0,0,0,0); wl5.setSpacing(6)
        wl5.addWidget(self.snapshot_ret_spin)
        wl5.addWidget(self._lbl(t("set.storage.days"), False, 12))
        wl5.addStretch(1)
        form.addRow(self._lbl(t("set.storage.snapshots_days")), w5)

        self.export_ret_spin = QSpinBox()
        self.export_ret_spin.setRange(1, 3650)
        self.export_ret_spin.setValue(90)
        self.export_ret_spin.setStyleSheet(_spin_qss())
        w6 = QWidget()
        wl6 = QHBoxLayout(w6); wl6.setContentsMargins(0,0,0,0); wl6.setSpacing(6)
        wl6.addWidget(self.export_ret_spin)
        wl6.addWidget(self._lbl(t("set.storage.days"), False, 12))
        wl6.addStretch(1)
        form.addRow(self._lbl(t("set.storage.exports_days")), w6)

        b2.addLayout(form)
        b2.addWidget(self._hint(t("set.storage.quota_hint")))
        lay.addWidget(c2)

        # Backup
        c3 = SettingsCard(t("set.backup.title"), t("set.backup.hint"), "📦")
        b3 = c3.body()

        self.backup_chk = QCheckBox(t("set.backup.enabled"))
        self.backup_chk.setStyleSheet(_checkbox_qss())
        b3.addWidget(self.backup_chk)

        form3 = self._form()

        path_row = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setStyleSheet(_line_qss())
        self.backup_path_edit.setPlaceholderText("/path/to/backup")
        path_row.addWidget(self.backup_path_edit, 1)
        browse_btn = QPushButton("📁  " + t("set.backup.browse"))
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid #2c333c;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #2c333c; }}
        """)
        browse_btn.clicked.connect(self._on_browse_backup)
        path_row.addWidget(browse_btn)
        pw = QWidget()
        pw.setLayout(path_row)
        form3.addRow(self._lbl(t("set.backup.path")), pw)

        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 168)
        self.backup_interval_spin.setValue(24)
        self.backup_interval_spin.setStyleSheet(_spin_qss())
        w7 = QWidget()
        wl7 = QHBoxLayout(w7); wl7.setContentsMargins(0,0,0,0); wl7.setSpacing(6)
        wl7.addWidget(self.backup_interval_spin)
        wl7.addWidget(self._lbl(t("set.storage.hours"), False, 12))
        wl7.addStretch(1)
        form3.addRow(self._lbl(t("set.backup.interval")), w7)

        self.backup_keep_spin = QSpinBox()
        self.backup_keep_spin.setRange(1, 90)
        self.backup_keep_spin.setValue(3)
        self.backup_keep_spin.setStyleSheet(_spin_qss())
        w8 = QWidget()
        wl8 = QHBoxLayout(w8); wl8.setContentsMargins(0,0,0,0); wl8.setSpacing(6)
        wl8.addWidget(self.backup_keep_spin)
        wl8.addWidget(self._lbl(t("set.storage.days"), False, 12))
        wl8.addStretch(1)
        form3.addRow(self._lbl(t("set.backup.keep_days")), w8)

        b3.addLayout(form3)
        lay.addWidget(c3)

        # Cleanup now
        c4 = SettingsCard(icon="🧹")
        b4 = c4.body()
        clean_btn = QPushButton("🧹  " + t("set.storage.cleanup_now"))
        clean_btn.setCursor(Qt.PointingHandCursor)
        clean_btn.setFixedHeight(40)
        clean_btn.setStyleSheet(f"""
            QPushButton {{
                background: #e67e22;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #f39c12; }}
        """)
        clean_btn.clicked.connect(self._on_cleanup_now)
        b4.addWidget(clean_btn)
        lay.addWidget(c4)

        lay.addStretch(1)
        return page

    # ============================================================
    # Page 3: Folders
    # ============================================================
    def _page_folders(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.folders.title"),
                          t("set.folders.hint"), "📁")
        b = c1.body()

        self.folder_by_camera_chk = QCheckBox(t("set.folders.by_camera"))
        self.folder_by_camera_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.folder_by_camera_chk)

        self.folder_by_day_chk = QCheckBox(t("set.folders.by_day"))
        self.folder_by_day_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.folder_by_day_chk)

        self.folder_by_hour_chk = QCheckBox(t("set.folders.by_hour"))
        self.folder_by_hour_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.folder_by_hour_chk)

        self.use_nvr_name_chk = QCheckBox(t("set.folders.use_nvr_name"))
        self.use_nvr_name_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.use_nvr_name_chk)

        self.incident_lock_chk = QCheckBox(t("set.folders.incident_lock"))
        self.incident_lock_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.incident_lock_chk)

        form = self._form()
        self.folder_pattern_edit = QLineEdit()
        self.folder_pattern_edit.setStyleSheet(_line_qss())
        self.folder_pattern_edit.setPlaceholderText(
            t("set.folders.pattern_ph"))
        self.folder_pattern_edit.textChanged.connect(self._update_path_preview)
        form.addRow(self._lbl(t("set.folders.pattern")),
                    self.folder_pattern_edit)
        b.addLayout(form)

        self.path_preview_lbl = QLabel("")
        self.path_preview_lbl.setWordWrap(True)
        self.path_preview_lbl.setStyleSheet(f"""
            color: {theme.COLOR_ACCENT};
            font-size: 11px;
            font-family: Consolas, monospace;
            background: {theme.COLOR_BG_DARK};
            padding: 8px 12px;
            border-radius: 6px;
        """)
        b.addWidget(self._lbl(t("set.folders.preview")))
        b.addWidget(self.path_preview_lbl)

        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 4: Live
    # ============================================================
    def _page_live(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.live.title"), t("set.live.hint"), "📺")
        b = c1.body()

        form = self._form()

        self.layout_combo = QComboBox()
        for k in ["1x1", "2x2", "3x3", "4x4", "1+4", "1+5", "1+9"]:
            self.layout_combo.addItem(k, k)
        self.layout_combo.setStyleSheet(_combo_qss())
        form.addRow(self._lbl(t("set.live.default_layout")),
                    self.layout_combo)

        self.grid_fps_spin = QSpinBox()
        self.grid_fps_spin.setRange(1, 30)
        self.grid_fps_spin.setValue(5)
        self.grid_fps_spin.setSuffix("  FPS")
        self.grid_fps_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.live.grid_fps")), self.grid_fps_spin)

        self.single_fps_spin = QSpinBox()
        self.single_fps_spin.setRange(1, 60)
        self.single_fps_spin.setValue(15)
        self.single_fps_spin.setSuffix("  FPS")
        self.single_fps_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.live.single_fps")), self.single_fps_spin)

        self.max_readers_spin = QSpinBox()
        self.max_readers_spin.setRange(1, 64)
        self.max_readers_spin.setValue(16)
        self.max_readers_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.live.max_readers")), self.max_readers_spin)

        self.reconnect_delay_spin = QSpinBox()
        self.reconnect_delay_spin.setRange(1, 60)
        self.reconnect_delay_spin.setValue(5)
        self.reconnect_delay_spin.setSuffix("  ثانیه")
        self.reconnect_delay_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.live.reconnect_delay")),
                    self.reconnect_delay_spin)

        self.transport_combo = QComboBox()
        self.transport_combo.addItem(t("set.live.transport.auto"), "auto")
        self.transport_combo.addItem(t("set.live.transport.tcp"), "tcp")
        self.transport_combo.addItem(t("set.live.transport.udp"), "udp")
        self.transport_combo.setStyleSheet(_combo_qss())
        form.addRow(self._lbl(t("set.live.transport")), self.transport_combo)

        b.addLayout(form)

        self.auto_reconnect_chk = QCheckBox(t("set.live.auto_reconnect"))
        self.auto_reconnect_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.auto_reconnect_chk)

        self.focus_mode_chk = QCheckBox(t("set.live.focus_mode"))
        self.focus_mode_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.focus_mode_chk)

        lay.addWidget(c1)

        c2 = SettingsCard(t("set.live.overlay_title"), icon="🎯")
        b2 = c2.body()

        self.show_timestamp_chk = QCheckBox(t("set.live.show_timestamp"))
        self.show_timestamp_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.show_timestamp_chk)

        self.show_cam_name_chk = QCheckBox(t("set.live.show_camera_name"))
        self.show_cam_name_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.show_cam_name_chk)

        self.show_rec_ind_chk = QCheckBox(t("set.live.show_rec_indicator"))
        self.show_rec_ind_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.show_rec_ind_chk)

        self.show_motion_ind_chk = QCheckBox(t("set.live.show_motion_indicator"))
        self.show_motion_ind_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.show_motion_ind_chk)

        lay.addWidget(c2)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 5: Appearance
    # ============================================================
    def _page_appearance(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.appear.title"),
                          t("set.appear.hint"), "🎨")
        b = c1.body()

        form = self._form()

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("🌙  " + t("set.appear.dark"), "dark")
        self.theme_combo.addItem("☀  " + t("set.appear.light"), "light")
        self.theme_combo.setStyleSheet(_combo_qss())
        form.addRow(self._lbl(t("set.appear.theme")), self.theme_combo)

        self.font_combo = QComboBox()
        self.font_combo.addItem(t("set.appear.font.small"), "small")
        self.font_combo.addItem(t("set.appear.font.medium"), "medium")
        self.font_combo.addItem(t("set.appear.font.large"), "large")
        self.font_combo.setStyleSheet(_combo_qss())
        form.addRow(self._lbl(t("set.appear.font_size")), self.font_combo)

        self.sidebar_width_spin = QSpinBox()
        self.sidebar_width_spin.setRange(180, 500)
        self.sidebar_width_spin.setValue(260)
        self.sidebar_width_spin.setSuffix("  px")
        self.sidebar_width_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.appear.sidebar_width")),
                    self.sidebar_width_spin)

        b.addLayout(form)

        self.compact_chk = QCheckBox(t("set.appear.compact"))
        self.compact_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.compact_chk)

        self.always_on_top_chk = QCheckBox(t("set.appear.always_on_top"))
        self.always_on_top_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.always_on_top_chk)

        self.start_min_chk = QCheckBox(t("set.appear.start_minimized"))
        self.start_min_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.start_min_chk)

        self.remember_geom_chk = QCheckBox(t("set.appear.remember_geometry"))
        self.remember_geom_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.remember_geom_chk)

        lay.addWidget(c1)

        c2 = SettingsCard(t("set.lang.title"), t("set.lang.hint"), "🌐")
        b2 = c2.body()

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("🇮🇷  فارسی", "fa")
        self.lang_combo.addItem("🌍  English", "en")
        self.lang_combo.setStyleSheet(_combo_qss())
        b2.addWidget(self.lang_combo)
        b2.addWidget(self._hint(t("set.lang.note")))

        lay.addWidget(c2)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 6: Startup
    # ============================================================
    def _page_startup(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.startup.title"),
                          t("set.startup.hint"), "🚀")
        b = c1.body()

        self.startup_autostart_chk = QCheckBox(t("set.startup.autostart"))
        self.startup_autostart_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.startup_autostart_chk)

        self.startup_mediamtx_chk = QCheckBox(t("set.startup.mediamtx"))
        self.startup_mediamtx_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.startup_mediamtx_chk)

        self.startup_record_chk = QCheckBox(t("set.startup.record"))
        self.startup_record_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.startup_record_chk)

        self.restore_tab_chk = QCheckBox(t("set.startup.restore_tab"))
        self.restore_tab_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.restore_tab_chk)

        self.restore_layout_chk = QCheckBox(t("set.startup.restore_layout"))
        self.restore_layout_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.restore_layout_chk)

        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 7: Alarms
    # ============================================================
    def _page_alarms(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.alarm.title"), t("set.alarm.hint"), "🔔")
        b = c1.body()

        self.sound_chk = QCheckBox(t("set.alarm.sound"))
        self.sound_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.sound_chk)

        self.desktop_notify_chk = QCheckBox(t("set.alarm.desktop"))
        self.desktop_notify_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.desktop_notify_chk)

        form = self._form()

        vol_wrap = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setStyleSheet(_slider_qss())
        vol_wrap.addWidget(self.volume_slider, 1)
        self.volume_lbl = QLabel("80%")
        self.volume_lbl.setStyleSheet(_label_qss(True, 12))
        self.volume_lbl.setFixedWidth(50)
        vol_wrap.addWidget(self.volume_lbl)
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_lbl.setText(f"{v}%"))
        vw = QWidget(); vw.setLayout(vol_wrap)
        form.addRow(self._lbl(t("set.alarm.volume")), vw)

        self.alarm_dur_spin = QSpinBox()
        self.alarm_dur_spin.setRange(1, 60)
        self.alarm_dur_spin.setValue(8)
        self.alarm_dur_spin.setSuffix("  ثانیه")
        self.alarm_dur_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.alarm.duration")), self.alarm_dur_spin)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 300)
        self.cooldown_spin.setValue(5)
        self.cooldown_spin.setSuffix("  ثانیه")
        self.cooldown_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.alarm.cooldown")), self.cooldown_spin)

        b.addLayout(form)
        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 8: Notifications
    # ============================================================
    def _page_notify(self):
        page = ScrollPage()
        lay = page.content_layout

        # Events
        c0 = SettingsCard(t("set.notify.events_title"),
                          t("set.notify.events.hint"), "🎯")
        b0 = c0.body()

        self.event_chks = {}
        events = [
            ("motion", t("set.notify.event.motion")),
            ("camera_offline", t("set.notify.event.camera_offline")),
            ("camera_online", t("set.notify.event.camera_online")),
            ("recording_start", t("set.notify.event.recording_start")),
            ("recording_stop", t("set.notify.event.recording_stop")),
            ("storage_low", t("set.notify.event.storage_low")),
            ("login_failed", t("set.notify.event.login_failed")),
            ("system_start", t("set.notify.event.system_start")),
            ("system_stop", t("set.notify.event.system_stop")),
        ]
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (key, label) in enumerate(events):
            chk = QCheckBox(label)
            chk.setStyleSheet(_checkbox_qss())
            grid.addWidget(chk, i // 2, i % 2)
            self.event_chks[key] = chk
        b0.addLayout(grid)
        lay.addWidget(c0)

        # Email
        c1 = SettingsCard(t("set.notify.email.title"),
                          t("set.notify.email.hint"), "📧")
        b1 = c1.body()

        self.email_enabled_chk = QCheckBox(t("set.notify.email.enabled"))
        self.email_enabled_chk.setStyleSheet(_checkbox_qss())
        b1.addWidget(self.email_enabled_chk)

        form1 = self._form()
        self.email_smtp_edit = QLineEdit()
        self.email_smtp_edit.setStyleSheet(_line_qss())
        self.email_smtp_edit.setPlaceholderText("smtp.gmail.com")
        form1.addRow(self._lbl(t("set.notify.email.smtp")),
                     self.email_smtp_edit)

        self.email_port_spin = QSpinBox()
        self.email_port_spin.setRange(1, 65535)
        self.email_port_spin.setValue(587)
        self.email_port_spin.setStyleSheet(_spin_qss())
        form1.addRow(self._lbl(t("set.notify.email.port")),
                     self.email_port_spin)

        self.email_user_edit = QLineEdit()
        self.email_user_edit.setStyleSheet(_line_qss())
        form1.addRow(self._lbl(t("set.notify.email.user")),
                     self.email_user_edit)

        self.email_pass_edit = QLineEdit()
        self.email_pass_edit.setEchoMode(QLineEdit.Password)
        self.email_pass_edit.setStyleSheet(_line_qss())
        form1.addRow(self._lbl(t("set.notify.email.pass")),
                     self.email_pass_edit)

        self.email_to_edit = QLineEdit()
        self.email_to_edit.setStyleSheet(_line_qss())
        form1.addRow(self._lbl(t("set.notify.email.to")),
                     self.email_to_edit)

        b1.addLayout(form1)

        self.email_tls_chk = QCheckBox(t("set.notify.email.tls"))
        self.email_tls_chk.setStyleSheet(_checkbox_qss())
        b1.addWidget(self.email_tls_chk)

        lay.addWidget(c1)

        # Telegram
        c2 = SettingsCard(t("set.notify.telegram.title"),
                          t("set.notify.telegram.hint"), "✈")
        b2 = c2.body()
        self.tg_enabled_chk = QCheckBox(t("set.notify.telegram.enabled"))
        self.tg_enabled_chk.setStyleSheet(_checkbox_qss())
        b2.addWidget(self.tg_enabled_chk)
        form2 = self._form()
        self.tg_token_edit = QLineEdit()
        self.tg_token_edit.setStyleSheet(_line_qss())
        form2.addRow(self._lbl(t("set.notify.telegram.token")),
                     self.tg_token_edit)
        self.tg_chat_edit = QLineEdit()
        self.tg_chat_edit.setStyleSheet(_line_qss())
        form2.addRow(self._lbl(t("set.notify.telegram.chat")),
                     self.tg_chat_edit)
        b2.addLayout(form2)
        lay.addWidget(c2)

        # Bale
        c3 = SettingsCard(t("set.notify.bale.title"),
                          t("set.notify.bale.hint"), "💬")
        b3 = c3.body()
        self.bale_enabled_chk = QCheckBox(t("set.notify.bale.enabled"))
        self.bale_enabled_chk.setStyleSheet(_checkbox_qss())
        b3.addWidget(self.bale_enabled_chk)
        form3 = self._form()
        self.bale_token_edit = QLineEdit()
        self.bale_token_edit.setStyleSheet(_line_qss())
        form3.addRow(self._lbl(t("set.notify.bale.token")),
                     self.bale_token_edit)
        self.bale_chat_edit = QLineEdit()
        self.bale_chat_edit.setStyleSheet(_line_qss())
        form3.addRow(self._lbl(t("set.notify.bale.chat")),
                     self.bale_chat_edit)
        b3.addLayout(form3)
        lay.addWidget(c3)

        # Eitaa
        c4 = SettingsCard(t("set.notify.eitaa.title"),
                          t("set.notify.eitaa.hint"), "📨")
        b4 = c4.body()
        self.eitaa_enabled_chk = QCheckBox(t("set.notify.eitaa.enabled"))
        self.eitaa_enabled_chk.setStyleSheet(_checkbox_qss())
        b4.addWidget(self.eitaa_enabled_chk)
        form4 = self._form()
        self.eitaa_token_edit = QLineEdit()
        self.eitaa_token_edit.setStyleSheet(_line_qss())
        form4.addRow(self._lbl(t("set.notify.eitaa.token")),
                     self.eitaa_token_edit)
        self.eitaa_chat_edit = QLineEdit()
        self.eitaa_chat_edit.setStyleSheet(_line_qss())
        form4.addRow(self._lbl(t("set.notify.eitaa.chat")),
                     self.eitaa_chat_edit)
        b4.addLayout(form4)
        lay.addWidget(c4)

        # Rubika
        c5 = SettingsCard(t("set.notify.rubika.title"),
                          t("set.notify.rubika.hint"), "📱")
        b5 = c5.body()
        self.rubika_enabled_chk = QCheckBox(t("set.notify.rubika.enabled"))
        self.rubika_enabled_chk.setStyleSheet(_checkbox_qss())
        b5.addWidget(self.rubika_enabled_chk)
        form5 = self._form()
        self.rubika_token_edit = QLineEdit()
        self.rubika_token_edit.setStyleSheet(_line_qss())
        form5.addRow(self._lbl(t("set.notify.rubika.token")),
                     self.rubika_token_edit)
        self.rubika_chat_edit = QLineEdit()
        self.rubika_chat_edit.setStyleSheet(_line_qss())
        form5.addRow(self._lbl(t("set.notify.rubika.chat")),
                     self.rubika_chat_edit)
        b5.addLayout(form5)
        lay.addWidget(c5)

        # Test
        c6 = SettingsCard(icon="🧪")
        b6 = c6.body()
        test_btn = QPushButton("🧪  " + t("set.notify.test_all"))
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.setFixedHeight(40)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #a66bbe; }}
        """)
        test_btn.clicked.connect(self._on_test_notifications)
        b6.addWidget(test_btn)
        lay.addWidget(c6)

        lay.addStretch(1)
        return page

    # ============================================================
    # Page 9: Security
    # ============================================================
    def _page_security(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.sec.title"), t("set.sec.hint"), "🔒")
        b = c1.body()

        form = self._form()

        self.max_attempts_spin = QSpinBox()
        self.max_attempts_spin.setRange(1, 20)
        self.max_attempts_spin.setValue(5)
        self.max_attempts_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.sec.max_attempts")),
                    self.max_attempts_spin)

        self.lock_dur_spin = QSpinBox()
        self.lock_dur_spin.setRange(1, 1440)
        self.lock_dur_spin.setValue(15)
        self.lock_dur_spin.setSuffix("  دقیقه")
        self.lock_dur_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.sec.lock_duration")),
                    self.lock_dur_spin)

        self.password_change_spin = QSpinBox()
        self.password_change_spin.setRange(0, 365)
        self.password_change_spin.setValue(0)
        self.password_change_spin.setSuffix("  روز")
        self.password_change_spin.setSpecialValueText("غیرفعال")
        self.password_change_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.sec.password_change_days")),
                    self.password_change_spin)

        b.addLayout(form)
        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 10: AI
    # ============================================================
    def _page_ai(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(t("set.ai.title"), t("set.ai.hint"), "🤖")
        b = c1.body()

        self.ai_enabled_chk = QCheckBox(t("set.ai.enabled"))
        self.ai_enabled_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.ai_enabled_chk)

        form = self._form()

        self.ai_confidence_spin = QDoubleSpinBox()
        self.ai_confidence_spin.setRange(0.05, 1.0)
        self.ai_confidence_spin.setValue(0.45)
        self.ai_confidence_spin.setDecimals(2)
        self.ai_confidence_spin.setSingleStep(0.05)
        self.ai_confidence_spin.setStyleSheet(_spin_qss())
        form.addRow(self._lbl(t("set.ai.confidence")),
                    self.ai_confidence_spin)

        b.addLayout(form)

        self.ai_person_chk = QCheckBox(t("set.ai.detect_person"))
        self.ai_person_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.ai_person_chk)

        self.ai_car_chk = QCheckBox(t("set.ai.detect_car"))
        self.ai_car_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.ai_car_chk)

        self.ai_bike_chk = QCheckBox(t("set.ai.detect_bike"))
        self.ai_bike_chk.setStyleSheet(_checkbox_qss())
        b.addWidget(self.ai_bike_chk)

        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Page 12: About
    # ============================================================
    def _page_about(self):
        page = ScrollPage()
        lay = page.content_layout

        c1 = SettingsCard(icon="ℹ")
        b = c1.body()
        b.setSpacing(12)

        logo = QLabel("K1 VMS")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"""
            color: {theme.COLOR_ACCENT};
            font-size: 32px; font-weight: 900;
            padding: 16px; background: transparent;
        """)
        b.addWidget(logo)

        ver = QLabel(
            f"{t('set.about.version')} {getattr(config, 'APP_VERSION', '1.0.0')}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 12px; background: transparent;
        """)
        b.addWidget(ver)

        b.addWidget(self._hint(t("set.about.desc")))

        lay.addWidget(c1)
        lay.addStretch(1)
        return page

    # ============================================================
    # Load
    # ============================================================
    def _load_all(self):
        self._loading = True
        try:
            s = settings_manager.load_settings()
            self._apply_to_ui(s)
        except Exception as e:
            print(f"[settings] load error: {e}")
        finally:
            self._loading = False

    def _apply_to_ui(self, s):
        try:
            # Recording
            self.rec_enabled_chk.setChecked(bool(getattr(s, "record_enabled", True)))
            self.rec_segment_spin.setValue(int(getattr(s, "record_segment_minutes", 5) or 5))
            idx = self.rec_format_combo.findData(getattr(s, "record_format", ".ts"))
            if idx >= 0: self.rec_format_combo.setCurrentIndex(idx)
            self.motion_enabled_chk.setChecked(bool(getattr(s, "motion_recording_enabled", False)))
            self.motion_after_chk.setChecked(bool(getattr(s, "motion_record_after", True)))
            self.pre_buffer_spin.setValue(int(getattr(s, "motion_pre_buffer_sec", 5) or 5))
            self.post_buffer_spin.setValue(int(getattr(s, "motion_post_buffer_sec", 5) or 5))
            self.sensitivity_spin.setValue(int(getattr(s, "motion_sensitivity_default", 100) or 100))
            self.min_area_spin.setValue(int(getattr(s, "motion_min_area_default", 400) or 400))
            self.corrupted_chk.setChecked(bool(getattr(s, "cleanup_corrupted_files", True)))
            idx = self.disk_policy_combo.findData(getattr(s, "disk_full_policy", "delete_oldest"))
            if idx >= 0: self.disk_policy_combo.setCurrentIndex(idx)

            # Storage
            self.auto_cleanup_chk.setChecked(bool(getattr(s, "auto_cleanup_enabled", True)))
            self.retention_spin.setValue(int(getattr(s, "retention_days", 7) or 7))
            self.quota_percent_spin.setValue(int(getattr(s, "max_storage_percent", 0) or 0))
            self.quota_gb_spin.setValue(float(getattr(s, "max_storage_gb", 0) or 0))
            self.cleanup_interval_spin.setValue(int(getattr(s, "cleanup_interval_hours", 6) or 6))
            self.cleanup_hour_spin.setValue(int(getattr(s, "cleanup_hour", 3) or 3))
            self.snapshot_ret_spin.setValue(int(getattr(s, "snapshots_retention_days", 30) or 30))
            self.export_ret_spin.setValue(int(getattr(s, "exports_retention_days", 90) or 90))
            self.backup_chk.setChecked(bool(getattr(s, "backup_enabled", False)))
            self.backup_path_edit.setText(getattr(s, "backup_path", "") or "")
            self.backup_interval_spin.setValue(int(getattr(s, "backup_interval_hours", 24) or 24))
            self.backup_keep_spin.setValue(int(getattr(s, "backup_keep_days", 3) or 3))

            # Folders
            self.folder_by_camera_chk.setChecked(bool(getattr(s, "record_folder_by_camera", True)))
            self.folder_by_day_chk.setChecked(bool(getattr(s, "record_folder_by_day", True)))
            self.folder_by_hour_chk.setChecked(bool(getattr(s, "record_folder_by_hour", False)))
            self.use_nvr_name_chk.setChecked(bool(getattr(s, "use_nvr_name_in_path", True)))
            self.incident_lock_chk.setChecked(bool(getattr(s, "incident_lock_enabled", True)))
            self.folder_pattern_edit.setText(getattr(s, "record_folder_pattern", "") or "")

            # Live
            idx = self.layout_combo.findData(getattr(s, "live_default_layout", "2x2"))
            if idx >= 0: self.layout_combo.setCurrentIndex(idx)
            self.grid_fps_spin.setValue(int(getattr(s, "live_grid_fps", 5) or 5))
            self.single_fps_spin.setValue(int(getattr(s, "live_single_fps", 15) or 15))
            self.max_readers_spin.setValue(int(getattr(s, "live_max_readers", 16) or 16))
            self.reconnect_delay_spin.setValue(int(getattr(s, "live_reconnect_delay_sec", 5) or 5))
            idx = self.transport_combo.findData(getattr(s, "live_default_transport", "auto"))
            if idx >= 0: self.transport_combo.setCurrentIndex(idx)
            self.auto_reconnect_chk.setChecked(bool(getattr(s, "live_auto_reconnect", True)))
            self.focus_mode_chk.setChecked(bool(getattr(s, "live_focus_mode", True)))
            self.show_timestamp_chk.setChecked(bool(getattr(s, "live_show_timestamp", True)))
            self.show_cam_name_chk.setChecked(bool(getattr(s, "live_show_camera_name", True)))
            self.show_rec_ind_chk.setChecked(bool(getattr(s, "live_show_recording_indicator", True)))
            self.show_motion_ind_chk.setChecked(bool(getattr(s, "live_show_motion_indicator", True)))

            # Appearance
            idx = self.theme_combo.findData(getattr(s, "theme", "dark"))
            if idx >= 0: self.theme_combo.setCurrentIndex(idx)
            idx = self.font_combo.findData(getattr(s, "font_size", "medium"))
            if idx >= 0: self.font_combo.setCurrentIndex(idx)
            self.sidebar_width_spin.setValue(int(getattr(s, "sidebar_width", 260) or 260))
            self.compact_chk.setChecked(bool(getattr(s, "compact_mode", False)))
            self.always_on_top_chk.setChecked(bool(getattr(s, "always_on_top", False)))
            self.start_min_chk.setChecked(bool(getattr(s, "start_minimized", False)))
            self.remember_geom_chk.setChecked(bool(getattr(s, "remember_window_geometry", True)))
            idx = self.lang_combo.findData(getattr(s, "language", "fa"))
            if idx >= 0: self.lang_combo.setCurrentIndex(idx)

            # Startup
            self.startup_autostart_chk.setChecked(bool(getattr(s, "autostart", False)))
            self.startup_mediamtx_chk.setChecked(bool(getattr(s, "autostart_mediamtx", True)))
            self.startup_record_chk.setChecked(bool(getattr(s, "autostart_recording_on_boot", True)))
            self.restore_tab_chk.setChecked(bool(getattr(s, "restore_last_tab", True)))
            self.restore_layout_chk.setChecked(bool(getattr(s, "restore_last_layout", True)))

            # Alarms
            self.sound_chk.setChecked(bool(getattr(s, "sound_enabled", True)))
            self.desktop_notify_chk.setChecked(bool(getattr(s, "desktop_notifications", True)))
            self.volume_slider.setValue(int(getattr(s, "sound_volume", 80) or 80))
            self.alarm_dur_spin.setValue(int(getattr(s, "alarm_duration_sec", 8) or 8))
            self.cooldown_spin.setValue(int(getattr(s, "cooldown_sec", 5) or 5))

            # Notify events
            events = getattr(s, "notify_events", []) or []
            for key, chk in self.event_chks.items():
                chk.setChecked(key in events)

            # Email
            self.email_enabled_chk.setChecked(bool(getattr(s, "notify_email_enabled", False)))
            self.email_smtp_edit.setText(getattr(s, "notify_email_smtp", "") or "")
            self.email_port_spin.setValue(int(getattr(s, "notify_email_port", 587) or 587))
            self.email_user_edit.setText(getattr(s, "notify_email_user", "") or "")
            self.email_pass_edit.setText(getattr(s, "notify_email_pass", "") or "")
            self.email_to_edit.setText(getattr(s, "notify_email_to", "") or "")
            self.email_tls_chk.setChecked(bool(getattr(s, "notify_email_use_tls", True)))

            # Telegram / Bale / Eitaa / Rubika
            self.tg_enabled_chk.setChecked(bool(getattr(s, "notify_telegram_enabled", False)))
            self.tg_token_edit.setText(getattr(s, "notify_telegram_bot_token", "") or "")
            self.tg_chat_edit.setText(getattr(s, "notify_telegram_chat_id", "") or "")

            self.bale_enabled_chk.setChecked(bool(getattr(s, "notify_bale_enabled", False)))
            self.bale_token_edit.setText(getattr(s, "notify_bale_bot_token", "") or "")
            self.bale_chat_edit.setText(getattr(s, "notify_bale_chat_id", "") or "")

            self.eitaa_enabled_chk.setChecked(bool(getattr(s, "notify_eitaa_enabled", False)))
            self.eitaa_token_edit.setText(getattr(s, "notify_eitaa_bot_token", "") or "")
            self.eitaa_chat_edit.setText(getattr(s, "notify_eitaa_chat_id", "") or "")

            self.rubika_enabled_chk.setChecked(bool(getattr(s, "notify_rubika_enabled", False)))
            self.rubika_token_edit.setText(getattr(s, "notify_rubika_bot_token", "") or "")
            self.rubika_chat_edit.setText(getattr(s, "notify_rubika_chat_id", "") or "")

            # Security
            self.max_attempts_spin.setValue(int(getattr(s, "max_login_attempts", 5) or 5))
            self.lock_dur_spin.setValue(int(getattr(s, "lock_duration_min", 15) or 15))
            self.password_change_spin.setValue(int(getattr(s, "require_password_change_days", 0) or 0))

            # AI
            self.ai_enabled_chk.setChecked(bool(getattr(s, "ai_enabled", False)))
            self.ai_confidence_spin.setValue(float(getattr(s, "ai_confidence_threshold", 0.45) or 0.45))
            objs = getattr(s, "ai_detect_objects", []) or []
            self.ai_person_chk.setChecked("person" in objs)
            self.ai_car_chk.setChecked("car" in objs)
            self.ai_bike_chk.setChecked("bike" in objs)

            self._update_path_preview()
        except Exception as e:
            print(f"[settings] apply error: {e}")

    # ============================================================
    # Save
    # ============================================================
    def _on_save(self):
        try:
            s = settings_manager.load_settings()

            # Recording
            s.record_enabled = self.rec_enabled_chk.isChecked()
            s.record_segment_minutes = int(self.rec_segment_spin.value())
            s.record_format = self.rec_format_combo.currentData() or ".ts"
            s.motion_recording_enabled = self.motion_enabled_chk.isChecked()
            s.motion_record_after = self.motion_after_chk.isChecked()
            s.motion_pre_buffer_sec = int(self.pre_buffer_spin.value())
            s.motion_post_buffer_sec = int(self.post_buffer_spin.value())
            s.motion_sensitivity_default = int(self.sensitivity_spin.value())
            s.motion_min_area_default = int(self.min_area_spin.value())
            s.cleanup_corrupted_files = self.corrupted_chk.isChecked()
            s.disk_full_policy = self.disk_policy_combo.currentData() or "delete_oldest"

            # Storage
            s.auto_cleanup_enabled = self.auto_cleanup_chk.isChecked()
            s.retention_days = int(self.retention_spin.value())
            s.max_storage_percent = int(self.quota_percent_spin.value())
            s.max_storage_gb = float(self.quota_gb_spin.value())
            s.cleanup_interval_hours = int(self.cleanup_interval_spin.value())
            s.cleanup_hour = int(self.cleanup_hour_spin.value())
            s.snapshots_retention_days = int(self.snapshot_ret_spin.value())
            s.exports_retention_days = int(self.export_ret_spin.value())
            s.backup_enabled = self.backup_chk.isChecked()
            s.backup_path = self.backup_path_edit.text().strip()
            s.backup_interval_hours = int(self.backup_interval_spin.value())
            s.backup_keep_days = int(self.backup_keep_spin.value())

            # Folders
            s.record_folder_by_camera = self.folder_by_camera_chk.isChecked()
            s.record_folder_by_day = self.folder_by_day_chk.isChecked()
            s.record_folder_by_hour = self.folder_by_hour_chk.isChecked()
            s.use_nvr_name_in_path = self.use_nvr_name_chk.isChecked()
            s.incident_lock_enabled = self.incident_lock_chk.isChecked()
            s.record_folder_pattern = self.folder_pattern_edit.text().strip()

            # Live
            s.live_default_layout = self.layout_combo.currentData() or "2x2"
            s.live_grid_fps = int(self.grid_fps_spin.value())
            s.live_single_fps = int(self.single_fps_spin.value())
            s.live_max_readers = int(self.max_readers_spin.value())
            s.live_reconnect_delay_sec = int(self.reconnect_delay_spin.value())
            s.live_default_transport = self.transport_combo.currentData() or "auto"
            s.live_auto_reconnect = self.auto_reconnect_chk.isChecked()
            s.live_focus_mode = self.focus_mode_chk.isChecked()
            s.live_show_timestamp = self.show_timestamp_chk.isChecked()
            s.live_show_camera_name = self.show_cam_name_chk.isChecked()
            s.live_show_recording_indicator = self.show_rec_ind_chk.isChecked()
            s.live_show_motion_indicator = self.show_motion_ind_chk.isChecked()

            # Appearance
            s.theme = self.theme_combo.currentData() or "dark"
            s.font_size = self.font_combo.currentData() or "medium"
            s.sidebar_width = int(self.sidebar_width_spin.value())
            s.compact_mode = self.compact_chk.isChecked()
            s.always_on_top = self.always_on_top_chk.isChecked()
            s.start_minimized = self.start_min_chk.isChecked()
            s.remember_window_geometry = self.remember_geom_chk.isChecked()
            new_lang = self.lang_combo.currentData() or "fa"
            s.language = new_lang

            # Startup
            s.autostart = self.startup_autostart_chk.isChecked()
            s.autostart_mediamtx = self.startup_mediamtx_chk.isChecked()
            s.autostart_recording_on_boot = self.startup_record_chk.isChecked()
            s.restore_last_tab = self.restore_tab_chk.isChecked()
            s.restore_last_layout = self.restore_layout_chk.isChecked()

            # Alarms
            s.sound_enabled = self.sound_chk.isChecked()
            s.desktop_notifications = self.desktop_notify_chk.isChecked()
            s.sound_volume = int(self.volume_slider.value())
            s.alarm_duration_sec = int(self.alarm_dur_spin.value())
            s.cooldown_sec = int(self.cooldown_spin.value())

            # Notify events
            s.notify_events = [k for k, chk in self.event_chks.items()
                               if chk.isChecked()]

            # Email
            s.notify_email_enabled = self.email_enabled_chk.isChecked()
            s.notify_email_smtp = self.email_smtp_edit.text().strip()
            s.notify_email_port = int(self.email_port_spin.value())
            s.notify_email_user = self.email_user_edit.text().strip()
            s.notify_email_pass = self.email_pass_edit.text()
            s.notify_email_to = self.email_to_edit.text().strip()
            s.notify_email_use_tls = self.email_tls_chk.isChecked()

            # Messengers
            s.notify_telegram_enabled = self.tg_enabled_chk.isChecked()
            s.notify_telegram_bot_token = self.tg_token_edit.text().strip()
            s.notify_telegram_chat_id = self.tg_chat_edit.text().strip()

            s.notify_bale_enabled = self.bale_enabled_chk.isChecked()
            s.notify_bale_bot_token = self.bale_token_edit.text().strip()
            s.notify_bale_chat_id = self.bale_chat_edit.text().strip()

            s.notify_eitaa_enabled = self.eitaa_enabled_chk.isChecked()
            s.notify_eitaa_bot_token = self.eitaa_token_edit.text().strip()
            s.notify_eitaa_chat_id = self.eitaa_chat_edit.text().strip()

            s.notify_rubika_enabled = self.rubika_enabled_chk.isChecked()
            s.notify_rubika_bot_token = self.rubika_token_edit.text().strip()
            s.notify_rubika_chat_id = self.rubika_chat_edit.text().strip()

            # Security
            s.max_login_attempts = int(self.max_attempts_spin.value())
            s.lock_duration_min = int(self.lock_dur_spin.value())
            s.require_password_change_days = int(self.password_change_spin.value())

            # AI
            s.ai_enabled = self.ai_enabled_chk.isChecked()
            s.ai_confidence_threshold = float(self.ai_confidence_spin.value())
            objs = []
            if self.ai_person_chk.isChecked(): objs.append("person")
            if self.ai_car_chk.isChecked(): objs.append("car")
            if self.ai_bike_chk.isChecked(): objs.append("bike")
            s.ai_detect_objects = objs

            # ★ Phase 14 — ذخیره تنظیمات تخصصی
            try:
                if hasattr(self, "advanced_tab"):
                    self.advanced_tab.save(s)
            except Exception as e:
                print(f"[settings] advanced tab save error: {e}")

            settings_manager.save_settings(s)

            if new_lang != get_language():
                QMessageBox.information(self, t("common.save"),
                                        t("set.lang.saved_restart"))
            else:
                QMessageBox.information(self, t("common.save"),
                                        t("set.saved_ok"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, t("common.error"),
                                f"{t('set.save_failed')}\n{e}")

    # ============================================================
    # Actions
    # ============================================================
    def _on_browse_backup(self):
        path = QFileDialog.getExistingDirectory(
            self, t("set.backup.browse"),
            self.backup_path_edit.text() or "")
        if path:
            self.backup_path_edit.setText(path)

    def _on_cleanup_now(self):
        try:
            s = settings_manager.load_settings()
            results = self.sm.run_cleanup(s)
            deleted = (results.get("retention", {}).get("deleted", 0)
                       + results.get("quota", {}).get("deleted", 0))
            freed = (results.get("retention", {}).get("freed_bytes", 0)
                     + results.get("quota", {}).get("freed_bytes", 0))
            freed_mb = freed / (1024 * 1024)

            QMessageBox.information(
                self, t("set.storage.cleanup_now"),
                f"{t('set.cleanup_done')}\n\n"
                f"{t('set.cleanup_deleted')}: {deleted}\n"
                f"{t('set.cleanup_freed')}: {freed_mb:.1f} MB"
            )
            self._refresh_stats()
        except Exception as e:
            QMessageBox.warning(self, t("common.error"),
                                f"{t('set.cleanup_failed')}\n{e}")

    def _on_test_notifications(self):
        """تست همه کانال‌های اعلان فعال."""
        try:
            from core.notifier import Notifier
            s = settings_manager.load_settings()

            # ذخیره موقت — تا اطلاعات فعلی تست شوند
            self._on_save_quiet(s)

            notifier = Notifier.instance()
            results = notifier.test_all(s)

            if not results:
                QMessageBox.information(self, t("set.notify.test_all"),
                                        t("set.notify.test_empty"))
                return

            lines = [t("set.notify.test_done"), ""]
            for channel, (ok, msg) in results.items():
                mark = t("set.notify.test_ok") if ok else t("set.notify.test_fail")
                lines.append(f"{mark}  {channel}")
                if not ok:
                    lines.append(f"      → {msg[:120]}")

            QMessageBox.information(self, t("set.notify.test_all"),
                                    "\n".join(lines))
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, t("common.error"),
                                f"خطا در تست:\n{e}")

    def _on_save_quiet(self, s):
        """ذخیره‌ی بی‌صدا — برای تست اعلان‌ها."""
        try:
            s.notify_email_enabled = self.email_enabled_chk.isChecked()
            s.notify_email_smtp = self.email_smtp_edit.text().strip()
            s.notify_email_port = int(self.email_port_spin.value())
            s.notify_email_user = self.email_user_edit.text().strip()
            s.notify_email_pass = self.email_pass_edit.text()
            s.notify_email_to = self.email_to_edit.text().strip()
            s.notify_email_use_tls = self.email_tls_chk.isChecked()

            s.notify_telegram_enabled = self.tg_enabled_chk.isChecked()
            s.notify_telegram_bot_token = self.tg_token_edit.text().strip()
            s.notify_telegram_chat_id = self.tg_chat_edit.text().strip()

            s.notify_bale_enabled = self.bale_enabled_chk.isChecked()
            s.notify_bale_bot_token = self.bale_token_edit.text().strip()
            s.notify_bale_chat_id = self.bale_chat_edit.text().strip()

            s.notify_eitaa_enabled = self.eitaa_enabled_chk.isChecked()
            s.notify_eitaa_bot_token = self.eitaa_token_edit.text().strip()
            s.notify_eitaa_chat_id = self.eitaa_chat_edit.text().strip()

            s.notify_rubika_enabled = self.rubika_enabled_chk.isChecked()
            s.notify_rubika_bot_token = self.rubika_token_edit.text().strip()
            s.notify_rubika_chat_id = self.rubika_chat_edit.text().strip()

            s.desktop_notifications = self.desktop_notify_chk.isChecked()

            settings_manager.save_settings(s)
        except Exception as e:
            print(f"[settings] quiet save error: {e}")

    # ============================================================
    # Path preview
    # ============================================================
    def _update_path_preview(self):
        try:
            parts = ["continuous"]
            if self.folder_by_camera_chk.isChecked():
                parts.append("camera_name")
            if self.folder_by_day_chk.isChecked():
                parts.append("2026-10-13")
            if self.folder_by_hour_chk.isChecked():
                parts.append("14")
            parts.append("14-25-03.ts")

            pattern = self.folder_pattern_edit.text().strip()
            if pattern:
                preview = pattern.replace("{camera}", "camera_name") \
                                 .replace("{date}", "2026-10-13") \
                                 .replace("{time}", "14-25-03") \
                                 .replace("{nvr}", "NVR_name")
            else:
                preview = "/".join(parts)

            self.path_preview_lbl.setText(preview)
        except Exception:
            pass

    # ============================================================
    # Stats
    # ============================================================
    def _refresh_stats(self):
        if self._loading:
            return
        try:
            stats = self.sm.compute_stats()
        except Exception as e:
            print(f"[settings] stats error: {e}")
            return

        pct = int(stats.usage_percent())
        self.disk_bar.setValue(pct)
        self.disk_bar.setFormat(
            f"{stats.disk_used_gb():.1f} / {stats.disk_total_gb():.1f} GB  "
            f"({pct}%)"
        )
        color = ("#e74c3c" if pct >= 90
                 else "#f39c12" if pct >= 75
                 else theme.COLOR_ACCENT)

        self.disk_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {theme.COLOR_BG_DARK};
                border: 1px solid #232932;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-size: 12px;
                font-weight: 700;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 7px;
            }}
        """)

        self.stat_disk_used._value.setText(
            f"{stats.disk_used_gb():.1f} / {stats.disk_total_gb():.1f} GB")
        self.stat_record_size._value.setText(f"{stats.total_gb():.2f} GB")
        self.stat_file_count._value.setText(f"{stats.file_count:,}")

        oldest = stats.oldest_date()
        newest = stats.newest_date()
        self.stat_oldest._value.setText(
            oldest.strftime("%Y-%m-%d %H:%M") if oldest else "—")
        self.stat_newest._value.setText(
            newest.strftime("%Y-%m-%d %H:%M") if newest else "—")

    # ============================================================
    def on_show(self):
        self._load_all()
        self._refresh_stats()

    def on_hide(self):
        pass