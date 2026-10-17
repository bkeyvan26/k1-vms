# -*- coding: utf-8 -*-
"""K1 VMS — Advanced Settings Tab (Phase 14)

⚠ این تب برای ادمین‌های حرفه‌ای است. تغییر مقادیر می‌تواند
   باعث ناپایداری شود.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox,
    QFormLayout, QSpinBox, QCheckBox, QPushButton, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt
from ui import theme
from core import settings_manager
from core.i18n import t


class WarningBanner(QFrame):
    """بنر هشدار قرمز در بالای تب."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: #4a1a1a;
                border: 2px solid {theme.COLOR_STATUS_ERROR};
                border-radius: 8px;
            }}
        """)
        h = QHBoxLayout(self)
        h.setContentsMargins(14, 12, 14, 12)
        h.setSpacing(10)

        icon = QLabel("⚠")
        icon.setStyleSheet(
            f"color: {theme.COLOR_STATUS_ERROR}; "
            f"font-size: 24px; font-weight: 900; background: transparent;"
        )
        h.addWidget(icon)

        v = QVBoxLayout()
        v.setSpacing(3)
        t1 = QLabel("هشدار — تنظیمات تخصصی")
        t1.setStyleSheet(
            f"color: {theme.COLOR_STATUS_ERROR}; "
            f"font-size: 14px; font-weight: 800; background: transparent;"
        )
        v.addWidget(t1)
        t2 = QLabel(
            "این تنظیمات فقط توسط ادمین‌های با دانش فنی کامل تغییر داده شوند. "
            "تغییر مقادیر نامناسب می‌تواند باعث کندی، پخش ناپایدار، "
            "یا از کار افتادن ضبط شود. "
            "اگر مطمئن نیستید، مقادیر پیش‌فرض را حفظ کنید."
        )
        t2.setWordWrap(True)
        t2.setStyleSheet(
            f"color: #ffb0b0; font-size: 11px; background: transparent;"
        )
        v.addWidget(t2)
        h.addLayout(v, 1)

        self.btn_reset = QPushButton("بازگردانی پیش‌فرض")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setStyleSheet(f"""
            QPushButton {{
                background: {theme.COLOR_STATUS_ERROR};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #c0392b; }}
        """)
        h.addWidget(self.btn_reset)


def _spin_qss():
    return f"""
        QSpinBox {{
            background: {theme.COLOR_BG_DARK};
            color: {theme.COLOR_TEXT_PRIMARY};
            border: 1px solid {theme.COLOR_BORDER};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 12px;
            min-height: 20px;
            min-width: 100px;
        }}
        QSpinBox:focus {{ border: 1px solid {theme.COLOR_ACCENT}; }}
    """


def _group_style():
    return f"""
        QGroupBox {{
            background: {theme.COLOR_BG_CARD};
            border: 1px solid {theme.COLOR_BORDER};
            border-radius: 8px;
            margin-top: 14px;
            padding-top: 12px;
            color: {theme.COLOR_TEXT_PRIMARY};
            font-size: 12px;
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 0 8px;
            color: {theme.COLOR_ACCENT};
            font-size: 12px;
            font-weight: 700;
        }}
    """


def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet(
        f"color: {theme.COLOR_TEXT_PRIMARY}; font-size: 11px;"
    )
    return l


def _hint(text):
    l = QLabel(text)
    l.setWordWrap(True)
    l.setStyleSheet(
        f"color: {theme.COLOR_TEXT_MUTED}; font-size: 10px;"
    )
    return l


class AdvancedSettingsTab(QWidget):
    """تب تنظیمات تخصصی."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spinboxes = {}
        self._checkboxes = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {theme.COLOR_BG_APP};
                border: none;
            }}
        """)
        outer.addWidget(scroll)

        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(14)

        # بنر هشدار
        banner = WarningBanner()
        banner.btn_reset.clicked.connect(self._on_reset)
        v.addWidget(banner)

        # ---- FFmpeg / Playback ----
        gb_ffmpeg = QGroupBox("موتور پخش (FFmpeg / Playback)")
        gb_ffmpeg.setStyleSheet(_group_style())
        gb_ffmpeg.setLayoutDirection(Qt.RightToLeft)
        form = QFormLayout(gb_ffmpeg)
        form.setSpacing(10)
        form.setContentsMargins(14, 18, 14, 14)

        self._add_spin(
            form, "adv.ffmpeg.probesize_kb",
            "Probesize (KB)",
            "مقدار داده‌ای که FFmpeg قبل از پخش آنالیز می‌کند. "
            "کمتر = seek سریع‌تر ولی ریسک تشخیص اشتباه کدک. "
            "پیش‌فرض: 512 — حداقل 128، حداکثر 10240.",
            lo=128, hi=10240, step=64,
        )
        self._add_spin(
            form, "adv.ffmpeg.analyzeduration_ms",
            "Analyzeduration (ms)",
            "مدت زمانی که FFmpeg صبر می‌کند تا استریم پایدار شود. "
            "پیش‌فرض: 300 — حداقل 100، حداکثر 10000.",
            lo=100, hi=10000, step=100,
        )
        self._add_spin(
            form, "adv.ffmpeg.threads",
            "Threads",
            "تعداد threadهای FFmpeg. 0 = خودکار (توصیه می‌شود).",
            lo=0, hi=64, step=1,
        )
        self._add_spin(
            form, "adv.playback.seek_debounce_ms",
            "Seek Debounce (ms)",
            "تأخیر بین seekهای سریع. کمتر = واکنش سریع‌تر ولی بار بیشتر. "
            "پیش‌فرض: 50.",
            lo=0, hi=500, step=10,
        )
        self._add_spin(
            form, "adv.playback.manifest_max_segments",
            "Manifest Max Segments",
            "حداکثر segment در manifest. کمتر = spawn سریع‌تر. "
            "پیش‌فرض: 8.",
            lo=1, hi=64, step=1,
        )
        self._add_spin(
            form, "adv.playback.auto_jump_max_distance_sec",
            "Auto-Jump Max Distance (sec)",
            "حداکثر فاصله برای پرش خودکار. پیش‌فرض: 120.",
            lo=0, hi=3600, step=10,
        )
        self._add_spin(
            form, "adv.playback.gap_tolerance_sec",
            "Gap Tolerance (sec)",
            "گپ‌های کمتر از این مقدار نادیده گرفته می‌شوند. پیش‌فرض: 8.",
            lo=1, hi=120, step=1,
        )
        self._add_spin(
            form, "adv.playback.max_source_fps",
            "Max Source FPS",
            "حداکثر FPS مبدأ. پیش‌فرض: 120.",
            lo=30, hi=240, step=10,
        )

        v.addWidget(gb_ffmpeg)

        # ---- Indexer ----
        gb_idx = QGroupBox("ایندکسر ضبط (Indexer)")
        gb_idx.setStyleSheet(_group_style())
        gb_idx.setLayoutDirection(Qt.RightToLeft)
        form = QFormLayout(gb_idx)
        form.setSpacing(10)
        form.setContentsMargins(14, 18, 14, 14)

        self._add_spin(
            form, "adv.indexer.contiguous_tolerance_sec",
            "Contiguous Tolerance (sec)",
            "فاصله‌های کمتر از این مقدار به عنوان gap نمایش داده نمی‌شوند. "
            "پیش‌فرض: 20.",
            lo=1, hi=300, step=1,
        )
        self._add_spin(
            form, "adv.indexer.finalize_threshold_sec",
            "Finalize Threshold (sec)",
            "فایل‌های جدیدتر از این مقدار به عنوان در حال ضبط در نظر گرفته می‌شوند. "
            "پیش‌فرض: 30.",
            lo=5, hi=300, step=5,
        )
        self._add_spin(
            form, "adv.indexer.probe_cache_hours",
            "Probe Cache (hours)",
            "مدت کش کردن نتایج probe. پیش‌فرض: 168 (۷ روز).",
            lo=1, hi=720, step=1,
        )
        v.addWidget(gb_idx)

        # ---- Live ----
        gb_live = QGroupBox("نمای زنده (Live)")
        gb_live.setStyleSheet(_group_style())
        gb_live.setLayoutDirection(Qt.RightToLeft)
        form = QFormLayout(gb_live)
        form.setSpacing(10)
        form.setContentsMargins(14, 18, 14, 14)

        self._add_spin(
            form, "adv.live.grid_budget",
            "Grid Budget (readers)",
            "حداکثر reader همزمان در گرید. پیش‌فرض: 16.",
            lo=1, hi=128, step=1,
        )
        self._add_spin(
            form, "adv.live.stagger_ms_min",
            "Stagger Min (ms)",
            "حداقل تأخیر بین راه‌اندازی readerها. پیش‌فرض: 20.",
            lo=0, hi=500, step=5,
        )
        self._add_spin(
            form, "adv.live.stagger_ms_max",
            "Stagger Max (ms)",
            "حداکثر تأخیر بین راه‌اندازی readerها. پیش‌فرض: 60.",
            lo=0, hi=1000, step=5,
        )
        v.addWidget(gb_live)

        # ---- Storage ----
        gb_st = QGroupBox("حافظه (Storage)")
        gb_st.setStyleSheet(_group_style())
        gb_st.setLayoutDirection(Qt.RightToLeft)
        form = QFormLayout(gb_st)
        form.setSpacing(10)
        form.setContentsMargins(14, 18, 14, 14)

        self._add_spin(
            form, "adv.storage.keep_recent_hours",
            "Keep Recent (hours)",
            "فایل‌های جدیدتر از این مقدار هرگز حذف نمی‌شوند. پیش‌فرض: 2.",
            lo=0, hi=168, step=1,
        )
        v.addWidget(gb_st)

        # ---- Debug ----
        gb_dbg = QGroupBox("اشکال‌زدایی (Debug)")
        gb_dbg.setStyleSheet(_group_style())
        gb_dbg.setLayoutDirection(Qt.RightToLeft)
        form = QFormLayout(gb_dbg)
        form.setSpacing(10)
        form.setContentsMargins(14, 18, 14, 14)

        self._add_check(
            form, "adv.debug.verbose_trace",
            "Verbose Trace",
            "نمایش لاگ‌های SEEK/PLAY با جزئیات کامل."
        )
        self._add_check(
            form, "adv.debug.log_ffmpeg_cmd",
            "Log FFmpeg Command",
            "نمایش فرمان کامل FFmpeg در کنسول هنگام هر spawn."
        )
        v.addWidget(gb_dbg)

        v.addStretch(1)

        scroll.setWidget(inner)

    # ============================================================
    def _add_spin(self, form, key, label, hint, lo, hi, step):
        sp = QSpinBox()
        sp.setRange(lo, hi)
        sp.setSingleStep(step)
        sp.setStyleSheet(_spin_qss())

        # خواندن مقدار فعلی
        try:
            from core.advanced_settings import DEFAULTS
            default = DEFAULTS.get(key, lo)
        except Exception:
            default = lo

        try:
            from core.advanced_settings import get
            val = get(key, default)
            sp.setValue(int(val))
        except Exception:
            sp.setValue(default)

        wrap = QWidget()
        wv = QVBoxLayout(wrap)
        wv.setContentsMargins(0, 0, 0, 0)
        wv.setSpacing(2)
        wv.addWidget(sp)
        wv.addWidget(_hint(hint))
        form.addRow(_lbl(label), wrap)
        self._spinboxes[key] = sp

    def _add_check(self, form, key, label, hint):
        cb = QCheckBox()
        cb.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.COLOR_TEXT_PRIMARY};
                font-size: 12px;
            }}
        """)
        try:
            from core.advanced_settings import get, DEFAULTS
            cb.setChecked(bool(get(key, DEFAULTS.get(key, False))))
        except Exception:
            pass

        wrap = QWidget()
        wv = QVBoxLayout(wrap)
        wv.setContentsMargins(0, 0, 0, 0)
        wv.setSpacing(2)
        wv.addWidget(cb)
        wv.addWidget(_hint(hint))
        form.addRow(_lbl(label), wrap)
        self._checkboxes[key] = cb

    # ============================================================
    def _on_reset(self):
        r = QMessageBox.question(
            self, "بازگردانی پیش‌فرض",
            "همه تنظیمات تخصصی به مقادیر پیش‌فرض برگردند؟",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        try:
            from core.advanced_settings import DEFAULTS
            from core import settings_manager
            s = settings_manager.load_settings()
            for k, v in DEFAULTS.items():
                attr = k.replace(".", "_")
                setattr(s, attr, v)
            settings_manager.save_settings(s)

            # آپدیت UI
            for k, sp in self._spinboxes.items():
                sp.setValue(int(DEFAULTS.get(k, sp.value())))
            for k, cb in self._checkboxes.items():
                cb.setChecked(bool(DEFAULTS.get(k, False)))

            QMessageBox.information(
                self, "انجام شد",
                "همه مقادیر به پیش‌فرض برگشتند.\n"
                "برای اعمال، برخی صفحات باید دوباره باز شوند."
            )
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    # ============================================================
def save(self, s=None):
    """ذخیره همه مقادیر در settings.json."""
    try:
        from core import settings_manager
        if s is None:
            s = settings_manager.load_settings()
        for k, sp in self._spinboxes.items():
            attr = k.replace(".", "_")
            setattr(s, attr, int(sp.value()))
        for k, cb in self._checkboxes.items():
            attr = k.replace(".", "_")
            setattr(s, attr, bool(cb.isChecked()))
        # ★ نکته: این‌جا save_settings صدا نزن — settings_page خودش می‌زند
        print("[advanced-settings] staged for save")
    except Exception as e:
        print(f"[advanced-settings] save failed: {e}")
