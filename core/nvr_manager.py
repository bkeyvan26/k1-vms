# -*- coding: utf-8 -*-
"""K1 VMS — NVR Manager (Phase 10.4: simplified + folder sync only)"""
import json
import re
import threading
from pathlib import Path
from typing import List, Optional

from core.models import (
    NVRDevice, NVRChannel, CameraConfig, StreamProfile, new_uid,
    ROLE_RECORDING, ROLE_LIVE_VIEW, ROLE_MOTION, ROLE_GRID,
)
import config


NVR_FILE = config.DATA_DIR / "nvrs.json"


class NVRManager:
    _instance = None
    _lock = threading.RLock()

    @classmethod
    def instance(cls) -> "NVRManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self._nvrs: List[NVRDevice] = []
        self._load()

    # ============================================================
    def _load(self):
        if not NVR_FILE.exists():
            self._nvrs = []
            return
        try:
            data = json.loads(NVR_FILE.read_text(encoding="utf-8"))
            items = data.get("nvrs") if isinstance(data, dict) else data
            self._nvrs = [NVRDevice.from_dict(d) for d in (items or [])]
            print(f"[NVRManager] loaded {len(self._nvrs)} NVR(s)")
        except Exception as e:
            print(f"[NVRManager] load failed: {e}")
            self._nvrs = []

    def _save(self):
        try:
            payload = {"nvrs": [n.to_dict() for n in self._nvrs]}
            NVR_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[NVRManager] save failed: {e}")

    # ============================================================
    # CRUD
    # ============================================================
    def all(self) -> List[NVRDevice]:
        return list(self._nvrs)

    def get(self, uid: str) -> Optional[NVRDevice]:
        for n in self._nvrs:
            if n.uid == uid:
                return n
        return None

    def add(self, nvr: NVRDevice) -> NVRDevice:
        if not nvr.uid:
            nvr.uid = new_uid()
        self._nvrs.append(nvr)
        self._save()
        return nvr

    def update(self, uid: str, nvr: NVRDevice):
        for i, n in enumerate(self._nvrs):
            if n.uid == uid:
                nvr.uid = uid
                self._nvrs[i] = nvr
                self._save()
                return

    def delete(self, uid: str):
        self._nvrs = [n for n in self._nvrs if n.uid != uid]
        self._save()

    def find_by_ip(self, ip: str) -> Optional[NVRDevice]:
        if not ip:
            return None
        for n in self._nvrs:
            if n.ip == ip:
                return n
        return None

    # ============================================================
    # sync_folder_names
    # ============================================================
    def sync_folder_names(self, camera_manager) -> int:
        updated = 0
        for nvr in self._nvrs:
            folder = (nvr.record_folder_name or "").strip()
            if not folder:
                continue
            for cam in camera_manager.all():
                if cam.nvr_uid != nvr.uid:
                    continue
                current = getattr(cam, "record_folder_name", "") or ""
                if current != folder:
                    cam.record_folder_name = folder
                    try:
                        camera_manager.update(cam.uid, cam)
                        updated += 1
                    except Exception as e:
                        print(f"[NVRManager] sync folder failed "
                              f"for {cam.name}: {e}")
        if updated:
            print(f"[NVRManager] ✓ synced folder_name for "
                  f"{updated} camera(s)")
        return updated

    # ============================================================
    # Channel → Camera
    # ============================================================
    @staticmethod
    def channel_to_camera(nvr: NVRDevice, ch: NVRChannel) -> CameraConfig:
        cam = CameraConfig()
        cam.name = f"{nvr.name} دوربین {ch.channel_id}".strip()
        cam.enabled = True
        cam.ip = nvr.ip
        cam.port = nvr.rtsp_port
        cam.user = nvr.user
        cam.password = nvr.password
        cam.nvr_uid = nvr.uid
        cam.nvr_name = nvr.name
        cam.record_folder_name = (nvr.record_folder_name or "").strip()

        main = StreamProfile(
            id="nvr_main",
            name="Main",
            url=ch.rtsp_url_main or "",
            resolution=ch.resolution or "",
            codec=ch.codec or "",
            roles=[ROLE_RECORDING, ROLE_LIVE_VIEW],
            discovered_by="nvr_onvif",
        )
        cam.stream_profiles.append(main)

        if ch.rtsp_url_sub:
            sub = StreamProfile(
                id="nvr_sub",
                name="Sub",
                url=ch.rtsp_url_sub,
                roles=[ROLE_MOTION, ROLE_GRID, ROLE_LIVE_VIEW],
                discovered_by="nvr_onvif",
            )
            cam.stream_profiles.append(sub)
            cam.motion_profile_id = "nvr_sub"
            cam.grid_profile_id = "nvr_sub"
        else:
            cam.motion_profile_id = "nvr_main"
            cam.grid_profile_id = "nvr_main"

        cam.recording_profile_id = "nvr_main"
        cam.live_profile_id = "nvr_main"
        # ★ مقدار اولیه = مقدار فعلی NVR
        record = bool(getattr(nvr, "record_channels", False))
        cam.record_enabled_continuous = record
        cam.record_enabled_motion = record
        return cam

    # ============================================================
    # add_channels_as_cameras — فقط افزودن + sync نام پوشه
    # (ضبط در cameras_page.py مدیریت می‌شود)
    # ============================================================
    def add_channels_as_cameras(self, nvr: NVRDevice, camera_manager,
                                only_enabled: bool = True) -> int:
        added = 0
        skipped = 0
        new_folder = (nvr.record_folder_name or "").strip()

        for ch in nvr.channels:
            existing = camera_manager.find_by_nvr_channel(
                nvr.uid, ch.channel_id)

            if existing is not None:
                # فقط folder name sync
                if new_folder and getattr(
                        existing, "record_folder_name", "") != new_folder:
                    existing.record_folder_name = new_folder
                    try:
                        camera_manager.update(existing.uid, existing)
                    except Exception:
                        pass
                skipped += 1
                continue

            if only_enabled and not ch.enabled:
                continue

            cam = self.channel_to_camera(nvr, ch)
            try:
                camera_manager.add(cam)
                added += 1
            except Exception as e:
                print(f"[NVRManager] add channel {ch.channel_id} failed: {e}")

        print(f"[NVRManager] {nvr.name}: added={added} skipped={skipped}")
        return added

    # ============================================================
    def count(self) -> int:
        return len(self._nvrs)

    def total_channels(self) -> int:
        return sum(len(n.channels) for n in self._nvrs)