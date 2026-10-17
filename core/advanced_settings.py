# -*- coding: utf-8 -*-
"""K1 VMS — Advanced Settings (Phase 14)

مقادیر پیشرفته که فقط ادمین حرفه‌ای باید تغییر دهد.
این مقادیر در settings.json ذخیره می‌شوند و در سراسر برنامه
خوانده می‌شوند.

⚠ هشدار: تغییر این مقادیر می‌تواند باعث کندی، خطا یا پخش
   ناپایدار شود. مقادیر پیش‌فرض برای اکثر سیستم‌ها بهینه هستند.
"""

# ============================================================
# پیش‌فرض‌ها
# ============================================================
DEFAULTS = {
    # ---- Playback / FFmpeg ----
    "adv.ffmpeg.probesize_kb": 512,       # از 512K (512 کیلوبایت)
    "adv.ffmpeg.analyzeduration_ms": 300, # از 300K (300 میلی‌ثانیه)
    "adv.ffmpeg.threads": 0,              # 0 = auto
    "adv.playback.seek_debounce_ms": 50,
    "adv.playback.manifest_max_segments": 8,
    "adv.playback.auto_jump_max_distance_sec": 120,
    "adv.playback.gap_tolerance_sec": 8,
    "adv.playback.max_source_fps": 120,

    # ---- Indexer ----
    "adv.indexer.contiguous_tolerance_sec": 20,
    "adv.indexer.finalize_threshold_sec": 30,
    "adv.indexer.probe_cache_hours": 168,  # 7 روز

    # ---- Live ----
    "adv.live.grid_budget": 16,
    "adv.live.stagger_ms_min": 20,
    "adv.live.stagger_ms_max": 60,
    "adv.live.bad_frame_threshold": 3,

    # ---- Recording ----
    "adv.record.buffer_size_mb": 4,
    "adv.record.disk_full_check_sec": 60,

    # ---- Storage ----
    "adv.storage.scan_chunk_size": 500,
    "adv.storage.keep_recent_hours": 2,

    # ---- Debug ----
    "adv.debug.verbose_trace": False,
    "adv.debug.log_ffmpeg_cmd": False,
}


def get(key: str, fallback=None):
    """خواندن مقدار پیشرفته از settings.json."""
    try:
        from core import settings_manager
        s = settings_manager.load_settings()
        val = getattr(s, key, None)
        if val is None:
            val = s.__dict__.get(key) if hasattr(s, "__dict__") else None
        if val is None:
            return DEFAULTS.get(key, fallback)
        return val
    except Exception:
        return DEFAULTS.get(key, fallback)


def get_all() -> dict:
    """برگرداندن همه مقادیر فعلی."""
    out = dict(DEFAULTS)
    try:
        from core import settings_manager
        s = settings_manager.load_settings()
        for k in DEFAULTS:
            v = getattr(s, k, None)
            if v is not None:
                out[k] = v
    except Exception:
        pass
    return out


def set_value(key: str, value):
    """ذخیره یک مقدار."""
    try:
        from core import settings_manager
        s = settings_manager.load_settings()
        setattr(s, key, value)
        settings_manager.save_settings(s)
        return True
    except Exception as e:
        print(f"[advanced_settings] set {key} failed: {e}")
        return False