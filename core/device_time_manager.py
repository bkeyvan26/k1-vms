# -*- coding: utf-8 -*-
"""K1 VMS — Device Time Manager (Phase 17.0)

★ تغییرات Phase 17.0:
  - read_at per device
  - cancel() واقعی برای لغو عملیات
  - _soap_call برای user management (رفع No element 'User')
  - MNA NTP + setCurrentTime اجباری
  - تشخیص برند: Dahua/MNA اول (رفع اشتباه Hikvision)
"""
import datetime
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

try:
    from onvif import ONVIFCamera
    HAS_ONVIF = True
except ImportError:
    ONVIFCamera = None
    HAS_ONVIF = False

try:
    from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
    HAS_WS_DISCOVERY = True
except ImportError:
    WSDiscovery = None
    HAS_WS_DISCOVERY = False

try:
    from core import http_time_setter as http_ts
    HAS_HTTP_API = True
except ImportError:
    http_ts = None
    HAS_HTTP_API = False

try:
    from core import settings_manager
    HAS_SETTINGS = True
except ImportError:
    settings_manager = None
    HAS_SETTINGS = False


ONVIF_PORT_DEFAULT = 80
ONVIF_PORT_ALT = 8000
CONNECT_TIMEOUT_SEC = 6
BATCH_WORKERS = 12
CREDENTIALS_KEY = "device_time_credentials"

HTTP_ONLY_NTP_BRANDS = {"dahua", "mna", "kdt", "axis"}
HTTP_FIRST_BRANDS = {"dahua", "hikvision", "mna", "kdt", "axis", "uniview", ""}


# ============================================================
# Data Model
# ============================================================
@dataclass
class DeviceTimeInfo:
    uid: str
    name: str
    ip: str
    port: int = ONVIF_PORT_DEFAULT
    user: str = "admin"
    password: str = ""

    reachable: bool = False
    current_dt: Optional[datetime.datetime] = None
    timezone: str = ""
    error: str = ""
    brand: str = "unknown"
    protocol: str = ""
    read_at: Optional[datetime.datetime] = None

    def to_dict(self):
        return {
            "uid": self.uid, "name": self.name, "ip": self.ip,
            "port": self.port, "user": self.user, "password": self.password,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            uid=d.get("uid", ""), name=d.get("name", ""),
            ip=d.get("ip", ""), port=int(d.get("port", ONVIF_PORT_DEFAULT)),
            user=d.get("user", "admin"), password=d.get("password", ""),
        )


