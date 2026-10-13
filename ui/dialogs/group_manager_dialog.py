# -*- coding: utf-8 -*-
"""K1 VMS — پنجره مدیریت گروه‌ها (Phase 10.6: professional editor)"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFrame,
    QDialogButtonBox, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.i18n import t
from core.group_manager import GroupManager, CameraGroup
from core.camera_manager import CameraManager
from ui.dialogs.group_edit_dialog import GroupEditDialog
import config


STYLE = f"""
QDialog {{ background-color: {config.COLOR_BG_DARK}; }}
QLabel {{ color: {config.COLOR_TEXT_PRIMARY}; background: transparent;
         font-size: 13px; }}
QListWidget {{ background: {config.COLOR_BG_CARD};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 6px;
    padding: 6px; font-size: 13px; }}
QListWidget::item {{ padding: 10px 12px; border-radius: 5px; }}
QListWidget::item:hover {{ background: #2c333c; }}
QListWidget::item:selected {{ background: {config.COLOR_ACCENT};
    color: white; }}
QPushButton {{
    background: {config.COLOR_BG_CARD};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 6px;
    padding: 8px 18px; font-size: 12px; font-weight: bold;
    min-width: 90px;
}}
QPushButton:hover {{ background: #2c333c; }}
"""


class GroupManagerDialog(QDialog):
    """پنجره مدیریت گروه‌ها — افزودن، ویرایش، حذف."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.gm = GroupManager.instance()
        self.cm = CameraManager()

        self.setWindowTitle(t("grp.title.manager"))
        self.resize(780, 580)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._refresh()

    # ============================================================
    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        # ---------- Header ----------
        head = QHBoxLayout()
        title = QLabel(t("grp.title.manager"))
        title.setStyleSheet(
            f"color: {config.COLOR_TEXT_PRIMARY}; "
            f"font-size: 18px; font-weight: bold;"
        )
        head.addWidget(title)
        head.addStretch(1)

        btn_new = QPushButton("➕ " + t("grp.btn.new"))
        btn_new.setStyleSheet(
            f"QPushButton {{ background: {config.COLOR_ACCENT}; color: white;"
            f" border: none; border-radius: 6px; padding: 8px 20px;"
            f" font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {config.COLOR_ACCENT_HOVER}; }}"
        )
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.clicked.connect(self._on_new)
        head.addWidget(btn_new)
        v.addLayout(head)

        # ---------- Body ----------
        body = QHBoxLayout()
        body.setSpacing(12)

        # Left: groups list
        left = QFrame()
        left.setStyleSheet(
            f"QFrame {{ background: {config.COLOR_BG_PANEL}; "
            f"border: 1px solid #2c333c; border-radius: 8px; }}"
        )
        lv = QVBoxLayout(left)
        lv.setContentsMargins(12, 12, 12, 12)
        lv.setSpacing(8)

        lbl_groups = QLabel("📁 " + t("grp.title.manager"))
        lbl_groups.setStyleSheet(
            f"color: {config.COLOR_ACCENT}; font-size: 12px; "
            f"font-weight: bold;"
        )
        lv.addWidget(lbl_groups)

        self.groups_list = QListWidget()
        self.groups_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.groups_list.currentItemChanged.connect(
            lambda _cur, _prev: self._on_group_selected())
        self.groups_list.itemDoubleClicked.connect(lambda _: self._on_edit())
        lv.addWidget(self.groups_list, 1)

        ga = QHBoxLayout()
        ga.setSpacing(6)
        btn_edit_g = QPushButton("✏ " + t("grp.btn.edit"))
        btn_edit_g.clicked.connect(self._on_edit)
        ga.addWidget(btn_edit_g)
        btn_del_g = QPushButton("🗑 " + t("grp.btn.delete"))
        btn_del_g.setStyleSheet(
            "QPushButton { background: #c0392b; color: white; "
            "border: none; border-radius: 6px; padding: 8px 18px; "
            "font-weight: bold; font-size: 12px; }"
            "QPushButton:hover { background: #e74c3c; }"
        )
        btn_del_g.clicked.connect(self._on_delete)
        ga.addWidget(btn_del_g)
        lv.addLayout(ga)

        body.addWidget(left, 1)

        # Right: cameras in selected group
        right = QFrame()
        right.setStyleSheet(
            f"QFrame {{ background: {config.COLOR_BG_PANEL}; "
            f"border: 1px solid #2c333c; border-radius: 8px; }}"
        )
        rv = QVBoxLayout(right)
        rv.setContentsMargins(12, 12, 12, 12)
        rv.setSpacing(8)

        self.lbl_cams = QLabel("📹 " + t("grp.cameras"))
        self.lbl_cams.setStyleSheet(
            f"color: {config.COLOR_ACCENT}; font-size: 12px; "
            f"font-weight: bold;"
        )
        rv.addWidget(self.lbl_cams)

        self.cams_list = QListWidget()
        rv.addWidget(self.cams_list, 1)

        body.addWidget(right, 1)
        v.addLayout(body, 1)

        # ---------- Close ----------
        btns = QDialogButtonBox()
        close_btn = btns.addButton(
            t("grp.btn.close"), QDialogButtonBox.RejectRole)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: {config.COLOR_BG_CARD};"
            f" color: {config.COLOR_TEXT_PRIMARY};"
            f" border: 1px solid #2c333c; border-radius: 5px;"
            f" padding: 8px 24px; font-size: 12px; font-weight: bold;"
            f" min-width: 90px; }}"
            f"QPushButton:hover {{ background: #2c333c; }}"
        )
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    # ============================================================
    def _refresh(self):
        self.groups_list.blockSignals(True)
        self.groups_list.clear()
        for g in self.gm.all():
            n = len(g.camera_uids or [])
            item = QListWidgetItem(f"📁  {g.name}   ({n})")
            item.setData(Qt.UserRole, g.uid)
            item.setForeground(QColor(g.color or "#f39c12"))
            self.groups_list.addItem(item)
        self.groups_list.blockSignals(False)

        if self.groups_list.count() > 0:
            self.groups_list.setCurrentRow(0)
        else:
            self.cams_list.clear()
            self.lbl_cams.setText("📹 " + t("grp.cameras"))

    def _on_group_selected(self):
        cur = self.groups_list.currentItem()
        if cur is None:
            self.cams_list.clear()
            return
        uid = cur.data(Qt.UserRole)
        grp = self.gm.get(uid)
        if not grp:
            return
        self.lbl_cams.setText(
            f"📹 {t('grp.cameras')} ({len(grp.camera_uids or [])})"
        )
        self.cams_list.clear()
        for cam_uid in grp.camera_uids or []:
            cam = self.cm.get(cam_uid)
            if cam:
                self.cams_list.addItem(f"  {cam.name}")

    # ============================================================
    def _on_new(self):
        dlg = GroupEditDialog(group=None, parent=self)
        if dlg.exec() != GroupEditDialog.Accepted:
            return
        try:
            grp = CameraGroup()
            grp.name = dlg.get_name()
            grp.color = dlg.get_color()
            self.gm.add(grp)
        except Exception as e:
            print(f"[groups] new failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, t("common.error"), str(e))
            return
        self._refresh()

    def _on_edit(self):
        cur = self.groups_list.currentItem()
        if cur is None:
            return
        uid = cur.data(Qt.UserRole)
        grp = self.gm.get(uid)
        if not grp:
            return
        dlg = GroupEditDialog(group=grp, parent=self)
        if dlg.exec() != GroupEditDialog.Accepted:
            return
        grp.name = dlg.get_name()
        grp.color = dlg.get_color()
        self.gm.update(uid, grp)
        self._refresh()

    def _on_delete(self):
        cur = self.groups_list.currentItem()
        if cur is None:
            return
        uid = cur.data(Qt.UserRole)
        grp = self.gm.get(uid)
        if not grp:
            return
        r = QMessageBox.question(
            self, t("common.confirm"),
            t("grp.confirm.delete", name=grp.name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        self.gm.delete(uid)
        self._refresh()