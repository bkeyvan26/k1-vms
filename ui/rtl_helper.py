"""
ui/rtl_helper.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
فقط متن ویجت‌های متنی را راست‌به‌چپ می‌کند.
ویجت‌هایی که با setProperty("no_rtl", True) علامت خورده‌اند،
دست‌نخورده (LTR) باقی می‌مانند — مثل فیلدهای URL، IP، Port.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QGroupBox, QCheckBox, QRadioButton, QToolButton,
    QSpinBox, QDoubleSpinBox,
    QListWidget, QTreeWidget, QTableWidget,
    QDialog, QMessageBox, QInputDialog, QProgressDialog,
    QDialogButtonBox,
)

_RTL_TYPES = (
    QLabel, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QGroupBox, QCheckBox, QRadioButton, QToolButton,
    QSpinBox, QDoubleSpinBox,
    QListWidget, QTreeWidget, QTableWidget,
    QDialog, QMessageBox, QInputDialog, QProgressDialog,
    QDialogButtonBox,
)


class _RTLFilter(QObject):
    def eventFilter(self, obj, event):
        try:
            et = event.type()
            if et in (QEvent.Polish, QEvent.Show, QEvent.LayoutRequest):
                if isinstance(obj, _RTL_TYPES):
                    # ★ اگر ویجت درخواست LTR کرده، دست نزن
                    try:
                        if bool(obj.property("no_rtl")):
                            return False
                    except RuntimeError:
                        return False
                    try:
                        if obj.layoutDirection() != Qt.RightToLeft:
                            obj.setLayoutDirection(Qt.RightToLeft)
                    except RuntimeError:
                        pass
        except Exception:
            pass
        return False


_filter_instance = None


def install_rtl_text_filter(app: QApplication) -> None:
    global _filter_instance
    if _filter_instance is not None:
        return
    _filter_instance = _RTLFilter()
    app.installEventFilter(_filter_instance)


def set_no_rtl(widget) -> None:
    """برای فیلدهای فنی (URL/IP/Port/User/Pass)."""
    try:
        widget.setProperty("no_rtl", True)
        widget.setLayoutDirection(Qt.LeftToRight)
        widget.setAlignment(Qt.AlignLeft)
    except Exception:
        pass