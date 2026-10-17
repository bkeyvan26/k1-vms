# -*- coding: utf-8 -*-
"""K1 VMS — Live grid (Phase 9.1: no-rebuild layout)"""
import json
import math
import numpy as np
from PySide6.QtWidgets import QWidget, QGridLayout, QFrame, QApplication
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QMimeData, QTimer
from PySide6.QtGui import (
    QImage, QPainter, QColor, QFont, QPen, QDrag, QPixmap, QPolygon
)
from ui import theme
from core.i18n import t


MIME_CAMERA = "application/x-k1vms-camera"

_SP_OVERLAY      = QColor(8, 8, 12, 170)
_SP_TRACK        = QColor(48, 54, 66, 220)
_SP_ARC          = QColor(22, 160, 133)
_SP_ARC_HI       = QColor(26, 188, 156)
_SP_TEXT         = QColor(190, 200, 215)
_SP_TEXT_SHADOW  = QColor(0, 0, 0, 180)
_SP_FONT         = QFont("Sans", 8)

_RC_BG           = QColor(24, 34, 48, 230)
_RC_BG_HOVER     = QColor(22, 160, 133, 245)
_RC_BORDER       = QColor(60, 80, 100)
_RC_BORDER_HOVER = QColor(46, 204, 113)
_RC_TEXT         = QColor(235, 245, 255)

_RC_FONT = QFont("Tahoma", 9)
_RC_FONT.setBold(True)


def _uniform(n):
    return [(r, c, 1, 1) for r in range(n) for c in range(n)]


LAYOUTS = [
    {"key": "1x1", "name": "1 × 1", "rows": 1, "cols": 1, "cells": _uniform(1)},
    {"key": "2x2", "name": "2 × 2", "rows": 2, "cols": 2, "cells": _uniform(2)},
    {"key": "3x3", "name": "3 × 3", "rows": 3, "cols": 3, "cells": _uniform(3)},
    {"key": "4x4", "name": "4 × 4", "rows": 4, "cols": 4, "cells": _uniform(4)},
    {"key": "5x5", "name": "5 × 5", "rows": 5, "cols": 5, "cells": _uniform(5)},
    {"key": "6x6", "name": "6 × 6", "rows": 6, "cols": 6, "cells": _uniform(6)},
    {"key": "7x7", "name": "7 × 7", "rows": 7, "cols": 7, "cells": _uniform(7)},
    {"key": "8x8", "name": "8 × 8", "rows": 8, "cols": 8, "cells": _uniform(8)},
    {"key": "1+3", "name": "1 + 3 (Hero)", "rows": 3, "cols": 3,
     "cells": [(0, 0, 2, 2), (0, 2, 1, 1), (1, 2, 1, 1), (2, 0, 1, 3)]},
    {"key": "1+4", "name": "1 + 4 (Focus)", "rows": 2, "cols": 4,
     "cells": [(0, 0, 2, 2), (0, 2, 1, 1), (0, 3, 1, 1),
               (1, 2, 1, 1), (1, 3, 1, 1)]},
    {"key": "1+5", "name": "1 + 5 (Focus)", "rows": 3, "cols": 3,
     "cells": [(0, 0, 2, 2), (0, 2, 1, 1), (1, 2, 1, 1),
               (2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)]},
    {"key": "1+8", "name": "1 + 8 (Tall)", "rows": 4, "cols": 3,
     "cells": [(0, 0, 4, 1),
               (0, 1, 1, 1), (0, 2, 1, 1),
               (1, 1, 1, 1), (1, 2, 1, 1),
               (2, 1, 1, 1), (2, 2, 1, 1),
               (3, 1, 1, 1), (3, 2, 1, 1)]},
    {"key": "1+9", "name": "1 + 9 (Tall)", "rows": 3, "cols": 4,
     "cells": [(0, 0, 3, 1),
               (0, 1, 1, 1), (0, 2, 1, 1), (0, 3, 1, 1),
               (1, 1, 1, 1), (1, 2, 1, 1), (1, 3, 1, 1),
               (2, 1, 1, 1), (2, 2, 1, 1), (2, 3, 1, 1)]},
    {"key": "4+1", "name": "4 + 1 (Stack)", "rows": 3, "cols": 2,
     "cells": [(0, 0, 1, 1), (0, 1, 1, 1),
               (1, 0, 1, 1), (1, 1, 1, 1),
               (2, 0, 1, 2)]},
    {"key": "2+4", "name": "2 + 4 (Split)", "rows": 2, "cols": 4,
     "cells": [(0, 0, 1, 2), (0, 2, 1, 2),
               (1, 0, 1, 1), (1, 1, 1, 1),
               (1, 2, 1, 1), (1, 3, 1, 1)]},
    {"key": "3+3", "name": "3 + 3 (Grid)", "rows": 2, "cols": 3,
     "cells": [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1),
               (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1)]},
    {"key": "cinema", "name": "Cinema", "rows": 2, "cols": 5,
     "cells": [(0, 0, 1, 5),
               (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1),
               (1, 3, 1, 1), (1, 4, 1, 1)]},
    {"key": "4+2", "name": "8 + 2 (Wide)", "rows": 3, "cols": 4,
     "cells": [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1), (0, 3, 1, 1),
               (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1), (1, 3, 1, 1),
               (2, 0, 1, 2), (2, 2, 1, 2)]},
    {"key": "pyramid", "name": "Pyramid", "rows": 3, "cols": 3,
     "cells": [(0, 0, 1, 3),
               (1, 0, 1, 1), (1, 2, 1, 1),
               (2, 0, 1, 1), (2, 1, 1, 1), (2, 2, 1, 1)]},
    {"key": "6+1", "name": "6 + 1 (Stack)", "rows": 3, "cols": 3,
     "cells": [(0, 0, 1, 1), (0, 1, 1, 1), (0, 2, 1, 1),
               (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1),
               (2, 0, 1, 3)]},
]


