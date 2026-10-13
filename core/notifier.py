# -*- coding: utf-8 -*-
"""
K1 VMS — Notifier
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ارسال اعلان به:
  • ایمیل (SMTP)
  • تلگرام (Bot API)
  • ایتا (Bot API)
  • بله (Bot API)
  • روبیکا (Bot API)
  • اعلان دسکتاپ ویندوز
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations

import smtplib
import ssl
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    print("[Notifier] requests not installed — messenger notifications disabled")


# ============================================================
# ارسال ایمیل
# ============================================================
def send_email(smtp_server: str, port: int, user: str, password: str,
               to_addr: str, subject: str, body: str,
               use_tls: bool = True, timeout: int = 15) -> tuple[bool, str]:
    """ارسال ایمیل با SMTP."""
    if not smtp_server or not user or not to_addr:
        return False, "اطلاعات SMTP کامل نیست"
    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, password)
                server.sendmail(user, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP_SSL(smtp_server, port, timeout=timeout) as server:
                server.login(user, password)
                server.sendmail(user, [to_addr], msg.as_string())

        return True, "ارسال شد"
    except Exception as e:
        return False, str(e)[:200]


# ============================================================
# ارسال به Bot API (تلگرام / ایتا / بله)
# ============================================================
def _send_bot_api(url: str, payload: dict, timeout: int = 10) -> tuple[bool, str]:
    if not _HAS_REQUESTS:
        return False, "کتابخانه requests نصب نیست"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code == 200:
            try:
                data = r.json()
                if data.get("ok") is False:
                    return False, data.get("description", "خطای نامشخص")
            except Exception:
                pass
            return True, "ارسال شد"
        return False, f"HTTP {r.status_code}: {r.text[:150]}"
    except Exception as e:
        return False, str(e)[:200]


def send_telegram(bot_token: str, chat_id: str,
                  message: str) -> tuple[bool, str]:
    if not bot_token or not chat_id:
        return False, "توکن یا chat_id خالی است"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    return _send_bot_api(url, {"chat_id": chat_id, "text": message})


def send_bale(bot_token: str, chat_id: str,
              message: str) -> tuple[bool, str]:
    if not bot_token or not chat_id:
        return False, "توکن یا chat_id خالی است"
    url = f"https://tapi.bale.ai/bot{bot_token}/sendMessage"
    return _send_bot_api(url, {"chat_id": chat_id, "text": message})


def send_eitaa(bot_token: str, chat_id: str,
               message: str) -> tuple[bool, str]:
    """ایتا از API مشابه تلگرام استفاده می‌کند."""
    if not bot_token or not chat_id:
        return False, "توکن یا chat_id خالی است"
    # EitaaYar API
    url = "https://eitaayar.ir/api/sendMessage"
    return _send_bot_api(url, {
        "token": bot_token,
        "chat_id": chat_id,
        "text": message,
    })


def send_rubika(bot_token: str, chat_id: str,
                message: str) -> tuple[bool, str]:
    """روبیکا از API مخصوص خودش استفاده می‌کند."""
    if not bot_token or not chat_id:
        return False, "توکن یا chat_id خالی است"
    # Rubika Bot API (ساده‌شده)
    url = f"https://botapi.rubika.ir/v3/{bot_token}/sendMessage"
    return _send_bot_api(url, {
        "chat_id": chat_id,
        "text": message,
    })


# ============================================================
# اعلان دسکتاپ ویندوز
# ============================================================
def send_desktop_notification(title: str, message: str,
                              duration_sec: int = 5) -> tuple[bool, str]:
    """اعلان دسکتاپ ویندوز."""
    try:
        # تلاش با plyer
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                timeout=duration_sec,
            )
            return True, "ارسال شد"
        except ImportError:
            pass

        # fallback: win10toast
        try:
            from win10toast import ToastNotifier
            toast = ToastNotifier()
            toast.show_toast(
                title=title,
                msg=message,
                duration=duration_sec,
                threaded=True,
            )
            return True, "ارسال شد"
        except ImportError:
            pass

        # fallback: PowerShell (بدون نصب پکیج)
        try:
            import subprocess
            ps_cmd = (
                f'[void][System.Reflection.Assembly]::LoadWithAssembly('
                f'[System.Reflection.Assembly]::Load("System.Windows.Forms"));'
                f'$n=New-Object System.Windows.Forms.NotifyIcon;'
                f'$n.Icon=[System.Drawing.SystemIcons]::Information;'
                f'$n.Visible=$true;'
                f'$n.ShowBalloonTip({duration_sec*1000},'
                f'"{title}","{message}",'
                f'[System.Windows.Forms.ToolTipIcon]::Info)'
            )
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                creationflags=0x08000000,
            )
            return True, "ارسال شد"
        except Exception as e:
            return False, str(e)[:200]

    except Exception as e:
        return False, str(e)[:200]


# ============================================================
# Notifier — واسط اصلی
# ============================================================
class Notifier:
    _instance = None
    _lock = threading.RLock()

    @classmethod
    def instance(cls) -> "Notifier":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self._last_sent: dict[str, float] = {}
        self._rate_limit_sec = 60

    def _rate_ok(self, key: str) -> bool:
        """جلوگیری از اسپم — هر کلید هر ۶۰ ثانیه یک بار."""
        now = time.time()
        last = self._last_sent.get(key, 0)
        if now - last < self._rate_limit_sec:
            return False
        self._last_sent[key] = now
        return True

    def notify(self, settings, event_type: str,
               title: str, message: str,
               rate_limit_key: Optional[str] = None) -> dict:
        """
        ارسال اعلان به همه کانال‌های فعال.

        Args:
            event_type: نوع رویداد (motion, camera_offline, ...)
            title: عنوان
            message: متن
            rate_limit_key: کلید برای جلوگیری از اسپم

        Returns:
            dict: {کانال: (success, message)}
        """
        # آیا این رویداد در لیست events فعال است؟
        events = getattr(settings, "notify_events", ["motion"])
        if event_type not in events:
            return {}

        if rate_limit_key and not self._rate_ok(rate_limit_key):
            return {}

        results = {}

        # ---- ایمیل ----
        if getattr(settings, "notify_email_enabled", False):
            ok, msg = send_email(
                smtp_server=getattr(settings, "notify_email_smtp", ""),
                port=int(getattr(settings, "notify_email_port", 587)),
                user=getattr(settings, "notify_email_user", ""),
                password=getattr(settings, "notify_email_pass", ""),
                to_addr=getattr(settings, "notify_email_to", ""),
                subject=f"[K1 VMS] {title}",
                body=message,
                use_tls=bool(getattr(settings, "notify_email_use_tls", True)),
            )
            results["email"] = (ok, msg)

        # ---- تلگرام ----
        if getattr(settings, "notify_telegram_enabled", False):
            ok, msg = send_telegram(
                getattr(settings, "notify_telegram_bot_token", ""),
                getattr(settings, "notify_telegram_chat_id", ""),
                f"🔔 {title}\n\n{message}",
            )
            results["telegram"] = (ok, msg)

        # ---- بله ----
        if getattr(settings, "notify_bale_enabled", False):
            ok, msg = send_bale(
                getattr(settings, "notify_bale_bot_token", ""),
                getattr(settings, "notify_bale_chat_id", ""),
                f"🔔 {title}\n\n{message}",
            )
            results["bale"] = (ok, msg)

        # ---- ایتا ----
        if getattr(settings, "notify_eitaa_enabled", False):
            ok, msg = send_eitaa(
                getattr(settings, "notify_eitaa_bot_token", ""),
                getattr(settings, "notify_eitaa_chat_id", ""),
                f"🔔 {title}\n\n{message}",
            )
            results["eitaa"] = (ok, msg)

        # ---- روبیکا ----
        if getattr(settings, "notify_rubika_enabled", False):
            ok, msg = send_rubika(
                getattr(settings, "notify_rubika_bot_token", ""),
                getattr(settings, "notify_rubika_chat_id", ""),
                f"🔔 {title}\n\n{message}",
            )
            results["rubika"] = (ok, msg)

        # ---- اعلان دسکتاپ ----
        if getattr(settings, "desktop_notifications", True):
            ok, msg = send_desktop_notification(title, message)
            results["desktop"] = (ok, msg)

        for ch, (ok, msg) in results.items():
            status = "✓" if ok else "✗"
            print(f"[Notifier] {status} {ch}: {msg}")

        return results

    def test_all(self, settings) -> dict:
        """تست همه کانال‌های فعال — برای دکمه «تست» در تنظیمات."""
        results = {}

        if getattr(settings, "notify_email_enabled", False):
            ok, msg = send_email(
                smtp_server=getattr(settings, "notify_email_smtp", ""),
                port=int(getattr(settings, "notify_email_port", 587)),
                user=getattr(settings, "notify_email_user", ""),
                password=getattr(settings, "notify_email_pass", ""),
                to_addr=getattr(settings, "notify_email_to", ""),
                subject="[K1 VMS] تست اعلان",
                body="این یک پیام تست از K1 VMS است.",
                use_tls=bool(getattr(settings, "notify_email_use_tls", True)),
            )
            results["ایمیل"] = (ok, msg)

        if getattr(settings, "notify_telegram_enabled", False):
            ok, msg = send_telegram(
                getattr(settings, "notify_telegram_bot_token", ""),
                getattr(settings, "notify_telegram_chat_id", ""),
                "✅ تست K1 VMS — تلگرام")
            results["تلگرام"] = (ok, msg)

        if getattr(settings, "notify_bale_enabled", False):
            ok, msg = send_bale(
                getattr(settings, "notify_bale_bot_token", ""),
                getattr(settings, "notify_bale_chat_id", ""),
                "✅ تست K1 VMS — بله")
            results["بله"] = (ok, msg)

        if getattr(settings, "notify_eitaa_enabled", False):
            ok, msg = send_eitaa(
                getattr(settings, "notify_eitaa_bot_token", ""),
                getattr(settings, "notify_eitaa_chat_id", ""),
                "✅ تست K1 VMS — ایتا")
            results["ایتا"] = (ok, msg)

        if getattr(settings, "notify_rubika_enabled", False):
            ok, msg = send_rubika(
                getattr(settings, "notify_rubika_bot_token", ""),
                getattr(settings, "notify_rubika_chat_id", ""),
                "✅ تست K1 VMS — روبیکا")
            results["روبیکا"] = (ok, msg)

        if getattr(settings, "desktop_notifications", True):
            ok, msg = send_desktop_notification(
                "K1 VMS", "✅ تست اعلان دسکتاپ")
            results["دسکتاپ"] = (ok, msg)

        return results