# -*- coding: utf-8 -*-
"""K1 VMS — Live Tabs Bar (Phase 9.1: incremental refresh)"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ui import theme


class LiveTabButton(QPushButton):
    clicked_uid = Signal(str)
    rename_requested = Signal(str)
    delete_requested = Signal(str)
    duplicate_requested = Signal(str)

    def __init__(self, tab, is_active, parent=None):
        super().__init__(parent)
        self.tab_uid = tab.uid
        self.setCheckable(True)
        self.setChecked(is_active)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context)
        self.setText(tab.name)
        self.setToolTip(
            f"{tab.name}\n{len(tab.cells)} دوربین چیده‌شده")
        self.clicked.connect(
            lambda: self.clicked_uid.emit(self.tab_uid))
        self._apply_style()

    def update_from(self, tab, is_active):
        if self.text() != tab.name:
            self.setText(tab.name)
        if self.isChecked() != is_active:
            self.setChecked(is_active)
        self.setToolTip(
            f"{tab.name}\n{len(tab.cells)} دوربین چیده‌شده")

    def _apply_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_SECONDARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 600;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background: {theme.COLOR_BG_HOVER};
                color: {theme.COLOR_TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background: {theme.COLOR_ACCENT};
                color: white;
                border-color: {theme.COLOR_ACCENT};
            }}
        """)

    def _on_context(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 6px 20px; border-radius: 4px; }}
            QMenu::item:selected {{
                background: {theme.COLOR_ACCENT};
                color: white;
            }}
        """)
        a_rename = QAction("✏ تغییر نام", self)
        a_rename.triggered.connect(
            lambda: self.rename_requested.emit(self.tab_uid))
        menu.addAction(a_rename)

        a_dup = QAction("📋 کپی تب", self)
        a_dup.triggered.connect(
            lambda: self.duplicate_requested.emit(self.tab_uid))
        menu.addAction(a_dup)

        menu.addSeparator()

        a_del = QAction("🗑 حذف تب", self)
        a_del.triggered.connect(
            lambda: self.delete_requested.emit(self.tab_uid))
        menu.addAction(a_del)

        menu.exec(self.mapToGlobal(pos))


class LiveTabsBar(QWidget):
    tab_changed = Signal(str)
    new_tab_requested = Signal()
    rename_requested = Signal(str)
    delete_requested = Signal(str)
    duplicate_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(
            f"background: {theme.COLOR_BG_HEADER};"
            f"border-bottom: 1px solid {theme.COLOR_BORDER};"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 5, 8, 5)
        self._layout.setSpacing(4)

        self._buttons = []

        from core.i18n import t
        self.btn_new = QPushButton("＋  " + t("live.tab.new").lstrip("+ ").strip())
        self.btn_new.setFixedHeight(28)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_tab_requested.emit)
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_ACCENT};
                border: 1px dashed {theme.COLOR_ACCENT};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme.COLOR_ACCENT};
                color: white;
                border-style: solid;
            }}
        """)

        self._layout.addStretch(1)
        self._layout.addWidget(self.btn_new)

    def refresh(self, tabs_manager):
        self.setUpdatesEnabled(False)
        try:
            tabs = tabs_manager.all()
            active_uid = tabs_manager.active_tab_uid

            existing = {btn.tab_uid: btn for btn in self._buttons}
            new_uids = {t.uid for t in tabs}

            removed = False
            for uid in list(existing.keys()):
                if uid not in new_uids:
                    btn = existing.pop(uid)
                    try:
                        self._layout.removeWidget(btn)
                        btn.deleteLater()
                    except Exception:
                        pass
                    removed = True
            if removed:
                self._buttons = [
                    b for b in self._buttons if b.tab_uid in existing
                ]

            for i, tab in enumerate(tabs):
                is_active = (tab.uid == active_uid)
                if tab.uid in existing:
                    existing[tab.uid].update_from(tab, is_active)
                else:
                    btn = LiveTabButton(tab, is_active)
                    btn.clicked_uid.connect(self.tab_changed.emit)
                    btn.rename_requested.connect(
                        self.rename_requested.emit)
                    btn.delete_requested.connect(
                        self.delete_requested.emit)
                    btn.duplicate_requested.connect(
                        self.duplicate_requested.emit)
                    self._layout.insertWidget(i, btn)
                    self._buttons.append(btn)

            existing = {btn.tab_uid: btn for btn in self._buttons}
            for i, tab in enumerate(tabs):
                if tab.uid in existing:
                    btn = existing[tab.uid]
                    current_idx = self._layout.indexOf(btn)
                    if current_idx != i:
                        self._layout.removeWidget(btn)
                        self._layout.insertWidget(i, btn)
        finally:
            self.setUpdatesEnabled(True)
            self.update()
