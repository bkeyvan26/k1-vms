# -*- coding: utf-8 -*-
"""K1 VMS — Data models (Phase 12: full settings)"""
import uuid
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from core.permissions import (
    ALL_PERMISSION_KEYS, DEFAULT_USER_PERMISSIONS, DEFAULT_ADMIN_PERMISSIONS
)


ROLE_RECORDING = "RECORDING"
ROLE_MOTION    = "MOTION"
ROLE_LIVE_VIEW = "LIVE_VIEW"
ROLE_GRID      = "GRID"

ALL_ROLES = [ROLE_RECORDING, ROLE_MOTION, ROLE_LIVE_VIEW, ROLE_GRID]


def new_uid() -> str:
    return uuid.uuid4().hex[:12]


# ============================================================
# NVR Models
# ============================================================
@dataclass
class NVRChannel:
    channel_id: int = 0
    name: str = ""
    rtsp_url_main: str = ""
    rtsp_url_sub: str = ""
    resolution: str = ""
    codec: str = ""
    enabled: bool = True

    def to_dict(self) -> dict: return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "NVRChannel":
        c = NVRChannel()
        for k, v in (d or {}).items():
            if hasattr(c, k): setattr(c, k, v)
        try:
            c.channel_id = int(c.channel_id or 0)
        except Exception:
            c.channel_id = 0
        return c


@dataclass
class NVRDevice:
    uid: str = field(default_factory=new_uid)
    name: str = ""
    record_folder_name: str = ""
    brand: str = "auto"
    ip: str = ""
    rtsp_port: int = 554
    onvif_port: int = 80
    user: str = "admin"
    password: str = ""
    protocol: str = "onvif"
    channels: List[NVRChannel] = field(default_factory=list)
    enabled: bool = True
    last_discovered: str = ""
    record_channels: bool = False
    record_channels_synced: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "uid": self.uid, "name": self.name,
            "record_folder_name": self.record_folder_name,
            "brand": self.brand, "ip": self.ip,
            "rtsp_port": self.rtsp_port, "onvif_port": self.onvif_port,
            "user": self.user, "password": self.password,
            "protocol": self.protocol,
            "channels": [c.to_dict() for c in self.channels],
            "enabled": self.enabled,
            "last_discovered": self.last_discovered,
            "record_channels": self.record_channels,
            "record_channels_synced": self.record_channels_synced,
        }

    @staticmethod
    def from_dict(d: dict) -> "NVRDevice":
        n = NVRDevice()
        d = dict(d or {})
        raw_channels = d.pop("channels", [])
        for k, v in d.items():
            if hasattr(n, k): setattr(n, k, v)
        if not isinstance(raw_channels, list):
            raw_channels = []
        n.channels = [NVRChannel.from_dict(c) for c in raw_channels]
        if not n.uid: n.uid = new_uid()
        try:
            n.rtsp_port = int(n.rtsp_port or 554)
            n.onvif_port = int(n.onvif_port or 80)
        except Exception:
            n.rtsp_port = 554; n.onvif_port = 80
        if not hasattr(n, "record_channels_synced"):
            n.record_channels_synced = None
        return n

    def get_channel(self, cid: int) -> Optional[NVRChannel]:
        for c in self.channels:
            if c.channel_id == cid: return c
        return None

    def enabled_channels(self) -> List[NVRChannel]:
        return [c for c in self.channels if c.enabled]