def get_layout(key):
    for L in LAYOUTS:
        if L["key"] == key:
            return L
    return LAYOUTS[1]


def get_uniform_layouts():
    return [L for L in LAYOUTS if "×" in L["name"]]


def get_focus_layouts():
    return [L for L in LAYOUTS if "×" not in L["name"]]


class LiveCell(QFrame):
    clicked = Signal(int)
    double_clicked = Signal(int)
    close_requested = Signal(int)
    context_requested = Signal(int, object)
    drop_camera = Signal(int, str)
    swap_cells = Signal(int, int)
    hover_entered = Signal(int)
    hover_left = Signal(int)
    reconnect_requested = Signal(int)

    MIN_ZOOM = 1.0
    MAX_ZOOM = 6.0
    ZOOM_STEP = 1.25

    def __init__(self, idx, parent=None):
        super().__init__(parent)
        self.idx = idx
        self._uid = ""
        self._frame = None
        self._cached_qimage = None
        self._cached_seq = -1
        self._title = ""
        self._status = ""
        self._show_close = False
        self._recording = False
        self._motion = False
        self._is_offline = False
        self._locked_offline = False
        self._border_color = "#232830"
        self._drag_start = None

        self._zoom = 1.0
        self._zoom_anchor = None

        self._spinner_angle = 0
        self._rc_hover = False

        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "LiveCell { background: #0a0a0a; "
            "border: 2px solid #232830; border-radius: 4px; }"
        )
        self.setMinimumSize(20, 20)
        self.setMouseTracking(True)

    def is_loading(self) -> bool:
        return self._frame is None and bool(self._uid) and not self._is_offline

    def set_spinner_angle(self, angle: int):
        self._spinner_angle = angle
        if self.is_loading() and not self._is_offline:
            self.update()

    def zoom_factor(self):
        return self._zoom

    def reset_zoom(self):
        self._zoom = 1.0
        self._zoom_anchor = None
        self.update()

    def zoom_at(self, factor, local_x, local_y, view_w, view_h, img_w, img_h):
        new_zoom = self._zoom * factor
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        if abs(new_zoom - self._zoom) < 0.001:
            return
        s = min(view_w / img_w, view_h / img_h) if img_w and img_h else 1.0
        dw, dh = int(img_w * s), int(img_h * s)
        ox, oy = (view_w - dw) // 2, (view_h - dh) // 2
        px = max(0.0, min(1.0, (local_x - ox) / max(1, dw)))
        py = max(0.0, min(1.0, (local_y - oy) / max(1, dh)))
        self._zoom = new_zoom
        self._zoom_anchor = (px * img_w, py * img_h)
        self.update()

    def set_uid(self, uid):
        self._uid = uid or ""
        self.update()

    def get_uid(self):
        return self._uid

    def get_state(self):
        return {
            "uid": self._uid,
            "title": self._title,
            "status": self._status,
            "frame": self._frame,
            "seq": self._cached_seq,
            "recording": self._recording,
            "motion": self._motion,
            "offline": self._is_offline,
            "locked_offline": self._locked_offline,
        }

    def set_state(self, state):
        self._uid = state.get("uid", "")
        self._title = state.get("title", "")
        self._status = state.get("status", "")
        self._frame = state.get("frame")
        self._cached_seq = state.get("seq", -1)
        self._cached_qimage = None
        self._recording = state.get("recording", False)
        self._motion = state.get("motion", False)
        self._is_offline = state.get("offline", False)
        self._locked_offline = state.get("locked_offline", False)
        self.update()

    def lock_offline(self):
        self._locked_offline = True
        self._is_offline = True
        self._frame = None
        self._cached_qimage = None
        self.update()

    def unlock_offline(self):
        self._locked_offline = False
        self._is_offline = False
        self.update()

    def set_frame(self, payload):
        if isinstance(payload, tuple) and len(payload) == 2:
            seq, frame = payload
        else:
            seq, frame = -1, payload
        if seq != -1 and seq == self._cached_seq:
            return
        self._cached_seq = seq

        try:
            if frame is not None and hasattr(frame, "shape"):
                h, w = frame.shape[:2]
                if h > 40 and w > 40:
                    strip_h = max(8, h // 10)
                    strip = frame[h - strip_h:, :, :]
                    mean_rgb = strip.reshape(-1, 3).mean(axis=0)
                    r = float(mean_rgb[0])
                    g = float(mean_rgb[1])
                    b = float(mean_rgb[2])
                    if g > 120 and (g - r) > 80 and (g - b) > 80:
                        return
        except Exception:
            pass

        if frame is not None:
            self._is_offline = False
            self._locked_offline = False

        self._frame = frame
        self._cached_qimage = None
        self.update()

    def clear(self):
        self._frame = None
        self._cached_qimage = None
        self._cached_seq = -1
        self._uid = ""
        self._zoom = 1.0
        self._zoom_anchor = None
        self._is_offline = False
        self._locked_offline = False
        self._status = ""
        self._title = ""
        self.update()

    def set_title(self, t):
        self._title = t or ""
        self.update()

    def set_status(self, s):
        s = s or ""
        if self._locked_offline:
            if s in ("online", "connected", "متصل", "playing", "live"):
                self._locked_offline = False
                self._is_offline = False
                self._status = s
                self.update()
            return
        self._status = s
        if s in ("آفلاین", "offline"):
            self._is_offline = True
        elif s in ("online", "connected", "متصل", "playing", "live"):
            self._is_offline = False
        self.update()

    def set_show_close(self, on):
        self._show_close = bool(on)
        self.update()

    def set_recording(self, on):
        self._recording = bool(on)
        self.update()

    def set_motion(self, on):
        self._motion = bool(on)
        self.update()

    def set_border_color(self, color):
        self._border_color = color
        self.setStyleSheet(
            f"LiveCell {{ background: #0a0a0a; "
            f"border: 2px solid {color}; border-radius: 4px; }}"
        )
        self.update()

    def _close_rect(self):
        r = 10
        return QRect(self.width() - r * 2 - 6, 6, r * 2, r * 2)

    def _reconnect_rect(self):
        """اندازه دکمه اتصال مجدد، متناسب با اندازه کاشی."""
        w, h = self.width(), self.height()
        # کوچک‌تر از قبل — متناسب با کاشی
        btn_w = max(70, min(140, int(w * 0.42)))
        btn_h = max(22, min(34, int(h * 0.11)))
        cx = w // 2
        cy = h // 2 + max(18, int(h * 0.14))
        return QRect(cx - btn_w // 2, cy - btn_h // 2, btn_w, btn_h)

    def enterEvent(self, e):
        self.hover_entered.emit(self.idx)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._rc_hover = False
        self.hover_left.emit(self.idx)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start = e.position().toPoint()
            if self._is_offline and self._uid:
                if self._reconnect_rect().contains(e.position().toPoint()):
                    print(f"[LiveCell] reconnect click idx={self.idx} "
                          f"uid={self._uid}")
                    self.reconnect_requested.emit(self.idx)
                    self._drag_start = None
                    return
            if self._show_close and self._frame is not None:
                if self._close_rect().contains(e.position().toPoint()):
                    self.close_requested.emit(self.idx)
                    self._drag_start = None
                    return
            self.clicked.emit(self.idx)

    def mouseMoveEvent(self, e):
        if self._is_offline and self._uid:
            pos = e.position().toPoint()
            hover = self._reconnect_rect().contains(pos)
            if hover != self._rc_hover:
                self._rc_hover = hover
                self.setCursor(
                    Qt.PointingHandCursor if hover else Qt.ArrowCursor
                )
                self.update()

        if not (e.buttons() & Qt.LeftButton):
            return
        if self._drag_start is None:
            return
        if not self._uid:
            return
        if (e.position().toPoint() - self._drag_start).manhattanLength() < \
                QApplication.startDragDistance():
            return

        md = QMimeData()
        payload = json.dumps({"uid": self._uid, "from_cell": self.idx})
        md.setData(MIME_CAMERA, payload.encode("utf-8"))
        md.setText(self._uid)

        drag = QDrag(self)
        drag.setMimeData(md)

        if self._frame is not None and self._cached_qimage is not None:
            try:
                thumb = QPixmap.fromImage(self._cached_qimage).scaled(
                    160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                drag.setPixmap(thumb)
                drag.setHotSpot(QPoint(thumb.width() // 2,
                                       thumb.height() // 2))
            except Exception:
                pass

        self._drag_start = None
        drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, e):
        self._drag_start = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self._is_offline and self._uid:
                if self._reconnect_rect().contains(
                        e.position().toPoint()):
                    return
            if self._zoom > 1.0:
                self.reset_zoom()
                return
            self.double_clicked.emit(self.idx)

    def contextMenuEvent(self, e):
        self.context_requested.emit(self.idx, self.mapToGlobal(e.pos()))

    def wheelEvent(self, e):
        if self._frame is None:
            e.ignore()
            return
        delta = e.angleDelta().y()
        if delta == 0:
            e.ignore()
            return
        factor = self.ZOOM_STEP if delta > 0 else 1.0 / self.ZOOM_STEP
        pos = e.position()
        vh, vw = self._frame.shape[:2]
        self.zoom_at(factor, pos.x(), pos.y(),
                     self.width(), self.height(), vw, vh)
        e.accept()

    def dragEnterEvent(self, e):
        # ★ پذیرش هر چیزی — اعتبارسنجی در dropEvent
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        md = e.mimeData()
        print(f"[LiveCell.drop] idx={self.idx} "
              f"has_mime={md.hasFormat(MIME_CAMERA)} "
              f"has_text={md.hasText()}")
        uid = ""
        src = -1

        # ★ مسیر ۱: MIME_CAMERA
        if md.hasFormat(MIME_CAMERA):
            try:
                raw = bytes(md.data(MIME_CAMERA)).decode("utf-8")
                print(f"[LiveCell.drop] raw={raw!r}")
                data = json.loads(raw)
                uid = (data.get("uid") or "").strip()
                try:
                    src = int(data.get("from_cell", -1))
                except (ValueError, TypeError):
                    src = -1
            except Exception as ex:
                print(f"[LiveCell.drop] MIME parse exception: {ex}")

        # ★ مسیر ۲: fallback روی text
        if not uid and md.hasText():
            uid = md.text().strip()
            print(f"[LiveCell.drop] fallback text={uid!r}")

        if not uid:
            print(f"[LiveCell.drop] no uid — ignoring")
            e.ignore()
            return

        # ★ سواپ کاشی به کاشی
        if src >= 0 and src != self.idx:
            print(f"[LiveCell.drop] swap {src} <-> {self.idx}")
            self.swap_cells.emit(src, self.idx)
            e.acceptProposedAction()
            return

        # ★ drop معمولی (دوربین / NVR / گروه)
        print(f"[LiveCell.drop] emit drop_camera idx={self.idx} uid={uid!r}")
        self.drop_camera.emit(self.idx, uid)
        e.acceptProposedAction()

    def _draw_loading(self, p: QPainter):
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _SP_OVERLAY)
        cx, cy = w // 2, h // 2
        r = max(12, min(30, min(w, h) // 6))

        p.setBrush(Qt.NoBrush)
        pen = QPen(_SP_TRACK, 3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawEllipse(QPoint(cx, cy), r, r)

        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(_SP_ARC, 3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(cx - r, cy - r, r * 2, r * 2,
                  int(self._spinner_angle * 16), int(100 * 16))

        tip_angle = math.radians(self._spinner_angle + 100)
        p.setPen(Qt.NoPen)
        p.setBrush(_SP_ARC_HI)
        p.drawEllipse(QPoint(int(cx + r * math.cos(tip_angle)),
                             int(cy + r * math.sin(tip_angle))), 2, 2)

        status = (self._status or "").strip()
        if status and h > 80:
            text_y = cy + r + 10
            p.setPen(_SP_TEXT_SHADOW)
            p.setFont(_SP_FONT)
            p.drawText(QRect(1, text_y + 1, w, 18),
                       Qt.AlignHCenter | Qt.AlignTop, status[:32])
            p.setPen(_SP_TEXT)
            p.drawText(QRect(0, text_y, w, 18),
                       Qt.AlignHCenter | Qt.AlignTop, status[:32])
        p.setRenderHint(QPainter.Antialiasing, False)

    def _draw_reconnect_button(self, p: QPainter):
        w, h = self.width(), self.height()
        # ★ حداقل اندازه لازم برای نمایش دکمه
        if w < 110 or h < 90:
            return

        rect = self._reconnect_rect()
        p.setRenderHint(QPainter.Antialiasing, True)

        bg = _RC_BG_HOVER if self._rc_hover else _RC_BG
        border = _RC_BORDER_HOVER if self._rc_hover else _RC_BORDER
        radius = max(6, rect.height() // 2)
        p.setBrush(bg)
        p.setPen(QPen(border, 1.2))
        p.drawRoundedRect(rect, radius, radius)

        # آیکن چرخ (کوچک، متناسب)
        icon_r = max(5, min(7, rect.height() // 4))
        icon_cx = rect.left() + rect.height() // 2 + 2
        icon_cy = rect.center().y()

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255), 1.5,
                      Qt.SolidLine, Qt.RoundCap))
        p.drawArc(icon_cx - icon_r, icon_cy - icon_r,
                  icon_r * 2, icon_r * 2, 60 * 16, 260 * 16)

        end_rad = math.radians(60)
        ax = icon_cx + icon_r * math.cos(end_rad)
        ay = icon_cy + icon_r * math.sin(end_rad)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255))
        arrow = QPolygon([
            QPoint(int(ax + 1), int(ay - 3)),
            QPoint(int(ax - 3), int(ay + 2)),
            QPoint(int(ax + 3), int(ay + 3)),
        ])
        p.drawPolygon(arrow)

        # متن دکمه (فونت متناسب با اندازه دکمه)
        font_size = max(8, min(10, rect.height() // 3))
        f = QFont("Tahoma", font_size)
        f.setBold(True)
        p.setFont(f)
        p.setPen(_RC_TEXT)

        text_rect = QRect(
            rect.left() + rect.height() + 2,
            rect.top(),
            rect.width() - rect.height() - 6,
            rect.height()
        )
        p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignCenter,
                   t("live.cell.reconnect"))

        p.setRenderHint(QPainter.Antialiasing, False)

    def paintEvent(self, e):
        p = QPainter(self)
        try:
            p.fillRect(self.rect(), QColor("#0a0a0a"))

            if self._is_offline and self._uid and self._frame is None:
                p.fillRect(self.rect(), QColor(18, 22, 28))
                w, h = self.width(), self.height()
                cx = w // 2
                # ★ اندازه متناسب با کاشی
                icon_r = max(10, min(22, min(w, h) // 7))
                cy = h // 2 - max(18, icon_r + 8)

                if w > 70 and h > 70:
                    p.setRenderHint(QPainter.Antialiasing, True)
                    p.setPen(QPen(QColor(120, 60, 60), max(1, icon_r // 8)))
                    p.setBrush(QColor(60, 30, 35, 200))
                    p.drawEllipse(QPoint(cx, cy), icon_r, icon_r)
                    p.setPen(QPen(QColor(230, 100, 100),
                                  max(1.5, icon_r / 5)))
                    m = int(icon_r * 0.42)
                    p.drawLine(cx - m, cy - m, cx + m, cy + m)
                    p.drawLine(cx + m, cy - m, cx - m, cy + m)
                    p.setRenderHint(QPainter.Antialiasing, False)

                    font_size = max(8, min(12, icon_r // 2 + 2))
                    offline_font = QFont("Tahoma", font_size)
                    offline_font.setBold(True)
                    p.setFont(offline_font)
                    p.setPen(QColor(235, 130, 130))
                    text_y = cy + icon_r + 4
                    p.drawText(QRect(0, text_y, w, font_size + 8),
                               Qt.AlignHCenter | Qt.AlignTop,
                               t("live.cell.offline"))
                self._draw_reconnect_button(p)
                
                bh = 18
                p.fillRect(QRect(0, self.height() - bh,
                                 self.width(), bh),
                           QColor(0, 0, 0, 200))
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("Sans", 8, QFont.Bold))
                txt = self._title or "—"
                p.drawText(QRect(6, self.height() - bh,
                                 self.width() - 12, bh),
                           Qt.AlignVCenter | Qt.AlignLeft, txt)
                return

            if self._frame is None:
                if not self._uid:
                    p.setPen(QColor(theme.COLOR_TEXT_MUTED))
                    p.setFont(QFont("Sans", 9))
                    txt = self._title or ""
                    if txt:
                        p.drawText(self.rect(), Qt.AlignCenter, txt)
                    else:
                        p.setPen(QPen(QColor(60, 60, 60), 1, Qt.DashLine))
                        p.drawRect(self.rect().adjusted(6, 6, -7, -7))
                        p.setPen(QColor("#4a5560"))
                        p.drawText(self.rect(), Qt.AlignCenter,
                                   t("live.cell.drop_camera"))
                        return
                self._draw_loading(p)
                return

            vh, vw = self._frame.shape[:2]
            ww = max(1, self.width())
            wh = max(1, self.height())

            if self._cached_qimage is None:
                rgb = np.ascontiguousarray(self._frame)
                self._cached_qimage = QImage(
                    rgb.data, vw, vh, vw * 3, QImage.Format_RGB888
                ).copy()

            if self._zoom > 1.0 and self._zoom_anchor is not None:
                src_w = vw / self._zoom
                src_h = vh / self._zoom
                cx, cy = self._zoom_anchor
                sx = max(0, min(vw - int(src_w), int(cx - src_w / 2)))
                sy = max(0, min(vh - int(src_h), int(cy - src_h / 2)))
                src_rect = QRect(sx, sy, int(src_w), int(src_h))
                p.drawImage(self.rect(), self._cached_qimage, src_rect)
            else:
                s = min(ww / vw, wh / vh)
                dw, dh = int(vw * s), int(vh * s)
                ox, oy = (ww - dw) // 2, (wh - dh) // 2
                p.drawImage(QRect(ox, oy, dw, dh), self._cached_qimage)

            bh = 18
            p.fillRect(QRect(0, self.height() - bh, self.width(), bh),
                       QColor(0, 0, 0, 200))
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Sans", 8, QFont.Bold))
            txt = self._title or "—"
            if self._status and self._status not in (
                    "online", "connected", "متصل"):
                txt += f" ({self._status})"
            p.drawText(QRect(6, self.height() - bh,
                             self.width() - 12, bh),
                       Qt.AlignVCenter | Qt.AlignLeft, txt)

            if self._zoom > 1.0:
                badge = f"🔍 {self._zoom:.1f}x"
                p.setFont(QFont("Sans", 8, QFont.Bold))
                tw = p.fontMetrics().horizontalAdvance(badge) + 12
                badge_rect = QRect(self.width() - tw - 6, 6, tw, 18)
                p.fillRect(badge_rect, QColor(22, 160, 133, 230))
                p.setPen(QColor("#ffffff"))
                p.drawText(badge_rect, Qt.AlignCenter, badge)

            if self._recording:
                p.setRenderHint(QPainter.Antialiasing, True)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(230, 60, 60))
                p.drawEllipse(8, 8, 10, 10)
                p.setRenderHint(QPainter.Antialiasing, False)

            if self._motion:
                p.setPen(QPen(QColor(241, 196, 15), 3))
                p.drawRect(self.rect().adjusted(2, 2, -3, -3))

            if self._show_close:
                r = self._close_rect()
                p.setRenderHint(QPainter.Antialiasing, True)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(180, 40, 40, 230))
                p.drawEllipse(r)
                p.setPen(QPen(QColor(255, 255, 255), 2))
                m = 5
                p.drawLine(r.left() + m, r.top() + m,
                           r.right() - m, r.bottom() - m)
                p.drawLine(r.right() - m, r.top() + m,
                           r.left() + m, r.bottom() - m)
                p.setRenderHint(QPainter.Antialiasing, False)

        except Exception as ex:
            print(f"[LiveCell.paintEvent] {ex}")
        finally:
            p.end()


class LiveGrid(QWidget):
    cell_clicked = Signal(int)
    cell_double_clicked = Signal(int)
    cell_close = Signal(int)
    cell_context = Signal(int, object)
    cell_drop_camera = Signal(int, str)
    cell_swap = Signal(int, int)
    cell_hover_entered = Signal(int)
    cell_hover_left = Signal(int)
    cell_reconnect = Signal(int)

    MAX_GRID = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #000;")
        self.setAcceptDrops(True)   # ★ جدید — drop روی کادر خالی هم کار کنه
        self._grid = QGridLayout(self)
        self._grid.setSpacing(3)
        self._grid.setContentsMargins(3, 3, 3, 3)

        self._cells = []
        self._layout_key = "2x2"
        self._active_idx = 0
        self._fullscreen_idx = None

        self._spinner_angle = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_timer.start(60)

        self.set_layout("2x2")

    def _tick_spinner(self):
        self._spinner_angle = (self._spinner_angle + 12) % 360
        for cell in self._cells:
            try:
                if cell.is_loading() and not cell._is_offline:
                    cell.set_spinner_angle(self._spinner_angle)
            except Exception:
                pass

    def get_layout_key(self):
        return self._layout_key

    def get_cells(self):
        return self._cells

    def get_active_index(self):
        return self._active_idx

    def is_fullscreen(self):
        return self._fullscreen_idx is not None

    def get_fullscreen_idx(self):
        return self._fullscreen_idx

    def reset_all_zooms(self):
        for c in self._cells:
            c.reset_zoom()

    def toggle_fullscreen_cell(self, idx):
        if self._fullscreen_idx == idx:
            self._fullscreen_idx = None
        else:
            self._fullscreen_idx = idx
        self._arrange()

    def exit_fullscreen(self):
        if self._fullscreen_idx is not None:
            self._fullscreen_idx = None
            self._arrange()

    def set_layout(self, key):
        new_layout = get_layout(key)
        old_count = len(self._cells)
        new_count = len(new_layout["cells"])

        self._layout_key = new_layout["key"]
        self._fullscreen_idx = None

        if old_count != new_count:
            self._create_cells()
        self._arrange()

    def _create_cells(self):
        while self._grid.count():
            self._grid.takeAt(0)
        for c in self._cells:
            c.setParent(None)
            c.deleteLater()
        self._cells = []

        L = get_layout(self._layout_key)
        for i in range(len(L["cells"])):
            cell = LiveCell(i)
            cell.clicked.connect(self._on_click)
            cell.double_clicked.connect(self.cell_double_clicked.emit)
            cell.close_requested.connect(self.cell_close.emit)
            cell.context_requested.connect(self.cell_context.emit)
            cell.drop_camera.connect(self.cell_drop_camera.emit)
            cell.swap_cells.connect(self.cell_swap.emit)
            cell.hover_entered.connect(self.cell_hover_entered.emit)
            cell.hover_left.connect(self.cell_hover_left.emit)
            cell.reconnect_requested.connect(self.cell_reconnect.emit)
            self._cells.append(cell)

    def _arrange(self):
        while self._grid.count():
            self._grid.takeAt(0)

        for r in range(self.MAX_GRID):
            self._grid.setRowStretch(r, 0)
        for c in range(self.MAX_GRID):
            self._grid.setColumnStretch(c, 0)

        if self._fullscreen_idx is not None:
            idx = self._fullscreen_idx
            if 0 <= idx < len(self._cells):
                target = self._cells[idx]
                target.show()
                target.setMinimumSize(20, 20)
                self._grid.addWidget(target, 0, 0, 1, 1)
            for i, c in enumerate(self._cells):
                if i != idx:
                    c.hide()
            self._grid.setRowStretch(0, 1)
            self._grid.setColumnStretch(0, 1)
        else:
            L = get_layout(self._layout_key)
            for i, (r, c, rs, cs) in enumerate(L["cells"]):
                if i < len(self._cells):
                    cell = self._cells[i]
                    cell.show()
                    self._grid.addWidget(cell, r, c, rs, cs)
            for i in range(len(L["cells"]), len(self._cells)):
                self._cells[i].hide()
            for r in range(L["rows"]):
                self._grid.setRowStretch(r, 1)
            for c in range(L["cols"]):
                self._grid.setColumnStretch(c, 1)

        self._grid.invalidate()
        self._update_active()
        self.update()

    def _update_active(self):
        for i, c in enumerate(self._cells):
            try:
                color = "#16a085" if i == self._active_idx else "#232830"
                c.set_border_color(color)
            except Exception:
                pass

    def _on_click(self, idx):
        self._active_idx = idx
        self._update_active()
        self.cell_clicked.emit(idx)

    # ============================================================
    # Grid-level drop forwarding
    # ============================================================
    def _nearest_cell(self, pos):
        """نزدیک‌ترین کاشی به نقطه‌ی داده‌شده."""
        target = None
        min_dist = None
        for cell in self._cells:
            if not cell.isVisible():
                continue
            try:
                cell_pos = cell.mapTo(self, QPoint(0, 0))
                cx = cell_pos.x() + cell.width() // 2
                cy = cell_pos.y() + cell.height() // 2
                dist = (pos.x() - cx) ** 2 + (pos.y() - cy) ** 2
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    target = cell
            except Exception:
                continue
        return target

    def dragEnterEvent(self, e):
        """پذیرش drop روی کل گرید."""
        md = e.mimeData()
        if md.hasFormat(MIME_CAMERA) or md.hasText():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        md = e.mimeData()
        if md.hasFormat(MIME_CAMERA) or md.hasText():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        """اگر روی کاشی نبود، به نزدیک‌ترین کاشی forward کن."""
        pos = e.position().toPoint()
        print(f"[LiveGrid.drop] at ({pos.x()},{pos.y()})")

        # اگر روی کاشی خالی نیست و بین کاشی‌هاست، نزدیک‌ترین رو بگیر
        target = self._nearest_cell(pos)
        if target is None:
            # اگر حتی یک کاشی هم نیست، active_idx رو استفاده کن
            if self._cells:
                target = self._cells[self._active_idx]
            else:
                e.ignore()
                return

        print(f"[LiveGrid.drop] forwarding to cell idx={target.idx}")
        target.dropEvent(e)

    def set_frame(self, idx, payload):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_frame(payload)
    def clear_cell(self, idx):
        if 0 <= idx < len(self._cells):
            self._cells[idx].clear()

    def set_title(self, idx, title):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_title(title)

    def set_uid(self, idx, uid):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_uid(uid)

    def set_status(self, idx, status):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_status(status)

    def set_recording(self, idx, on):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_recording(on)

    def set_motion(self, idx, on):
        if 0 <= idx < len(self._cells):
            self._cells[idx].set_motion(on)

    def set_show_close(self, on):
        for c in self._cells:
            c.set_show_close(on)
