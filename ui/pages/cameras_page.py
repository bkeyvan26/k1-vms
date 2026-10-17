# -*- coding: utf-8 -*-
"""K1 VMS — Cameras page (Phase 10.5: search + tri-state + i18n)"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
    QLabel, QMenu, QAbstractItemView, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction

from ui import theme
from ui.icons import make_icon
from ui.pages import BasePage
from core.i18n import t
from ui.camera_dialog import CameraDialog
from ui.dialogs import info as dlg_info, warning as dlg_warning, question as dlg_question
from core.camera_manager import CameraManager
from core.nvr_manager import NVRManager
from core.group_manager import GroupManager
from core import settings_manager
import config


STATUS_ICONS = {
    "recording":     ("🟢", "REC",       "#2ecc71"),
    "online":        ("🔵", "ONLINE",    "#3498db"),
    "reconnecting":  ("🟡", "RECONNECT", "#f39c12"),
    "error":         ("🔴", "ERROR",     "#e74c3c"),
    "starting":      ("🟠", "STARTING",  "#f39c12"),
    "offline":       ("⚫", "OFFLINE",   "#5a6674"),
    "unknown":       ("⚪", "—",         "#5a6674"),
}


class CamerasPage(BasePage):
    PAGE_KEY = "cameras"
    PAGE_TITLE = "Cameras"
    PANEL_TITLE = "Cameras"
    HAS_PANEL = False   # ★ بدون پنل کناری
    cameras_changed = Signal()

    def __init__(self, nvr_engine=None, parent=None):
        super().__init__(parent)
        self.cam_manager = CameraManager()
        self.nvr_manager = NVRManager.instance()
        self.group_manager = GroupManager.instance()
        self.nvr = nvr_engine
        self._statuses = {}
        self._last_summary = None
        self._tree_items = {}
        self._expanded_keys = set()

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        # ---------- Header ----------
        head = QHBoxLayout()
        title = QLabel(t("cam.title"))
        title.setStyleSheet(
            f"color: {theme.COLOR_TEXT_PRIMARY}; "
            f"font-size: 20px; font-weight: 700;"
        )
        head.addWidget(title)
        head.addStretch(1)

        bulk_btn = QPushButton("  " + t("cam.btn.bulk"))
        bulk_btn.setIcon(make_icon("plus-circle", "white", 14))
        bulk_btn.setCursor(Qt.PointingHandCursor)
        bulk_btn.setStyleSheet(
            "QPushButton { background: #16a085; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; "
            "font-weight: 700; font-size: 12px; } "
            "QPushButton:hover { background: #1abc9c; }")
        bulk_btn.clicked.connect(self._on_bulk_add)
        head.addWidget(bulk_btn)

        add_btn = QPushButton("  " + t("cam.btn.add_camera"))
        add_btn.setIcon(make_icon("plus", "#ffffff", 14))
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {theme.COLOR_ACCENT}; color: white;
                border: none; border-radius: 6px; padding: 8px 16px;
                font-weight: 700; font-size: 12px; }}
            QPushButton:hover {{ background: {theme.COLOR_ACCENT_HOVER}; }}
        """)
        add_btn.clicked.connect(self._add_camera)
        head.addWidget(add_btn)

        add_nvr_btn = QPushButton("  " + t("cam.btn.add_nvr"))
        add_nvr_btn.setIcon(make_icon("plus", "#ffffff", 14))
        add_nvr_btn.setCursor(Qt.PointingHandCursor)
        add_nvr_btn.setStyleSheet(
            "QPushButton { background: #8e44ad; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; "
            "font-weight: 700; font-size: 12px; } "
            "QPushButton:hover { background: #9b59b6; }")
        add_nvr_btn.clicked.connect(self._add_nvr)
        head.addWidget(add_nvr_btn)

        groups_btn = QPushButton("  " + t("cam.btn.groups"))
        groups_btn.setIcon(make_icon("folder", "#ffffff", 14))
        groups_btn.setCursor(Qt.PointingHandCursor)
        groups_btn.setStyleSheet(
            "QPushButton { background: #e67e22; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; "
            "font-weight: 700; font-size: 12px; } "
            "QPushButton:hover { background: #f39c12; }")
        groups_btn.clicked.connect(self._manage_groups)
        head.addWidget(groups_btn)

        apply_btn = QPushButton("  " + t("cam.btn.apply"))
        apply_btn.setIcon(make_icon("refresh", theme.COLOR_TEXT_PRIMARY, 14))
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(self._btn_style())
        apply_btn.clicked.connect(self._manual_apply)
        head.addWidget(apply_btn)

        v.addLayout(head)

        # ---------- Hint ----------
        hint = QLabel("💡 " + t("cam.hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"""
            color: {theme.COLOR_TEXT_SECONDARY};
            font-size: 11px;
            background: {theme.COLOR_BG_CARD};
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {theme.COLOR_ACCENT};
        """)
        v.addWidget(hint)

        # ---------- Search box ----------
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(
            f"color: {theme.COLOR_TEXT_SECONDARY}; font-size: 14px;")
        search_row.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(t("cam.search.ph"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                min-height: 22px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme.COLOR_ACCENT};
            }}
        """)
        self.search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_edit, 1)
        v.addLayout(search_row)

        # ---------- Tree ----------
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.tree.setIndentation(18)
        self.tree.setAnimated(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {theme.COLOR_BG_CARD};
                color: {theme.COLOR_TEXT_PRIMARY};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 8px; padding: 6px; font-size: 13px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 8px 6px; border-radius: 5px;
            }}
            QTreeWidget::item:hover {{
                background: {theme.COLOR_BG_HOVER};
            }}
            QTreeWidget::item:selected {{
                background: {theme.COLOR_ACCENT}; color: white;
            }}
            QTreeView::indicator, QTreeWidget::indicator {{
                width: 18px; height: 18px;
                border: 2px solid #6b7280; border-radius: 4px;
                background: #0d0d0d;
                margin-right: 6px;
            }}
            QTreeView::indicator:hover, QTreeWidget::indicator:hover {{
                border-color: {theme.COLOR_ACCENT};
            }}
            QTreeView::indicator:checked, QTreeWidget::indicator:checked {{
                background: {theme.COLOR_ACCENT};
                border-color: {theme.COLOR_ACCENT};
            }}
            QTreeView::indicator:indeterminate,
            QTreeWidget::indicator:indeterminate {{
                background: #f39c12;
                border-color: #f39c12;
            }}
        """)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)
        self.tree.itemChanged.connect(self._on_tree_item_changed)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        v.addWidget(self.tree, 1)

        # ---------- Actions ----------
        act = QHBoxLayout()
        act.setSpacing(8)

        self.edit_btn = QPushButton("  " + t("cam.btn.edit"))
        self.edit_btn.setIcon(make_icon("edit", theme.COLOR_TEXT_PRIMARY, 14))
        self.edit_btn.setStyleSheet(self._btn_style())
        self.edit_btn.clicked.connect(self._edit_selected)
        act.addWidget(self.edit_btn)

        self.del_btn = QPushButton("  " + t("cam.btn.delete"))
        self.del_btn.setIcon(make_icon("trash", "white", 14))
        self.del_btn.setStyleSheet(self._btn_style(danger=True))
        self.del_btn.clicked.connect(self._delete_selected)
        act.addWidget(self.del_btn)

        act.addStretch(1)
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            f"color: {theme.COLOR_TEXT_SECONDARY}; font-size: 11px;"
        )
        act.addWidget(self.count_lbl)
        v.addLayout(act)

        self._refresh_tree()

        if self.nvr:
            try:
                self.nvr.register_listener(self._on_nvr_status)
            except Exception:
                pass

    # ============================================================
    def _btn_style(self, danger=False):
        base = theme.COLOR_STATUS_ERROR if danger else theme.COLOR_BG_CARD
        text = "white" if danger else theme.COLOR_TEXT_PRIMARY
        return f"""
            QPushButton {{
                background: {base};
                color: {text};
                border: 1px solid {theme.COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme.COLOR_BG_HOVER};
            }}
        """

    def _menu_style(self):
        return (f"QMenu {{ background: {theme.COLOR_BG_CARD}; "
                f"color: {theme.COLOR_TEXT_PRIMARY}; "
                f"border: 1px solid {theme.COLOR_BORDER}; "
                f"border-radius: 6px; padding: 4px; }} "
                f"QMenu::item {{ padding: 6px 20px; border-radius: 4px; }} "
                f"QMenu::item:selected {{ background: {theme.COLOR_ACCENT}; "
                f"color: white; }}")

    # ============================================================
    # Search filter
    # ============================================================
    def _on_search_changed(self, text: str):
        text = (text or "").strip().lower()
        try:
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                self._filter_item(top, text)
        except Exception as e:
            print(f"[cameras] search filter error: {e}")

    def _filter_item(self, item, text: str) -> bool:
        item_text = (item.text(0) or "").lower()
        self_match = (not text) or (text in item_text)

        any_child_match = False
        for i in range(item.childCount()):
            child = item.child(i)
            if self._filter_item(child, text):
                any_child_match = True

        visible = self_match or any_child_match
        item.setHidden(not visible)
        return visible

    # ============================================================
    def _on_nvr_status(self, statuses):
        new_summary = {
            uid: info.get("status", "unknown")
            for uid, info in statuses.items()
        }
        if new_summary == self._last_summary:
            return
        self._last_summary = new_summary
        self._statuses = statuses
        self._refresh_tree()

    def _auto_apply_to_nvr(self):
        if not self.nvr:
            return
        if not config.MEDIAMTX_EXE.exists():
            return
        try:
            ok = self.nvr.reload(cameras=self.cam_manager.all(),
                                 settings=settings_manager.load_settings())
            if ok:
                print("[NVR] Auto-reload OK")
            else:
                print(f"[NVR] Auto-reload FAILED: {self.nvr.get_last_error()}")
        except Exception as e:
            print(f"[NVR] Auto-reload exception: {e}")

    def _manual_apply(self):
        if not self.nvr:
            dlg_info(self, "NVR Engine not available.")
            return
        if not config.MEDIAMTX_EXE.exists():
            dlg_warning(self, f"MediaMTX not found at:\n{config.MEDIAMTX_EXE}")
            return
        ok = self.nvr.reload(cameras=self.cam_manager.all(),
                             settings=settings_manager.load_settings())
        if ok:
            dlg_info(self, "MediaMTX reloaded successfully.", "NVR")
        else:
            dlg_warning(self, f"Reload failed:\n{self.nvr.get_last_error()}", "NVR")

    # ============================================================
    def _on_bulk_add(self):
        try:
            from ui.dialogs.bulk_add_camera_dialog import BulkAddCameraDialog
            dlg = BulkAddCameraDialog(self)
            result = dlg.exec()
            if result == QDialog.Accepted:
                self.cam_manager.reload()
                self._refresh_tree()
                self.cameras_changed.emit()
                self._auto_apply_to_nvr()
                n_added = len(getattr(dlg, "_new_cameras", []))
                if n_added > 0:
                    dlg_info(
                        self,
                        f"{n_added} دوربین اضافه شد و MediaMTX reload شد.",
                        "افزودن گروهی"
                    )
        except Exception as e:
            print(f"[cameras] bulk add error: {e}")
            dlg_warning(self, f"خطا: {e}")

    # ============================================================
    # Tree building
    # ============================================================
    def _key_of(self, item):
        data = item.data(0, Qt.UserRole)
        if not data:
            return None
        kind, uid = data
        return f"{kind}:{uid}"

    def _on_item_expanded(self, item):
        k = self._key_of(item)
        if k:
            self._expanded_keys.add(k)

    def _on_item_collapsed(self, item):
        k = self._key_of(item)
        if k and k in self._expanded_keys:
            self._expanded_keys.discard(k)

    def _refresh_tree(self):
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            k = self._key_of(top)
            if k and top.isExpanded():
                self._expanded_keys.add(k)

        self.tree.blockSignals(True)
        self.tree.clear()
        self._tree_items = {}

        cameras = self.cam_manager.all()

        nvrs = self.nvr_manager.all()
        for nvr in nvrs:
            nvr_cams = [c for c in cameras if c.nvr_uid == nvr.uid]
            if not nvr_cams:
                continue

            nvr_item = QTreeWidgetItem(self.tree)
            nvr_item.setText(
                0,
                f"📹  {nvr.name}   ({len(nvr_cams)} ch)   —   {nvr.ip}"
            )
            nvr_item.setData(0, Qt.UserRole, ("nvr", nvr.uid))
            nvr_item.setForeground(0, QColor("#c39bd3"))
            f = nvr_item.font(0)
            f.setBold(True)
            nvr_item.setFont(0, f)
            nvr_item.setFlags(
                nvr_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
            )
            nvr_item.setCheckState(0, Qt.Unchecked)

            def _ch_num(c):
                import re
                m = re.search(r"دوربین\s+(\d+)", c.name or "")
                if m:
                    return int(m.group(1))
                m = re.search(r"(\d+)", c.name or "")
                return int(m.group(1)) if m else 999
            nvr_cams.sort(key=_ch_num)

            for cam in nvr_cams:
                child = self._make_camera_item(cam, parent=nvr_item)
                self._tree_items[cam.uid] = child

            key = f"nvr:{nvr.uid}"
            nvr_item.setExpanded(key in self._expanded_keys)

        for grp in self.group_manager.all():
            grp_cams = []
            for u in grp.camera_uids:
                c = self.cam_manager.get(u)
                if c is not None:
                    grp_cams.append(c)
            grp_item = QTreeWidgetItem(self.tree)
            grp_item.setText(0, f"📁  {grp.name}   ({len(grp_cams)})")
            grp_item.setData(0, Qt.UserRole, ("group", grp.uid))
            grp_item.setForeground(0, QColor(grp.color or "#f39c12"))
            f = grp_item.font(0)
            f.setBold(True)
            grp_item.setFont(0, f)
            grp_item.setFlags(
                grp_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
            )
            grp_item.setCheckState(0, Qt.Unchecked)

            for cam in grp_cams:
                child = self._make_camera_item(cam, parent=grp_item,
                                               group_color=grp.color)
                if cam.uid not in self._tree_items:
                    self._tree_items[cam.uid] = child

            key = f"group:{grp.uid}"
            grp_item.setExpanded(key in self._expanded_keys)

        standalone = [c for c in cameras if not c.nvr_uid]
        if standalone:
            standalone_root = QTreeWidgetItem(self.tree)
            standalone_root.setText(
                0, f"📷  دوربین‌های مستقل   ({len(standalone)})")
            standalone_root.setData(
                0, Qt.UserRole, ("standalone_root", "root"))
            standalone_root.setForeground(0, QColor("#85c1e9"))
            f = standalone_root.font(0)
            f.setBold(True)
            standalone_root.setFont(0, f)
            standalone_root.setFlags(
                standalone_root.flags() | Qt.ItemIsUserCheckable
                | Qt.ItemIsAutoTristate
            )
            standalone_root.setCheckState(0, Qt.Unchecked)

            for cam in standalone:
                child = self._make_camera_item(cam, parent=standalone_root)
                self._tree_items[cam.uid] = child

            key = "standalone_root:root"
            standalone_root.setExpanded(key in self._expanded_keys)

        nvr_count = len(nvrs)
        grp_count = self.group_manager.count()
        self.count_lbl.setText(
            t("cam.count",
              cams=len(cameras), nvrs=nvr_count, groups=grp_count)
        )
        self.tree.blockSignals(False)

        # اعمال فیلتر فعلی روی درخت جدید
        cur_search = self.search_edit.text() if hasattr(self, "search_edit") else ""
        if cur_search:
            self._on_search_changed(cur_search)

    def _make_camera_item(self, cam, parent, group_color=None):
        st = self._statuses.get(cam.uid, {}).get("status", "unknown")
        if not cam.enabled:
            st = "offline"
        icon, label, color = STATUS_ICONS.get(st, STATUS_ICONS["unknown"])

        main_url = cam.get_recording_url() or ""
        has_sub = bool(cam.get_motion_url()
                       and cam.get_motion_url() != main_url)
        stream_tag = "  [M+S]" if has_sub else "  [M]"

        text = f"  {icon}  {cam.name}   —   {label}{stream_tag}"
        item = QTreeWidgetItem(parent)
        item.setText(0, text)
        item.setData(0, Qt.UserRole, ("camera", cam.uid))
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Unchecked)
        if group_color:
            item.setForeground(0, QColor(group_color).lighter(140))
        else:
            item.setForeground(0, QColor(color))
        return item

    # ============================================================
    def _selected_node(self):
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.UserRole)

    def _on_tree_double_click(self, item, col):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        kind, uid = data
        if kind == "camera":
            self._edit_camera(uid)
        else:
            item.setExpanded(not item.isExpanded())

    def _on_tree_item_changed(self, item, col):
        pass

    def _selected_camera_uids(self):
        uids = set()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            self._collect_checked(top, uids)
        for item in self.tree.selectedItems():
            data = item.data(0, Qt.UserRole)
            if not data:
                continue
            kind, uid = data
            if kind == "camera":
                uids.add(uid)
        return list(uids)

    def _collect_checked(self, item, out: set):
        data = item.data(0, Qt.UserRole)
        if data:
            kind, uid = data
            if kind == "camera" and item.checkState(0) == Qt.Checked:
                out.add(uid)
        for i in range(item.childCount()):
            self._collect_checked(item.child(i), out)

    # ============================================================
    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())

        selected_uids = self._selected_camera_uids()
        if len(selected_uids) > 1:
            self._build_bulk_menu(menu, selected_uids)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return

        if item is not None:
            data = item.data(0, Qt.UserRole)
        else:
            data = None

        if data:
            kind, uid = data
            if kind == "camera":
                a1 = QAction("✏ " + t("common.edit"), self)
                a1.triggered.connect(lambda: self._edit_camera(uid))
                menu.addAction(a1)
                menu.addSeparator()
                a2 = QAction("➕ افزودن به گروه…", self)
                a2.triggered.connect(lambda: self._add_camera_to_group(uid))
                menu.addAction(a2)
                groups_of_cam = self.group_manager.groups_containing(uid)
                if groups_of_cam:
                    sub = menu.addMenu("➖ حذف از گروه")
                    sub.setStyleSheet(self._menu_style())
                    for g in groups_of_cam:
                        a_rm = QAction(g.name, self)
                        a_rm.triggered.connect(
                            lambda checked=False, gg=g:
                            self._remove_camera_from_group(gg.uid, uid))
                        sub.addAction(a_rm)
                menu.addSeparator()
                a3 = QAction("🗑 " + t("common.delete"), self)
                a3.triggered.connect(lambda: self._delete_camera_by_uid(uid))
                menu.addAction(a3)

            elif kind == "nvr":
                a1 = QAction("⚙ ویرایش دستگاه", self)
                a1.triggered.connect(lambda: self._edit_nvr(uid))
                menu.addAction(a1)
                a2 = QAction("🔄 کشف مجدد کانال‌ها", self)
                a2.triggered.connect(lambda: self._rediscover_nvr(uid))
                menu.addAction(a2)
                menu.addSeparator()
                a3 = QAction("🗑 حذف دستگاه و کانال‌ها", self)
                a3.triggered.connect(lambda: self._delete_nvr(uid))
                menu.addAction(a3)

            elif kind == "group":
                a1 = QAction("✏ " + t("common.edit"), self)
                a1.triggered.connect(lambda: self._edit_group(uid))
                menu.addAction(a1)
                menu.addSeparator()
                a2 = QAction("🗑 " + t("common.delete"), self)
                a2.triggered.connect(lambda: self._delete_group(uid))
                menu.addAction(a2)

        else:
            a1 = QAction("➕ " + t("cam.btn.bulk"), self)
            a1.triggered.connect(self._on_bulk_add)
            menu.addAction(a1)
            a2 = QAction("➕ " + t("cam.btn.add_camera"), self)
            a2.triggered.connect(self._add_camera)
            menu.addAction(a2)
            a3 = QAction("➕ " + t("cam.btn.add_nvr"), self)
            a3.triggered.connect(self._add_nvr)
            menu.addAction(a3)
            menu.addSeparator()
            a4 = QAction("➕ " + t("grp.btn.new"), self)
            a4.triggered.connect(lambda: self._open_new_group())
            menu.addAction(a4)
            a5 = QAction("🔄 " + t("common.refresh"), self)
            a5.triggered.connect(self._refresh_tree)
            menu.addAction(a5)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ============================================================
    def _build_bulk_menu(self, menu: QMenu, uids: list):
        n = len(uids)
        header = QAction("📌 " + t("bulk.header", n=n), menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        a_del_top = QAction("🗑 " + t("bulk.delete", n=n), menu)
        a_del_top.triggered.connect(lambda: self._bulk_delete(uids))
        menu.addAction(a_del_top)
        menu.addSeparator()

        sub_cont = menu.addMenu("🎬 " + t("bulk.cont"))
        sub_cont.setStyleSheet(self._menu_style())
        a1 = QAction("✅ " + t("bulk.enable"), menu)
        a1.triggered.connect(
            lambda: self._bulk_set_record(uids, "continuous", True))
        sub_cont.addAction(a1)
        a2 = QAction("❌ " + t("bulk.disable"), menu)
        a2.triggered.connect(
            lambda: self._bulk_set_record(uids, "continuous", False))
        sub_cont.addAction(a2)

        sub_mot = menu.addMenu("⚠ " + t("bulk.motion"))
        sub_mot.setStyleSheet(self._menu_style())
        a3 = QAction("✅ " + t("bulk.enable"), menu)
        a3.triggered.connect(
            lambda: self._bulk_set_record(uids, "motion", True))
        sub_mot.addAction(a3)
        a4 = QAction("❌ " + t("bulk.disable"), menu)
        a4.triggered.connect(
            lambda: self._bulk_set_record(uids, "motion", False))
        sub_mot.addAction(a4)

    def _bulk_set_record(self, uids: list, kind: str, value: bool):
        changed = 0
        for uid in uids:
            cam = self.cam_manager.get(uid)
            if cam is None:
                continue
            if kind == "continuous":
                if cam.record_enabled_continuous != value:
                    cam.record_enabled_continuous = value
                    self.cam_manager.update(uid, cam)
                    changed += 1
            elif kind == "motion":
                if cam.record_enabled_motion != value:
                    cam.record_enabled_motion = value
                    self.cam_manager.update(uid, cam)
                    changed += 1
        self._refresh_tree()
        self.cameras_changed.emit()
        try:
            self._auto_apply_to_nvr()
        except Exception:
            pass
        label = t("bulk.cont") if kind == "continuous" else t("bulk.motion")
        state = t("bulk.enable") if value else t("bulk.disable")
        dlg_info(
            self,
            f"{label}: {state} — {changed}/{len(uids)}",
            t("common.info")
        )

    def _bulk_delete(self, uids: list):
        n = len(uids)
        if not dlg_question(
            self,
            f"آیا از حذف {n} دوربین انتخاب‌شده مطمئن هستید؟",
            t("common.confirm")
        ):
            return
        for uid in uids:
            try:
                self.cam_manager.delete(uid)
                try:
                    self.group_manager.remove_camera(uid)
                except Exception:
                    pass
            except Exception:
                pass
        self._refresh_tree()
        self.cameras_changed.emit()
        try:
            self._auto_apply_to_nvr()
        except Exception:
            pass
        dlg_info(self, f"{n} دوربین حذف شد.", t("common.info"))

    # ============================================================
    def _apply_record_to_all_channels(self, nvr, value: bool) -> int:
        n = 0
        for cam in self.cam_manager.all():
            if cam.nvr_uid != nvr.uid:
                continue
            changed = False
            if cam.record_enabled_continuous != value:
                cam.record_enabled_continuous = value
                changed = True
            if cam.record_enabled_motion != value:
                cam.record_enabled_motion = value
                changed = True
            if changed:
                try:
                    self.cam_manager.update(cam.uid, cam)
                    n += 1
                except Exception:
                    pass
        return n

    # ============================================================
    def _add_camera(self):
        dlg = CameraDialog(None, self)
        if dlg.exec() == CameraDialog.Accepted:
            cam = dlg.get_camera()
            self.cam_manager.add(cam)
            settings_manager.append_audit("camera.add", "-",
                {"uid": cam.uid, "name": cam.name})
            self._refresh_tree()
            self.cameras_changed.emit()
            self._auto_apply_to_nvr()

    def _add_nvr(self):
        from ui.dialogs.nvr_dialog import NVRDialog

        dlg = NVRDialog(None, self)
        if dlg.exec() != NVRDialog.Accepted:
            return

        new_nvr = dlg.get_nvr()
        if not new_nvr.name or not new_nvr.ip:
            return

        self.nvr_manager.add(new_nvr)
        settings_manager.append_audit("nvr.add", "-",
            {"uid": new_nvr.uid, "name": new_nvr.name, "ip": new_nvr.ip})

        added = self.nvr_manager.add_channels_as_cameras(
            new_nvr, self.cam_manager, only_enabled=True
        )

        self._refresh_tree()
        self.cameras_changed.emit()

        if added > 0:
            rec_state = ("با ضبط دائم" if new_nvr.record_channels
                         else "بدون ضبط")
            dlg_info(
                self,
                f"دستگاه «{new_nvr.name}» اضافه شد.\n"
                f"{added} کانال به عنوان دوربین اضافه شد ({rec_state}).",
                "افزودن دستگاه"
            )
            self._auto_apply_to_nvr()
        else:
            dlg_info(
                self,
                f"دستگاه «{new_nvr.name}» اضافه شد ولی هیچ کانال جدیدی "
                "اضافه نشد.",
                "افزودن دستگاه"
            )

    def _edit_selected(self):
        data = self._selected_node()
        if not data:
            dlg_info(self, "یک مورد انتخاب کنید.")
            return
        kind, uid = data
        if kind == "camera":
            self._edit_camera(uid)
        elif kind == "nvr":
            self._edit_nvr(uid)
        elif kind == "group":
            self._edit_group(uid)

    def _edit_camera(self, uid: str):
        old_cam = self.cam_manager.get(uid)
        if old_cam is None:
            return
        old_state = self._mediatmx_state(old_cam)
        dlg = CameraDialog(old_cam, self)
        if dlg.exec() == CameraDialog.Accepted:
            updated = dlg.get_camera()
            self.cam_manager.update(uid, updated)
            settings_manager.append_audit("camera.edit", "-", {"uid": uid})
            self._refresh_tree()
            self.cameras_changed.emit()
            if old_state != self._mediatmx_state(updated):
                self._auto_apply_to_nvr()

    def _edit_nvr(self, uid: str):
        from ui.dialogs.nvr_dialog import NVRDialog
        nvr = self.nvr_manager.get(uid)
        if nvr is None:
            return

        original_record = bool(getattr(nvr, "record_channels", False))

        dlg = NVRDialog(nvr, self)
        if dlg.exec() == NVRDialog.Accepted:
            updated = dlg.get_nvr()
            new_record = bool(getattr(updated, "record_channels", False))

            self.nvr_manager.update(uid, updated)
            added = self.nvr_manager.add_channels_as_cameras(
                updated, self.cam_manager, only_enabled=True
            )

            applied = 0
            if new_record != original_record:
                applied = self._apply_record_to_all_channels(updated, new_record)
                print(f"[cameras] record_channels changed "
                      f"{original_record} → {new_record} "
                      f"applied to {applied} camera(s)")

            self._refresh_tree()
            self.cameras_changed.emit()
            self._auto_apply_to_nvr()

            if applied:
                state = "روشن" if new_record else "خاموش"
                dlg_info(self, f"ضبط برای {applied} دوربین «{state}» شد.")
            elif added > 0:
                dlg_info(self, f"{added} کانال جدید هم اضافه شد.")

    def _rediscover_nvr(self, uid: str):
        from ui.dialogs.nvr_dialog import NVRDialog
        nvr = self.nvr_manager.get(uid)
        if nvr is None:
            return
        dlg = NVRDialog(nvr, self)
        if dlg.exec() == NVRDialog.Accepted:
            updated = dlg.get_nvr()
            self.nvr_manager.update(uid, updated)
            added = self.nvr_manager.add_channels_as_cameras(
                updated, self.cam_manager, only_enabled=True
            )
            self._refresh_tree()
            self.cameras_changed.emit()
            if added > 0:
                dlg_info(self, f"{added} کانال جدید اضافه شد.")
                self._auto_apply_to_nvr()
            else:
                dlg_info(self, "هیچ کانال جدیدی نبود.")

    @staticmethod
    def _mediatmx_state(cam):
        try:
            profiles = getattr(cam, "stream_profiles", []) or []
            prof_sig = tuple((p.id, p.url, p.rtsp_path) for p in profiles)
        except Exception:
            prof_sig = ()
        return {
            "enabled": cam.enabled, "ip": cam.ip, "port": cam.port,
            "user": cam.user, "password": cam.password,
            "rtsp_path_main": cam.rtsp_path_main,
            "rtsp_path_sub": cam.rtsp_path_sub,
            "recording_profile_id": getattr(cam, "recording_profile_id", ""),
            "motion_profile_id": getattr(cam, "motion_profile_id", ""),
            "record_enabled_continuous": cam.record_enabled_continuous,
            "record_enabled_motion": cam.record_enabled_motion,
            "record_segment_minutes": cam.record_segment_minutes,
            "record_path_override": cam.record_path_override,
            "profiles": prof_sig,
        }

    def _delete_selected(self):
        uids = self._selected_camera_uids()
        if len(uids) > 1:
            self._bulk_delete(uids)
            return
        data = self._selected_node()
        if not data:
            dlg_info(self, "یک مورد انتخاب کنید.")
            return
        kind, uid = data
        if kind == "camera":
            self._delete_camera_by_uid(uid)
        elif kind == "nvr":
            self._delete_nvr(uid)
        elif kind == "group":
            self._delete_group(uid)

    def _delete_camera_by_uid(self, uid: str):
        c = self.cam_manager.get(uid)
        if c is None:
            return
        if not dlg_question(self, f'حذف دوربین "{c.name}"؟',
                            t("common.confirm")):
            return
        self.cam_manager.delete(uid)
        try:
            self.group_manager.remove_camera(uid)
        except Exception:
            pass
        settings_manager.append_audit("camera.delete", "-", {"uid": uid})
        self._refresh_tree()
        self.cameras_changed.emit()
        self._auto_apply_to_nvr()

    def _delete_nvr(self, uid: str):
        nvr = self.nvr_manager.get(uid)
        if nvr is None:
            return
        if not dlg_question(
            self,
            f'حذف دستگاه "{nvr.name}" و همه‌ی کانال‌هایش؟',
            t("common.confirm")
        ):
            return
        for cam in list(self.cam_manager.all()):
            if cam.nvr_uid == uid:
                self.cam_manager.delete(cam.uid)
                try:
                    self.group_manager.remove_camera(cam.uid)
                except Exception:
                    pass
        self.nvr_manager.delete(uid)
        settings_manager.append_audit("nvr.delete", "-", {"uid": uid})
        self._refresh_tree()
        self.cameras_changed.emit()
        self._auto_apply_to_nvr()

    # ============================================================
    def _manage_groups(self):
        try:
            from ui.dialogs.group_manager_dialog import GroupManagerDialog
            dlg = GroupManagerDialog(self)
            dlg.exec()
            self._refresh_tree()
            self.cameras_changed.emit()
        except Exception as e:
            print(f"[cameras] group manager error: {e}")
            import traceback
            traceback.print_exc()
            dlg_warning(self, f"خطا: {e}")

    def _open_new_group(self):
        try:
            from ui.dialogs.group_dialog import GroupDialog
            dlg = GroupDialog(None, self)
            if dlg.exec() == GroupDialog.Accepted:
                self.group_manager.add(dlg.get_group())
                self._refresh_tree()
                self.cameras_changed.emit()
        except Exception as e:
            dlg_warning(self, f"خطا: {e}")

    def _edit_group(self, uid: str):
        try:
            from ui.dialogs.group_dialog import GroupDialog
            grp = self.group_manager.get(uid)
            if grp is None:
                return
            dlg = GroupDialog(grp, self)
            if dlg.exec() == GroupDialog.Accepted:
                self.group_manager.update(uid, dlg.get_group())
                self._refresh_tree()
                self.cameras_changed.emit()
        except Exception as e:
            dlg_warning(self, f"خطا: {e}")

    def _delete_group(self, uid: str):
        grp = self.group_manager.get(uid)
        if grp is None:
            return
        if not dlg_question(self, f'حذف گروه "{grp.name}"؟',
                            t("common.confirm")):
            return
        self.group_manager.delete(uid)
        self._refresh_tree()
        self.cameras_changed.emit()

    def _add_camera_to_group(self, cam_uid: str):
        gm = self.group_manager
        groups = gm.all()
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())

        if groups:
            for g in groups:
                if cam_uid in g.camera_uids:
                    continue
                a = QAction(f"➕ {g.name}", self)
                a.triggered.connect(
                    lambda checked=False, gg=g:
                    self._append_camera_to_group(gg.uid, cam_uid))
                menu.addAction(a)
            menu.addSeparator()

        a_new = QAction("➕ " + t("grp.btn.new") + "…", self)
        a_new.triggered.connect(
            lambda: self._new_group_with_camera(cam_uid))
        menu.addAction(a_new)

        pos = self.tree.viewport().mapToGlobal(
            self.tree.viewport().rect().center())
        menu.exec(pos)

    def _append_camera_to_group(self, group_uid: str, cam_uid: str):
        grp = self.group_manager.get(group_uid)
        if grp is None:
            return
        if cam_uid not in grp.camera_uids:
            grp.camera_uids.append(cam_uid)
            self.group_manager.update(group_uid, grp)
            self._refresh_tree()

    def _remove_camera_from_group(self, group_uid: str, cam_uid: str):
        grp = self.group_manager.get(group_uid)
        if grp is None:
            return
        grp.camera_uids = [u for u in grp.camera_uids if u != cam_uid]
        self.group_manager.update(group_uid, grp)
        self._refresh_tree()

    def _new_group_with_camera(self, cam_uid: str):
        try:
            from ui.dialogs.group_dialog import GroupDialog
            dlg = GroupDialog(None, self)
            if dlg.exec() == GroupDialog.Accepted:
                grp = dlg.get_group()
                if cam_uid not in grp.camera_uids:
                    grp.camera_uids.append(cam_uid)
                self.group_manager.add(grp)
                self._refresh_tree()
                self.cameras_changed.emit()
        except Exception as e:
            dlg_warning(self, f"خطا: {e}")

    # ============================================================
    def on_show(self):
        self._refresh_tree()