# ============================================================
# StreamProfile
# ============================================================
@dataclass
class StreamProfile:
    id: str = ""
    name: str = ""
    rtsp_path: str = ""
    url: str = ""
    resolution: str = ""
    width: int = 0
    height: int = 0
    codec: str = ""
    fps: int = 0
    bitrate_kbps: int = 0
    roles: List[str] = field(default_factory=list)
    discovered_by: str = ""
    onvif_profile_token: str = ""
    has_ptz: bool = False
    has_zoom_only: bool = False
    has_presets: bool = False

    def to_dict(self) -> dict: return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "StreamProfile":
        p = StreamProfile()
        for k, v in (d or {}).items():
            if hasattr(p, k): setattr(p, k, v)
        if not isinstance(p.roles, list): p.roles = []
        try:
            p.width = int(p.width or 0)
            p.height = int(p.height or 0)
            p.fps = int(p.fps or 0)
            p.bitrate_kbps = int(p.bitrate_kbps or 0)
        except Exception: pass
        if not p.resolution and p.width and p.height:
            p.resolution = f"{p.width}x{p.height}"
        return p

    def has_role(self, role: str) -> bool:
        return role in (self.roles or [])

    def add_role(self, role: str):
        if not self.has_role(role):
            self.roles = list(self.roles or []) + [role]

    def remove_role(self, role: str):
        self.roles = [r for r in (self.roles or []) if r != role]

    def resolution_or(self, fallback: str = "—") -> str:
        if self.resolution: return self.resolution
        if self.width and self.height: return f"{self.width}x{self.height}"
        return fallback

    def pixel_count(self) -> int:
        return int(self.width or 0) * int(self.height or 0)

    def summary(self) -> str:
        parts = []
        res = self.resolution_or("")
        if res: parts.append(res)
        if self.codec: parts.append(self.codec.upper())
        if self.fps: parts.append(f"{self.fps}fps")
        return " • ".join(parts) if parts else "—"


