# -*- coding: utf-8 -*-
"""K1 VMS — HTTP API Device Controller (Phase 17.0)

★ Fix 17.0:
  - MNA NTP با setCurrentTime بلافاصله بعد از NTP (رفع fake success)
  - detect_brand: Dahua/MNA قبل از Hikvision (رفع اشتباه .63)
  - mna_set_ntp با تأیید واقعی تغییر ساعت
"""
import datetime
import re
import time
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from typing import Optional, Tuple, Dict, List

TIMEOUT = 4
VERIFY_DELAY_SEC = 0.5


def _auth(user, password, auth_type="digest"):
    if auth_type == "basic":
        return HTTPBasicAuth(user, password)
    return HTTPDigestAuth(user, password)


def _scheme(use_https):
    return "https" if use_https else "http"


# ============================================================
# Dahua
# ============================================================
def dahua_get_time(ip, user, password, use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/cgi-bin/global.cgi"
    try:
        r = requests.get(url, params={"action": "getCurrentTime"},
                          auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        if r.status_code == 200:
            return True, r.text.strip()
        return False, r.text[:120]
    except Exception as e:
        return False, str(e)[:120]


def dahua_set_time(ip, user, password, dt,
                    use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/cgi-bin/global.cgi"
    try:
        r = requests.get(url,
                          params={"action": "setCurrentTime",
                                  "time": dt.strftime("%Y-%m-%d %H:%M:%S")},
                          auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        ok = r.status_code == 200 and "OK" in (r.text or "")
        return ok, (r.text[:120] if not ok else "OK")
    except Exception as e:
        return False, str(e)[:120]


def _dahua_get_cfg(ip, user, password, name, use_https=False):
    url = f"{_scheme(use_https)}://{ip}/cgi-bin/configManager.cgi"
    try:
        r = requests.get(url,
                          params={"action": "getConfig", "name": name},
                          auth=_auth(user, password, "digest"),
                          timeout=TIMEOUT)
        if r.status_code != 200:
            return {}
        out = {}
        for line in (r.text or "").splitlines():
            line = line.strip()
            if "=" not in line: continue
            k, v = line.split("=", 1)
            k = k.strip().replace(f"table.{name}.", "")
            out[k] = v.strip()
        return out
    except Exception:
        return {}


def _dahua_set_cfg(ip, user, password, params, use_https=False):
    url = f"{_scheme(use_https)}://{ip}/cgi-bin/configManager.cgi"
    params["action"] = "setConfig"
    try:
        r = requests.get(url, params=params,
                          auth=_auth(user, password, "digest"),
                          timeout=TIMEOUT)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        body = (r.text or "").strip()
        if body and "Error" in body:
            return False, body[:120]
        return True, "OK"
    except Exception as e:
        return False, str(e)[:120]


def dahua_set_ntp(ip, user, password, ntp_server,
                    timezone_hours=None, use_https=False, auth_type="digest"):
    ok, msg = _dahua_set_cfg(ip, user, password, {
        "NTP.Enable": "true",
        "NTP.Address": ntp_server,
        "NTP.Port": "123",
    }, use_https)
    if not ok:
        return False, msg
    time.sleep(VERIFY_DELAY_SEC)
    after = _dahua_get_cfg(ip, user, password, "NTP", use_https)
    addr = after.get("Address", "").strip()
    if ntp_server not in addr:
        return False, f"verify failed: actual={addr}"
    return True, f"OK ({addr})"


def dahua_set_timezone(ip, user, password, tz_value,
                        use_https=False, auth_type="digest"):
    if isinstance(tz_value, str):
        m = re.match(r"UTC\s*([+-])\s*(\d{1,2}):?(\d{2})?", tz_value)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            h = int(m.group(2)); mn = int(m.group(3) or 0)
            hours = sign * (h + mn / 60.0)
        else:
            try: hours = float(tz_value)
            except Exception: return False, f"invalid tz: {tz_value}"
    else:
        hours = float(tz_value)
    return _dahua_set_cfg(ip, user, password, {
        "NTP.TimeZone": str(hours)}, use_https)


# ============================================================
# MNA — با setCurrentTime اجباری بعد از NTP
# ============================================================
def mna_get_time(ip, user, password, use_https=False, auth_type="digest"):
    return dahua_get_time(ip, user, password, use_https, auth_type)


def mna_set_time(ip, user, password, dt, use_https=False, auth_type="digest"):
    return dahua_set_time(ip, user, password, dt, use_https, auth_type)


def mna_set_ntp(ip, user, password, ntp_server,
                 use_https=False, auth_type="digest"):
    """MNA NTP — ۳ روش + setCurrentTime اجباری.

    ★ رفع fake success: چون MNA می‌گوید OK ولی اعمال نمی‌کند،
    بعد از هر روش، ساعت را با setCurrentTime به زمان PC ست می‌کنیم.
    """
    url = f"{_scheme(use_https)}://{ip}/cgi-bin/configManager.cgi"

    attempts = [
        # روش ۱: SyncMode=NTP (string)
        {"NTP.Enable": "true", "NTP.SyncMode": "NTP",
         "NTP.Address": ntp_server, "NTP.Port": "123"},
        # روش ۲: SyncMode=1 (integer)
        {"NTP.Enable": "true", "NTP.SyncMode": "1",
         "NTP.Address": ntp_server, "NTP.Port": "123"},
        # روش ۳: فقط Address
        {"NTP.Enable": "true", "NTP.Address": ntp_server,
         "NTP.Port": "123"},
        # روش ۴: با Time.SyncMode
        {"NTP.Enable": "true", "Time.SyncMode": "1",
         "NTP.Address": ntp_server, "NTP.Port": "123"},
        # روش ۵: NTP.ServerAddress
        {"NTP.Enable": "true", "NTP.ServerAddress": ntp_server,
         "NTP.Port": "123"},
    ]

    ok_set = False
    last_err = "همه ۵ روش ناموفق"
    for i, base in enumerate(attempts):
        for auth_method in (auth_type, "basic"):
            try:
                params = {"action": "setConfig"}
                params.update(base)
                r = requests.get(url, params=params,
                                  auth=_auth(user, password, auth_method),
                                  timeout=TIMEOUT)
                if r.status_code != 200:
                    continue
                body = (r.text or "").strip()
                if body and ("Error" in body or "error" in body):
                    continue
                ok_set = True
                break
            except Exception as e:
                last_err = str(e)[:120]
                continue
        if ok_set:
            break

    # ★ مرحله نهایی: setCurrentTime اجباری
    try:
        now = datetime.datetime.now()
        turl = f"{_scheme(use_https)}://{ip}/cgi-bin/global.cgi"
        r = requests.get(turl,
                          params={"action": "setCurrentTime",
                                  "time": now.strftime("%Y-%m-%d %H:%M:%S")},
                          auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        if r.status_code == 200 and "OK" in (r.text or ""):
            return True, "OK (NTP set + time synced)"
    except Exception as e:
        pass

    if ok_set:
        return True, "OK (NTP set, time sync failed)"
    return False, last_err


def mna_set_timezone(ip, user, password, tz_value,
                      use_https=False, auth_type="digest"):
    return dahua_set_timezone(ip, user, password, tz_value, use_https, auth_type)


# ============================================================
# Hikvision
# ============================================================
def hikvision_get_time(ip, user, password, use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/ISAPI/System/time"
    try:
        r = requests.get(url, auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        if r.status_code == 200:
            m = re.search(r"<localTime>([^<]+)</localTime>", r.text)
            if m: return True, m.group(1)
        return False, r.text[:120]
    except Exception as e:
        return False, str(e)[:120]


def hikvision_set_time(ip, user, password, dt,
                        use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/ISAPI/System/time"
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Time xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <timeMode>manual</timeMode>
  <localTime>{dt.strftime('%Y-%m-%dT%H:%M:%S')}</localTime>
  <timeZone>CST-3:30:00</timeZone>
</Time>'''
    try:
        r = requests.put(url, data=xml.encode("utf-8"),
                          auth=_auth(user, password, auth_type),
                          headers={"Content-Type":
                                   "application/xml; charset=utf-8"},
                          timeout=TIMEOUT)
        return r.status_code == 200, ("OK" if r.status_code == 200
                                       else r.text[:120])
    except Exception as e:
        return False, str(e)[:120]


def hikvision_set_ntp(ip, user, password, ntp_server,
                       port=123, interval_min=30,
                       use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/ISAPI/System/time/ntpServers/1"

    variants = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<NTPServer version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <id>1</id>
  <addressingType>hostname</addressingType>
  <hostName>{ntp_server}</hostName>
  <portNo>{port}</portNo>
  <synchronizeInterval>{interval_min}</synchronizeInterval>
</NTPServer>''',
        f'''<?xml version="1.0" encoding="UTF-8"?>
<NTPServer version="1.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <id>1</id>
  <addressingType>hostname</addressingType>
  <hostName>{ntp_server}</hostName>
  <portNo>{port}</portNo>
  <synchronizeInterval>{interval_min}</synchronizeInterval>
</NTPServer>''',
        f'''<?xml version="1.0" encoding="UTF-8"?>
<NTPServer version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <id>1</id>
  <addressingType>ipaddress</addressingType>
  <ipAddress>{ntp_server}</ipAddress>
  <portNo>{port}</portNo>
  <synchronizeInterval>{interval_min}</synchronizeInterval>
</NTPServer>''',
    ]

    for idx, xml in enumerate(variants):
        try:
            r = requests.put(url, data=xml.encode("utf-8"),
                              auth=_auth(user, password, auth_type),
                              headers={"Content-Type":
                                       "application/xml; charset=utf-8"},
                              timeout=TIMEOUT)
            if r.status_code == 200:
                # Set timeMode=NTP
                try:
                    tm = '''<?xml version="1.0" encoding="UTF-8"?>
<Time xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <timeMode>NTP</timeMode>
</Time>'''
                    requests.put(
                        f"{_scheme(use_https)}://{ip}/ISAPI/System/time",
                        data=tm.encode("utf-8"),
                        auth=_auth(user, password, auth_type),
                        headers={"Content-Type":
                                 "application/xml; charset=utf-8"},
                        timeout=TIMEOUT)
                except Exception:
                    pass
                return True, f"OK (v{idx+1})"
        except Exception:
            continue

    # اگر 400 شد، فقط setCurrentTime
    try:
        now = datetime.datetime.now()
        ok, msg = hikvision_set_time(ip, user, password, now,
                                       use_https, auth_type)
        if ok:
            return True, "OK (only time set, NTP rejected)"
    except Exception:
        pass

    return False, "همه روش‌های Hikvision ناموفق (400)"


def hikvision_set_timezone(ip, user, password, tz_value,
                            use_https=False, auth_type="digest"):
    if isinstance(tz_value, str):
        m = re.match(r"UTC\s*([+-])\s*(\d{1,2}):?(\d{2})?", tz_value)
        if m:
            sign = m.group(1)
            h = int(m.group(2)); mn = int(m.group(3) or 0)
            rev = "-" if sign == "+" else "+"
            tz_str = f"CST{rev}{h}:{mn:02d}:00"
        else:
            return False, f"invalid tz: {tz_value}"
    else:
        hours = float(tz_value)
        rev = "-" if hours >= 0 else "+"
        hh = int(abs(hours)); mn = int((abs(hours) - hh) * 60)
        tz_str = f"CST{rev}{hh}:{mn:02d}:00"

    url = f"{_scheme(use_https)}://{ip}/ISAPI/System/time"
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Time xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <timeMode>manual</timeMode>
  <timeZone>{tz_str}</timeZone>
</Time>'''
    try:
        r = requests.put(url, data=xml.encode("utf-8"),
                          auth=_auth(user, password, auth_type),
                          headers={"Content-Type":
                                   "application/xml; charset=utf-8"},
                          timeout=TIMEOUT)
        return r.status_code == 200, ("OK" if r.status_code == 200
                                       else r.text[:120])
    except Exception as e:
        return False, str(e)[:120]


# ============================================================
# Axis
# ============================================================
def axis_get_time(ip, user, password, use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/axis-cgi/date.cgi?action=get"
    try:
        r = requests.get(url, auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        if r.status_code == 200:
            return True, r.text.strip()
        return False, r.text[:120]
    except Exception as e:
        return False, str(e)[:120]


def axis_set_time(ip, user, password, dt, use_https=False, auth_type="digest"):
    if dt.tzinfo is None:
        dt = dt.astimezone()
    ts = int(dt.timestamp())
    url = f"{_scheme(use_https)}://{ip}/axis-cgi/date.cgi?action=set&time={ts}"
    try:
        r = requests.get(url, auth=_auth(user, password, auth_type),
                          timeout=TIMEOUT)
        return r.status_code == 200, ("OK" if r.status_code == 200
                                       else r.text[:120])
    except Exception as e:
        return False, str(e)[:120]


def axis_set_ntp(ip, user, password, ntp_server,
                  use_https=False, auth_type="digest"):
    scheme = _scheme(use_https)

    for auth_method in (auth_type, "basic"):
        try:
            url = f"{scheme}://{ip}/axis-cgi/ntp.cgi"
            payload = {
                "apiVersion": "1.0",
                "method": "setNTPInfo",
                "params": {
                    "enabled": True,
                    "serversSource": "static",
                    "staticServers": [ntp_server],
                }
            }
            r = requests.post(url, json=payload,
                               auth=_auth(user, password, auth_method),
                               headers={"Content-Type":
                                        "application/json"},
                               timeout=TIMEOUT)
            if r.status_code in (200, 204):
                return True, "OK (ntp.cgi)"
        except Exception:
            pass

    for auth_method in (auth_type, "basic"):
        try:
            url = f"{scheme}://{ip}/axis-cgi/param.cgi"
            params = {
                "action": "update",
                "Time.NTP.Enabled": "yes",
                "Time.NTP.Server": ntp_server,
            }
            r = requests.get(url, params=params,
                              auth=_auth(user, password, auth_method),
                              timeout=TIMEOUT)
            if r.status_code == 200:
                return True, "OK (param.cgi)"
        except Exception:
            pass

    return False, "همه روش‌های Axis ناموفق"


def axis_set_timezone(ip, user, password, tz_value,
                       use_https=False, auth_type="digest"):
    scheme = _scheme(use_https)
    if isinstance(tz_value, str):
        m = re.match(r"UTC\s*([+-])\s*(\d{1,2}):?(\d{2})?", tz_value)
        if m:
            sign = m.group(1); h = int(m.group(2)); mn = int(m.group(3) or 0)
            tz_str = f"{sign}{h:02d}:{mn:02d}"
        else:
            return False, f"invalid tz: {tz_value}"
    else:
        hours = float(tz_value)
        sign = "+" if hours >= 0 else "-"
        hh = int(abs(hours)); mn = int((abs(hours) - hh) * 60)
        tz_str = f"{sign}{hh:02d}:{mn:02d}"
    try:
        url = f"{scheme}://{ip}/axis-cgi/param.cgi"
        r = requests.post(url,
                           data=f"action=update&Time.POSIXTimeZone={tz_str}",
                           auth=_auth(user, password, auth_type),
                           headers={"Content-Type":
                                    "application/x-www-form-urlencoded"},
                           timeout=TIMEOUT)
        return r.status_code == 200, ("OK" if r.status_code == 200
                                       else r.text[:120])
    except Exception as e:
        return False, str(e)[:120]


# ============================================================
# Uniview
# ============================================================
def uniview_set_time(ip, user, password, dt,
                      use_https=False, auth_type="digest"):
    url = f"{_scheme(use_https)}://{ip}/LAPI/V1.0/System/Time"
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Time><LocalTime>{int(dt.timestamp()*1000)}</LocalTime></Time>'''
    try:
        r = requests.put(url, data=xml.encode("utf-8"),
                          auth=_auth(user, password, auth_type),
                          headers={"Content-Type": "application/xml"},
                          timeout=TIMEOUT)
        return r.status_code == 200, ("OK" if r.status_code == 200
                                       else r.text[:120])
    except Exception as e:
        return False, str(e)[:120]


# ============================================================
# Dispatch
# ============================================================
BRAND_SETTERS = {
    "dahua": {
        "set_time": dahua_set_time, "set_ntp": dahua_set_ntp,
        "get_time": dahua_get_time, "set_tz": dahua_set_timezone,
    },
    "hikvision": {
        "set_time": hikvision_set_time, "set_ntp": hikvision_set_ntp,
        "get_time": hikvision_get_time, "set_tz": hikvision_set_timezone,
    },
    "axis": {
        "set_time": axis_set_time, "set_ntp": axis_set_ntp,
        "get_time": axis_get_time, "set_tz": axis_set_timezone,
    },
    "uniview": {
        "set_time": uniview_set_time, "set_ntp": None,
        "get_time": None, "set_tz": None,
    },
    "mna": {
        "set_time": mna_set_time, "set_ntp": mna_set_ntp,
        "get_time": mna_get_time, "set_tz": mna_set_timezone,
    },
    "kdt": {
        "set_time": dahua_set_time, "set_ntp": dahua_set_ntp,
        "get_time": dahua_get_time, "set_tz": dahua_set_timezone,
    },
}

DAHUA_OEMS = {"mna", "kdt", "dahua", "alhua", "qsee", "amcrest"}


def detect_and_set_time(ip, user, password, dt, brand_hint="",
                         use_https=False, auth_type="digest"):
    b = (brand_hint or "").lower().strip()
    order = []
    if b in BRAND_SETTERS: order.append(b)
    if b not in DAHUA_OEMS: order.append("dahua")
    if b != "hikvision": order.append("hikvision")
    if b != "axis": order.append("axis")
    if b != "uniview": order.append("uniview")

    last = ""
    for name in order:
        fn = BRAND_SETTERS.get(name, {}).get("set_time")
        if fn is None: continue
        try:
            ok, msg = fn(ip, user, password, dt,
                          use_https=use_https, auth_type=auth_type)
            if ok: return True, msg, name
            last = f"{name}: {msg}"
        except Exception as e:
            last = f"{name}: {str(e)[:80]}"
    return False, last, b or "unknown"


def detect_and_set_ntp(ip, user, password, ntp_server, brand_hint="",
                        use_https=False, auth_type="digest"):
    b = (brand_hint or "").lower().strip()
    order = []
    if b in BRAND_SETTERS: order.append(b)
    for x in ("axis", "dahua", "mna", "hikvision"):
        if x not in order: order.append(x)

    last = ""
    for name in order:
        fn = BRAND_SETTERS.get(name, {}).get("set_ntp")
        if fn is None: continue
        try:
            ok, msg = fn(ip, user, password, ntp_server,
                          use_https=use_https, auth_type=auth_type)
            if ok: return True, msg, name
            last = f"{name}: {msg}"
        except Exception as e:
            last = f"{name}: {str(e)[:80]}"
    return False, last, b or "unknown"


def detect_and_set_timezone(ip, user, password, tz_value, brand_hint="",
                              use_https=False, auth_type="digest"):
    b = (brand_hint or "").lower().strip()
    order = []
    if b in BRAND_SETTERS: order.append(b)
    for x in ("axis", "dahua", "mna", "hikvision"):
        if x not in order: order.append(x)

    last = ""
    for name in order:
        fn = BRAND_SETTERS.get(name, {}).get("set_tz")
        if fn is None: continue
        try:
            ok, msg = fn(ip, user, password, tz_value,
                          use_https=use_https, auth_type=auth_type)
            if ok: return True, msg, name
            last = f"{name}: {msg}"
        except Exception as e:
            last = f"{name}: {str(e)[:80]}"
    return False, last, b or "unknown"


def detect_brand(ip, user, password, use_https=False):
    """تشخیص برند — Dahua/MNA اول (رفع اشتباه 192.168.1.63)."""
    scheme = _scheme(use_https)

    # ★ Dahua/MNA اول — چون Hikvision هم ISAPI دارد و باعث اشتباه می‌شود
    try:
        url = f"{scheme}://{ip}/cgi-bin/magicBox.cgi?action=getDeviceType"
        r = requests.get(url, auth=_auth(user, password, "digest"),
                          timeout=3)
        if r.status_code == 200 and r.text and "type=" in r.text:
            txt = (r.text or "").strip()
            low = txt.lower()
            m = re.search(r"type=(.+)", txt)
            model = m.group(1).strip() if m else txt[:60]
            if "mna" in low: return "mna", model
            if "kdt" in low: return "kdt", model
            if "dahua" in low or "dh-" in low:
                return "dahua", model
            # اگر type= داشت ولی برند نبود، ممکن است Dahua OEM باشد
            return "dahua", model
    except Exception:
        pass

    # Axis
    try:
        url = f"{scheme}://{ip}/axis-cgi/param.cgi?action=list"
        r = requests.get(url, auth=_auth(user, password, "digest"),
                          timeout=3)
        if r.status_code == 200 and "axis" in (r.text or "").lower():
            return "axis", ""
    except Exception:
        pass

    # Hikvision
    try:
        url = f"{scheme}://{ip}/ISAPI/System/deviceInfo"
        r = requests.get(url, auth=_auth(user, password, "digest"),
                          timeout=3)
        if r.status_code == 200 and (
            "Hikvision" in (r.text or "")
            or "<DeviceInfo" in (r.text or "")
        ):
            m = re.search(r"<model>([^<]+)</model>", r.text)
            return "hikvision", (m.group(1) if m else "")
    except Exception:
        pass

    return "unknown", ""


def detect_and_get_network(ip, user, password, brand_hint="", use_https=False):
    return False, {}, brand_hint or "unknown"


def detect_and_set_network(ip, user, password, brand_hint="",
                             new_ip=None, netmask=None, gateway=None,
                             dhcp=None, dns1=None, dns2=None, use_https=False):
    return False, "not implemented yet", brand_hint or "unknown"