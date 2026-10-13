# -*- coding: utf-8 -*-
"""K1 VMS — افزودن گروهی دوربین با اسکن IP (Phase 9.1)"""
import subprocess
import shutil
import sys
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QCheckBox,
    QComboBox, QProgressBar, QMessageBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from ui import theme
from core.models import CameraConfig, StreamProfile
from core.camera_manager import CameraManager
import config


BULK_DIALOG_STYLE = f"""
QDialog {{ background: {config.COLOR_BG_DARK}; }}
QLabel {{ color: {config.COLOR_TEXT_PRIMARY}; font-size: 12px;
         background: transparent; }}
QLineEdit, QSpinBox, QComboBox {{
    background: {config.COLOR_BG_CARD}; color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 5px;
    padding: 6px 8px; font-size: 12px; min-height: 20px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {config.COLOR_ACCENT}; }}
QCheckBox {{ color: {config.COLOR_TEXT_PRIMARY}; font-size: 12px;
             spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px;
    background: {config.COLOR_BG_CARD}; border: 1px solid #2c333c;
    border-radius: 3px; }}
QCheckBox::indicator:checked {{ background: {config.COLOR_ACCENT};
    border: 1px solid {config.COLOR_ACCENT}; }}
QTableWidget {{
    background: {config.COLOR_BG_CARD}; color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 5px;
    gridline-color: #2c333c; font-size: 11px;
}}
QHeaderView::section {{
    background: {config.COLOR_BG_PANEL}; color: {config.COLOR_ACCENT};
    padding: 6px; border: none; border-bottom: 1px solid #2c333c;
    font-weight: bold; font-size: 11px;
}}
QPushButton {{
    background: {config.COLOR_BG_CARD}; color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid #2c333c; border-radius: 5px;
    padding: 8px 16px; font-size: 12px; font-weight: bold;
    min-height: 22px;
}}
QPushButton:hover {{ background: #2c333c; }}
QPushButton:disabled {{ color: #6b7280; }}
QProgressBar {{
    background: {config.COLOR_BG_CARD}; border: 1px solid #2c333c;
    border-radius: 4px; text-align: center; color: white;
    font-size: 11px; height: 18px;
}}
QProgressBar::chunk {{ background: {config.COLOR_ACCENT};
    border-radius: 3px; }}
"""


def _find_ffprobe():
    try:
        from core.ffprobe_util import get_ffprobe_exe
        e = get_ffprobe_exe()
        if e:
            return e
    except Exception:
        pass
    p = shutil.which("ffprobe")
    if p:
        return p
    return None


def _spawn_hidden():
    if sys.platform.startswith("win"):
        return {"creationflags": 0x08000000}
    return {}


def _probe_rtsp(ip, port, user, password, timeout=3.0):
    if user:
        url = f"rtsp://{user}:{password}@{ip}:{port}/"
    else:
        url = f"rtsp://{ip}:{port}/"

    ffprobe = _find_ffprobe()
    if not ffprobe:
        return {"ok": False, "error": "ffprobe_not_found"}

    try:
        result = subprocess.run(
            [ffprobe,
             "-v", "error",
             "-rtsp_transport", "tcp",
             "-timeout", str(int(timeout * 1_000_000)),
             "-probesize", "500000",
             "-analyzeduration", "2000000",
             "-i", url,
             "-show_entries", "stream=codec_type,codec_name,width,height",
             "-of", "compact"],
            capture_output=True, text=True,
            timeout=timeout + 2,
            **_spawn_hidden())
        out = (result.stdout or "") + "\n" + (result.stderr or "")
        low = out.lower()

        if "401" in out or "unauthorized" in low:
            return {"ok": False, "error": "auth_failed"}
        if "403" in out or "forbidden" in low:
            return {"ok": False, "error": "auth_forbidden"}

        if "codec_type=video" not in out and "codec_name=" not in out:
            if "timed out" in low or "timeout" in low:
                return {"ok": False, "error": "timeout"}
            if "connection refused" in low:
                return {"ok": False, "error": "refused"}
            return {"ok": False, "error": "no_stream"}

        codecs = []
        for line in out.splitlines():
            if line.startswith("codec_name="):
                codecs.append(line.split("=", 1)[1].strip())
        return {"ok": True, "codecs": codecs, "url": url}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:40]}


def _is_ip_alive(ip, port=554, timeout=0.7):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception:
        return False


class ScanWorker(QThread):
    progress = Signal(int, int, str)
    found = Signal(str, dict)
    finished_all = Signal(int, int)

    def __init__(self, ips, port, user, password, max_threads=30):
        super().__init__()
        self.ips = ips
        self.port = port
        self.user = user
        self.password = password
        self.max_threads = max_threads
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        total = len(self.ips)
        done = 0
        found_count = 0

        def _check(ip):
            if self._cancel:
                return ip, {"ok": False, "error": "cancelled"}
            if not _is_ip_alive(ip, self.port):
                return ip, {"ok": False, "error": "port_closed"}
            return ip, _probe_rtsp(
                ip, self.port, self.user, self.password, timeout=3.5)

        with ThreadPoolExecutor(max_workers=self.max_threads) as ex:
            futures = {ex.submit(_check, ip): ip for ip in self.ips}
            for fut in as_completed(futures):
                if self._cancel:
                    break
                try:
                    ip, result = fut.result()
                except Exception as e:
                    ip = futures[fut]
                    result = {"ok": False, "error": str(e)[:40]}
                done += 1
                self.progress.emit(done, total, ip)
                if result.get("ok"):
                    found_count += 1
                    self.found.emit(ip, result)

        self.finished_all.emit(done, found_count)


class BulkAddCameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن گروهی دوربین")
        self.resize(900, 720)
        self.setStyleSheet(BULK_DIALOG_STYLE)

        self._worker = None
        self._found = {}
        self._cam_manager = CameraManager()
        self._existing_ips = {
            (c.ip or "").strip() for c in self._cam_manager.all()
        }
        self._new_cameras = []

        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        title = QLabel("🔍 اسکن خودکار رنج IP برای یافتن دوربین‌ها")
        title.setStyleSheet(
            f"color: {config.COLOR_ACCENT}; font-size: 14px; "
            f"font-weight: 800; padding-bottom: 4px;")
        v.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        ip_row = QHBoxLayout()
        self.ip_start = QLineEdit("192.168.1.1")
        ip_row.addWidget(QLabel("از:"))
        ip_row.addWidget(self.ip_start, 1)
        ip_row.addWidget(QLabel("تا:"))
        self.ip_end = QLineEdit("192.168.1.254")
        ip_row.addWidget(self.ip_end, 1)
        form.addRow("رنج IP:", ip_row)

        port_row = QHBoxLayout()
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(554)
        port_row.addWidget(QLabel("RTSP:"))
        port_row.addWidget(self.port_spin)
        port_row.addSpacing(20)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 100)
        self.threads_spin.setValue(40)
        port_row.addWidget(QLabel("thread:"))
        port_row.addWidget(self.threads_spin)
        port_row.addStretch(1)
        form.addRow("پورت:", port_row)

        cred_row = QHBoxLayout()
        self.user_edit = QLineEdit("admin")
        cred_row.addWidget(QLabel("یوزر:"))
        cred_row.addWidget(self.user_edit, 1)
        cred_row.addSpacing(10)
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        cred_row.addWidget(QLabel("رمز:"))
        cred_row.addWidget(self.pass_edit, 1)
        form.addRow("ورود:", cred_row)

        defaults_row = QHBoxLayout()
        self.record_chk = QCheckBox("ضبط دائمی")
        self.record_chk.setChecked(True)
        defaults_row.addWidget(self.record_chk)
        self.motion_chk = QCheckBox("تشخیص حرکت")
        defaults_row.addWidget(self.motion_chk)
        self.enabled_chk = QCheckBox("فعال")
        self.enabled_chk.setChecked(True)
        defaults_row.addWidget(self.enabled_chk)
        defaults_row.addStretch(1)
        form.addRow("پیش‌فرض‌ها:", defaults_row)

        prefix_row = QHBoxLayout()
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("مثلاً: street_")
        prefix_row.addWidget(QLabel("پیشوند:"))
        prefix_row.addWidget(self.prefix_edit, 1)
        form.addRow("", prefix_row)

        v.addLayout(form)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        v.addWidget(self.progress_bar)

        self.status_lbl = QLabel(
            f"آماده — {len(self._existing_ips)} IP قبلاً اضافه شده "
            f"(نادیده گرفته می‌شوند)")
        self.status_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_SECONDARY}; font-size: 11px;")
        v.addWidget(self.status_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["", "IP", "کدک‌ها", "وضعیت"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.resizeSection(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        v.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.start_btn = QPushButton("▶ شروع اسکن")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {config.COLOR_ACCENT}; color: white;
                border: none; padding: 10px 20px; font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{ background: {config.COLOR_ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: #2c333c; color: #6b7280; }}
        """)
        self.start_btn.clicked.connect(self._on_start_scan)
        btn_row.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("لغو")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel_scan)
        btn_row.addWidget(self.cancel_btn)

        self.select_all_chk = QCheckBox("انتخاب همه")
        self.select_all_chk.setChecked(True)
        self.select_all_chk.toggled.connect(self._on_select_all)
        btn_row.addWidget(self.select_all_chk)

        btn_row.addStretch(1)

        self.add_btn = QPushButton("➕ افزودن انتخاب‌شده‌ها")
        self.add_btn.setEnabled(False)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {config.COLOR_ACCENT}; color: white;
                border: none; padding: 10px 20px; font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{ background: {config.COLOR_ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: #2c333c; color: #6b7280; }}
        """)
        self.add_btn.clicked.connect(self._on_add_selected)
        btn_row.addWidget(self.add_btn)

        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        v.addLayout(btn_row)

    def _parse_ip(self, s):
        try:
            parts = s.strip().split(".")
            if len(parts) != 4:
                return None
            return tuple(int(p) for p in parts)
        except Exception:
            return None

    def _build_ip_list(self):
        s = self._parse_ip(self.ip_start.text())
        e = self._parse_ip(self.ip_end.text())
        if not s or not e:
            return []
        ips = []
        for a in range(s[0], e[0] + 1):
            for b in range(s[1], e[1] + 1):
                for c in range(s[2], e[2] + 1):
                    for d in range(s[3], e[3] + 1):
                        ips.append(f"{a}.{b}.{c}.{d}")
                        if len(ips) > 4096:
                            return ips
        return ips

    def _on_start_scan(self):
        ips = self._build_ip_list()
        if not ips:
            QMessageBox.warning(self, "خطا", "رنج IP معتبر نیست.")
            return

        ips = [ip for ip in ips if ip not in self._existing_ips]
        if not ips:
            QMessageBox.information(
                self, "تکراری",
                "همه‌ی IPهای این رنج قبلاً اضافه شده‌اند.")
            return

        self.table.setRowCount(0)
        self._found.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(ips))

        self._worker = ScanWorker(
            ips, self.port_spin.value(),
            self.user_edit.text().strip(),
            self.pass_edit.text(),
            max_threads=self.threads_spin.value())
        self._worker.progress.connect(self._on_progress)
        self._worker.found.connect(self._on_found)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.add_btn.setEnabled(False)
        self.status_lbl.setText(f"در حال اسکن {len(ips)} آدرس…")

    def _on_progress(self, cur, total, ip):
        self.progress_bar.setValue(cur)
        self.status_lbl.setText(f"اسکن: {ip}  ({cur}/{total})")

    def _on_found(self, ip, result):
        self._found[ip] = result
        row = self.table.rowCount()
        self.table.insertRow(row)

        w = QTableWidgetItem()
        w.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        w.setCheckState(Qt.Checked)
        self.table.setItem(row, 0, w)

        self.table.setItem(row, 1, QTableWidgetItem(ip))
        codecs = ", ".join(result.get("codecs", [])) or "—"
        self.table.setItem(row, 2, QTableWidgetItem(codecs))

        st = QTableWidgetItem("✅ پیدا شد")
        st.setForeground(QColor(config.COLOR_ACCENT))
        self.table.setItem(row, 3, st)

    def _on_finished(self, done, found_count):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if found_count > 0:
            self.add_btn.setEnabled(True)
            self.status_lbl.setText(
                f"✅ اسکن کامل — {found_count} دوربین با اعتبار صحیح")
        else:
            self.status_lbl.setText(
                "هیچ دوربینی با اعتبار صحیح پیدا نشد.")

    def _on_cancel_scan(self):
        if self._worker is not None:
            self._worker.cancel()
            self.status_lbl.setText("در حال لغو…")

    def _on_select_all(self, checked):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(
                    Qt.Checked if checked else Qt.Unchecked)

    def _on_add_selected(self):
        selected = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.checkState() == Qt.Checked:
                ip_item = self.table.item(r, 1)
                if ip_item:
                    selected.append(ip_item.text())

        if not selected:
            QMessageBox.warning(self, "خطا", "هیچ دوربینی انتخاب نشده.")
            return

        selected = [ip for ip in selected if ip not in self._existing_ips]
        if not selected:
            QMessageBox.information(
                self, "تکراری",
                "همه انتخاب‌شده‌ها قبلاً اضافه شده‌اند.")
            self.accept()
            return

        prefix = self.prefix_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text()
        port = self.port_spin.value()
        record = self.record_chk.isChecked()
        motion = self.motion_chk.isChecked()
        enabled = self.enabled_chk.isChecked()

        added = 0
        for ip in selected:
            try:
                cam = CameraConfig()
                cam.name = f"{prefix}{ip}" if prefix else ip
                cam.ip = ip
                cam.port = port
                cam.user = user
                cam.password = pwd
                cam.enabled = enabled
                cam.record_enabled_continuous = record
                cam.record_enabled_motion = motion

                main_profile = StreamProfile(
                    id="main_auto",
                    name="Main",
                    rtsp_path="/Streaming/Channels/101",
                    url=f"rtsp://{user}:{pwd}@{ip}:{port}/Streaming/Channels/101",
                    roles=["recording", "live_view"],
                    discovered_by="bulk_scan",
                )
                cam.stream_profiles = [main_profile]
                cam.recording_profile_id = "main_auto"
                cam.live_profile_id = "main_auto"
                cam.grid_profile_id = "main_auto"
                try:
                    cam._ensure_profile_defaults()
                except Exception:
                    pass

                self._cam_manager.add(cam)
                self._new_cameras.append(cam)
                self._existing_ips.add(ip)
                added += 1
            except Exception as e:
                print(f"[bulk] add {ip} failed: {e}")

        try:
            self._cam_manager.save()
        except Exception:
            try:
                self._cam_manager.reload()
            except Exception:
                pass

        self.status_lbl.setText(f"✅ {added} دوربین اضافه شد")
        self.accept()

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)