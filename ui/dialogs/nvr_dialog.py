# -*- coding: utf-8 -*-
"""K1 VMS — پنجره افزودن/ویرایش دستگاه ضبط (NVR)"""
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QPushButton, QDialogButtonBox, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QProgressDialog, QMessageBox,
    QAbstractItemView, QCheckBox, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QThread

from core.models import NVRDevice, NVRChannel
from core.nvr_discovery import NVRDiscoveryWorker
from ui.rtl_helper import set_no_rtl
import config


DIALOG_STYLE = f"""
QDialog {{ background-color: {config.COLOR_BG_DARK}; }}
QLabel {{ color: {config.COLOR_TEXT_PRIMARY}; background: transparent;
         font-size: 12px; }}
QLineEdit, QSpinBox, QComboBox {{
    background: {config.COLOR_BG_CARD}; color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 5px;
    padding: 6px 8px; font-size: 12px; min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {config.COLOR_ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {config.COLOR_BG_CARD}; color: {config.COLOR_TEXT_PRIMARY};
    selection-background-color: {config.COLOR_ACCENT};
    border: 1px solid #2c333c; outline: none; }}

QGroupBox {{ color: {config.COLOR_TEXT_PRIMARY}; font-weight: bold;
    font-size: 13px; border: 1px solid #2c333c; border-radius: 6px;
    margin-top: 16px; padding-top: 18px; }}
QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top right;
    right: 16px; padding: 0 10px 0 10px;
    color: {config.COLOR_ACCENT}; }}

QCheckBox {{
    color: {config.COLOR_TEXT_PRIMARY};
    font-size: 13px; font-weight: bold;
    spacing: 10px; padding: 6px 4px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 20px; height: 20px;
    border: 2px solid #6b7280; border-radius: 4px;
    background: #0d0d0d;
}}
QCheckBox::indicator:hover {{ border-color: {config.COLOR_ACCENT}; }}
QCheckBox::indicator:checked {{
    background: {config.COLOR_ACCENT};
    border-color: {config.COLOR_ACCENT};
}}

QListWidget {{ background: {config.COLOR_BG_CARD};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 5px;
    padding: 4px; font-size: 12px; }}
QListWidget::item {{ padding: 8px 10px; border-radius: 4px; }}
QListWidget::item:hover {{ background: #2c333c; }}
QListWidget::item:selected {{ background: {config.COLOR_ACCENT};
    color: white; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {config.COLOR_BG_DARK};
    width: 10px; border-radius: 5px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #3a4550; min-height: 30px; border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: {config.COLOR_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0; background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""


def _sanitize_folder_name(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", text).strip("_-")[:40]


class NVRDialog(QDialog):
    def __init__(self, nvr: NVRDevice = None, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self.is_new = nvr is None
        self.nvr = nvr if nvr else NVRDevice()
        self._original_record = bool(
            getattr(self.nvr, "record_channels", False))

        self._detect_thread = None
        self._detect_worker = None
        self._detect_progress = None

        self.setWindowTitle(
            "افزودن دستگاه ضبط" if self.is_new
            else f"ویرایش دستگاه ضبط: {self.nvr.name}"
        )
        # ★ ارتفاع کمتر — به اندازه صفحه‌های معمولی
        self.resize(820, 760)
        self.setMinimumSize(700, 550)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()
        self._populate_channels()

    # ============================================================
    def _build_ui(self):
        # ★ ساختار کلی: scroll area بالا + دکمه‌ها پایین (ثابت)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---------- Scroll area ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        v = QVBoxLayout(body)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(10)

        # ---------- اطلاعات اتصال ----------
        grp = QGroupBox("اطلاعات اتصال")
        form = QFormLayout(grp)
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)

        self.name_edit = QLineEdit(self.nvr.name)
        self.name_edit.setPlaceholderText(
            "مثلاً: دستگاه طبقه اول")
        form.addRow("نام دستگاه:", self.name_edit)

        self.folder_edit = QLineEdit(
            getattr(self.nvr, "record_folder_name", "") or "")
        self.folder_edit.setPlaceholderText(
            "مثلاً: parkings  یا negahbani")
        self.folder_edit.setMaxLength(40)
        set_no_rtl(self.folder_edit)
        self.folder_edit.textChanged.connect(self._on_folder_changed)
        form.addRow("نام پوشه ذخیره:", self.folder_edit)

        self.folder_hint = QLabel(
            "فقط حروف انگلیسی، اعداد، _ و - مجاز است."
        )
        self.folder_hint.setWordWrap(True)
        self.folder_hint.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 10px; "
            f"background: {config.COLOR_BG_CARD}; padding: 6px 8px; "
            f"border-radius: 4px; border-left: 3px solid {config.COLOR_ACCENT};"
        )
        form.addRow("", self.folder_hint)

        # ---------- چک‌باکس ضبط ----------
        record_box = QFrame()
        record_box.setStyleSheet(
            f"QFrame {{ background: {config.COLOR_BG_CARD}; "
            f"border: 1px solid #2c333c; border-radius: 6px; }}"
        )
        rb_lay = QVBoxLayout(record_box)
        rb_lay.setContentsMargins(12, 8, 12, 8)
        rb_lay.setSpacing(2)

        self.record_channels_cb = QCheckBox(
            "تصاویر همه‌ی دوربین‌های این دستگاه ضبط شوند؟"
        )
        self.record_channels_cb.setChecked(
            bool(getattr(self.nvr, "record_channels", False))
        )
        self.record_channels_cb.setToolTip(
            "✅ تیک بزنید: همه‌ی دوربین‌های این دستگاه پیوسته ضبط می‌شوند.\n"
            "❌ تیک نزنید (پیش‌فرض): فقط پخش زنده — ضبط نمی‌شوند.\n\n"
            "بعداً می‌توانید در تنظیمات هر دوربین، ضبط آن را جداگانه "
            "روشن/خاموش کنید."
        )
        rb_lay.addWidget(self.record_channels_cb)

        hint_rec = QLabel(
            "پیش‌فرض: خاموش — بعداً برای هر دوربین جداگانه قابل تغییر است."
        )
        hint_rec.setWordWrap(True)
        hint_rec.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 10px; "
            f"padding: 0 4px; background: transparent;"
        )
        rb_lay.addWidget(hint_rec)
        form.addRow("ضبط تصاویر:", record_box)

        # ---------- برند ----------
        self.brand_combo = QComboBox()
        for k, label in [
            ("auto", "تشخیص خودکار"),
            ("hikvision", "هایک‌ویژن"),
            ("dahua", "داهوا"),
            ("uniview", "یونی‌ویو"),
            ("axis", "اکسیس"),
            ("amcrest", "آمکرست"),
            ("kdt", "کِی‌دی‌تی"),
        ]:
            self.brand_combo.addItem(label, k)
        idx = self.brand_combo.findData(self.nvr.brand or "auto")
        if idx >= 0:
            self.brand_combo.setCurrentIndex(idx)
        form.addRow("برند سازنده:", self.brand_combo)

        self.ip_edit = QLineEdit(self.nvr.ip)
        self.ip_edit.setPlaceholderText("192.168.1.100")
        set_no_rtl(self.ip_edit)
        form.addRow("آدرس IP:", self.ip_edit)

        port_row = QHBoxLayout()
        port_row.setSpacing(6)
        self.rtsp_port_spin = QSpinBox()
        self.rtsp_port_spin.setRange(1, 65535)
        self.rtsp_port_spin.setValue(self.nvr.rtsp_port or 554)
        set_no_rtl(self.rtsp_port_spin)
        self.rtsp_port_spin.setFixedWidth(90)
        port_row.addWidget(QLabel("RTSP:"))
        port_row.addWidget(self.rtsp_port_spin)
        self.onvif_port_spin = QSpinBox()
        self.onvif_port_spin.setRange(1, 65535)
        self.onvif_port_spin.setValue(self.nvr.onvif_port or 80)
        set_no_rtl(self.onvif_port_spin)
        self.onvif_port_spin.setFixedWidth(90)
        port_row.addWidget(QLabel("ONVIF:"))
        port_row.addWidget(self.onvif_port_spin)
        port_row.addStretch(1)
        form.addRow("درگاه اتصال:", port_row)

        port_hint = QLabel(
            "معمولاً نیازی به تغییر مقادیر پیش‌فرض نیست."
        )
        port_hint.setWordWrap(True)
        port_hint.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 10px;"
        )
        form.addRow("", port_hint)

        self.user_edit = QLineEdit(self.nvr.user)
        set_no_rtl(self.user_edit)
        form.addRow("نام کاربری:", self.user_edit)

        self.pass_edit = QLineEdit(self.nvr.password)
        self.pass_edit.setEchoMode(QLineEdit.Password)
        set_no_rtl(self.pass_edit)
        form.addRow("رمز عبور:", self.pass_edit)

        v.addWidget(grp)

        # ---------- الگوی دستی (اختیاری) ----------
        grp_manual = QGroupBox(
            "الگوی آدرس دستی (فقط برای دستگاه‌های قدیمی‌تر)"
        )
        mv = QVBoxLayout(grp_manual)
        mv.setSpacing(6)
        mv.setContentsMargins(14, 22, 14, 14)

        hint_manual = QLabel(
            "اگر دستگاه شما از جستجوی خودکار پشتیبانی نمی‌کند، "
            "آدرس دقیق را اینجا وارد کنید. در غیر این‌صورت خالی بگذارید."
        )
        hint_manual.setWordWrap(True)
        hint_manual.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 10px; "
            f"background: {config.COLOR_BG_CARD}; padding: 6px 8px; "
            f"border-radius: 4px;"
        )
        mv.addWidget(hint_manual)

        self.custom_main_edit = QLineEdit()
        self.custom_main_edit.setPlaceholderText(
            "rtsp://{user}:{pwd}@{ip}:{port}/mode=real&idc={ch}&ids=1"
        )
        set_no_rtl(self.custom_main_edit)

        self.custom_sub_edit = QLineEdit()
        self.custom_sub_edit.setPlaceholderText(
            "rtsp://{user}:{pwd}@{ip}:{port}/mode=real&idc={ch}&ids=2"
        )
        set_no_rtl(self.custom_sub_edit)

        mf = QFormLayout()
        mf.setSpacing(6)
        mf.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mf.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        mf.addRow("تصویر اصلی:", self.custom_main_edit)
        mf.addRow("تصویر کم‌حجم:", self.custom_sub_edit)
        mv.addLayout(mf)

        hint_m = QLabel(
            "متغیرها: {user} کاربر — {pwd} رمز — {ip} آدرس — "
            "{port} درگاه — {ch} شماره — {stream} نوع"
        )
        hint_m.setWordWrap(True)
        hint_m.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 10px;"
        )
        mv.addWidget(hint_m)
        v.addWidget(grp_manual)

        # ---------- دکمه جستجو ----------
        self.discover_btn = QPushButton("جستجوی خودکار دوربین‌ها")
        self.discover_btn.setMinimumHeight(40)
        self.discover_btn.setCursor(Qt.PointingHandCursor)
        self.discover_btn.setStyleSheet(f"""
            QPushButton {{ background: {config.COLOR_ACCENT}; color: white;
                border: none; border-radius: 6px; font-size: 13px;
                font-weight: bold; padding: 8px 16px; }}
            QPushButton:hover {{ background: {config.COLOR_ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: #2c333c; color: #6b7280; }}
        """)
        self.discover_btn.clicked.connect(self._on_discover)
        v.addWidget(self.discover_btn)

        # ---------- لیست دوربین‌ها ----------
        info = QLabel("دوربین‌های پیدا شده — موارد دلخواه را تیک بزنید:")
        info.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 11px;"
        )
        v.addWidget(info)

        self.channels_list = QListWidget()
        self.channels_list.setMinimumHeight(160)
        self.channels_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.channels_list.itemChanged.connect(lambda _: self._update_count())
        v.addWidget(self.channels_list)

        sel_row = QHBoxLayout()
        sel_row.setSpacing(6)
        sel_all = QPushButton("انتخاب همه")
        sel_all.clicked.connect(lambda: self._set_all(True))
        sel_row.addWidget(sel_all)
        desel_all = QPushButton("حذف انتخاب همه")
        desel_all.clicked.connect(lambda: self._set_all(False))
        sel_row.addWidget(desel_all)
        sel_row.addStretch(1)
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 11px;"
        )
        sel_row.addWidget(self.count_lbl)
        v.addLayout(sel_row)

        v.addStretch(1)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        # ---------- دکمه‌های ثابت پایین ----------
        btn_container = QFrame()
        btn_container.setStyleSheet(
            f"QFrame {{ background: {config.COLOR_BG_DARK}; "
            f"border-top: 1px solid #2c333c; }}"
        )
        btn_lay = QHBoxLayout(btn_container)
        btn_lay.setContentsMargins(20, 10, 20, 12)
        btn_lay.setSpacing(10)

        buttons = QDialogButtonBox()
        save = buttons.addButton("ذخیره", QDialogButtonBox.AcceptRole)
        save.setStyleSheet(f"""
            QPushButton {{ background: {config.COLOR_ACCENT}; color: white;
                padding: 8px 24px; border-radius: 5px; font-weight: bold;
                border: none; min-width: 90px; font-size: 12px; }}
            QPushButton:hover {{ background: {config.COLOR_ACCENT_HOVER}; }}
        """)
        cancel = buttons.addButton("انصراف", QDialogButtonBox.RejectRole)
        cancel.setStyleSheet(f"""
            QPushButton {{ background: {config.COLOR_BG_CARD};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid #2c333c; border-radius: 5px;
                padding: 8px 24px; font-size: 12px; font-weight: bold;
                min-width: 90px; }}
            QPushButton:hover {{ background: #2c333c; }}
        """)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        btn_lay.addStretch(1)
        btn_lay.addWidget(buttons)
        outer.addWidget(btn_container)

    # ============================================================
    def _on_folder_changed(self, text):
        clean = _sanitize_folder_name(text)
        if clean != text:
            cur_pos = self.folder_edit.cursorPosition()
            self.folder_edit.blockSignals(True)
            self.folder_edit.setText(clean)
            self.folder_edit.setCursorPosition(min(cur_pos, len(clean)))
            self.folder_edit.blockSignals(False)

        if clean:
            preview = (f"مسیر ذخیره: continuous/{clean}/ch_NN/2026-10-10/"
                       "13-14-47.ts")
        else:
            preview = ("مسیر ذخیره: continuous/nvr_{{uid}}/ch_NN/  "
                       "(اگر خالی بماند، خودکار ساخته می‌شود)")
        self.folder_hint.setText(
            "فقط حروف انگلیسی، اعداد، _ و - مجاز است.\n" + preview
        )

    def _populate_channels(self):
        self.channels_list.blockSignals(True)
        self.channels_list.clear()
        for ch in self.nvr.channels:
            self._add_channel_item(ch)
        self.channels_list.blockSignals(False)
        self._update_count()

    def _add_channel_item(self, ch: NVRChannel):
        res = ch.resolution or "—"
        codec = ch.codec or "—"
        has_sub = bool(ch.rtsp_url_sub)
        tag = " (اصلی+فرعی)" if has_sub else " (اصلی)"
        text = (f"  دوربین {ch.channel_id:>2}   {ch.name}   —   "
                f"{res}  {codec}{tag}")
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, ch.to_dict())
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if ch.enabled else Qt.Unchecked)
        self.channels_list.addItem(item)

    def _set_all(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        self.channels_list.blockSignals(True)
        for i in range(self.channels_list.count()):
            self.channels_list.item(i).setCheckState(state)
        self.channels_list.blockSignals(False)
        self._update_count()

    def _update_count(self):
        total = self.channels_list.count()
        selected = sum(
            1 for i in range(total)
            if self.channels_list.item(i).checkState() == Qt.Checked
        )
        self.count_lbl.setText(f"{selected} از {total} انتخاب شده")

    # ============================================================
    def _on_save(self):
        name = self.name_edit.text().strip()
        ip = self.ip_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام دستگاه را وارد کنید.")
            return
        if not ip:
            QMessageBox.warning(self, "خطا", "آدرس IP را وارد کنید.")
            return

        folder = _sanitize_folder_name(self.folder_edit.text())

        self.nvr.name = name
        self.nvr.record_folder_name = folder
        self.nvr.brand = self.brand_combo.currentData() or "auto"
        self.nvr.ip = ip
        self.nvr.rtsp_port = self.rtsp_port_spin.value()
        self.nvr.onvif_port = self.onvif_port_spin.value()
        self.nvr.user = self.user_edit.text().strip()
        self.nvr.password = self.pass_edit.text()
        self.nvr.record_channels = self.record_channels_cb.isChecked()

        selected = []
        for i in range(self.channels_list.count()):
            item = self.channels_list.item(i)
            d = item.data(Qt.UserRole) or {}
            d["enabled"] = (item.checkState() == Qt.Checked)
            selected.append(NVRChannel.from_dict(d))
        self.nvr.channels = selected
        self.accept()

    def get_nvr(self) -> NVRDevice:
        return self.nvr

    # ============================================================
    # جستجوی خودکار
    # ============================================================
    def _on_discover(self):
        if self._detect_worker is not None:
            QMessageBox.information(
                self, "در حال اجرا",
                "جستجوی خودکار در حال انجام است."
            )
            return

        ip = self.ip_edit.text().strip()
        user = self.user_edit.text().strip()
        password = self.pass_edit.text()
        if not ip or not user:
            QMessageBox.warning(
                self, "خطا", "آدرس IP و نام کاربری را وارد کنید."
            )
            return

        custom_main = self.custom_main_edit.text().strip()
        custom_sub = self.custom_sub_edit.text().strip()

        temp = NVRDevice()
        temp.ip = ip
        temp.user = user
        temp.password = password
        temp.rtsp_port = self.rtsp_port_spin.value()
        temp.onvif_port = self.onvif_port_spin.value()
        temp.brand = self.brand_combo.currentData() or "auto"

        prog = QProgressDialog("در حال جستجو…", "لغو", 0, 100, self)
        prog.setWindowTitle("جستجوی خودکار")
        prog.setWindowModality(Qt.WindowModal)
        prog.setMinimumDuration(0)
        prog.setAutoClose(False)
        prog.setAutoReset(False)
        prog.setStyleSheet(DIALOG_STYLE)
        prog.show()

        thread = QThread(self)
        worker = NVRDiscoveryWorker(temp,
                                    custom_main=custom_main,
                                    custom_sub=custom_sub)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log.connect(lambda m: print(m))
        worker.progress.connect(self._on_progress)
        worker.finished_ok.connect(self._on_ok)
        worker.finished_fail.connect(self._on_fail)
        worker.cancelled.connect(self._on_cancelled)
        prog.canceled.connect(worker.cancel)

        self._detect_thread = thread
        self._detect_worker = worker
        self._detect_progress = prog
        self.discover_btn.setEnabled(False)
        thread.start()

    def _on_progress(self, cur, total, msg):
        p = self._detect_progress
        if not p:
            return
        try:
            p.setMaximum(max(total, 1))
            p.setValue(cur)
            if msg:
                p.setLabelText(msg)
        except Exception:
            pass

    def _on_ok(self, payload):
        self._cleanup()
        self.channels_list.blockSignals(True)
        self.channels_list.clear()
        for d in (payload or []):
            ch = NVRChannel.from_dict(d)
            ch.enabled = True
            self._add_channel_item(ch)
        self.channels_list.blockSignals(False)
        self._update_count()
        n = len(payload or [])
        QMessageBox.information(
            self, "موفق",
            f"{n} دوربین پیدا شد.\n"
            "موارد دلخواه را تیک بزنید و ذخیره کنید."
        )

    def _on_fail(self, msg):
        self._cleanup()
        QMessageBox.warning(self, "جستجو ناموفق", str(msg))

    def _on_cancelled(self):
        self._cleanup()

    def _cleanup(self):
        prog = self._detect_progress
        thread = self._detect_thread
        worker = self._detect_worker
        self._detect_progress = None
        self._detect_thread = None
        self._detect_worker = None

        if prog:
            try: prog.reset()
            except Exception: pass
            try: prog.close()
            except Exception: pass
            try: prog.deleteLater()
            except Exception: pass
        if worker:
            for sig in ("log", "progress", "finished_ok",
                        "finished_fail", "cancelled"):
                try: getattr(worker, sig).disconnect()
                except Exception: pass
        if thread:
            try:
                thread.quit()
                if not thread.wait(3000):
                    thread.terminate()
                    thread.wait(500)
            except Exception: pass
            try: thread.deleteLater()
            except Exception: pass
        try: self.discover_btn.setEnabled(True)
        except Exception: pass

    def closeEvent(self, event):
        if self._detect_worker is not None:
            try: self._detect_worker.cancel()
            except Exception: pass
            self._cleanup()
        super().closeEvent(event)
