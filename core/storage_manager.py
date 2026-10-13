# -*- coding: utf-8 -*-
"""
K1 VMS — Storage Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
مدیریت حافظه ضبط:
  1. پاک کردن فایل‌های قدیمی‌تر از retention_days
  2. اگر مصرف دیسک از quota عبور کرد، قدیمی‌ترین‌ها رو پاک کن
  3. محاسبه‌ی حجم کل، تعداد فایل، قدیمی‌ترین و جدیدترین فایل
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import config


# ============================================================
# داده‌های آماری
# ============================================================
@dataclass
class StorageStats:
    total_bytes: int = 0
    file_count: int = 0
    oldest_mtime: Optional[float] = None
    newest_mtime: Optional[float] = None
    # فضای کل و آزاد درایو
    disk_total_bytes: int = 0
    disk_free_bytes: int = 0
    disk_used_bytes: int = 0
    # مسیر اسکن‌شده
    root: str = ""

    def total_gb(self) -> float:
        return self.total_bytes / (1024 ** 3)

    def total_mb(self) -> float:
        return self.total_bytes / (1024 ** 2)

    def disk_total_gb(self) -> float:
        return self.disk_total_bytes / (1024 ** 3)

    def disk_free_gb(self) -> float:
        return self.disk_free_bytes / (1024 ** 3)

    def disk_used_gb(self) -> float:
        return self.disk_used_bytes / (1024 ** 3)

    def usage_percent(self) -> float:
        """درصد مصرف دیسک کل."""
        if self.disk_total_bytes <= 0:
            return 0.0
        return (self.disk_used_bytes / self.disk_total_bytes) * 100.0

    def oldest_date(self) -> Optional[datetime]:
        if self.oldest_mtime is None:
            return None
        return datetime.fromtimestamp(self.oldest_mtime)

    def newest_date(self) -> Optional[datetime]:
        if self.newest_mtime is None:
            return None
        return datetime.fromtimestamp(self.newest_mtime)


# ============================================================
# Storage Manager
# ============================================================
class StorageManager:
    """عملیات مدیریت حافظه ضبط."""

    _instance = None
    _lock = threading.RLock()

    @classmethod
    def instance(cls) -> "StorageManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self._stop_flag = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._last_result: dict = {}

    # ============================================================
    # Statistics — پیمایش فایل‌ها
    # ============================================================
    def compute_stats(self, root: Optional[Path] = None) -> StorageStats:
        """پیمایش بازگشتی پوشه ضبط برای محاسبه آمار."""
        if root is None:
            root = Path(config.CONTINUOUS_DIR)

        stats = StorageStats()
        stats.root = str(root)

        # فضای درایو
        try:
            usage = shutil.disk_usage(str(root.drive + "\\") if root.drive else str(root))
            stats.disk_total_bytes = usage.total
            stats.disk_free_bytes = usage.free
            stats.disk_used_bytes = usage.used
        except Exception:
            pass

        if not root.exists():
            return stats

        oldest = None
        newest = None
        total = 0
        count = 0

        # پسوندهای ضبط
        exts = (".ts", ".mp4", ".mkv")

        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.lower().endswith(exts):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp)
                    total += st.st_size
                    count += 1
                    mtime = st.st_mtime
                    if oldest is None or mtime < oldest:
                        oldest = mtime
                    if newest is None or mtime > newest:
                        newest = mtime
                except OSError:
                    continue

        stats.total_bytes = total
        stats.file_count = count
        stats.oldest_mtime = oldest
        stats.newest_mtime = newest
        return stats

    # ============================================================
    # Cleanup strategies
    # ============================================================
    def _iter_recording_files(self, root: Path, exts=(".ts", ".mp4", ".mkv")):
        """تولید (path, mtime, size) از همه فایل‌های ضبط."""
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.lower().endswith(exts):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp)
                    yield fp, st.st_mtime, st.st_size
                except OSError:
                    continue

    def cleanup_by_retention(self, root: Path, retention_days: int,
                             keep_recent_hours: float = 0.5) -> dict:
        """
        پاک کردن فایل‌های قدیمی‌تر از retention_days.

        Args:
            keep_recent_hours: فایل‌های تازه‌تر از این مقدار را دست نزن
                              (ضبط در حال انجام)
        """
        result = {"deleted": 0, "freed_bytes": 0, "errors": 0}
        if retention_days <= 0:
            return result

        cutoff = time.time() - (retention_days * 86400)
        keep_after = time.time() - (keep_recent_hours * 3600)

        for fp, mtime, size in self._iter_recording_files(root):
            # فایل تازه‌تر از keep_recent_hours → skip
            if mtime > keep_after:
                continue
            if mtime < cutoff:
                try:
                    os.remove(fp)
                    result["deleted"] += 1
                    result["freed_bytes"] += size
                except OSError:
                    result["errors"] += 1

        self._cleanup_empty_dirs(root)
        return result

    def cleanup_by_quota(self, root: Path, max_gb: float,
                         keep_recent_hours: float = 0.5,
                         target_ratio: float = 0.9) -> dict:
        """
        اگر مصرف از max_gb عبور کرد، قدیمی‌ترین فایل‌ها رو حذف کن
        تا رسیدن به target_ratio × max_gb.

        Args:
            target_ratio: به چه کسری از max_gb برگرده (0.9 = 90%)
        """
        result = {"deleted": 0, "freed_bytes": 0, "errors": 0,
                  "before_gb": 0.0, "after_gb": 0.0}

        if max_gb <= 0:
            return result

        max_bytes = int(max_gb * (1024 ** 3))
        target_bytes = int(max_bytes * target_ratio)
        keep_after = time.time() - (keep_recent_hours * 3600)

        # جمع‌آوری همه فایل‌ها با mtime و size
        files = []
        total = 0
        for fp, mtime, size in self._iter_recording_files(root):
            if mtime > keep_after:
                continue
            files.append((fp, mtime, size))
            total += size

        result["before_gb"] = total / (1024 ** 3)

        if total <= max_bytes:
            result["after_gb"] = result["before_gb"]
            return result

        # مرتب‌سازی از قدیمی‌ترین
        files.sort(key=lambda x: x[1])

        # حذف تا رسیدن به target
        for fp, mtime, size in files:
            if total <= target_bytes:
                break
            try:
                os.remove(fp)
                result["deleted"] += 1
                result["freed_bytes"] += size
                total -= size
            except OSError:
                result["errors"] += 1

        result["after_gb"] = total / (1024 ** 3)
        self._cleanup_empty_dirs(root)
        return result

    def _cleanup_empty_dirs(self, root: Path):
        """حذف پوشه‌های خالی به صورت بازگشتی."""
        try:
            for dirpath, dirnames, filenames in os.walk(root, topdown=False):
                if Path(dirpath) == root:
                    continue
                try:
                    if not any(os.scandir(dirpath)):
                        os.rmdir(dirpath)
                except OSError:
                    pass
        except Exception:
            pass

    # ============================================================
    # Full cleanup — retention + quota
    # ============================================================
    def run_cleanup(self, settings) -> dict:
        """
        اجرای کامل cleanup بر اساس تنظیمات.

        Args:
            settings: GlobalSettings (از settings_manager.load_settings())

        Returns:
            dict با آمار
        """
        root = Path(config.CONTINUOUS_DIR)
        if not root.exists():
            return {"error": "root_not_found"}

        retention_days = int(getattr(settings, "retention_days", 7) or 0)
        max_gb = float(getattr(settings, "max_storage_gb", 0) or 0)
        auto_enabled = bool(getattr(settings, "auto_cleanup_enabled", True))

        if not auto_enabled:
            return {"skipped": "auto_disabled"}

        results = {
            "retention": {"deleted": 0, "freed_bytes": 0},
            "quota": {"deleted": 0, "freed_bytes": 0},
            "timestamp": datetime.now().isoformat(),
        }

        # مرحله ۱: حذف بر اساس سن
        if retention_days > 0:
            r1 = self.cleanup_by_retention(root, retention_days)
            results["retention"] = r1

        # مرحله ۲: حذف بر اساس سهمیه
        if max_gb > 0:
            r2 = self.cleanup_by_quota(root, max_gb)
            results["quota"] = r2

        total_deleted = (results["retention"]["deleted"]
                         + results["quota"]["deleted"])
        total_freed = (results["retention"]["freed_bytes"]
                       + results["quota"]["freed_bytes"])

        print(f"[StorageManager] cleanup: deleted={total_deleted} "
              f"freed={total_freed / (1024**2):.1f}MB")

        self._last_result = results
        return results

    # ============================================================
    # Background worker
    # ============================================================
    def start_auto_cleanup(self, settings, interval_sec: int = 3600):
        """شروع thread پس‌زمینه که هر interval_sec یک بار cleanup می‌کنه."""
        if self._worker is not None and self._worker.is_alive():
            return

        self._stop_flag.clear()

        def _loop():
            # اولین اجرا با تاخیر کوتاه (تا برنامه کاملاً بالا بیاد)
            time.sleep(60)
            while not self._stop_flag.is_set():
                try:
                    # reload تنظیمات هر بار (تا تغییرات ادمین اعمال شه)
                    from core import settings_manager
                    s = settings_manager.load_settings()
                    self.run_cleanup(s)
                except Exception as e:
                    print(f"[StorageManager] auto-cleanup error: {e}")
                # خواب تا اجرای بعدی
                self._stop_flag.wait(interval_sec)

        self._worker = threading.Thread(
            target=_loop, daemon=True, name="StorageCleanup"
        )
        self._worker.start()
        print(f"[StorageManager] auto-cleanup started "
              f"(interval={interval_sec}s)")

    def stop_auto_cleanup(self):
        self._stop_flag.set()
        if self._worker is not None:
            try:
                self._worker.join(timeout=2.0)
            except Exception:
                pass