# ============================================================
# CameraConfig
# ============================================================
@dataclass
class CameraConfig:
    uid: str = field(default_factory=new_uid)
    name: str = ""
    record_folder_name: str = ""
    enabled: bool = True
    ip: str = ""
    port: int = 554
    user: str = "admin"
    password: str = ""
    rtsp_path_main: str = ""
    rtsp_path_sub: str = ""
    nvr_uid: str = ""
    nvr_name: str = ""
    stream_profiles: List[StreamProfile] = field(default_factory=list)
    recording_profile_id: str = ""
    motion_profile_id: str = ""
    live_profile_id: str = ""
    grid_profile_id: str = ""
    recording_fps_note: int = 0
    live_display_fps: int = 0
    grid_display_fps: int = 0
    live_transport: str = "auto"
    grid_transport: str = "auto"
    motion_processing_fps: int = 0
    live_resolution_override: str = ""
    grid_resolution_override: str = ""
    record_enabled_continuous: bool = False
    record_enabled_motion: bool = True
    record_segment_minutes: int = 0
    record_path_override: str = ""
    sensitivity: int = 100
    min_area: int = 400
    detect_every: int = 3
    roi_regions: List[dict] = field(default_factory=list)
    motion_pre_buffer_sec: int = 5
    motion_post_buffer_sec: int = 5
    ai_enabled: bool = False
    ai_filter_person_only: bool = False
    incident_locked: bool = False

    def to_dict(self) -> dict: return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "CameraConfig":
        c = CameraConfig()
        d = dict(d or {})
        raw_profiles = d.pop("stream_profiles", None)
        OLD_TO_NEW = {
            "live_fps_single": "live_display_fps",
            "live_fps_grid": "grid_display_fps",
        }
        for k, v in d.items():
            new_k = OLD_TO_NEW.get(k, k)
            if hasattr(c, new_k): setattr(c, new_k, v)
            elif k == "live_resolution_single":
                if isinstance(v, str) and v != "auto":
                    c.live_resolution_override = v
            elif k == "live_resolution_grid":
                if isinstance(v, str) and v != "auto":
                    c.grid_resolution_override = v
        if raw_profiles:
            for pd in raw_profiles:
                if isinstance(pd, dict):
                    c.stream_profiles.append(StreamProfile.from_dict(pd))
                elif isinstance(pd, StreamProfile):
                    c.stream_profiles.append(pd)
        if not c.uid: c.uid = new_uid()
        c.migrate_legacy_to_profiles()
        c._ensure_profile_defaults()
        return c

    def migrate_legacy_to_profiles(self):
        if not self.stream_profiles:
            if self.rtsp_path_main:
                self.stream_profiles.append(StreamProfile(
                    id="main", name="Main Stream",
                    rtsp_path=self.rtsp_path_main,
                    url=self._build_url(self.rtsp_path_main),
                    roles=[ROLE_RECORDING, ROLE_LIVE_VIEW],
                    discovered_by="legacy"))
            if self.rtsp_path_sub:
                self.stream_profiles.append(StreamProfile(
                    id="sub", name="Sub Stream",
                    rtsp_path=self.rtsp_path_sub,
                    url=self._build_url(self.rtsp_path_sub),
                    roles=[ROLE_MOTION, ROLE_GRID, ROLE_LIVE_VIEW],
                    discovered_by="legacy"))

    def _ensure_profile_defaults(self):
        if not self.stream_profiles: return
        if not self.recording_profile_id:
            for p in self.stream_profiles:
                if p.has_role(ROLE_RECORDING):
                    self.recording_profile_id = p.id; break
            if not self.recording_profile_id:
                h = max(self.stream_profiles, key=lambda p: p.pixel_count() or 0)
                self.recording_profile_id = h.id
        if not self.motion_profile_id:
            for p in self.stream_profiles:
                if p.has_role(ROLE_MOTION):
                    self.motion_profile_id = p.id; break
            if not self.motion_profile_id:
                l = min(self.stream_profiles, key=lambda p: p.pixel_count() or 999999999)
                self.motion_profile_id = l.id
        if not self.live_profile_id:
            for p in self.stream_profiles:
                if p.has_role(ROLE_LIVE_VIEW):
                    self.live_profile_id = p.id; break
            if not self.live_profile_id:
                self.live_profile_id = self.recording_profile_id or self.stream_profiles[0].id
        if not self.grid_profile_id:
            for p in self.stream_profiles:
                if p.has_role(ROLE_GRID):
                    self.grid_profile_id = p.id; break
            if not self.grid_profile_id:
                if self.motion_profile_id:
                    self.grid_profile_id = self.motion_profile_id
                elif len(self.stream_profiles) > 1:
                    l = min(self.stream_profiles, key=lambda p: p.pixel_count() or 999999999)
                    self.grid_profile_id = l.id
                else:
                    self.grid_profile_id = self.stream_profiles[0].id

    def _build_url(self, path: str) -> str:
        if not path: return ""
        if path.startswith("rtsp://"): return path
        if not path.startswith("/"): path = "/" + path
        u = urllib.parse.quote(self.user or "", safe="")
        pw = urllib.parse.quote(self.password or "", safe="")
        return f"rtsp://{u}:{pw}@{self.ip}:{self.port}{path}"

    def get_profile_by_id(self, pid: str) -> Optional[StreamProfile]:
        if not pid: return None
        for p in self.stream_profiles:
            if p.id == pid: return p
        return None

    def get_recording_profile(self): return self.get_profile_by_id(self.recording_profile_id)
    def get_motion_profile(self):    return self.get_profile_by_id(self.motion_profile_id)
    def get_live_profile(self):      return self.get_profile_by_id(self.live_profile_id)
    def get_grid_profile(self):      return self.get_profile_by_id(self.grid_profile_id)

    def get_recording_url(self) -> str:
        p = self.get_recording_profile()
        if p and p.url: return p.url
        return self._build_url(self.rtsp_path_main) if self.rtsp_path_main else ""

    def get_motion_url(self) -> str:
        p = self.get_motion_profile()
        if p and p.url: return p.url
        path = self.rtsp_path_sub or self.rtsp_path_main
        return self._build_url(path) if path else ""

    def get_live_url(self) -> str:
        p = self.get_live_profile()
        if p and p.url: return p.url
        return self._build_url(self.rtsp_path_main) if self.rtsp_path_main else ""

    def get_grid_url(self) -> str:
        p = self.get_grid_profile()
        if p and p.url: return p.url
        path = self.rtsp_path_sub or self.rtsp_path_main
        return self._build_url(path) if path else ""

    def get_recording_source_fps(self) -> int:
        p = self.get_recording_profile(); return int(p.fps) if p else 0
    def get_motion_source_fps(self) -> int:
        p = self.get_motion_profile(); return int(p.fps) if p else 0
    def get_live_source_fps(self) -> int:
        p = self.get_live_profile(); return int(p.fps) if p else 0
    def get_grid_source_fps(self) -> int:
        p = self.get_grid_profile(); return int(p.fps) if p else 0

    def effective_live_fps(self) -> int:
        return self.live_display_fps or self.get_live_source_fps() or 15
    def effective_grid_fps(self) -> int:
        return self.grid_display_fps or self.get_grid_source_fps() or 5
    def effective_motion_fps(self) -> int:
        return self.motion_processing_fps or self.get_motion_source_fps() or 5

    def supports_ptz(self) -> bool:
        return any((p.has_ptz or p.has_zoom_only) for p in self.stream_profiles)
    def ptz_profile(self):
        for p in self.stream_profiles:
            if p.has_ptz or p.has_zoom_only: return p
        return None
    def has_connection_info(self) -> bool:
        return bool(self.ip and (self.rtsp_path_main or self.rtsp_path_sub or self.stream_profiles))


