# -*- coding: utf-8 -*-
"""K1 VMS — پنجره حرفه‌ای ساخت/ویرایش گروه"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.icons import make_icon
from core.i18n import t
import config


# رنگ‌های آماده
PRESET_COLORS = [
    "#f39c12", "#e74c3c", "#9b59b6", "#3498db",
    "#1abc9c", "#2ecc71", "#f1c40f", "#e67e22",
]


class GroupEditDialog(QDialog):
    """پنجره‌ی ساخت/ویرایش گروه با ظاهر حرفه‌ای."""

    def __init__(self, group=None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.is_new = group is None
        self.group = group
        self._selected_color = (
            getattr(group, "color", "#f39c12") if group else "#f39c12"
        )
        self._name = getattr(group, "name", "") if group else ""

        title_txt = t("grp.btn.new") if self.is_new else t("grp.btn.edit")
        self.setWindowTitle(title_txt)
        self.setFixedSize(480, 320)
        self.setStyleSheet(f"""
            QDialog {{
                background: {config.COLOR_BG_DARK};
            }}
            QLabel {{
                color: {config.COLOR_TEXT_PRIMARY};
                background: transparent;
                font-size: 13px;
            }}
            QLineEdit {{
                background: {config.COLOR_BG_CARD};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid #2c333c;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
                min-height: 24px;
                selection-background-color: {config.COLOR_ACCENT};
            }}
            QLineEdit:focus {{
                border: 1px solid {config.COLOR_ACCENT};
                background: #232932;
            }}
            QPushButton {{
                background: {config.COLOR_BG_CARD};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid #2c333c;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: #2c333c;
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(16)

        # عنوان
        title = QLabel(title_txt)
        title.setStyleSheet(
            f"color: {config.COLOR_ACCENT}; font-size: 18px; "
            f"font-weight: bold; padding-bottom: 4px;"
        )
        v.addWidget(title)

        # نام گروه
        name_lbl = QLabel(t("grp.name"))
        name_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 12px; "
            f"font-weight: 600;"
        )
        v.addWidget(name_lbl)

        self.name_edit = QLineEdit(self._name)
        self.name_edit.setPlaceholderText("مثلاً: نگهبانی، پارکینگ، ورودی اصلی")
        self.name_edit.selectAll()
        v.addWidget(self.name_edit)

        # رنگ
        color_lbl = QLabel(t("grp.color"))
        color_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 12px; "
            f"font-weight: 600; padding-top: 6px;"
        )
        v.addWidget(color_lbl)

        colors_row = QHBoxLayout()
        colors_row.setSpacing(8)
        self._color_btns = []
        for col in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(38, 38)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("color_value", col)
            btn.clicked.connect(lambda _=False, c=col: self._set_color(c))
            colors_row.addWidget(btn)
            self._color_btns.append(btn)
        colors_row.addStretch(1)
        v.addLayout(colors_row)

        v.addStretch(1)

        # دکمه‌ها
        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addStretch(1)

        cancel_btn = QPushButton(t("common.cancel"))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton(t("common.save"))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {config.COLOR_ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {config.COLOR_ACCENT_HOVER};
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        save_btn.setDefault(True)
        btns.addWidget(save_btn)
        v.addLayout(btns)

        self._refresh_color_buttons()
        self.name_edit.setFocus()

    def _set_color(self, color: str):
        self._selected_color = color
        self._refresh_color_buttons()

    def _refresh_color_buttons(self):
        for btn in self._color_btns:
            col = btn.property("color_value")
            selected = (col == self._selected_color)
            border = "3px solid #ffffff" if selected else "1px solid #2c333c"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {col};
                    border: {border};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border: 2px solid #ffffff;
                }}
            """)

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            self.name_edit.setStyleSheet(f"""
                QLineEdit {{
                    background: {config.COLOR_BG_CARD};
                    color: {config.COLOR_TEXT_PRIMARY};
                    border: 2px solid #e74c3c;
                    border-radius: 6px;
                    padding: 10px 12px;
                    font-size: 14px;
                    min-height: 24px;
                }}
            """)
            self.name_edit.setPlaceholderText("نام گروه را وارد کنید!")
            self.name_edit.setFocus()
            return
        self._name = name
        self.accept()

    def get_name(self) -> str:
        return self._name

    def get_color(self) -> str:
        return self._selected_color