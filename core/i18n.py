# -*- coding: utf-8 -*-
"""K1 VMS — سیستم دو زبانه (فارسی / انگلیسی)"""
from __future__ import annotations


_TRANSLATIONS = {
    "fa": {
        # ============================================================
        # عمومی
        # ============================================================
        "app.title": "K1 VMS",
        "common.ok": "تأیید",
        "common.cancel": "انصراف",
        "common.yes": "بله",
        "common.no": "خیر",
        "common.save": "ذخیره",
        "common.edit": "ویرایش",
        "common.delete": "حذف",
        "common.close": "بستن",
        "common.error": "خطا",
        "common.warning": "هشدار",
        "common.info": "اطلاع",
        "common.confirm": "تأیید",
        "common.loading": "در حال انجام…",
        "common.apply": "اعمال",
        "common.refresh": "بازخوانی",
        "common.new": "جدید",

        # ============================================================
        # هدر بالا
        # ============================================================
        "header.user": "کاربر",
        "header.search": "جستجو…",
        "header.no_alarms": "بدون هشدار",
        "header.ai_disabled": "هوش مصنوعی غیرفعال",
        "header.ai_ready": "هوش مصنوعی آماده",
        "header.ai_processing": "در حال پردازش",
        "header.ai_error": "خطای هوش مصنوعی",
        "header.ai_short": "هوش مصنوعی",
        "header.online_count": "{online} / {total} آنلاین",
        "header.offline_all": "همه‌ی {total} آفلاین",
        "header.no_cameras": "بدون دوربین",
        "header.alarms": "{n} هشدار",
        "header.not_recording": "بدون ضبط",
        "header.rec_count": "{n} در حال ضبط",
        "header.rec_none": "۰ از {total} در حال ضبط",
        "header.rec_count_total": "{active} از {total} در حال ضبط",

        # ============================================================
        # پنجره اصلی
        # ============================================================
        "main.ready": "آماده",
        "main.user_dialog.title": "کاربر",
        "main.user_dialog.msg": "مدیریت کاربران در فاز ۷ اضافه می‌شود.",
        "main.panel.no_options": "گزینه‌ای برای {title} نیست",

        # ============================================================
        # تب‌های اصلی
        # ============================================================
        "tab.live": "پخش زنده",
        "tab.cameras": "دوربین‌ها",
        "tab.playback": "پخش مجدد",
        "tab.dashboard": "داشبورد",

        # ============================================================
        # صفحه دوربین‌ها
        # ============================================================
        "cam.title": "مدیریت دوربین و دستگاه ضبط",
        "cam.btn.add_camera": "افزودن دوربین",
        "cam.btn.add_nvr": "افزودن دستگاه ضبط",
        "cam.btn.groups": "گروه‌ها",
        "cam.btn.bulk": "افزودن گروهی",
        "cam.btn.apply": "به‌روزرسانی اتصال‌ها",
        "cam.btn.edit": "ویرایش",
        "cam.btn.delete": "حذف",
        "cam.search.ph": "جستجوی دوربین یا دستگاه…",
        "cam.hint": (
            "ساختار درختی: دستگاه‌های ضبط و گروه‌ها با کانال‌هایشان.\n"
            "☑ برای انتخاب گروهی، چک‌باکس هر ردیف را تیک بزنید."
        ),
        "cam.count": "{cams} دوربین • {nvrs} دستگاه • {groups} گروه",

        # ============================================================
        # Live View
        # ============================================================
        "live.title": "پخش زنده",
        "live.layout": "چیدمان",
        "live.tab.new": "+ تب جدید",
        "live.panel.cameras_nvr": "دوربین‌ها و دستگاه‌ها",
        "live.hint": (
            "• Drag دستگاه/گروه روی کاشی: همه پخش شوند\n"
            "• راست‌کلیک روی دستگاه/گروه: پخش/توقف\n"
            "• روی کاشی آفلاین: دکمه «اتصال مجدد»"
        ),
        "live.status.ready": "آماده",
        "live.status.connecting": "در حال اتصال…",
        "live.cell.reconnect": "اتصال مجدد",
        "live.cell.offline": "آفلاین",
        "live.cell.drop_camera": "این‌جا رها کنید",
        "live.cell.cells": "کاشی‌ها: {n}",

        # ============================================================
        # NVR Dialog
        # ============================================================
        "nvr.title.add": "افزودن دستگاه ضبط",
        "nvr.title.edit": "ویرایش دستگاه ضبط: {name}",
        "nvr.group.connection": "اطلاعات اتصال",
        "nvr.name": "نام دستگاه:",
        "nvr.name.ph": "مثلاً: دستگاه طبقه اول",
        "nvr.folder": "نام پوشه ذخیره:",
        "nvr.folder.ph": "مثلاً: parkings  یا negahbani",
        "nvr.folder.hint": "فقط حروف انگلیسی، اعداد، _ و - مجاز است.",
        "nvr.record": "ضبط تصاویر:",
        "nvr.record.cb": "تصاویر همه‌ی دوربین‌های این دستگاه ضبط شوند؟",
        "nvr.record.hint": "پیش‌فرض: خاموش — بعداً برای هر دوربین جداگانه قابل تغییر است.",
        "nvr.brand": "برند سازنده:",
        "nvr.brand.auto": "تشخیص خودکار",
        "nvr.ip": "آدرس IP:",
        "nvr.port": "درگاه اتصال:",
        "nvr.port.hint": "معمولاً نیازی به تغییر مقادیر پیش‌فرض نیست.",
        "nvr.user": "نام کاربری:",
        "nvr.pass": "رمز عبور:",
        "nvr.group.manual": "الگوی آدرس دستی (فقط برای دستگاه‌های قدیمی‌تر)",
        "nvr.manual.hint": (
            "اگر دستگاه شما از جستجوی خودکار پشتیبانی نمی‌کند، "
            "آدرس دقیق را اینجا وارد کنید."
        ),
        "nvr.manual.main": "تصویر اصلی:",
        "nvr.manual.sub": "تصویر کم‌حجم:",
        "nvr.manual.vars": (
            "متغیرها: {user} کاربر — {pwd} رمز — {ip} آدرس — "
            "{port} درگاه — {ch} شماره — {stream} نوع"
        ),
        "nvr.discover": "جستجوی خودکار دوربین‌ها",
        "nvr.channels.info": "دوربین‌های پیدا شده — موارد دلخواه را تیک بزنید:",
        "nvr.channels.select_all": "انتخاب همه",
        "nvr.channels.deselect_all": "حذف انتخاب همه",
        "nvr.channels.count": "{selected} از {total} انتخاب شده",
        "nvr.btn.save": "ذخیره",
        "nvr.btn.cancel": "انصراف",

        # ============================================================
        # Camera Dialog
        # ============================================================
        "camdlg.title.add": "افزودن دوربین",
        "camdlg.title.edit": "ویرایش: {name}",
        "camdlg.tab.connection": "اتصال",
        "camdlg.tab.streams": "استریم و لایو",
        "camdlg.tab.recording": "ضبط",
        "camdlg.tab.motion": "حرکت",
        "camdlg.tab.ai": "هوش مصنوعی",
        "camdlg.name": "نام دوربین:",
        "camdlg.folder": "نام پوشه ضبط:",
        "camdlg.enabled": "دوربین فعال باشد",
        "camdlg.ip": "آدرس IP:",
        "camdlg.port": "پورت RTSP:",
        "camdlg.user": "نام کاربری:",
        "camdlg.pass": "رمز عبور:",
        "camdlg.rec.continuous": "ضبط دائمی (۲۴ ساعته)",
        "camdlg.rec.motion": "ضبط هنگام تشخیص حرکت",
        "camdlg.rec.segment": "طول هر قطعه:",
        "camdlg.rec.path": "مسیر اختصاصی:",
        "camdlg.save": "ذخیره",
        "camdlg.cancel": "انصراف",

        # ============================================================
        # گروه‌ها
        # ============================================================
        "grp.title.manager": "مدیریت گروه‌ها",
        "grp.btn.new": "گروه جدید",
        "grp.btn.edit": "ویرایش",
        "grp.btn.delete": "حذف",
        "grp.btn.close": "بستن",
        "grp.name": "نام گروه:",
        "grp.color": "رنگ گروه:",
        "grp.cameras": "دوربین‌های این گروه:",
        "grp.empty": "هنوز گروهی ساخته نشده است.",
        "grp.empty.hint": "روی «گروه جدید» کلیک کنید تا اولین گروه ساخته شود.",
        "grp.confirm.delete": 'گروه "{name}" حذف شود؟',

        # ============================================================
        # Bulk ops
        # ============================================================
        "bulk.header": "{n} دوربین انتخاب شده",
        "bulk.delete": "حذف {n} دوربین",
        "bulk.cont": "ضبط دائم (۲۴ ساعته)",
        "bulk.motion": "ضبط هنگام حرکت",
        "bulk.enable": "فعال شود",
        "bulk.disable": "غیرفعال شود",

        # ============================================================
        # Playback
        # ============================================================
        "pb.title": "پخش مجدد",
        "pb.today": "امروز",
        "pb.yesterday": "دیروز",
        "pb.play": "پخش",
        "pb.pause": "توقف",
        "pb.export": "خروجی",
        "pb.live": "پخش زنده",
        "pb.no_camera": "دوربینی انتخاب نشده",
        "pb.no_recording": "ضبطی موجود نیست",
        "pb.search": "جستجو در ضبط…",
        "pb.cameras": "دوربین‌ها",
        "pb.layout": "چیدمان:",
        "pb.tile_1": "۱ کاشی",
        "pb.tile_2": "۲ کاشی",
        "pb.tile_4": "۴ کاشی",
        "pb.tile_9": "۹ کاشی",
        "pb.loading_playback": "در حال آماده‌سازی پخش…",
        "pb.loading_scan": "در حال بررسی تاریخ‌های ضبط…",
        "pb.loading_seek": "در حال رفتن به زمان انتخاب‌شده…",
        "pb.loading_timeline": "در حال آماده‌سازی نوار زمان…",
        "pb.select_camera_first": "ابتدا دوربین و سپس تاریخ ضبط را انتخاب کنید",
        "pb.select_date": "یک تاریخ ضبط را انتخاب کنید",
        "pb.calendar_title": "تقویم ضبط",
        "pb.info_title": "اطلاعات کاشی فعال",
        "pb.segments_title": "قطعات کاشی فعال",
        "pb.camera": "دوربین",
        "pb.date": "تاریخ",
        "pb.time": "زمان",
        "pb.count": "قطعه",
        "pb.no_segment": "بدون قطعه",
        "pb.segment_summary": "{n} قطعه • مجموع {h:02d}:{m:02d}",
        "pb.legend_recorded": "ضبط‌شده",
        "pb.legend_motion": "حرکت",
        "pb.legend_no_motion": "بدون حرکت",
        "pb.legend_no_record": "بدون ضبط",
        "pb.btn_close_cell": "بستن کاشی فعال",
        "pb.btn_snapshot": "عکس فوری",
        "pb.btn_prev_seg": "قطعه قبلی",
        "pb.btn_step_back": "یک فریم عقب",
        "pb.btn_play_pause": "پخش / توقف (Space)",
        "pb.btn_stop": "توقف",
        "pb.btn_step_fwd": "یک فریم جلو",
        "pb.btn_next_seg": "قطعه بعدی",
        "pb.btn_cut": "برش: کلیک ۱ = شروع، کلیک ۲ = پایان",
        "pb.btn_export": "خروجی",
        "pb.btn_fs_cell": "کاشی فعال — تمام‌صفحه",
        "pb.btn_fs_app": "کل برنامه — تمام‌صفحه (F11)",
        "pb.hint": (
            "• دابل کلیک: کاشی خالی بعدی\n"
            "• Drag روی کاشی: همان کاشی\n"
            "• دابل کلیک روی کاشی: تک‌صفحه\n"
            "• 💡 فقط کاشی فعال پخش می‌شود"
        ),
        "pb.menu_close_cell": "بستن کاشی",
        "pb.menu_snapshot": "عکس فوری",
        "pb.menu_exit_fs": "خروج از تمام‌صفحه",
        "pb.menu_fs_cell": "تمام‌صفحه کاشی",
        "pb.menu_export": "خروجی...",
        "pb.menu_drag_hint": "برای بارگذاری، دوربین را drag کن",
        "pb.timeline": "نوار زمان",
        "pb.no_frame_snapshot": "فریمی برای ذخیره وجود ندارد.",
        "pb.saved": "ذخیره شد: {name}",
        "pb.snapshot": "عکس فوری",
        "pb.snapshot_failed": "ذخیره عکس ناموفق بود:\n{e}",
        "pb.cut_invalid": "پایان باید بعد از شروع باشد.",
        "pb.load_camera_first": "ابتدا یک دوربین روی کاشی بارگذاری کنید.",
        "pb.no_recording_today": "برای این روز ضبطی وجود ندارد.",

        # ============================================================
        # Dashboard
        # ============================================================
        "dash.title": "داشبورد",
        "dash.system_overview": "نمای کلی سیستم",
        "dash.cameras_online": "دوربین‌های آنلاین",
        "dash.active_alarms": "هشدارهای فعال",
        "dash.recording": "در حال ضبط",
        "dash.ai_engine": "موتور هوش مصنوعی",
        "dash.recent_events": "رویدادهای اخیر",
        "dash.no_events": "رویداد جدیدی نیست",
        "dash.system_health": "سلامت سیستم",
        "dash.cpu": "پردازنده",
        "dash.ram": "حافظه",
        "dash.storage": "فضای ذخیره",
        "dash.network": "شبکه",

        # ============================================================
        # Icon Rail
        # ============================================================
        "rail.dashboard": "داشبورد  (D)",
        "rail.live": "پخش زنده  (L)",
        "rail.cameras": "دوربین‌ها  (C)",
        "rail.playback": "پخش مجدد  (P)",
        "rail.alarms": "هشدارها  (A)",
        "rail.ai": "هوش مصنوعی  (I)",
        "rail.search": "جستجو  (S)",
        "rail.map": "نقشه  (M)",
        "rail.reports": "گزارش‌ها  (R)",
        "rail.settings": "تنظیمات",
        "rail.users": "کاربران",
        "rail.exit": "خروج",

        # ============================================================
        # Command Bar
        # ============================================================
        "cmd.placeholder": "یک فرمان تایپ کنید یا جستجو…",
        "cmd.dashboard": "داشبورد",
        "cmd.live": "پخش زنده",
        "cmd.cameras": "دوربین‌ها",
        "cmd.playback": "پخش مجدد",
        "cmd.alarms": "هشدارها",
        "cmd.ai": "هوش مصنوعی",
        "cmd.search": "جستجو",
        "cmd.map": "نقشه",
        "cmd.reports": "گزارش‌ها",
        "cmd.settings": "تنظیمات",
        "cmd.users": "کاربران",
        "cmd.exit": "خروج از برنامه",

        # ============================================================
        # Settings — General
        # ============================================================
        "set.title": "تنظیمات",
        "set.saved_ok": "تنظیمات با موفقیت ذخیره شد.",
        "set.save_failed": "ذخیره ناموفق:",
        "set.lang.saved_restart": (
            "تنظیمات ذخیره شد.\n"
            "برای اعمال تغییر زبان، برنامه را دوباره باز کنید."
        ),

        # ----------------------------------------
        # Tabs
        # ----------------------------------------
        "set.tab.recording": "ضبط",
        "set.tab.storage": "حافظه",
        "set.tab.folders": "ساختار پوشه",
        "set.tab.live": "نمای زنده",
        "set.tab.appearance": "ظاهر",
        "set.tab.startup": "شروع",
        "set.tab.alarms": "هشدارها",
        "set.tab.notify": "اعلان‌ها",
        "set.tab.security": "امنیت",
        "set.tab.about": "درباره",

        # ============================================================
        # Recording Tab
        # ============================================================
        "set.record.title": "رفتار ضبط",
        "set.record.hint": "تنظیمات کلی ضبط پیوسته دوربین‌ها.",
        "set.record.enabled": "ضبط پیوسته به‌صورت پیش‌فرض فعال باشد",
        "set.record.segment": "طول هر قطعه ضبط:",
        "set.record.format": "فرمت فایل خروجی:",
        "set.record.segment_hint": "قطعه‌های کوچک‌تر = مدیریت راحت‌تر. قطعه‌های بزرگ‌تر = فایل‌های کمتر.",

        "set.record.motion_title": "ضبط حرکتی",
        "set.record.motion_hint": "ضبط فقط زمانی که حرکت تشخیص داده می‌شود.",
        "set.record.motion_enabled": "ضبط حرکتی فعال باشد",
        "set.record.motion_after": "چند ثانیه بعد از حرکت هم ضبط ادامه یابد",
        "set.record.pre_buffer": "ضبط قبل از حرکت (ثانیه):",
        "set.record.post_buffer": "ضبط بعد از حرکت (ثانیه):",
        "set.record.sensitivity": "حساسیت پیش‌فرض حرکت:",
        "set.record.min_area": "حداقل ناحیه حرکت (پیکسل):",

        "set.record.health_title": "سلامت ضبط",
        "set.record.health_hint": "رفتار سیستم در شرایط خاص.",
        "set.record.corrupted_cleanup": "حذف خودکار فایل‌های خراب",
        "set.record.disk_policy": "وقتی دیسک پر شد:",
        "set.record.disk_policy.delete": "قدیمی‌ترین‌ها پاک شوند",
        "set.record.disk_policy.stop": "ضبط متوقف شود",
        "set.record.disk_policy.rotate": "چرخش خودکار",

        # ============================================================
        # Storage Tab
        # ============================================================
        "set.storage.title": "وضعیت حافظه",
        "set.storage.hint": "مصرف فعلی دیسک و اطلاعات فایل‌های ضبط‌شده.",
        "set.storage.disk_used": "مصرف کل دیسک",
        "set.storage.rec_size": "حجم ضبط‌ها",
        "set.storage.file_count": "تعداد فایل‌ها",
        "set.storage.oldest": "قدیمی‌ترین فایل",
        "set.storage.newest": "جدیدترین فایل",

        "set.storage.policy_title": "سیاست نگهداری",
        "set.storage.policy_hint": "تعیین کنید چه مدت و چه حجمی از ضبط نگهداری شود.",
        "set.storage.auto_cleanup": "پاک‌سازی خودکار فعال باشد",
        "set.storage.keep_days": "نگهداری ضبط‌ها برای:",
        "set.storage.days": "روز",
        "set.storage.max_percent": "حداکثر درصد مصرف دیسک:",
        "set.storage.of_disk": "درصد از کل دیسک",
        "set.storage.max_gb": "یا حداکثر حجم مشخص:",
        "set.storage.unlimited": "بدون محدودیت",
        "set.storage.gb_or_unlimited": "(۰ = نامحدود)",
        "set.storage.quota_hint": (
            "• اگر «درصد» تعیین شود: وقتی مصرف دیسک از این حد گذشت، "
            "قدیمی‌ترین ضبط‌ها پاک می‌شوند.\n"
            "• اگر «حجم مشخص» تعیین شود: مجموع فایل‌های ضبط از این حجم "
            "بیشتر نشود.\n"
            "• ۰ = بدون محدودیت."
        ),
        "set.storage.cleanup_interval": "فاصله اجرای پاک‌سازی:",
        "set.storage.hours": "ساعت",
        "set.storage.cleanup_hour": "ساعت اجرای پاک‌سازی روزانه:",
        "set.storage.snapshots_days": "نگهداری عکس‌های فوری:",
        "set.storage.exports_days": "نگهداری خروجی‌ها:",

        # Backup
        "set.backup.title": "پشتیبان‌گیری",
        "set.backup.hint": "پشتیبان‌گیری خودکار از ضبط‌ها روی مسیر دیگر.",
        "set.backup.enabled": "پشتیبان‌گیری خودکار فعال",
        "set.backup.path": "مسیر پشتیبان:",
        "set.backup.interval": "فاصله پشتیبان‌گیری:",
        "set.backup.keep_days": "نگهداری نسخه‌های پشتیبان (روز):",
        "set.backup.browse": "انتخاب مسیر",

        "set.storage.cleanup_now": "پاک‌سازی همین حالا",
        "set.cleanup_done": "✅ پاک‌سازی انجام شد.",
        "set.cleanup_deleted": "تعداد فایل حذف‌شده",
        "set.cleanup_freed": "فضای آزادشده (MB)",
        "set.cleanup_failed": "خطا در پاک‌سازی:",

        # ============================================================
        # Folders Tab
        # ============================================================
        "set.folders.title": "ساختار پوشه‌های ضبط",
        "set.folders.hint": "نحوه‌ی چیدمان فایل‌های ضبط روی دیسک.",
        "set.folders.by_camera": "پوشه مجزا برای هر دوربین",
        "set.folders.by_day": "زیرپوشه برای هر روز",
        "set.folders.by_hour": "زیرپوشه برای هر ساعت",
        "set.folders.use_nvr_name": "استفاده از نام دستگاه در مسیر",
        "set.folders.pattern": "الگوی سفارشی نام:",
        "set.folders.pattern_ph": "خالی = پیش‌فرض",
        "set.folders.incident_lock": "محافظت از رویدادهای قفل‌شده",
        "set.folders.preview": "پیش‌نمایش مسیر:",

        # ============================================================
        # Live Tab
        # ============================================================
        "set.live.title": "تنظیمات نمای زنده",
        "set.live.hint": "پارامترهای نمایش زنده و کارایی.",
        "set.live.default_layout": "چیدمان پیش‌فرض:",
        "set.live.grid_fps": "نرخ فریم نمایش گرید:",
        "set.live.single_fps": "نرخ فریم نمایش تکی:",
        "set.live.max_readers": "حداکثر دوربین همزمان:",
        "set.live.auto_reconnect": "اتصال مجدد خودکار در صورت قطعی",
        "set.live.reconnect_delay": "تاخیر بین تلاش‌های مجدد:",
        "set.live.focus_mode": "حالت Focus (خاموش کردن بقیه در تکی)",
        "set.live.transport": "نوع اتصال پیش‌فرض:",
        "set.live.transport.auto": "خودکار (TCP → UDP)",
        "set.live.transport.tcp": "TCP (پایدارتر)",
        "set.live.transport.udp": "UDP (سریع‌تر)",
        "set.live.overlay_title": "نمایش‌گرهای روی تصویر",
        "set.live.show_timestamp": "نمایش زمان روی تصویر",
        "set.live.show_camera_name": "نمایش نام دوربین",
        "set.live.show_rec_indicator": "نمایش نشانگر ضبط",
        "set.live.show_motion_indicator": "نمایش نشانگر حرکت",

        # ============================================================
        # Appearance Tab
        # ============================================================
        "set.appear.title": "ظاهر برنامه",
        "set.appear.hint": "شخصی‌سازی نمای کلی برنامه.",
        "set.appear.theme": "پوسته برنامه:",
        "set.appear.dark": "تیره",
        "set.appear.light": "روشن",
        "set.appear.font_size": "اندازه فونت:",
        "set.appear.font.small": "کوچک",
        "set.appear.font.medium": "متوسط",
        "set.appear.font.large": "بزرگ",
        "set.appear.compact": "حالت فشرده (فضای کمتر)",
        "set.appear.always_on_top": "پنجره همیشه روی بقیه باشد",
        "set.appear.start_minimized": "شروع به‌صورت Minimize",
        "set.appear.remember_geometry": "به یاد داشتن اندازه و مکان پنجره",
        "set.appear.sidebar_width": "عرض پنل کناری (پیکسل):",

        "set.lang.title": "زبان برنامه",
        "set.lang.hint": "زبان رابط کاربری را انتخاب کنید.",
        "set.lang.note": "⚠ برای اعمال تغییر زبان، برنامه باید دوباره راه‌اندازی شود.",

        # ============================================================
        # Startup Tab
        # ============================================================
        "set.startup.title": "تنظیمات شروع برنامه",
        "set.startup.hint": "رفتار برنامه هنگام روشن شدن ویندوز.",
        "set.startup.autostart": "اجرا هنگام روشن شدن ویندوز",
        "set.startup.mediamtx": "شروع خودکار MediaMTX",
        "set.startup.record": "شروع خودکار ضبط",
        "set.startup.restore_tab": "بازگردانی آخرین تب",
        "set.startup.restore_layout": "بازگردانی آخرین چیدمان",

        # ============================================================
        # Alarms Tab
        # ============================================================
        "set.alarm.title": "هشدارها و صدا",
        "set.alarm.hint": "نحوه اعلان هشدارها.",
        "set.alarm.sound": "صدای هشدار فعال باشد",
        "set.alarm.volume": "بلندی صدا:",
        "set.alarm.duration": "مدت زمان هشدار:",
        "set.alarm.cooldown": "فاصله بین هشدارها:",
        "set.alarm.desktop": "اعلان دسکتاپ ویندوز",

        # ============================================================
        # Notifications Tab
        # ============================================================
        "set.notify.title": "اعلان‌های پیام‌رسان",
        "set.notify.hint": "ارسال هشدار از طریق ایمیل و پیام‌رسان‌ها.",
        "set.notify.events_title": "رویدادهای اعلان",
        "set.notify.events.hint": "برای کدام رویدادها اعلان ارسال شود؟",
        "set.notify.event.motion": "تشخیص حرکت",
        "set.notify.event.camera_offline": "آفلاین شدن دوربین",
        "set.notify.event.camera_online": "آنلاین شدن دوربین",
        "set.notify.event.recording_start": "شروع ضبط",
        "set.notify.event.recording_stop": "پایان ضبط",
        "set.notify.event.storage_low": "کم شدن فضای دیسک",
        "set.notify.event.login_failed": "تلاش ناموفق ورود",
        "set.notify.event.system_start": "شروع برنامه",
        "set.notify.event.system_stop": "بسته شدن برنامه",

        "set.notify.email.title": "ایمیل (SMTP)",
        "set.notify.email.hint": "ارسال اعلان از طریق ایمیل.",
        "set.notify.email.enabled": "ارسال ایمیل فعال باشد",
        "set.notify.email.smtp": "سرور SMTP:",
        "set.notify.email.port": "پورت:",
        "set.notify.email.user": "نام کاربری (ایمیل):",
        "set.notify.email.pass": "رمز عبور:",
        "set.notify.email.to": "ارسال به:",
        "set.notify.email.tls": "استفاده از STARTTLS",

        "set.notify.telegram.title": "تلگرام",
        "set.notify.telegram.hint": "از طریق بات تلگرام.",
        "set.notify.telegram.enabled": "ارسال به تلگرام فعال",
        "set.notify.telegram.token": "توکن بات:",
        "set.notify.telegram.chat": "Chat ID:",

        "set.notify.bale.title": "بله",
        "set.notify.bale.hint": "پیام‌رسان بله (مشابه تلگرام).",
        "set.notify.bale.enabled": "ارسال به بله فعال",
        "set.notify.bale.token": "توکن بات:",
        "set.notify.bale.chat": "Chat ID:",

        "set.notify.eitaa.title": "ایتا",
        "set.notify.eitaa.hint": "پیام‌رسان ایتا.",
        "set.notify.eitaa.enabled": "ارسال به ایتا فعال",
        "set.notify.eitaa.token": "توکن بات:",
        "set.notify.eitaa.chat": "Chat ID:",

        "set.notify.rubika.title": "روبیکا",
        "set.notify.rubika.hint": "پیام‌رسان روبیکا.",
        "set.notify.rubika.enabled": "ارسال به روبیکا فعال",
        "set.notify.rubika.token": "توکن بات:",
        "set.notify.rubika.chat": "Chat ID:",

        "set.notify.test_all": "🧪  تست همه کانال‌ها",
        "set.notify.test_done": "نتیجه تست:",
        "set.notify.test_ok": "✓ ارسال شد",
        "set.notify.test_fail": "✗ ناموفق",
        "set.notify.test_empty": "هیچ کانالی فعال نیست.",

        # ============================================================
        # Security Tab
        # ============================================================
        "set.sec.title": "امنیت ورود",
        "set.sec.hint": "محافظت در برابر تلاش‌های ناموفق ورود.",
        "set.sec.max_attempts": "حداکثر تلاش ناموفق:",
        "set.sec.lock_duration": "مدت قفل حساب:",
        "set.sec.password_change_days": "اجبار تغییر رمز هر ... روز (۰=غیرفعال):",

        # ============================================================
        # AI Tab
        # ============================================================
        "set.ai.title": "هوش مصنوعی",
        "set.ai.hint": "تنظیمات تحلیل تصویر.",
        "set.ai.enabled": "هوش مصنوعی فعال",
        "set.ai.confidence": "حد آستانه اعتماد:",
        "set.ai.detect_person": "تشخیص شخص",
        "set.ai.detect_car": "تشخیص خودرو",
        "set.ai.detect_bike": "تشخیص دوچرخه",

        # ============================================================
        # About Tab
        # ============================================================
        "set.about.desc": (
            "نرم‌افزار مدیریت ویدیو سبک، CPU-only، متن‌باز.\n"
            "هدف: جایگزینی Genetec روی سخت‌افزار معمولی."
        ),
        "set.about.version": "نسخه",
        "set.about.build": "بیلد",
    },

    "en": {
        # ============================================================
        # Common
        # ============================================================
        "app.title": "K1 VMS",
        "common.ok": "OK",
        "common.cancel": "Cancel",
        "common.yes": "Yes",
        "common.no": "No",
        "common.save": "Save",
        "common.edit": "Edit",
        "common.delete": "Delete",
        "common.close": "Close",
        "common.error": "Error",
        "common.warning": "Warning",
        "common.info": "Info",
        "common.confirm": "Confirm",
        "common.loading": "Loading…",
        "common.apply": "Apply",
        "common.refresh": "Refresh",
        "common.new": "New",

        # ============================================================
        # Header
        # ============================================================
        "header.user": "User",
        "header.search": "Search…",
        "header.no_alarms": "No Alarms",
        "header.ai_disabled": "AI Disabled",
        "header.ai_ready": "AI Ready",
        "header.ai_processing": "AI Processing",
        "header.ai_error": "AI Error",
        "header.ai_short": "AI",
        "header.online_count": "{online} / {total} Online",
        "header.offline_all": "All {total} Offline",
        "header.no_cameras": "No cameras",
        "header.alarms": "{n} Alarms",
        "header.not_recording": "Not Recording",
        "header.rec_count": "{n} REC",
        "header.rec_none": "0 / {total} REC",
        "header.rec_count_total": "{active} / {total} REC",

        # ============================================================
        # Main window
        # ============================================================
        "main.ready": "Ready",
        "main.user_dialog.title": "User",
        "main.user_dialog.msg": "User management coming in Phase 7.",
        "main.panel.no_options": "No options for {title}",

        # ============================================================
        # Main tabs
        # ============================================================
        "tab.live": "Live",
        "tab.cameras": "Cameras",
        "tab.playback": "Playback",
        "tab.dashboard": "Dashboard",

        # ============================================================
        # Cameras
        # ============================================================
        "cam.title": "Camera & NVR Management",
        "cam.btn.add_camera": "Add Camera",
        "cam.btn.add_nvr": "Add NVR",
        "cam.btn.groups": "Groups",
        "cam.btn.bulk": "Bulk Add",
        "cam.btn.apply": "Reload Streams",
        "cam.btn.edit": "Edit",
        "cam.btn.delete": "Delete",
        "cam.search.ph": "Search camera or NVR…",
        "cam.hint": (
            "Tree: NVRs and groups with their channels.\n"
            "☑ For bulk selection, check the box on each row."
        ),
        "cam.count": "{cams} camera(s) • {nvrs} NVR(s) • {groups} group(s)",

        # ============================================================
        # Live
        # ============================================================
        "live.title": "Live View",
        "live.layout": "Layout",
        "live.tab.new": "+ New Tab",
        "live.panel.cameras_nvr": "CAMERAS & NVR",
        "live.hint": (
            "• Drag NVR/Group to tile: play all\n"
            "• Right-click on NVR/Group: play/stop\n"
            "• On offline tile: 'Reconnect' button"
        ),
        "live.status.ready": "Ready",
        "live.status.connecting": "Connecting…",
        "live.cell.reconnect": "Reconnect",
        "live.cell.offline": "Offline",
        "live.cell.drop_camera": "Drop camera",
        "live.cell.cells": "Tiles: {n}",

        # ============================================================
        # NVR Dialog
        # ============================================================
        "nvr.title.add": "Add NVR",
        "nvr.title.edit": "Edit NVR: {name}",
        "nvr.group.connection": "Connection",
        "nvr.name": "Device name:",
        "nvr.name.ph": "e.g. Floor 1 NVR",
        "nvr.folder": "Recording folder:",
        "nvr.folder.ph": "e.g. parkings or negahbani",
        "nvr.folder.hint": "Only A-Z, 0-9, _ and - are allowed.",
        "nvr.record": "Record channels:",
        "nvr.record.cb": "Record all channels of this NVR?",
        "nvr.record.hint": "Default: OFF — can be changed per-camera later.",
        "nvr.brand": "Brand:",
        "nvr.brand.auto": "Auto detect",
        "nvr.ip": "IP address:",
        "nvr.port": "Ports:",
        "nvr.port.hint": "Default values are usually fine.",
        "nvr.user": "Username:",
        "nvr.pass": "Password:",
        "nvr.group.manual": "Manual URL pattern (for legacy devices)",
        "nvr.manual.hint": (
            "If your device doesn't support auto-discovery, "
            "enter the exact URL here."
        ),
        "nvr.manual.main": "Main stream:",
        "nvr.manual.sub": "Sub stream:",
        "nvr.manual.vars": (
            "Vars: {user} user — {pwd} pass — {ip} addr — "
            "{port} port — {ch} channel — {stream} type"
        ),
        "nvr.discover": "Auto-discover channels",
        "nvr.channels.info": "Discovered channels — check the ones you want:",
        "nvr.channels.select_all": "Select all",
        "nvr.channels.deselect_all": "Deselect all",
        "nvr.channels.count": "{selected} of {total} selected",
        "nvr.btn.save": "Save",
        "nvr.btn.cancel": "Cancel",

        # ============================================================
        # Camera Dialog
        # ============================================================
        "camdlg.title.add": "Add Camera",
        "camdlg.title.edit": "Edit: {name}",
        "camdlg.tab.connection": "Connection",
        "camdlg.tab.streams": "Streams & Live",
        "camdlg.tab.recording": "Recording",
        "camdlg.tab.motion": "Motion",
        "camdlg.tab.ai": "AI",
        "camdlg.name": "Camera name:",
        "camdlg.folder": "Recording folder:",
        "camdlg.enabled": "Camera enabled",
        "camdlg.ip": "IP address:",
        "camdlg.port": "RTSP port:",
        "camdlg.user": "Username:",
        "camdlg.pass": "Password:",
        "camdlg.rec.continuous": "Continuous recording (24/7)",
        "camdlg.rec.motion": "Record on motion",
        "camdlg.rec.segment": "Segment length:",
        "camdlg.rec.path": "Custom path:",
        "camdlg.save": "Save",
        "camdlg.cancel": "Cancel",

        # ============================================================
        # Groups
        # ============================================================
        "grp.title.manager": "Group Manager",
        "grp.btn.new": "New Group",
        "grp.btn.edit": "Edit",
        "grp.btn.delete": "Delete",
        "grp.btn.close": "Close",
        "grp.name": "Group name:",
        "grp.color": "Color:",
        "grp.cameras": "Cameras in this group:",
        "grp.empty": "No groups yet.",
        "grp.empty.hint": "Click 'New Group' to create the first one.",
        "grp.confirm.delete": 'Delete group "{name}"?',

        # ============================================================
        # Bulk
        # ============================================================
        "bulk.header": "{n} cameras selected",
        "bulk.delete": "Delete {n} cameras",
        "bulk.cont": "Continuous recording (24/7)",
        "bulk.motion": "Record on motion",
        "bulk.enable": "Enable",
        "bulk.disable": "Disable",

        # ============================================================
        # Playback
        # ============================================================
        "pb.title": "Playback",
        "pb.today": "Today",
        "pb.yesterday": "Yesterday",
        "pb.play": "Play",
        "pb.pause": "Pause",
        "pb.export": "Export",
        "pb.live": "Live",
        "pb.no_camera": "No camera selected",
        "pb.no_recording": "No recording available",
        "pb.search": "Search recording…",
        "pb.cameras": "CAMERAS",
        "pb.layout": "Layout:",
        "pb.tile_1": "1 Tile",
        "pb.tile_2": "2 Tiles",
        "pb.tile_4": "4 Tiles",
        "pb.tile_9": "9 Tiles",
        "pb.loading_playback": "Preparing playback…",
        "pb.loading_scan": "Scanning recording dates…",
        "pb.loading_seek": "Seeking…",
        "pb.loading_timeline": "Preparing timeline…",
        "pb.select_camera_first": "Select camera, then a recording date",
        "pb.select_date": "Select a recording date",
        "pb.calendar_title": "RECORDING CALENDAR",
        "pb.info_title": "ACTIVE TILE INFO",
        "pb.segments_title": "ACTIVE TILE SEGMENTS",
        "pb.camera": "Camera",
        "pb.date": "Date",
        "pb.time": "Time",
        "pb.count": "Segments",
        "pb.no_segment": "No segments",
        "pb.segment_summary": "{n} segments • Total {h:02d}:{m:02d}",
        "pb.legend_recorded": "Recorded",
        "pb.legend_motion": "Motion",
        "pb.legend_no_motion": "No motion",
        "pb.legend_no_record": "No record",
        "pb.btn_close_cell": "Close active tile",
        "pb.btn_snapshot": "Snapshot",
        "pb.btn_prev_seg": "Previous segment",
        "pb.btn_step_back": "Step back one frame",
        "pb.btn_play_pause": "Play / Pause (Space)",
        "pb.btn_stop": "Stop",
        "pb.btn_step_fwd": "Step forward one frame",
        "pb.btn_next_seg": "Next segment",
        "pb.btn_cut": "Cut: 1st click = start, 2nd click = end",
        "pb.btn_export": "Export",
        "pb.btn_fs_cell": "Active tile — Fullscreen",
        "pb.btn_fs_app": "Whole app — Fullscreen (F11)",
        "pb.hint": (
            "• Double-click: next empty tile\n"
            "• Drag onto tile: that tile\n"
            "• Double-click on tile: single view\n"
            "• 💡 Only active tile plays"
        ),
        "pb.menu_close_cell": "Close tile",
        "pb.menu_snapshot": "Snapshot",
        "pb.menu_exit_fs": "Exit fullscreen",
        "pb.menu_fs_cell": "Fullscreen tile",
        "pb.menu_export": "Export...",
        "pb.menu_drag_hint": "Drag a camera to load",
        "pb.timeline": "Timeline",
        "pb.no_frame_snapshot": "No frame to save.",
        "pb.saved": "Saved: {name}",
        "pb.snapshot": "Snapshot",
        "pb.snapshot_failed": "Snapshot failed:\n{e}",
        "pb.cut_invalid": "End must be after start.",
        "pb.load_camera_first": "Load a camera to a tile first.",
        "pb.no_recording_today": "No recording for this day.",

        # ============================================================
        # Dashboard
        # ============================================================
        "dash.title": "Dashboard",
        "dash.system_overview": "System Overview",
        "dash.cameras_online": "Cameras Online",
        "dash.active_alarms": "Active Alarms",
        "dash.recording": "Recording",
        "dash.ai_engine": "AI Engine",
        "dash.recent_events": "RECENT EVENTS",
        "dash.no_events": "No recent events",
        "dash.system_health": "SYSTEM HEALTH",
        "dash.cpu": "CPU",
        "dash.ram": "RAM",
        "dash.storage": "Storage",
        "dash.network": "Network",

        # ============================================================
        # Rail
        # ============================================================
        "rail.dashboard": "Dashboard  (D)",
        "rail.live": "Live View  (L)",
        "rail.cameras": "Cameras  (C)",
        "rail.playback": "Playback  (P)",
        "rail.alarms": "Alarms  (A)",
        "rail.ai": "AI Analytics  (I)",
        "rail.search": "Search  (S)",
        "rail.map": "Map  (M)",
        "rail.reports": "Reports  (R)",
        "rail.settings": "Settings",
        "rail.users": "Users",
        "rail.exit": "Exit",

        # ============================================================
        # Command Bar
        # ============================================================
        "cmd.placeholder": "Type a command or search…",
        "cmd.dashboard": "Dashboard",
        "cmd.live": "Live View",
        "cmd.cameras": "Cameras",
        "cmd.playback": "Playback",
        "cmd.alarms": "Alarms",
        "cmd.ai": "AI Analytics",
        "cmd.search": "Search",
        "cmd.map": "Map",
        "cmd.reports": "Reports",
        "cmd.settings": "Settings",
        "cmd.users": "Users",
        "cmd.exit": "Exit Application",

        # ============================================================
        # Settings — General
        # ============================================================
        "set.title": "Settings",
        "set.saved_ok": "Settings saved successfully.",
        "set.save_failed": "Save failed:",
        "set.lang.saved_restart": (
            "Settings saved.\n"
            "Restart the app to apply the language change."
        ),

        # Tabs
        "set.tab.recording": "Recording",
        "set.tab.storage": "Storage",
        "set.tab.folders": "Folders",
        "set.tab.live": "Live View",
        "set.tab.appearance": "Appearance",
        "set.tab.startup": "Startup",
        "set.tab.alarms": "Alarms",
        "set.tab.notify": "Notifications",
        "set.tab.security": "Security",
        "set.tab.about": "About",

        # ============================================================
        # Recording Tab
        # ============================================================
        "set.record.title": "Recording Behavior",
        "set.record.hint": "General settings for continuous recording.",
        "set.record.enabled": "Continuous recording enabled by default",
        "set.record.segment": "Segment length:",
        "set.record.format": "Output file format:",
        "set.record.segment_hint": "Smaller segments = easier management. Larger segments = fewer files.",

        "set.record.motion_title": "Motion Recording",
        "set.record.motion_hint": "Record only when motion is detected.",
        "set.record.motion_enabled": "Enable motion recording",
        "set.record.motion_after": "Continue recording a few seconds after motion",
        "set.record.pre_buffer": "Pre-motion buffer (sec):",
        "set.record.post_buffer": "Post-motion buffer (sec):",
        "set.record.sensitivity": "Default motion sensitivity:",
        "set.record.min_area": "Min motion area (px):",

        "set.record.health_title": "Recording Health",
        "set.record.health_hint": "System behavior in special conditions.",
        "set.record.corrupted_cleanup": "Auto-delete corrupted files",
        "set.record.disk_policy": "When disk is full:",
        "set.record.disk_policy.delete": "Delete oldest",
        "set.record.disk_policy.stop": "Stop recording",
        "set.record.disk_policy.rotate": "Auto rotate",

        # ============================================================
        # Storage Tab
        # ============================================================
        "set.storage.title": "Storage Status",
        "set.storage.hint": "Current disk usage and recording file info.",
        "set.storage.disk_used": "Disk usage",
        "set.storage.rec_size": "Recordings size",
        "set.storage.file_count": "File count",
        "set.storage.oldest": "Oldest file",
        "set.storage.newest": "Newest file",

        "set.storage.policy_title": "Retention Policy",
        "set.storage.policy_hint": "Define how long and how much to keep.",
        "set.storage.auto_cleanup": "Enable automatic cleanup",
        "set.storage.keep_days": "Keep recordings for:",
        "set.storage.days": "days",
        "set.storage.max_percent": "Max disk usage percent:",
        "set.storage.of_disk": "percent of disk",
        "set.storage.max_gb": "Or max size:",
        "set.storage.unlimited": "Unlimited",
        "set.storage.gb_or_unlimited": "(0 = unlimited)",
        "set.storage.quota_hint": (
            "• If percent is set: when disk usage exceeds, oldest recordings "
            "are deleted.\n"
            "• If size is set: total recording files never exceed this size.\n"
            "• 0 = no limit."
        ),
        "set.storage.cleanup_interval": "Cleanup interval:",
        "set.storage.hours": "hours",
        "set.storage.cleanup_hour": "Daily cleanup hour:",
        "set.storage.snapshots_days": "Snapshot retention:",
        "set.storage.exports_days": "Export retention:",

        # Backup
        "set.backup.title": "Backup",
        "set.backup.hint": "Automatic backup of recordings to another path.",
        "set.backup.enabled": "Enable automatic backup",
        "set.backup.path": "Backup path:",
        "set.backup.interval": "Backup interval:",
        "set.backup.keep_days": "Keep backup versions (days):",
        "set.backup.browse": "Browse",

        "set.storage.cleanup_now": "Cleanup Now",
        "set.cleanup_done": "✅ Cleanup complete.",
        "set.cleanup_deleted": "Files deleted",
        "set.cleanup_freed": "Freed (MB)",
        "set.cleanup_failed": "Cleanup error:",

        # ============================================================
        # Folders Tab
        # ============================================================
        "set.folders.title": "Recording Folder Structure",
        "set.folders.hint": "How recording files are arranged on disk.",
        "set.folders.by_camera": "Separate folder per camera",
        "set.folders.by_day": "Subfolder per day",
        "set.folders.by_hour": "Subfolder per hour",
        "set.folders.use_nvr_name": "Use NVR name in path",
        "set.folders.pattern": "Custom name pattern:",
        "set.folders.pattern_ph": "Empty = default",
        "set.folders.incident_lock": "Protect locked incidents",
        "set.folders.preview": "Path preview:",

        # ============================================================
        # Live Tab
        # ============================================================
        "set.live.title": "Live View Settings",
        "set.live.hint": "Live display and performance parameters.",
        "set.live.default_layout": "Default layout:",
        "set.live.grid_fps": "Grid display FPS:",
        "set.live.single_fps": "Single display FPS:",
        "set.live.max_readers": "Max concurrent cameras:",
        "set.live.auto_reconnect": "Auto-reconnect on failure",
        "set.live.reconnect_delay": "Reconnect delay:",
        "set.live.focus_mode": "Focus mode (pause others in single)",
        "set.live.transport": "Default transport:",
        "set.live.transport.auto": "Auto (TCP → UDP)",
        "set.live.transport.tcp": "TCP (stable)",
        "set.live.transport.udp": "UDP (fast)",
        "set.live.overlay_title": "Overlays on video",
        "set.live.show_timestamp": "Show timestamp",
        "set.live.show_camera_name": "Show camera name",
        "set.live.show_rec_indicator": "Show recording indicator",
        "set.live.show_motion_indicator": "Show motion indicator",

        # ============================================================
        # Appearance Tab
        # ============================================================
        "set.appear.title": "Appearance",
        "set.appear.hint": "Customize the general look of the app.",
        "set.appear.theme": "Theme:",
        "set.appear.dark": "Dark",
        "set.appear.light": "Light",
        "set.appear.font_size": "Font size:",
        "set.appear.font.small": "Small",
        "set.appear.font.medium": "Medium",
        "set.appear.font.large": "Large",
        "set.appear.compact": "Compact mode",
        "set.appear.always_on_top": "Always on top",
        "set.appear.start_minimized": "Start minimized",
        "set.appear.remember_geometry": "Remember window geometry",
        "set.appear.sidebar_width": "Sidebar width (px):",

        "set.lang.title": "Language",
        "set.lang.hint": "Select UI language.",
        "set.lang.note": "⚠ App must be restarted to apply the language change.",

        # ============================================================
        # Startup Tab
        # ============================================================
        "set.startup.title": "Startup Settings",
        "set.startup.hint": "App behavior at Windows startup.",
        "set.startup.autostart": "Run at Windows startup",
        "set.startup.mediamtx": "Auto-start MediaMTX",
        "set.startup.record": "Auto-start recording",
        "set.startup.restore_tab": "Restore last tab",
        "set.startup.restore_layout": "Restore last layout",

        # ============================================================
        # Alarms Tab
        # ============================================================
        "set.alarm.title": "Alarms & Sound",
        "set.alarm.hint": "How alarms are announced.",
        "set.alarm.sound": "Enable alarm sound",
        "set.alarm.volume": "Volume:",
        "set.alarm.duration": "Alarm duration:",
        "set.alarm.cooldown": "Cooldown between alarms:",
        "set.alarm.desktop": "Windows desktop notification",

        # ============================================================
        # Notifications Tab
        # ============================================================
        "set.notify.title": "Messenger Notifications",
        "set.notify.hint": "Send alerts via email and messengers.",
        "set.notify.events_title": "Notification Events",
        "set.notify.events.hint": "Which events trigger notifications?",
        "set.notify.event.motion": "Motion detected",
        "set.notify.event.camera_offline": "Camera offline",
        "set.notify.event.camera_online": "Camera online",
        "set.notify.event.recording_start": "Recording start",
        "set.notify.event.recording_stop": "Recording stop",
        "set.notify.event.storage_low": "Low disk space",
        "set.notify.event.login_failed": "Failed login",
        "set.notify.event.system_start": "App start",
        "set.notify.event.system_stop": "App shutdown",

        "set.notify.email.title": "Email (SMTP)",
        "set.notify.email.hint": "Send alerts via email.",
        "set.notify.email.enabled": "Enable email notifications",
        "set.notify.email.smtp": "SMTP server:",
        "set.notify.email.port": "Port:",
        "set.notify.email.user": "Username (email):",
        "set.notify.email.pass": "Password:",
        "set.notify.email.to": "Send to:",
        "set.notify.email.tls": "Use STARTTLS",

        "set.notify.telegram.title": "Telegram",
        "set.notify.telegram.hint": "Via Telegram bot.",
        "set.notify.telegram.enabled": "Enable Telegram",
        "set.notify.telegram.token": "Bot token:",
        "set.notify.telegram.chat": "Chat ID:",

        "set.notify.bale.title": "Bale",
        "set.notify.bale.hint": "Bale messenger (Telegram-like).",
        "set.notify.bale.enabled": "Enable Bale",
        "set.notify.bale.token": "Bot token:",
        "set.notify.bale.chat": "Chat ID:",

        "set.notify.eitaa.title": "Eitaa",
        "set.notify.eitaa.hint": "Eitaa messenger.",
        "set.notify.eitaa.enabled": "Enable Eitaa",
        "set.notify.eitaa.token": "Bot token:",
        "set.notify.eitaa.chat": "Chat ID:",

        "set.notify.rubika.title": "Rubika",
        "set.notify.rubika.hint": "Rubika messenger.",
        "set.notify.rubika.enabled": "Enable Rubika",
        "set.notify.rubika.token": "Bot token:",
        "set.notify.rubika.chat": "Chat ID:",

        "set.notify.test_all": "🧪  Test All Channels",
        "set.notify.test_done": "Test results:",
        "set.notify.test_ok": "✓ Sent",
        "set.notify.test_fail": "✗ Failed",
        "set.notify.test_empty": "No channels enabled.",

        # ============================================================
        # Security Tab
        # ============================================================
        "set.sec.title": "Login Security",
        "set.sec.hint": "Protection against failed login attempts.",
        "set.sec.max_attempts": "Max failed attempts:",
        "set.sec.lock_duration": "Account lock duration:",
        "set.sec.password_change_days": "Force password change every ... days (0=off):",

        # ============================================================
        # AI Tab
        # ============================================================
        "set.ai.title": "AI Analytics",
        "set.ai.hint": "Image analysis settings.",
        "set.ai.enabled": "Enable AI",
        "set.ai.confidence": "Confidence threshold:",
        "set.ai.detect_person": "Detect person",
        "set.ai.detect_car": "Detect car",
        "set.ai.detect_bike": "Detect bike",

        # ============================================================
        # About Tab
        # ============================================================
        "set.about.desc": (
            "Lightweight, CPU-only, open-source VMS.\n"
            "Goal: replace Genetec on commodity hardware."
        ),
        "set.about.version": "Version",
        "set.about.build": "Build",
    },
}


_current_lang: str = "fa"


def set_language(lang: str) -> None:
    global _current_lang
    if lang in _TRANSLATIONS:
        _current_lang = lang
    print(f"[i18n] language = {_current_lang}")


def get_language() -> str:
    return _current_lang


def t(key: str, **kwargs) -> str:
    lang_dict = _TRANSLATIONS.get(_current_lang) or _TRANSLATIONS["fa"]
    text = lang_dict.get(key) or _TRANSLATIONS["fa"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text