# ============================================================
# UserConfig
# ============================================================
@dataclass
class UserConfig:
    uid: str = field(default_factory=new_uid)
    username: str = ""
    full_name: str = ""
    password_hash: str = ""
    password_salt: str = ""
    is_admin: bool = False
    enabled: bool = True
    permissions: Dict[str, bool] = field(default_factory=dict)
    allowed_camera_uids: List[str] = field(default_factory=list)
    failed_attempts: int = 0
    locked_until: str = ""
    locked_by_admin: bool = False

    def to_dict(self) -> dict: return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "UserConfig":
        u = UserConfig()
        for k, v in d.items():
            if hasattr(u, k): setattr(u, k, v)
        for key in ALL_PERMISSION_KEYS:
            if key not in u.permissions:
                u.permissions[key] = (
                    DEFAULT_ADMIN_PERMISSIONS.get(key, False) if u.is_admin
                    else DEFAULT_USER_PERMISSIONS.get(key, False))
        return u

    def has(self, perm: str) -> bool:
        if self.is_admin: return True
        return bool(self.permissions.get(perm, False))

    def can_see_camera(self, cam: CameraConfig) -> bool:
        if self.is_admin: return True
        if not self.allowed_camera_uids: return True
        return cam.uid in self.allowed_camera_uids