# ============================================================
# Manager
# ============================================================
class DeviceTimeManager:
    def __init__(self):
        if not HAS_ONVIF:
            print("[DeviceTimeManager] WARNING: onvif-zeep not installed")
        if not HAS_HTTP_API:
            print("[DeviceTimeManager] WARNING: http_time_setter not available")
        self._devices: List[DeviceTimeInfo] = []
        self._cancelled = False

    def set_devices(self, devices):
        self._devices = list(devices)

    def get_devices(self):
        return list(self._devices)

    def cancel(self):
        """درخواست لغو عملیات جاری."""
        self._cancelled = True
        print("[DTM] cancel requested")

    # ============================================================
    # Credentials
    # ============================================================
    @staticmethod
    def load_credentials() -> Dict[str, Dict[str, str]]:
        if not HAS_SETTINGS:
            return {}
        try:
            s = settings_manager.load_settings()
            raw = getattr(s, CREDENTIALS_KEY, None)
            if raw is None and hasattr(s, "__dict__"):
                raw = s.__dict__.get(CREDENTIALS_KEY)
            if isinstance(raw, str) and raw:
                raw = json.loads(raw)
            if isinstance(raw, dict):
                return raw
        except Exception as e:
            print(f"[DTM] load creds: {e}")
        return {}

    @staticmethod
    def save_credentials(creds) -> bool:
        if not HAS_SETTINGS:
            return False
        try:
            s = settings_manager.load_settings()
            setattr(s, CREDENTIALS_KEY, creds)
            settings_manager.save_settings(s)
            return True
        except Exception as e:
            print(f"[DTM] save creds: {e}")
            return False

    @staticmethod
    def update_credentials(ip, user, password, port=ONVIF_PORT_DEFAULT) -> bool:
        creds = DeviceTimeManager.load_credentials()
        creds[ip] = {"user": user, "password": password, "port": int(port)}
        return DeviceTimeManager.save_credentials(creds)

    @staticmethod
    def remove_credentials(ip) -> bool:
        creds = DeviceTimeManager.load_credentials()
        if ip in creds:
            del creds[ip]
            return DeviceTimeManager.save_credentials(creds)
        return True

    # ============================================================
    # ONVIF helpers
    # ============================================================
    @staticmethod
    def _connect(dev, user=None, password=None):
        if not HAS_ONVIF:
            return None
        u = user if user is not None else dev.user
        p = password if password is not None else dev.password
        for port in (dev.port or ONVIF_PORT_DEFAULT, ONVIF_PORT_ALT):
            try:
                return ONVIFCamera(dev.ip, port, u, p)
            except Exception:
                continue
        return None

    @staticmethod
    def _detect_brand(cam) -> str:
        try:
            info = cam.devicemgmt.GetDeviceInformation()
            m = (info.Manufacturer or "").lower()
            if "hikvision" in m: return "hikvision"
            if "dahua" in m: return "dahua"
            if "uniview" in m or "unv" in m: return "uniview"
            if "mna" in m: return "mna"
            if "kdt" in m: return "kdt"
            if "axis" in m: return "axis"
            return m or "unknown"
        except Exception:
            return "unknown"

    # ============================================================
    # SOAP raw calls (رفع WSDL ناقص)
    # ============================================================
    def _soap_call(self, dev, action, body_inner=""):
        """درخواست SOAP خام — بدون نیاز به WSDL کامل."""
        import requests
        from requests.auth import HTTPDigestAuth
        url = f"http://{dev.ip}:{dev.port or 80}/onvif/device_service"
        body = f"<tds:{action}>{body_inner}</tds:{action}>"
        env = f'''<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
  <s:Body>{body}</s:Body>
</s:Envelope>'''
        try:
            r = requests.post(
                url, data=env.encode("utf-8"),
                auth=HTTPDigestAuth(dev.user, dev.password),
                headers={"Content-Type":
                         "application/soap+xml; charset=utf-8"},
                timeout=CONNECT_TIMEOUT_SEC)
            return r.status_code, (r.text or "")
        except Exception as e:
            return 0, str(e)[:200]

    # ============================================================
    # READ
    # ============================================================
    def _read_one(self, dev):
        read_at = datetime.datetime.now(datetime.timezone.utc)

        # Axis اول HTTP
        if (dev.brand or "").lower() == "axis" and HAS_HTTP_API:
            try:
                ok, msg = http_ts.axis_get_time(dev.ip, dev.user, dev.password)
                if ok:
                    dev.reachable = True
                    dev.protocol = "http_axis"
                    dev.error = ""
                    try:
                        dev.current_dt = datetime.datetime.fromtimestamp(
                            int(msg), tz=datetime.timezone.utc)
                    except Exception:
                        pass
                    dev.read_at = read_at
                    return dev
            except Exception:
                pass

        # ONVIF
        cam = self._connect(dev)
        if cam is not None:
            try:
                dev.brand = self._detect_brand(cam)
                dt_resp = cam.devicemgmt.GetSystemDateAndTime()
                utc = dt_resp.UTCDateTime
                if utc is not None:
                    dev.current_dt = datetime.datetime(
                        utc.Date.Year, utc.Date.Month, utc.Date.Day,
                        utc.Time.Hour, utc.Time.Minute, utc.Time.Second,
                        tzinfo=datetime.timezone.utc)
                if dt_resp.TimeZone and dt_resp.TimeZone.TZ:
                    dev.timezone = dt_resp.TimeZone.TZ
                dev.reachable = True
                dev.protocol = "onvif"
                dev.error = ""
                dev.read_at = read_at
                return dev
            except Exception as e:
                dev.error = f"ONVIF: {str(e)[:80]}"

        # HTTP fallback
        if HAS_HTTP_API:
            try:
                ok, msg = http_ts.dahua_get_time(dev.ip, dev.user, dev.password)
                if ok:
                    dev.reachable = True
                    dev.protocol = "http_dahua"
                    dev.error = ""
                    try:
                        dev.current_dt = datetime.datetime.strptime(
                            msg, "%Y-%m-%d %H:%M:%S").replace(
                                tzinfo=datetime.timezone.utc)
                    except Exception:
                        pass
                    dev.read_at = read_at
                    return dev
            except Exception:
                pass

            try:
                ok, msg = http_ts.hikvision_get_time(dev.ip, dev.user, dev.password)
                if ok:
                    dev.reachable = True
                    dev.protocol = "http_hikvision"
                    dev.error = ""
                    try:
                        dev.current_dt = datetime.datetime.fromisoformat(
                            msg).replace(tzinfo=datetime.timezone.utc)
                    except Exception:
                        pass
                    dev.read_at = read_at
                    return dev
            except Exception:
                pass

        if not dev.error:
            dev.error = "بدون ONVIF و HTTP API شناخته‌شده"
        dev.read_at = read_at
        return dev

    def read_all_times(self, on_progress=None):
        return self._run_batch(self._read_one, on_progress)

    # ============================================================
    # SET TIME
    # ============================================================
    def _set_manual_time(self, dev, target_dt):
        brand = (dev.brand or "").lower()

        if HAS_HTTP_API and brand in HTTP_FIRST_BRANDS:
            try:
                ok, msg, b = http_ts.detect_and_set_time(
                    dev.ip, dev.user, dev.password, target_dt,
                    brand_hint=dev.brand)
                if ok:
                    dev.reachable = True
                    dev.brand = b
                    dev.protocol = f"http_{b}"
                    dev.error = ""
                    return dev
            except Exception:
                pass

        try:
            cam = self._connect(dev)
            if cam is not None:
                dev.brand = self._detect_brand(cam) or dev.brand
                if target_dt.tzinfo is None:
                    target_dt = target_dt.astimezone()
                utc_dt = target_dt.astimezone(datetime.timezone.utc)
                tp = cam.devicemgmt.create_type("SetSystemDateAndTime")
                tp.DateTimeType = "Manual"
                tp.DaylightSavings = False
                try:
                    offset = datetime.datetime.now().astimezone().utcoffset()
                    if offset is not None:
                        tm = int(offset.total_seconds() / 60)
                        sign = "+" if tm >= 0 else "-"
                        hh = abs(tm) // 60
                        mm = abs(tm) % 60
                        tp.TimeZone.TZ = f"UTC{sign}{hh:02d}:{mm:02d}"
                except Exception:
                    pass
                tp.UTCDateTime.Date.Year = utc_dt.year
                tp.UTCDateTime.Date.Month = utc_dt.month
                tp.UTCDateTime.Date.Day = utc_dt.day
                tp.UTCDateTime.Time.Hour = utc_dt.hour
                tp.UTCDateTime.Time.Minute = utc_dt.minute
                tp.UTCDateTime.Time.Second = utc_dt.second
                cam.devicemgmt.SetSystemDateAndTime(tp)
                dev.reachable = True
                dev.protocol = "onvif"
                dev.error = ""
                return dev
        except Exception as e:
            dev.error = f"ONVIF: {str(e)[:80]}"

        if HAS_HTTP_API and brand not in HTTP_FIRST_BRANDS:
            try:
                ok, msg, b = http_ts.detect_and_set_time(
                    dev.ip, dev.user, dev.password, target_dt,
                    brand_hint=dev.brand)
                if ok:
                    dev.reachable = True
                    dev.brand = b
                    dev.protocol = f"http_{b}"
                    dev.error = ""
                    return dev
                dev.error = f"HTTP {b}: {msg[:80]}"
            except Exception as e:
                dev.error = f"HTTP: {str(e)[:80]}"
        return dev

    def sync_all_to_pc(self, on_progress=None):
        now = datetime.datetime.now()
        return self._run_batch(
            lambda d: self._set_manual_time(d, now), on_progress)

    def set_time_batch(self, devices, target_dt, on_progress=None):
        self.set_devices(devices)
        return self._run_batch(
            lambda d: self._set_manual_time(d, target_dt), on_progress)

    # ============================================================
    # NTP
    # ============================================================
    def _set_ntp(self, dev, ntp_server):
        brand = (dev.brand or "").lower()

        if brand in ("", "unknown") and HAS_HTTP_API:
            try:
                detected, model = http_ts.detect_brand(
                    dev.ip, dev.user, dev.password)
                if detected != "unknown":
                    dev.brand = detected
                    brand = detected
                    print(f"[NTP] {dev.ip} → brand: {brand}")
            except Exception as e:
                print(f"[NTP] {dev.ip} detect exc: {e}")

        # Axis
        if brand == "axis":
            if not HAS_HTTP_API:
                dev.error = "HTTP module not available"
                return dev
            try:
                print(f"[NTP] {dev.ip} → VAPIX (axis)...")
                ok, msg = http_ts.axis_set_ntp(
                    dev.ip, dev.user, dev.password, ntp_server)
                if ok:
                    dev.reachable = True
                    dev.protocol = "http_axis"
                    dev.error = ""
                    print(f"[NTP] {dev.ip} → VAPIX ✓ {msg[:80]}")
                    return dev
                dev.error = f"NTP VAPIX: {msg[:100]}"
                return dev
            except Exception as e:
                dev.error = f"NTP VAPIX: {str(e)[:100]}"
                return dev

        # Dahua / MNA / KDT
        if brand in ("dahua", "mna", "kdt"):
            if not HAS_HTTP_API:
                dev.error = "HTTP module not available"
                return dev
            try:
                print(f"[NTP] {dev.ip} → HTTP ({brand})...")
                ok, msg, b = http_ts.detect_and_set_ntp(
                    dev.ip, dev.user, dev.password, ntp_server,
                    brand_hint=brand)
                if ok:
                    dev.reachable = True
                    dev.brand = b
                    dev.protocol = f"http_{b}"
                    dev.error = ""
                    print(f"[NTP] {dev.ip} → HTTP {b} ✓ {msg[:80]}")
                    return dev
                dev.error = f"NTP HTTP: {msg[:100]}"
                return dev
            except Exception as e:
                dev.error = f"NTP HTTP: {str(e)[:100]}"
                return dev

        # Hikvision
        if brand == "hikvision":
            if HAS_HTTP_API:
                try:
                    ok, msg, b = http_ts.detect_and_set_ntp(
                        dev.ip, dev.user, dev.password, ntp_server,
                        brand_hint=brand)
                    if ok:
                        dev.reachable = True
                        dev.brand = b
                        dev.protocol = f"http_{b}"
                        dev.error = ""
                        return dev
                except Exception:
                    pass
            try:
                cam = self._connect(dev)
                if cam is not None:
                    tp = cam.devicemgmt.create_type("SetSystemDateAndTime")
                    tp.DateTimeType = "NTP"
                    tp.DaylightSavings = False
                    try:
                        tp.NTP = cam.devicemgmt.create_type("NTPInformation")
                        tp.NTP.FromDHCP = False
                        tp.NTP.NTPManual = cam.devicemgmt.create_type(
                            "NetworkInterface")
                        tp.NTP.NTPManual.Type = "IPv4"
                        tp.NTP.NTPManual.IPv4Address = ntp_server
                    except Exception:
                        pass
                    cam.devicemgmt.SetSystemDateAndTime(tp)
                    dev.reachable = True
                    dev.protocol = "onvif"
                    dev.error = ""
                    return dev
            except Exception as e:
                dev.error = f"ONVIF: {str(e)[:80]}"
            return dev

        # بقیه برندها
        try:
            cam = self._connect(dev)
            if cam is not None:
                dev.brand = self._detect_brand(cam) or dev.brand
                tp = cam.devicemgmt.create_type("SetSystemDateAndTime")
                tp.DateTimeType = "NTP"
                tp.DaylightSavings = False
                try:
                    tp.NTP = cam.devicemgmt.create_type("NTPInformation")
                    tp.NTP.FromDHCP = False
                    tp.NTP.NTPManual = cam.devicemgmt.create_type(
                        "NetworkInterface")
                    tp.NTP.NTPManual.Type = "IPv4"
                    tp.NTP.NTPManual.IPv4Address = ntp_server
                except Exception:
                    pass
                cam.devicemgmt.SetSystemDateAndTime(tp)
                dev.reachable = True
                dev.protocol = "onvif"
                dev.error = ""
                return dev
        except Exception as e:
            dev.error = f"ONVIF: {str(e)[:80]}"

        if HAS_HTTP_API:
            try:
                ok, msg, b = http_ts.detect_and_set_ntp(
                    dev.ip, dev.user, dev.password, ntp_server,
                    brand_hint=dev.brand)
                if ok:
                    dev.reachable = True
                    dev.brand = b
                    dev.protocol = f"http_{b}"
                    dev.error = ""
                    return dev
                dev.error = f"HTTP {b}: {msg[:80]}"
            except Exception as e:
                dev.error = f"HTTP: {str(e)[:80]}"
        return dev

    def enable_ntp_all(self, ntp_server="pool.ntp.org", on_progress=None):
        return self._run_batch(
            lambda d: self._set_ntp(d, ntp_server), on_progress)

    # ============================================================
    # TIMEZONE
    # ============================================================
    def _set_timezone(self, dev, tz_value):
        if HAS_HTTP_API:
            try:
                ok, msg, b = http_ts.detect_and_set_timezone(
                    dev.ip, dev.user, dev.password, tz_value,
                    brand_hint=dev.brand)
                if ok:
                    dev.reachable = True
                    dev.brand = b
                    dev.protocol = f"http_{b}"
                    dev.error = ""
                    return dev
                dev.error = f"TZ {b}: {msg[:80]}"
            except Exception as e:
                dev.error = f"TZ: {str(e)[:80]}"
        return dev

    def set_timezone_batch(self, devices, tz_value, on_progress=None):
        self.set_devices(devices)
        return self._run_batch(
            lambda d: self._set_timezone(d, tz_value), on_progress)

    # ============================================================
    # USER MANAGEMENT (SOAP raw)
    # ============================================================
    def get_users(self, dev):
        cam = self._connect(dev)
        if cam is not None:
            try:
                resp = cam.devicemgmt.GetUsers()
                users = []
                for u in (resp or []):
                    users.append({
                        "username": getattr(u, "Username", "") or "",
                        "level": getattr(u, "UserLevel", "") or "User",
                    })
                if users:
                    return True, users, ""
            except Exception:
                pass

        # SOAP raw
        code, text = self._soap_call(dev, "GetUsers")
        if code != 200:
            return False, [], f"HTTP {code}"
        users = []
        for m in re.finditer(
            r"<[^>]*Username[^>]*>([^<]+)</[^>]*Username[^>]*>", text):
            users.append({"username": m.group(1).strip(), "level": "User"})
        if not users:
            return False, [], "پاسخ نامعتبر از دستگاه"
        return True, users, ""

    def add_user(self, dev, username, password, level="User"):
        inner = (f"<tds:User>"
                  f"<tds:Username>{username}</tds:Username>"
                  f"<tds:Password>{password}</tds:Password>"
                  f"<tds:UserLevel>{level}</tds:UserLevel>"
                  f"</tds:User>")
        code, text = self._soap_call(dev, "CreateUsers", inner)
        if code == 200:
            return True, ""
        inner2 = inner.replace("<tds:User>", "<tds:Users>").replace(
            "</tds:User>", "</tds:Users>")
        code2, _ = self._soap_call(dev, "CreateUsers", inner2)
        if code2 == 200:
            return True, ""
        return False, f"HTTP {code}: {text[:200]}"

    def set_user(self, dev, username, password, level=None):
        lv = f"<tds:UserLevel>{level}</tds:UserLevel>" if level else ""
        inner = (f"<tds:User>"
                  f"<tds:Username>{username}</tds:Username>"
                  f"<tds:Password>{password}</tds:Password>"
                  f"{lv}</tds:User>")
        code, text = self._soap_call(dev, "SetUser", inner)
        if code == 200:
            return True, ""
        inner2 = inner.replace("<tds:User>", "<tds:Users>").replace(
            "</tds:User>", "</tds:Users>")
        code2, _ = self._soap_call(dev, "SetUser", inner2)
        if code2 == 200:
            return True, ""
        return False, f"HTTP {code}: {text[:200]}"

    def delete_user(self, dev, username):
        inner = f"<tds:Username>{username}</tds:Username>"
        code, text = self._soap_call(dev, "DeleteUsers", inner)
        if code == 200:
            return True, ""
        return False, f"HTTP {code}: {text[:200]}"

    # ============================================================
    # BATCH runner با cancel flag
    # ============================================================
    def _run_batch(self, fn, on_progress=None):
        results = []
        total = len(self._devices)
        if total == 0:
            return results

        self._cancelled = False

        with ThreadPoolExecutor(max_workers=BATCH_WORKERS) as ex:
            futures = {ex.submit(fn, dev): dev for dev in self._devices}
            done = 0
            for fut in as_completed(futures):
                if self._cancelled:
                    print("[DTM] cancelled by user")
                    break
                dev = futures[fut]
                try:
                    result = fut.result()
                except Exception as e:
                    dev.error = str(e)[:200]
                    result = dev
                results.append(result)
                done += 1
                if on_progress:
                    try:
                        on_progress(done, total, result)
                    except Exception:
                        pass
        return results

    # ============================================================
    # Discovery & Build
    # ============================================================
    @staticmethod
    def discover_devices(timeout=5):
        found = []
        if not HAS_WS_DISCOVERY:
            return found
        try:
            wsd = WSDiscovery()
            wsd.start()
            services = wsd.searchServices(timeout=timeout)
            for svc in services:
                xaddrs = svc.getXAddrs()
                if not xaddrs:
                    continue
                found.append({
                    "xaddr": xaddrs[0],
                    "scopes": " ".join(svc.getScopes() or []),
                })
            wsd.stop()
        except Exception as e:
            print(f"[DTM] discovery: {e}")
        return found

    @staticmethod
    def build_device_list_from_cameras(cameras, apply_saved_credentials=True):
        saved = (DeviceTimeManager.load_credentials()
                 if apply_saved_credentials else {})
        devices = []
        seen_ips = set()
        for cam in cameras:
            ip = getattr(cam, "ip", "") or ""
            if not ip or ip in seen_ips:
                continue
            seen_ips.add(ip)

            user = getattr(cam, "user", "") or "admin"
            password = getattr(cam, "password", "") or ""
            port = ONVIF_PORT_DEFAULT

            if ip in saved:
                creds = saved[ip]
                user = creds.get("user", user) or user
                password = creds.get("password", password) or password
                port = int(creds.get("port", port) or port)

            nvr_name = getattr(cam, "nvr_name", "") or ""
            name = nvr_name if nvr_name else (getattr(cam, "name", "") or ip)

            devices.append(DeviceTimeInfo(
                uid=getattr(cam, "uid", "") or ip,
                name=name, ip=ip, port=port,
                user=user, password=password,
            ))
        return devices

    @staticmethod
    def ping_host(ip, timeout=1.5):
        import subprocess, platform
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=timeout + 1)
            return r.returncode == 0
        except Exception:
            return False