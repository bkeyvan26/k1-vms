"""
core/recording_organizer.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
مهاجرت ایمن ضبط‌های قدیمی از ساختار cam_xxxx به _data/cam_xxxx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- فایل‌های در حال ضبط توسط MediaMTX قفل هستند (WinError 32)
- با WRITE_GRACE_SEC از mtime، فایل‌های تازه skip می‌شوند
- تمام move ها با try/except جدا محافظت می‌شوند
- این ماژول هرگز باعث کرش startup نمی‌شود
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

# فایل‌هایی که کمتر از این مدت از mtime‌شان گذشته، در حال نوشتن در نظر گرفته می‌شوند
WRITE_GRACE_SEC = 90.0

# پسوند فایل‌های ضبط
RECORDING_EXTENSIONS = (".ts", ".mp4", ".mkv")

# پیشوند پوشه‌های standalone (دوربین‌های مستقل)
CAMERA_PREFIX = "cam_"

# نام پوشه‌ی مقصد مهاجرت
ARCHIVE_DIR_NAME = "_data"

# مسیر پیش‌فرض (اگر از main.py پاس داده نشد)
DEFAULT_CONTINUOUS_DIR = r"D:\recorde\k1Motion\recordings\continuous"


def _is_recently_written(path: Path, grace_sec: float = WRITE_GRACE_SEC) -> bool:
    """آیا فایل به تازگی نوشته شده؟ (یعنی احتمالاً در حال ضبط است)"""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return True
    return (time.time() - mtime) < grace_sec


def _safe_move(src: Path, dst: Path) -> bool:
    """
    انتقال ایمن فایل. اگر قفل بود، False برمی‌گرداند.

    Returns:
        True اگر موفق، False اگر skip شد.
    """
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)

        # اگر مقصد وجود دارد، نام را تغییر بده
        if dst.exists():
            base = dst.stem
            suffix = dst.suffix
            counter = 1
            new_dst = dst
            while new_dst.exists():
                new_dst = dst.parent / f"{base}_{counter}{suffix}"
                counter += 1
            dst = new_dst

        # اول: rename (سریع‌تر، در همان دیسک)
        try:
            os.replace(src, dst)
            return True
        except OSError:
            pass

        # fallback: copy + delete
        shutil.copy2(src, dst)
        try:
            src.unlink()
        except OSError:
            pass
        return True

    except PermissionError:
        # WinError 32: فایل توسط process دیگری قفل است
        return False
    except OSError:
        return False
    except Exception as e:
        print(f"[RecordingOrganizer] ⚠ خطای غیرمنتظره در {src}: {e}")
        return False


def _should_migrate(cam_dir: Path) -> bool:
    """آیا این پوشه دوربین نیاز به مهاجرت دارد؟"""
    if not cam_dir.is_dir():
        return False
    if cam_dir.name == ARCHIVE_DIR_NAME:
        return False
    if not cam_dir.name.startswith(CAMERA_PREFIX):
        return False
    return True


def _cleanup_empty_dirs(root: Path) -> None:
    """حذف پوشه‌های خالی به صورت بازگشتی (بدون خطا)."""
    try:
        for current, dirs, files in os.walk(root, topdown=False):
            current_path = Path(current)
            if current_path == root:
                continue
            try:
                if not any(current_path.iterdir()):
                    current_path.rmdir()
            except OSError:
                pass
    except Exception:
        pass


def organize_recordings(continuous_dir: Path | str) -> dict:
    """
    مهاجرت ایمن ضبط‌های قدیمی.

    Args:
        continuous_dir: مسیر D:\\recorde\\k1Motion\\recordings\\continuous

    Returns:
        dict با آمار: {"moved": int, "skipped": int, "errors": int}
    """
    continuous_dir = Path(continuous_dir)
    if not continuous_dir.is_dir():
        return {"moved": 0, "skipped": 0, "errors": 0}

    stats = {"moved": 0, "skipped": 0, "errors": 0}
    archive_root = continuous_dir / ARCHIVE_DIR_NAME

    try:
        cam_dirs = list(continuous_dir.iterdir())
    except OSError:
        return stats

    for cam_dir in cam_dirs:
        if not _should_migrate(cam_dir):
            continue

        try:
            date_dirs = list(cam_dir.rglob("*"))
        except OSError:
            continue

        for item in date_dirs:
            if not item.is_file():
                continue
            if item.suffix.lower() not in RECORDING_EXTENSIONS:
                continue

            # skip فایل‌های تازه (در حال ضبط)
            if _is_recently_written(item):
                stats["skipped"] += 1
                continue

            try:
                rel = item.relative_to(continuous_dir)
            except ValueError:
                continue

            dst = archive_root / rel

            if _safe_move(item, dst):
                stats["moved"] += 1
            else:
                stats["errors"] += 1

    # پاکسازی پوشه‌های خالی
    _cleanup_empty_dirs(continuous_dir)

    return stats


def migrate_old_recordings(continuous_dir: Path | str | None = None) -> int:
    """
    API سازگار با main.py — تعداد فایل‌های منتقل‌شده را برمی‌گرداند.

    این تابع هرگز exception پرتاب نمی‌کند (کاملاً safe برای startup).
    """
    try:
        if continuous_dir is None:
            continuous_dir = DEFAULT_CONTINUOUS_DIR

        stats = organize_recordings(continuous_dir)
        moved = stats.get("moved", 0)

        if moved or stats.get("errors") or stats.get("skipped"):
            print(
                f"[RecordingOrganizer] moved={stats['moved']} "
                f"skipped={stats['skipped']} errors={stats['errors']}"
            )
        return moved
    except Exception as e:
        print(f"[RecordingOrganizer] migrate failed (safe): {e}")
        return 0