# ============================================================
# GlobalSettings — Phase 12: 55 تنظیم
# ============================================================
@dataclass
class GlobalSettings:
    # ----------------------------------------
    # سیستم
    # ----------------------------------------
    language: str = "fa"
    theme: str = "dark"          # dark | light
    font_size: str = "medium"    # small | medium | large
    compact_mode: bool = False

    # ----------------------------------------
    # ضبط
    # ----------------------------------------
    record_enabled: bool = True
    record_segment_minutes: int = 5
    record_format: str = ".ts"
    autostart_recording_on_boot: bool = True
    motion_recording_enabled: bool = False
    motion_record_after: bool = True
    motion_pre_buffer_sec: int = 5
    motion_post_buffer_sec: int = 5
    motion_sensitivity_default: int = 100
    motion_min_area_default: int = 400

    # ----------------------------------------
    # حافظه
    # ----------------------------------------
    recording_root: str = ""
    auto_cleanup_enabled: bool = True
    retention_days: int = 7
    max_storage_gb: float = 0.0
    max_storage_percent: int = 0
    cleanup_interval_hours: int = 6
    cleanup_hour: int = 3              # ساعت اجرا (0-23)
    cleanup_corrupted_files: bool = True
    disk_full_policy: str = "delete_oldest"  # delete_oldest | stop | rotate
    snapshots_retention_days: int = 30
    exports_retention_days: int = 90

    # ----------------------------------------
    # پشتیبان‌گیری
    # ----------------------------------------
    backup_enabled: bool = False
    backup_path: str = ""
    backup_interval_hours: int = 24
    backup_keep_days: int = 3

    # ----------------------------------------
    # ساختار پوشه
    # ----------------------------------------
    record_folder_by_camera: bool = True
    record_folder_by_day: bool = True
    record_folder_by_hour: bool = False
    record_folder_pattern: str = ""     # الگوی سفارشی، خالی = پیش‌فرض
    use_nvr_name_in_path: bool = True
    incident_lock_enabled: bool = True  # جلوگیری از پاک‌شدن رویدادهای قفل‌شده

    # ----------------------------------------
    # نمای زنده
    # ----------------------------------------
    live_default_layout: str = "2x2"
    live_grid_fps: int = 5
    live_single_fps: int = 15
    live_max_readers: int = 16
    live_auto_reconnect: bool = True
    live_reconnect_delay_sec: int = 5
    live_focus_mode: bool = True
    live_default_transport: str = "auto"  # auto | tcp | udp
    live_show_timestamp: bool = True
    live_show_camera_name: bool = True
    live_show_recording_indicator: bool = True
    live_show_motion_indicator: bool = True
    live_grid_background: str = "#0a0a0a"

    # ----------------------------------------
    # ظاهر
    # ----------------------------------------
    always_on_top: bool = False
    start_minimized: bool = False
    remember_window_geometry: bool = True
    sidebar_width: int = 260

    # ----------------------------------------
    # شروع
    # ----------------------------------------
    autostart: bool = False
    autostart_mediamtx: bool = True
    restore_last_tab: bool = True
    restore_last_layout: bool = True

    # ----------------------------------------
    # هشدارها
    # ----------------------------------------
    sound_enabled: bool = True
    sound_volume: int = 80
    alarm_duration_sec: int = 8
    cooldown_sec: int = 5
    desktop_notifications: bool = True

    # ----------------------------------------
    # اعلان‌های پیام‌رسان
    # ----------------------------------------
    # ایمیل
    notify_email_enabled: bool = False
    notify_email_smtp: str = "smtp.gmail.com"
    notify_email_port: int = 587
    notify_email_user: str = ""
    notify_email_pass: str = ""
    notify_email_to: str = ""
    notify_email_use_tls: bool = True

    # تلگرام
    notify_telegram_enabled: bool = False
    notify_telegram_bot_token: str = ""
    notify_telegram_chat_id: str = ""

    # ایتا
    notify_eitaa_enabled: bool = False
    notify_eitaa_bot_token: str = ""
    notify_eitaa_chat_id: str = ""

    # بله
    notify_bale_enabled: bool = False
    notify_bale_bot_token: str = ""
    notify_bale_chat_id: str = ""

    # روبیکا
    notify_rubika_enabled: bool = False
    notify_rubika_bot_token: str = ""
    notify_rubika_chat_id: str = ""

    # چه رویدادهایی اعلان بفرست
    notify_events: List[str] = field(
        default_factory=lambda: ["motion", "camera_offline"])

    # ----------------------------------------
    # امنیت
    # ----------------------------------------
    max_login_attempts: int = 5
    lock_duration_min: int = 15
    require_password_change_days: int = 0   # 0 = غیرفعال

    # ----------------------------------------
    # MediaMTX و AI
    # ----------------------------------------
    mediamtx_enabled: bool = True
    ai_enabled: bool = False
    ai_confidence_threshold: float = 0.45
    ai_detect_objects: List[str] = field(
        default_factory=lambda: ["person"])

    # ----------------------------------------
    def to_dict(self) -> dict: return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "GlobalSettings":
        g = GlobalSettings()
        for k, v in (d or {}).items():
            if hasattr(g, k):
                try: setattr(g, k, v)
                except Exception: pass

        # Normalize
        g.record_segment_minutes = max(1, min(30, int(g.record_segment_minutes)))
        g.retention_days = max(1, min(3650, int(g.retention_days)))
        if g.record_format not in (".ts", ".mp4"):
            g.record_format = ".ts"
        try:
            g.max_storage_gb = max(0.0, float(g.max_storage_gb or 0))
        except Exception:
            g.max_storage_gb = 0.0
        try:
            g.max_storage_percent = max(0, min(100, int(g.max_storage_percent or 0)))
        except Exception:
            g.max_storage_percent = 0
        if g.theme not in ("dark", "light"): g.theme = "dark"
        if g.font_size not in ("small", "medium", "large"): g.font_size = "medium"
        if g.live_default_transport not in ("auto", "tcp", "udp"):
            g.live_default_transport = "auto"
        if g.disk_full_policy not in ("delete_oldest", "stop", "rotate"):
            g.disk_full_policy = "delete_oldest"
        try:
            g.cleanup_hour = max(0, min(23, int(g.cleanup_hour)))
            g.cleanup_interval_hours = max(1, min(168, int(g.cleanup_interval_hours)))
            g.live_max_readers = max(1, min(64, int(g.live_max_readers)))
            g.sidebar_width = max(200, min(500, int(g.sidebar_width)))
        except Exception: pass
        if not isinstance(g.notify_events, list):
            g.notify_events = ["motion", "camera_offline"]
        if not isinstance(g.ai_detect_objects, list):
            g.ai_detect_objects = ["person"]
        return g